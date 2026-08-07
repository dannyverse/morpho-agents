import ast
import unittest
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from execution_size_normalizer import (
    NormalizationStatus,
    normalize_execution_size,
)
from margin_admission import (
    AccountEnvironment,
    AccountNormalizationStatus,
    AccountSnapshotV1,
    AccountSource,
    AdmissionDecision,
    AdmissionPolicyV1,
    CandidateOrderV1,
    CandidateSizeStatus,
    CycleContextV1,
    MarginMode,
    evaluate_margin_admission,
)


D = Decimal
UTC = timezone.utc
BASE_TIME = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


def _load_production_execution_functions():
    source_path = Path(__file__).resolve().parent / "execution_agent.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function_names = {
        "_attempt_live_execution",
        "_refresh_cycle_context",
        "_record_admission_result",
        "_release_candidate_reservation",
    }
    function_nodes = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in function_names
        )
    ]
    if {node.name for node in function_nodes} != function_names:
        raise AssertionError("production execution functions are missing")

    namespace = {
        "AdmissionDecision": AdmissionDecision,
        "CycleContextV1": CycleContextV1,
        "Decimal": Decimal,
        "replace": replace,
    }
    exec(
        compile(
            ast.Module(body=function_nodes, type_ignores=[]),
            filename=str(source_path),
            mode="exec",
        ),
        namespace,
    )
    return namespace


production_execution_functions = _load_production_execution_functions()
production_live_execution_boundary = production_execution_functions[
    "_attempt_live_execution"
]
production_refresh_cycle_context = production_execution_functions[
    "_refresh_cycle_context"
]
production_record_admission_result = production_execution_functions[
    "_record_admission_result"
]
production_release_candidate_reservation = production_execution_functions[
    "_release_candidate_reservation"
]


@dataclass(frozen=True)
class RawCandidate:
    candidate_id: str
    cycle_id: str
    asset: str
    direction: str
    raw_size: Decimal
    reference_price: Decimal
    created_at: datetime


class ExecutionAgentMarginBoundaryHarness:
    """Executable specification of the future execution-agent boundary."""

    def __init__(
        self,
        *,
        context,
        policy,
        metadata_provider,
        account_provider,
        admission,
        authority,
        workflow,
        persistence,
    ):
        self.context = context
        self.policy = policy
        self.metadata_provider = metadata_provider
        self.account_provider = account_provider
        self.admission = admission
        self.authority = authority
        self.workflow = workflow
        self.persistence = persistence
        self.execution_openings_blocked = False
        self.block_reason = None
        self.reservation_events = []

    def process(self, raw_candidate):
        if self.execution_openings_blocked:
            outcome = {
                "status": "BLOCKED",
                "reason": self.block_reason,
                "candidate_id": raw_candidate.candidate_id,
            }
            self.persistence(outcome)
            return outcome

        size_decimals = self.metadata_provider(raw_candidate.asset)
        normalization = normalize_execution_size(
            raw_size=raw_candidate.raw_size,
            size_decimals=size_decimals,
        )

        if normalization.status is not NormalizationStatus.NORMALIZED:
            outcome = {
                "status": "BLOCKED",
                "reason": normalization.reason_code.value,
                "candidate_id": raw_candidate.candidate_id,
            }
            self.persistence(outcome)
            return outcome

        snapshot = self.account_provider()
        requested_notional = (
            normalization.normalized_size
            * raw_candidate.reference_price
        )
        candidate_order = CandidateOrderV1(
            schema_version="1.0",
            candidate_id=raw_candidate.candidate_id,
            cycle_id=raw_candidate.cycle_id,
            created_at=raw_candidate.created_at,
            asset=raw_candidate.asset,
            direction=raw_candidate.direction,
            requested_size=normalization.normalized_size,
            reference_price=raw_candidate.reference_price,
            reference_price_timestamp=raw_candidate.created_at,
            requested_notional=requested_notional,
            margin_mode=MarginMode.CROSS,
            reduce_only=False,
            size_normalization_status=CandidateSizeStatus.NORMALIZED,
        )

        admission_result = self.admission(
            account_snapshot=snapshot,
            candidate_order=candidate_order,
            cycle_context=self.context,
            policy=self.policy,
        )

        if admission_result.decision is AdmissionDecision.ACCOUNT_UNKNOWN:
            self.execution_openings_blocked = True
            self.block_reason = AdmissionDecision.ACCOUNT_UNKNOWN.value

        if admission_result.decision is AdmissionDecision.STALE_DATA:
            self.execution_openings_blocked = True
            self.block_reason = AdmissionDecision.STALE_DATA.value

        if admission_result.decision is not AdmissionDecision.ADMITTED:
            outcome = {
                "status": "BLOCKED",
                "reason": admission_result.decision.value,
                "candidate_id": raw_candidate.candidate_id,
            }
            self.persistence(outcome)
            return outcome

        reservation_amount = admission_result.reservation_amount
        self.context = replace(
            self.context,
            reserved_capacity=(
                self.context.reserved_capacity
                + reservation_amount
            ),
            pending_candidate_ids=(
                self.context.pending_candidate_ids
                + (raw_candidate.candidate_id,)
            ),
        )
        self.reservation_events.append(
            ("RESERVED", raw_candidate.candidate_id, reservation_amount)
        )

        if not self.authority():
            self.context = replace(
                self.context,
                reserved_capacity=(
                    self.context.reserved_capacity
                    - reservation_amount
                ),
                pending_candidate_ids=tuple(
                    candidate_id
                    for candidate_id in self.context.pending_candidate_ids
                    if candidate_id != raw_candidate.candidate_id
                ),
            )
            self.reservation_events.append(
                ("RELEASED", raw_candidate.candidate_id, reservation_amount)
            )
            outcome = {
                "status": "BLOCKED",
                "reason": "LIVE_EXECUTION_NOT_AUTHORIZED",
                "candidate_id": raw_candidate.candidate_id,
            }
            self.persistence(outcome)
            return outcome

        workflow_result = self.workflow(
            asset=raw_candidate.asset,
            direction=raw_candidate.direction,
            position_size=normalization.normalized_size,
        )
        outcome = {
            "status": "EXECUTION_ATTEMPTED",
            "reason": "ADMITTED_AND_AUTHORIZED",
            "candidate_id": raw_candidate.candidate_id,
            "workflow_result": workflow_result,
        }
        self.persistence(outcome)
        return outcome


class ExecutionAgentMarginIntegrationContractTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = AccountSnapshotV1(
            schema_version="1.0",
            snapshot_id="snapshot-1",
            account_address="0x1111111111111111111111111111111111111111",
            environment=AccountEnvironment.MAINNET,
            source=AccountSource.HYPERLIQUID_CLEARINGHOUSE_STATE,
            exchange_timestamp=BASE_TIME,
            received_at=BASE_TIME + timedelta(seconds=1),
            account_value=D("200"),
            total_margin_used=D("20"),
            withdrawable=D("100"),
            asset_positions=(),
            normalization_status=AccountNormalizationStatus.VALID,
            normalization_errors=(),
        )
        self.context = CycleContextV1(
            schema_version="1.0",
            cycle_id="cycle-1",
            account_snapshot_id="snapshot-1",
            account_refresh_sequence=1,
            reserved_capacity=D("10"),
            evaluated_candidates=0,
            pending_candidate_ids=(),
            execution_blocked=False,
            block_reason=None,
            created_at=BASE_TIME + timedelta(seconds=1),
            updated_at=BASE_TIME + timedelta(seconds=2),
        )
        self.policy = AdmissionPolicyV1(
            schema_version="1.0",
            max_snapshot_age_seconds=D("60"),
            absolute_reserve=D("20"),
            safety_buffer=D("5"),
            supported_margin_mode=MarginMode.CROSS,
            notional_tolerance=D("0.000001"),
        )
        self.candidate = RawCandidate(
            candidate_id="candidate-1",
            cycle_id="cycle-1",
            asset="BTC",
            direction="LONG",
            raw_size=D("1"),
            reference_price=D("30"),
            created_at=BASE_TIME + timedelta(seconds=2),
        )
        self.metadata_provider = Mock(return_value=3)
        self.account_provider = Mock(return_value=self.snapshot)
        self.admission = Mock(wraps=evaluate_margin_admission)
        self.authority = Mock(return_value=True)
        self.workflow = Mock(return_value={"success": True})
        self.persistence = Mock()

    def make_harness(self):
        return ExecutionAgentMarginBoundaryHarness(
            context=self.context,
            policy=self.policy,
            metadata_provider=self.metadata_provider,
            account_provider=self.account_provider,
            admission=self.admission,
            authority=self.authority,
            workflow=self.workflow,
            persistence=self.persistence,
        )

    def test_invalid_normalization_skips_admission_authority_and_workflow(self):
        harness = self.make_harness()
        candidate = replace(
            self.candidate,
            raw_size=D("0.0009"),
        )

        outcome = harness.process(candidate)

        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertEqual(
            outcome["reason"],
            "SIZE_BELOW_PRECISION_QUANTUM",
        )
        self.admission.assert_not_called()
        self.authority.assert_not_called()
        self.workflow.assert_not_called()
        self.persistence.assert_called_once()

    def test_insufficient_margin_skips_authority_and_workflow(self):
        harness = self.make_harness()
        candidate = replace(
            self.candidate,
            raw_size=D("3"),
            reference_price=D("30"),
        )

        outcome = harness.process(candidate)

        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertEqual(outcome["reason"], "INSUFFICIENT_MARGIN")
        self.admission.assert_called_once()
        self.authority.assert_not_called()
        self.workflow.assert_not_called()
        self.persistence.assert_called_once()

    def test_account_unknown_blocks_later_openings(self):
        self.account_provider.return_value = None
        harness = self.make_harness()
        later_candidate = replace(
            self.candidate,
            candidate_id="candidate-2",
        )

        first = harness.process(self.candidate)
        second = harness.process(later_candidate)

        self.assertEqual(first["reason"], "ACCOUNT_UNKNOWN")
        self.assertEqual(second["reason"], "ACCOUNT_UNKNOWN")
        self.assertTrue(harness.execution_openings_blocked)
        self.admission.assert_called_once()
        self.account_provider.assert_called_once()
        self.authority.assert_not_called()
        self.workflow.assert_not_called()
        self.assertEqual(self.persistence.call_count, 2)

    def test_stale_data_blocks_later_openings(self):
        stale_context = replace(
            self.context,
            updated_at=BASE_TIME + timedelta(seconds=61),
        )
        harness = self.make_harness()
        harness.context = stale_context
        later_candidate = replace(
            self.candidate,
            candidate_id="candidate-2",
        )

        first = harness.process(self.candidate)
        second = harness.process(later_candidate)

        self.assertEqual(first["reason"], "STALE_DATA")
        self.assertEqual(second["reason"], "STALE_DATA")
        self.assertTrue(harness.execution_openings_blocked)
        self.admission.assert_called_once()
        self.account_provider.assert_called_once()
        self.authority.assert_not_called()
        self.workflow.assert_not_called()
        self.assertEqual(self.persistence.call_count, 2)

    def test_admitted_without_authority_reserves_then_releases(self):
        self.authority.return_value = False
        harness = self.make_harness()

        outcome = harness.process(self.candidate)

        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertEqual(
            outcome["reason"],
            "LIVE_EXECUTION_NOT_AUTHORIZED",
        )
        self.assertEqual(
            harness.reservation_events,
            [
                ("RESERVED", "candidate-1", D("30")),
                ("RELEASED", "candidate-1", D("30")),
            ],
        )
        self.assertEqual(harness.context.reserved_capacity, D("10"))
        self.assertEqual(harness.context.pending_candidate_ids, ())
        self.authority.assert_called_once()
        self.workflow.assert_not_called()
        self.persistence.assert_called_once()

    def test_admitted_with_authority_calls_workflow_once(self):
        self.authority.return_value = True
        harness = self.make_harness()

        outcome = harness.process(self.candidate)

        self.assertEqual(outcome["status"], "EXECUTION_ATTEMPTED")
        self.assertEqual(
            outcome["reason"],
            "ADMITTED_AND_AUTHORIZED",
        )
        self.assertEqual(
            harness.reservation_events,
            [("RESERVED", "candidate-1", D("30"))],
        )
        self.assertEqual(harness.context.reserved_capacity, D("40"))
        self.assertEqual(
            harness.context.pending_candidate_ids,
            ("candidate-1",),
        )
        self.authority.assert_called_once()
        self.workflow.assert_called_once_with(
            asset="BTC",
            direction="LONG",
            position_size=D("1.000"),
        )
        self.persistence.assert_called_once()

    def test_boundary_call_order_is_admission_authority_workflow(self):
        call_order = []
        self.admission.side_effect = lambda **kwargs: (
            call_order.append("admission")
            or evaluate_margin_admission(**kwargs)
        )
        self.authority.side_effect = lambda: (
            call_order.append("authority") or True
        )
        self.workflow.side_effect = lambda **kwargs: (
            call_order.append("workflow") or {"success": True}
        )
        harness = self.make_harness()

        harness.process(self.candidate)

        self.assertEqual(
            call_order,
            ["admission", "authority", "workflow"],
        )


class ProductionExecutionAgentControlFlowTest(unittest.TestCase):
    def setUp(self):
        self.authority = Mock(return_value=True)
        self.workflow = Mock(return_value={"success": True})
        self.workflow_kwargs = {
            "asset": "BTC",
            "direction": "LONG",
            "position_size": D("1"),
        }

    def attempt(self, *, execution_decision="APPROVED", admission_decision):
        admission_result = (
            None
            if admission_decision is None
            else Mock(decision=admission_decision)
        )
        return production_live_execution_boundary(
            execution_decision=execution_decision,
            admission_result=admission_result,
            authority=self.authority,
            workflow=self.workflow,
            workflow_kwargs=self.workflow_kwargs,
        )

    def test_production_admitted_and_authorized_calls_workflow_once(self):
        status, result = self.attempt(
            admission_decision=AdmissionDecision.ADMITTED
        )

        self.assertEqual(status, "EXECUTION_ATTEMPTED")
        self.assertEqual(result, {"success": True})
        self.authority.assert_called_once_with()
        self.workflow.assert_called_once_with(**self.workflow_kwargs)

    def test_production_insufficient_margin_skips_authority_and_workflow(self):
        status, result = self.attempt(
            admission_decision=AdmissionDecision.INSUFFICIENT_MARGIN
        )

        self.assertEqual(status, "SKIPPED")
        self.assertIsNone(result)
        self.authority.assert_not_called()
        self.workflow.assert_not_called()

    def test_production_unknown_and_stale_skip_authority_and_workflow(self):
        for decision in (
            AdmissionDecision.ACCOUNT_UNKNOWN,
            AdmissionDecision.STALE_DATA,
        ):
            with self.subTest(decision=decision):
                self.authority.reset_mock()
                self.workflow.reset_mock()

                status, result = self.attempt(admission_decision=decision)

                self.assertEqual(status, "SKIPPED")
                self.assertIsNone(result)
                self.authority.assert_not_called()
                self.workflow.assert_not_called()

    def test_production_invalid_market_data_skips_live_execution(self):
        status, result = self.attempt(
            execution_decision="REJECTED",
            admission_decision=None,
        )

        self.assertEqual(status, "SKIPPED")
        self.assertIsNone(result)
        self.authority.assert_not_called()
        self.workflow.assert_not_called()

    def test_production_valid_admission_without_authority_skips_workflow(self):
        self.authority.return_value = False

        status, result = self.attempt(
            admission_decision=AdmissionDecision.ADMITTED
        )

        self.assertEqual(status, "NOT_AUTHORIZED")
        self.assertIsNone(result)
        self.authority.assert_called_once_with()
        self.workflow.assert_not_called()


class ProductionCycleReservationLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.policy = AdmissionPolicyV1(
            schema_version="1.0",
            max_snapshot_age_seconds=D("60"),
            absolute_reserve=D("20"),
            safety_buffer=D("5"),
            supported_margin_mode=MarginMode.CROSS,
            notional_tolerance=D("0.000001"),
        )
        self.snapshot = AccountSnapshotV1(
            schema_version="1.0",
            snapshot_id="snapshot-1",
            account_address="0x1111111111111111111111111111111111111111",
            environment=AccountEnvironment.MAINNET,
            source=AccountSource.HYPERLIQUID_CLEARINGHOUSE_STATE,
            exchange_timestamp=BASE_TIME,
            received_at=BASE_TIME,
            account_value=D("200"),
            total_margin_used=D("20"),
            withdrawable=D("100"),
            asset_positions=(),
            normalization_status=AccountNormalizationStatus.VALID,
            normalization_errors=(),
        )

    def candidate(self, *, candidate_id, created_at, notional=D("50")):
        return CandidateOrderV1(
            schema_version="1.0",
            candidate_id=candidate_id,
            cycle_id="cycle-1",
            created_at=created_at,
            asset="BTC",
            direction="LONG",
            requested_size=D("1"),
            reference_price=notional,
            reference_price_timestamp=created_at,
            requested_notional=notional,
            margin_mode=MarginMode.CROSS,
            reduce_only=False,
            size_normalization_status=CandidateSizeStatus.NORMALIZED,
        )

    def evaluate_and_record(self, context, snapshot, candidate, evaluated_at):
        context = production_refresh_cycle_context(
            context,
            cycle_id="cycle-1",
            snapshot_id=snapshot.snapshot_id,
            updated_at=evaluated_at,
        )
        result = evaluate_margin_admission(
            account_snapshot=snapshot,
            candidate_order=candidate,
            cycle_context=context,
            policy=self.policy,
        )
        context = production_record_admission_result(
            context,
            admission_result=result,
            candidate_id=candidate.candidate_id,
            updated_at=evaluated_at,
        )
        return context, result

    def test_second_candidate_sees_first_candidate_reservation(self):
        authority = Mock(return_value=True)
        workflow = Mock(return_value={"success": True})
        first_time = BASE_TIME + timedelta(seconds=1)
        first_candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=first_time,
        )

        context, first_result = self.evaluate_and_record(
            None,
            self.snapshot,
            first_candidate,
            first_time,
        )
        first_status, _ = production_live_execution_boundary(
            execution_decision="APPROVED",
            admission_result=first_result,
            authority=authority,
            workflow=workflow,
            workflow_kwargs={"asset": "BTC"},
        )

        self.assertEqual(first_result.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(first_status, "EXECUTION_ATTEMPTED")
        self.assertEqual(context.reserved_capacity, D("50"))
        self.assertEqual(context.pending_candidate_ids, ("candidate-1",))
        self.assertEqual(context.evaluated_candidates, 1)

        second_time = BASE_TIME + timedelta(seconds=2)
        second_snapshot = replace(
            self.snapshot,
            snapshot_id="snapshot-2",
            exchange_timestamp=second_time,
            received_at=second_time,
        )
        second_candidate = self.candidate(
            candidate_id="candidate-2",
            created_at=second_time,
        )
        context, second_result = self.evaluate_and_record(
            context,
            second_snapshot,
            second_candidate,
            second_time,
        )
        second_status, _ = production_live_execution_boundary(
            execution_decision="REJECTED",
            admission_result=second_result,
            authority=authority,
            workflow=workflow,
            workflow_kwargs={"asset": "ETH"},
        )

        self.assertEqual(
            second_result.decision,
            AdmissionDecision.INSUFFICIENT_MARGIN,
        )
        self.assertEqual(second_result.reserved_capacity, D("50"))
        self.assertEqual(second_result.usable_capacity, D("25"))
        self.assertEqual(second_result.snapshot_id, "snapshot-2")
        self.assertEqual(second_result.account_refresh_sequence, 2)
        self.assertEqual(second_status, "SKIPPED")
        self.assertEqual(context.account_snapshot_id, "snapshot-2")
        self.assertEqual(context.account_refresh_sequence, 2)
        self.assertEqual(context.reserved_capacity, D("50"))
        self.assertEqual(context.pending_candidate_ids, ("candidate-1",))
        self.assertEqual(context.evaluated_candidates, 2)
        authority.assert_called_once_with()
        workflow.assert_called_once_with(asset="BTC")

    def test_authority_rejection_releases_candidate_reservation(self):
        evaluated_at = BASE_TIME + timedelta(seconds=1)
        candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=evaluated_at,
        )
        context, result = self.evaluate_and_record(
            None,
            self.snapshot,
            candidate,
            evaluated_at,
        )
        authority = Mock(return_value=False)
        workflow = Mock()

        status, _ = production_live_execution_boundary(
            execution_decision="APPROVED",
            admission_result=result,
            authority=authority,
            workflow=workflow,
            workflow_kwargs={"asset": "BTC"},
        )
        if status == "NOT_AUTHORIZED":
            context = production_release_candidate_reservation(
                context,
                candidate_id=candidate.candidate_id,
                reservation_amount=result.reservation_amount,
                updated_at=evaluated_at,
            )

        self.assertEqual(status, "NOT_AUTHORIZED")
        self.assertEqual(context.reserved_capacity, D("0"))
        self.assertEqual(context.pending_candidate_ids, ())
        self.assertEqual(context.evaluated_candidates, 1)
        workflow.assert_not_called()

    def test_successful_workflow_keeps_reservation_pending(self):
        evaluated_at = BASE_TIME + timedelta(seconds=1)
        candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=evaluated_at,
        )
        context, result = self.evaluate_and_record(
            None,
            self.snapshot,
            candidate,
            evaluated_at,
        )
        workflow_result = Mock(success=True, position_open=True)
        workflow = Mock(return_value=workflow_result)

        status, returned_result = production_live_execution_boundary(
            execution_decision="APPROVED",
            admission_result=result,
            authority=Mock(return_value=True),
            workflow=workflow,
            workflow_kwargs={"asset": "BTC"},
        )

        self.assertEqual(status, "EXECUTION_ATTEMPTED")
        self.assertIs(returned_result, workflow_result)
        self.assertEqual(context.reserved_capacity, D("50"))
        self.assertEqual(context.pending_candidate_ids, ("candidate-1",))
        self.assertEqual(context.evaluated_candidates, 1)
        workflow.assert_called_once_with(asset="BTC")

    def test_failed_workflow_with_open_position_keeps_reservation_pending(self):
        evaluated_at = BASE_TIME + timedelta(seconds=1)
        candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=evaluated_at,
        )
        context, result = self.evaluate_and_record(
            None,
            self.snapshot,
            candidate,
            evaluated_at,
        )
        workflow_result = Mock(success=False, position_open=True)

        status, returned_result = production_live_execution_boundary(
            execution_decision="APPROVED",
            admission_result=result,
            authority=Mock(return_value=True),
            workflow=Mock(return_value=workflow_result),
            workflow_kwargs={"asset": "BTC"},
        )

        self.assertEqual(status, "EXECUTION_ATTEMPTED")
        self.assertIs(returned_result, workflow_result)
        self.assertEqual(context.reserved_capacity, D("50"))
        self.assertEqual(context.pending_candidate_ids, ("candidate-1",))

    def test_failed_workflow_without_open_position_releases_reservation(self):
        evaluated_at = BASE_TIME + timedelta(seconds=1)
        candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=evaluated_at,
        )
        context, result = self.evaluate_and_record(
            None,
            self.snapshot,
            candidate,
            evaluated_at,
        )
        workflow_result = Mock(success=False, position_open=False)

        status, returned_result = production_live_execution_boundary(
            execution_decision="APPROVED",
            admission_result=result,
            authority=Mock(return_value=True),
            workflow=Mock(return_value=workflow_result),
            workflow_kwargs={"asset": "BTC"},
        )
        if not returned_result.success and not returned_result.position_open:
            context = production_release_candidate_reservation(
                context,
                candidate_id=candidate.candidate_id,
                reservation_amount=result.reservation_amount,
                updated_at=evaluated_at,
            )

        self.assertEqual(status, "EXECUTION_ATTEMPTED")
        self.assertEqual(context.reserved_capacity, D("0"))
        self.assertEqual(context.pending_candidate_ids, ())

    def test_released_capacity_is_available_to_later_candidate(self):
        first_time = BASE_TIME + timedelta(seconds=1)
        first_candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=first_time,
        )
        context, first_result = self.evaluate_and_record(
            None,
            self.snapshot,
            first_candidate,
            first_time,
        )
        context = production_release_candidate_reservation(
            context,
            candidate_id=first_candidate.candidate_id,
            reservation_amount=first_result.reservation_amount,
            updated_at=first_time,
        )

        second_time = BASE_TIME + timedelta(seconds=2)
        second_snapshot = replace(
            self.snapshot,
            snapshot_id="snapshot-2",
            exchange_timestamp=second_time,
            received_at=second_time,
        )
        second_candidate = self.candidate(
            candidate_id="candidate-2",
            created_at=second_time,
        )
        context, second_result = self.evaluate_and_record(
            context,
            second_snapshot,
            second_candidate,
            second_time,
        )

        self.assertEqual(second_result.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(context.reserved_capacity, D("50"))
        self.assertEqual(context.pending_candidate_ids, ("candidate-2",))
        self.assertEqual(context.evaluated_candidates, 2)

    def test_releasing_non_pending_candidate_raises(self):
        evaluated_at = BASE_TIME + timedelta(seconds=1)
        candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=evaluated_at,
        )
        context, result = self.evaluate_and_record(
            None,
            self.snapshot,
            candidate,
            evaluated_at,
        )
        context = production_release_candidate_reservation(
            context,
            candidate_id=candidate.candidate_id,
            reservation_amount=result.reservation_amount,
            updated_at=evaluated_at,
        )

        with self.assertRaisesRegex(ValueError, "not pending"):
            production_release_candidate_reservation(
                context,
                candidate_id=candidate.candidate_id,
                reservation_amount=result.reservation_amount,
                updated_at=evaluated_at,
            )

    def test_reservation_amount_exceeding_reserved_capacity_raises(self):
        evaluated_at = BASE_TIME + timedelta(seconds=1)
        candidate = self.candidate(
            candidate_id="candidate-1",
            created_at=evaluated_at,
        )
        context, _ = self.evaluate_and_record(
            None,
            self.snapshot,
            candidate,
            evaluated_at,
        )

        with self.assertRaisesRegex(ValueError, "exceeds"):
            production_release_candidate_reservation(
                context,
                candidate_id=candidate.candidate_id,
                reservation_amount=D("50.000001"),
                updated_at=evaluated_at,
            )


if __name__ == "__main__":
    unittest.main()
