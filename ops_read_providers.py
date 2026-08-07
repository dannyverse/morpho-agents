import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class Availability(Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ProviderResult:
    availability: Availability
    observed_at: str | None
    data: Any
    errors: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return self.availability == Availability.AVAILABLE


class OpsReadProviders:
    def __init__(
        self,
        *,
        db_path: str | Path = "trading_system.db",
        runtime_state_path: str | Path = "runtime_state.json",
        kill_switch_path: str | Path = "kill_switch_state.json",
        portfolio_health_path: str | Path = "portfolio_health_state.json",
        now: Callable[[], datetime] | None = None,
    ):
        self.db_path = Path(db_path)
        self.runtime_state_path = Path(runtime_state_path)
        self.kill_switch_path = Path(kill_switch_path)
        self.portfolio_health_path = Path(portfolio_health_path)
        self._now = now or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _unavailable(*errors: str) -> ProviderResult:
        return ProviderResult(
            availability=Availability.UNAVAILABLE,
            observed_at=None,
            data=None,
            errors=tuple(errors),
        )

    @staticmethod
    def _read_json(
        path: Path,
        *,
        required_fields: tuple[str, ...],
        observed_at_field: str | None,
    ) -> ProviderResult:
        if not path.is_file():
            return OpsReadProviders._unavailable("SOURCE_MISSING")

        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return OpsReadProviders._unavailable(
                f"SOURCE_INVALID:{type(exc).__name__}"
            )

        if not isinstance(data, dict):
            return OpsReadProviders._unavailable("SOURCE_INVALID:NOT_OBJECT")

        missing = [field for field in required_fields if field not in data]
        if missing:
            return OpsReadProviders._unavailable(
                "SCHEMA_MISSING_FIELDS:" + ",".join(missing)
            )

        observed_at = (
            str(data.get(observed_at_field))
            if observed_at_field and data.get(observed_at_field) is not None
            else None
        )
        return ProviderResult(
            availability=Availability.AVAILABLE,
            observed_at=observed_at,
            data=data,
        )

    def runtime(self) -> ProviderResult:
        return self._read_json(
            self.runtime_state_path,
            required_fields=(
                "cycle_id",
                "heartbeat_timestamp",
                "system_status",
                "runtime_mode",
                "active_modules",
                "failed_modules",
                "last_error",
                "heartbeat_ok",
                "cycle_duration_seconds",
                "last_successful_cycle",
            ),
            observed_at_field="heartbeat_timestamp",
        )

    def kill_switch(self) -> ProviderResult:
        return self._read_json(
            self.kill_switch_path,
            required_fields=(
                "kill_switch_active",
                "activation_timestamp",
                "deactivation_timestamp",
                "reason",
                "activated_by",
                "deactivated_by",
                "deactivation_reason",
            ),
            observed_at_field=None,
        )

    def portfolio_health(self) -> ProviderResult:
        result = self._read_json(
            self.portfolio_health_path,
            required_fields=(
                "schema_version",
                "timestamp",
                "health_score",
                "status",
                "metrics",
                "alerts",
                "derived_from",
            ),
            observed_at_field="timestamp",
        )
        if not result.available:
            return result

        metrics = result.data.get("metrics")
        required_metrics = (
            "position_count",
            "deployment_efficiency",
            "directional_bias",
            "max_asset_concentration",
        )
        if not isinstance(metrics, dict):
            return self._unavailable("SCHEMA_INVALID:METRICS")
        missing = [field for field in required_metrics if field not in metrics]
        if missing:
            return self._unavailable(
                "SCHEMA_MISSING_METRICS:" + ",".join(missing)
            )
        return result

    def _connect_read_only(self) -> sqlite3.Connection:
        if not self.db_path.is_file():
            raise FileNotFoundError(str(self.db_path))
        uri = self.db_path.resolve().as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)

    @staticmethod
    def _parse_utc(value: str) -> datetime:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def reconciliation(self) -> ProviderResult:
        try:
            with closing(self._connect_read_only()) as conn:
                row = conn.execute(
                    """
                    SELECT
                        cycle_id,
                        state,
                        capability,
                        blocking_reason,
                        evaluated_at,
                        valid_until,
                        snapshot_timestamp
                    FROM reconciliation_results
                    WHERE is_final = 1
                    ORDER BY evaluated_at DESC
                    LIMIT 1
                    """
                ).fetchone()
        except FileNotFoundError:
            return self._unavailable("DATABASE_MISSING")
        except sqlite3.Error as exc:
            return self._unavailable(f"DATABASE_ERROR:{type(exc).__name__}")

        if row is None:
            return self._unavailable("RECONCILIATION_MISSING")

        try:
            valid_until = self._parse_utc(row[5])
            now = self._now().astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError) as exc:
            return self._unavailable(
                f"RECONCILIATION_TIME_INVALID:{type(exc).__name__}"
            )

        data = {
            "cycle_id": row[0],
            "state": row[1],
            "capability": row[2],
            "blocking_reason": row[3],
            "evaluated_at": row[4],
            "valid_until": row[5],
            "snapshot_timestamp": row[6],
            "expired": now > valid_until,
        }
        return ProviderResult(
            availability=Availability.AVAILABLE,
            observed_at=str(row[4]),
            data=data,
        )

    def positions(self) -> ProviderResult:
        required_fields = (
            "position_id",
            "asset",
            "direction",
            "entry_price",
            "current_price",
            "position_size",
            "opened_at",
            "updated_at",
            "unrealized_pnl",
            "realized_pnl",
            "cycle_opened",
            "status",
        )
        optional_fields = (
            "exchange_order_id",
            "stop_loss_order_id",
            "take_profit_order_id",
        )

        try:
            with closing(self._connect_read_only()) as conn:
                schema_rows = conn.execute(
                    "PRAGMA table_info(positions)"
                ).fetchall()
                available_fields = {row[1] for row in schema_rows}
                if not available_fields:
                    return self._unavailable("POSITIONS_TABLE_MISSING")

                missing = [
                    field
                    for field in required_fields
                    if field not in available_fields
                ]
                if missing:
                    return self._unavailable(
                        "POSITIONS_SCHEMA_MISSING:" + ",".join(missing)
                    )

                selected_fields = list(required_fields[:-1])
                selected_fields.extend(
                    field
                    for field in optional_fields
                    if field in available_fields
                )
                query = (
                    "SELECT "
                    + ", ".join(selected_fields)
                    + " FROM positions WHERE status = ? ORDER BY opened_at, position_id"
                )
                cursor = conn.execute(query, ("OPEN",))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
        except FileNotFoundError:
            return self._unavailable("DATABASE_MISSING")
        except sqlite3.Error as exc:
            return self._unavailable(f"DATABASE_ERROR:{type(exc).__name__}")

        data = [dict(zip(columns, row)) for row in rows]
        observed_values = [
            str(position["updated_at"])
            for position in data
            if position.get("updated_at") is not None
        ]
        return ProviderResult(
            availability=Availability.AVAILABLE,
            observed_at=max(observed_values) if observed_values else None,
            data=data,
        )
