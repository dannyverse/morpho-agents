import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from margin_admission import (
    AccountEnvironment,
    AccountNormalizationStatus,
    AccountSnapshotV1,
    AccountSource,
    AdmissionDecision,
    AdmissionPolicyV1,
    AdmissionReasonCode,
    CandidateOrderV1,
    CandidateSizeStatus,
    CycleContextV1,
    MarginMode,
    evaluate_margin_admission,
)


D = Decimal
UTC = timezone.utc
BASE_TIME = datetime(2026, 8, 4, 12, 0, 0, tzinfo=UTC)


class MarginAdmissionContractTest(unittest.TestCase):
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
        self.candidate = CandidateOrderV1(
            schema_version="1.0",
            candidate_id="candidate-1",
            cycle_id="cycle-1",
            created_at=BASE_TIME + timedelta(seconds=2),
            asset="BTC",
            direction="LONG",
            requested_size=D("1"),
            reference_price=D("30"),
            reference_price_timestamp=BASE_TIME + timedelta(seconds=1),
            requested_notional=D("30"),
            margin_mode=MarginMode.CROSS,
            reduce_only=False,
            size_normalization_status=CandidateSizeStatus.NORMALIZED,
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

    def evaluate(
        self,
        snapshot=None,
        candidate=None,
        context=None,
        policy=None,
    ):
        return evaluate_margin_admission(
            account_snapshot=self.snapshot if snapshot is None else snapshot,
            candidate_order=self.candidate if candidate is None else candidate,
            cycle_context=self.context if context is None else context,
            policy=self.policy if policy is None else policy,
        )

    def test_admits_when_capacity_is_sufficient(self):
        result = self.evaluate()

        self.assertEqual(result.schema_version, "1.0")
        self.assertEqual(result.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.CAPACITY_SUFFICIENT,
        )
        self.assertEqual(result.candidate_id, "candidate-1")
        self.assertEqual(result.cycle_id, "cycle-1")
        self.assertEqual(result.snapshot_id, "snapshot-1")
        self.assertEqual(result.account_refresh_sequence, 1)
        self.assertEqual(result.withdrawable, D("100"))
        self.assertEqual(result.reserved_capacity, D("10"))
        self.assertEqual(result.absolute_reserve, D("20"))
        self.assertEqual(result.safety_buffer, D("5"))
        self.assertEqual(result.usable_capacity, D("65"))
        self.assertEqual(result.candidate_notional, D("30"))
        self.assertEqual(result.candidate_requirement, D("30"))
        self.assertEqual(result.reservation_amount, D("30"))
        self.assertEqual(result.remaining_capacity, D("35"))
        self.assertEqual(result.validation_errors, ())

    def test_capacity_formula_uses_only_confirmed_v1_terms(self):
        result = self.evaluate()

        expected = (
            self.snapshot.withdrawable
            - self.policy.absolute_reserve
            - self.policy.safety_buffer
            - self.context.reserved_capacity
        )

        self.assertEqual(result.usable_capacity, expected)
        self.assertEqual(result.usable_capacity, D("65"))

    def test_candidate_requirement_equals_requested_notional(self):
        candidate = replace(
            self.candidate,
            requested_size=D("2"),
            reference_price=D("20"),
            requested_notional=D("40"),
        )

        result = self.evaluate(candidate=candidate)

        self.assertEqual(result.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(result.candidate_requirement, D("40"))
        self.assertEqual(result.reservation_amount, D("40"))

    def test_total_margin_used_is_not_subtracted_twice(self):
        first = self.evaluate()
        snapshot = replace(
            self.snapshot,
            total_margin_used=D("90"),
        )

        second = self.evaluate(snapshot=snapshot)

        self.assertEqual(first.usable_capacity, D("65"))
        self.assertEqual(second.usable_capacity, D("65"))
        self.assertEqual(second.decision, AdmissionDecision.ADMITTED)

    def test_exact_capacity_boundary_is_admitted(self):
        candidate = replace(
            self.candidate,
            requested_size=D("1"),
            reference_price=D("65"),
            requested_notional=D("65"),
        )

        result = self.evaluate(candidate=candidate)

        self.assertEqual(result.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(result.candidate_requirement, D("65"))
        self.assertEqual(result.reservation_amount, D("65"))
        self.assertEqual(result.remaining_capacity, D("0"))

    def test_rejects_when_capacity_is_insufficient(self):
        candidate = replace(
            self.candidate,
            requested_size=D("1"),
            reference_price=D("65.01"),
            requested_notional=D("65.01"),
        )

        result = self.evaluate(candidate=candidate)

        self.assertEqual(
            result.decision,
            AdmissionDecision.INSUFFICIENT_MARGIN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.CAPACITY_BELOW_REQUIREMENT,
        )
        self.assertEqual(result.usable_capacity, D("65"))
        self.assertEqual(result.candidate_requirement, D("65.01"))
        self.assertEqual(result.reservation_amount, D("0"))
        self.assertEqual(result.remaining_capacity, D("-0.01"))
        self.assertEqual(result.validation_errors, ())

    def test_negative_usable_capacity_is_not_clamped(self):
        context = replace(
            self.context,
            reserved_capacity=D("80"),
        )

        result = self.evaluate(context=context)

        self.assertEqual(result.usable_capacity, D("-5"))
        self.assertEqual(
            result.decision,
            AdmissionDecision.INSUFFICIENT_MARGIN,
        )
        self.assertEqual(result.reservation_amount, D("0"))

    def test_existing_cycle_reservations_reduce_capacity(self):
        no_reservations = replace(
            self.context,
            reserved_capacity=D("0"),
        )
        with_reservations = replace(
            self.context,
            reserved_capacity=D("50"),
        )

        admitted = self.evaluate(context=no_reservations)
        rejected = self.evaluate(context=with_reservations)

        self.assertEqual(admitted.usable_capacity, D("75"))
        self.assertEqual(admitted.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(rejected.usable_capacity, D("25"))
        self.assertEqual(
            rejected.decision,
            AdmissionDecision.INSUFFICIENT_MARGIN,
        )


class MarginAdmissionAccountValidationTest(
    MarginAdmissionContractTest
):
    def test_missing_snapshot_returns_account_unknown(self):
        result = evaluate_margin_admission(
            account_snapshot=None,
            candidate_order=self.candidate,
            cycle_context=self.context,
            policy=self.policy,
        )

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.SNAPSHOT_MISSING,
        )
        self.assertEqual(result.reservation_amount, D("0"))
        self.assertIsNone(result.usable_capacity)
        self.assertIsNone(result.remaining_capacity)
        self.assertTrue(result.validation_errors)

    def test_invalid_normalized_snapshot_returns_account_unknown(self):
        snapshot = replace(
            self.snapshot,
            normalization_status=AccountNormalizationStatus.INVALID,
            normalization_errors=("withdrawable is missing",),
        )

        result = self.evaluate(snapshot=snapshot)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.SNAPSHOT_INVALID,
        )
        self.assertEqual(result.reservation_amount, D("0"))
        self.assertTrue(result.validation_errors)

    def test_negative_withdrawable_returns_account_unknown(self):
        snapshot = replace(
            self.snapshot,
            withdrawable=D("-1"),
        )

        result = self.evaluate(snapshot=snapshot)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.SNAPSHOT_INVALID,
        )
        self.assertEqual(result.reservation_amount, D("0"))

    def test_non_finite_account_value_returns_account_unknown(self):
        snapshot = replace(
            self.snapshot,
            account_value=D("NaN"),
        )

        result = self.evaluate(snapshot=snapshot)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.SNAPSHOT_INVALID,
        )

    def test_non_finite_margin_used_returns_account_unknown(self):
        snapshot = replace(
            self.snapshot,
            total_margin_used=D("Infinity"),
        )

        result = self.evaluate(snapshot=snapshot)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )

    def test_non_finite_withdrawable_returns_account_unknown(self):
        snapshot = replace(
            self.snapshot,
            withdrawable=D("Infinity"),
        )

        result = self.evaluate(snapshot=snapshot)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )

    def test_stale_snapshot_returns_stale_data(self):
        context = replace(
            self.context,
            updated_at=BASE_TIME + timedelta(seconds=61),
        )

        result = self.evaluate(context=context)

        self.assertEqual(
            result.decision,
            AdmissionDecision.STALE_DATA,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.SNAPSHOT_TOO_OLD,
        )
        self.assertEqual(result.snapshot_age_seconds, D("61"))
        self.assertEqual(result.reservation_amount, D("0"))
        self.assertIsNone(result.remaining_capacity)
        self.assertEqual(result.validation_errors, ())

    def test_snapshot_at_staleness_boundary_is_accepted(self):
        context = replace(
            self.context,
            updated_at=BASE_TIME + timedelta(seconds=60),
        )

        result = self.evaluate(context=context)

        self.assertEqual(result.decision, AdmissionDecision.ADMITTED)
        self.assertEqual(result.snapshot_age_seconds, D("60"))


class MarginAdmissionCandidateValidationTest(
    MarginAdmissionContractTest
):
    def assert_invalid_candidate(self, candidate, expected_reason):
        result = self.evaluate(candidate=candidate)

        self.assertEqual(
            result.decision,
            AdmissionDecision.INVALID_CANDIDATE,
        )
        self.assertEqual(result.reason_code, expected_reason)
        self.assertEqual(result.reservation_amount, D("0"))
        self.assertTrue(result.validation_errors)

    def test_zero_size_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, requested_size=D("0")),
            AdmissionReasonCode.INVALID_SIZE,
        )

    def test_negative_size_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, requested_size=D("-1")),
            AdmissionReasonCode.INVALID_SIZE,
        )

    def test_non_finite_size_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, requested_size=D("NaN")),
            AdmissionReasonCode.INVALID_SIZE,
        )

    def test_zero_price_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, reference_price=D("0")),
            AdmissionReasonCode.INVALID_PRICE,
        )

    def test_non_finite_price_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, reference_price=D("Infinity")),
            AdmissionReasonCode.INVALID_PRICE,
        )

    def test_zero_notional_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, requested_notional=D("0")),
            AdmissionReasonCode.INVALID_NOTIONAL,
        )

    def test_non_finite_notional_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, requested_notional=D("NaN")),
            AdmissionReasonCode.INVALID_NOTIONAL,
        )

    def test_notional_mismatch_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, requested_notional=D("31")),
            AdmissionReasonCode.NOTIONAL_MISMATCH,
        )

    def test_cycle_id_mismatch_is_invalid(self):
        self.assert_invalid_candidate(
            replace(self.candidate, cycle_id="different-cycle"),
            AdmissionReasonCode.CYCLE_ID_MISMATCH,
        )

    def test_snapshot_id_mismatch_is_invalid(self):
        context = replace(
            self.context,
            account_snapshot_id="different-snapshot",
        )

        result = self.evaluate(context=context)

        self.assertEqual(
            result.decision,
            AdmissionDecision.INVALID_CANDIDATE,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.SNAPSHOT_ID_MISMATCH,
        )
        self.assertEqual(result.reservation_amount, D("0"))

    def test_unnormalized_size_is_invalid(self):
        self.assert_invalid_candidate(
            replace(
                self.candidate,
                size_normalization_status=(
                    CandidateSizeStatus.UNNORMALIZED
                ),
            ),
            AdmissionReasonCode.SIZE_NOT_NORMALIZED,
        )

    def test_isolated_margin_mode_is_not_supported(self):
        candidate = replace(
            self.candidate,
            margin_mode=MarginMode.ISOLATED,
        )

        result = self.evaluate(candidate=candidate)

        self.assertEqual(
            result.decision,
            AdmissionDecision.UNSUPPORTED_MARGIN_MODE,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.MARGIN_MODE_NOT_SUPPORTED,
        )
        self.assertEqual(result.reservation_amount, D("0"))
        self.assertEqual(result.validation_errors, ())


class MarginAdmissionPolicyAndContextValidationTest(
    MarginAdmissionContractTest
):
    def test_negative_reserved_capacity_is_invalid_context(self):
        context = replace(
            self.context,
            reserved_capacity=D("-1"),
        )

        result = self.evaluate(context=context)

        self.assertEqual(
            result.decision,
            AdmissionDecision.INVALID_CANDIDATE,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.INVALID_CYCLE_CONTEXT,
        )
        self.assertEqual(result.reservation_amount, D("0"))

    def test_negative_absolute_reserve_is_invalid_policy(self):
        policy = replace(
            self.policy,
            absolute_reserve=D("-1"),
        )

        result = self.evaluate(policy=policy)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.INVALID_POLICY,
        )
        self.assertEqual(result.reservation_amount, D("0"))

    def test_negative_safety_buffer_is_invalid_policy(self):
        policy = replace(
            self.policy,
            safety_buffer=D("-1"),
        )

        result = self.evaluate(policy=policy)

        self.assertEqual(
            result.decision,
            AdmissionDecision.ACCOUNT_UNKNOWN,
        )
        self.assertEqual(
            result.reason_code,
            AdmissionReasonCode.INVALID_POLICY,
        )


class MarginAdmissionInvariantTest(MarginAdmissionContractTest):
    def test_only_admitted_result_has_positive_reservation(self):
        admitted = self.evaluate()
        insufficient = self.evaluate(
            candidate=replace(
                self.candidate,
                requested_size=D("3"),
                reference_price=D("30"),
                requested_notional=D("90"),
            )
        )
        stale = self.evaluate(
            context=replace(
                self.context,
                updated_at=BASE_TIME + timedelta(seconds=61),
            )
        )

        self.assertGreater(admitted.reservation_amount, D("0"))
        self.assertEqual(insufficient.reservation_amount, D("0"))
        self.assertEqual(stale.reservation_amount, D("0"))

    def test_remaining_capacity_matches_capacity_minus_requirement(self):
        result = self.evaluate()

        self.assertEqual(
            result.remaining_capacity,
            result.usable_capacity - result.candidate_requirement,
        )

    def test_result_is_deterministic(self):
        first = self.evaluate()
        second = self.evaluate()

        self.assertEqual(first, second)

    def test_inputs_are_not_mutated(self):
        snapshot_before = self.snapshot
        candidate_before = self.candidate
        context_before = self.context
        policy_before = self.policy

        self.evaluate()

        self.assertEqual(self.snapshot, snapshot_before)
        self.assertEqual(self.candidate, candidate_before)
        self.assertEqual(self.context, context_before)
        self.assertEqual(self.policy, policy_before)

    def test_result_correlates_all_input_identifiers(self):
        result = self.evaluate()

        self.assertEqual(result.candidate_id, self.candidate.candidate_id)
        self.assertEqual(result.cycle_id, self.context.cycle_id)
        self.assertEqual(result.snapshot_id, self.snapshot.snapshot_id)
        self.assertEqual(
            result.account_refresh_sequence,
            self.context.account_refresh_sequence,
        )


if __name__ == "__main__":
    unittest.main()
