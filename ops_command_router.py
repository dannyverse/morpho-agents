import logging
from dataclasses import dataclass
from typing import Callable

from ops_read_providers import OpsReadProviders, ProviderResult


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandRequest:
    text: str
    chat_id: str
    user_id: str | None = None
    update_id: int | None = None


class OpsCommandRouter:
    def __init__(self, providers: OpsReadProviders | None = None):
        self.providers = providers or OpsReadProviders()
        self._handlers: dict[str, Callable[[], str]] = {
            "/status": self._status,
            "/health": self._health,
            "/positions": self._positions,
            "/risk": self._risk,
            "/help": self._help,
        }

    def route(self, request: CommandRequest) -> str:
        text = str(request.text or "").strip()
        if not text:
            return "Unknown command. Use /help."

        tokens = text.split()
        command = tokens[0].lower().split("@", 1)[0]
        handler = self._handlers.get(command)
        if handler is None:
            return "Unknown command. Use /help."
        if len(tokens) > 1:
            return f"Arguments are not supported for {command}. Use /help."

        try:
            return handler()
        except Exception:
            logger.exception("unexpected_ops_command_error command=%s", command)
            return "Operational data is temporarily unavailable."

    @staticmethod
    def _value(value) -> str:
        return "UNAVAILABLE" if value is None else str(value)

    @staticmethod
    def _source_unavailable(label: str, result: ProviderResult) -> list[str]:
        lines = [f"{label}: UNAVAILABLE"]
        if result.errors:
            lines.append(f"Reason: {result.errors[0]}")
        return lines

    def _status(self) -> str:
        runtime = self.providers.runtime()
        positions = self.providers.positions()
        reconciliation = self.providers.reconciliation()
        kill_switch = self.providers.kill_switch()
        lines = ["MORPHO STATUS", ""]

        runtime_cycle = None
        if runtime.available:
            data = runtime.data
            runtime_cycle = str(data.get("cycle_id"))
            cycle_state = (
                "IN PROGRESS"
                if data.get("system_status") == "INITIALIZING"
                else "COMPLETE"
            )
            lines.extend([
                f"Runtime: {self._value(data.get('system_status'))}",
                f"Mode: {self._value(data.get('runtime_mode'))}",
                f"Cycle: {self._value(data.get('cycle_id'))}",
                f"Cycle State: {cycle_state}",
            ])
        else:
            lines.extend(self._source_unavailable("Runtime", runtime))

        lines.append("")
        if positions.available:
            lines.append(f"Open Positions: {len(positions.data)}")
        else:
            lines.extend(self._source_unavailable("Open Positions", positions))

        lines.append("")
        if reconciliation.available:
            data = reconciliation.data
            lines.extend([
                f"Reconciliation: {self._value(data.get('state'))}",
                f"Capability: {self._value(data.get('capability'))}",
                "Reconciliation Expired: "
                + ("YES" if data.get("expired") else "NO"),
            ])
            reconciliation_cycle = str(data.get("cycle_id"))
            if runtime_cycle is not None and reconciliation_cycle != runtime_cycle:
                lines.append(
                    "Cycle Mismatch: "
                    f"runtime={runtime_cycle}, reconciliation={reconciliation_cycle}"
                )
        else:
            lines.extend(
                self._source_unavailable("Reconciliation", reconciliation)
            )

        lines.append("")
        if kill_switch.available:
            state = "ACTIVE" if kill_switch.data.get("kill_switch_active") else "INACTIVE"
            lines.append(f"Kill Switch: {state}")
        else:
            lines.extend(self._source_unavailable("Kill Switch", kill_switch))
        return "\n".join(lines)

    def _health(self) -> str:
        runtime = self.providers.runtime()
        lines = ["MORPHO HEALTH", ""]
        if not runtime.available:
            lines.extend(self._source_unavailable("Runtime State", runtime))
            return "\n".join(lines)

        data = runtime.data
        cycle_state = (
            "IN PROGRESS"
            if data.get("system_status") == "INITIALIZING"
            else "COMPLETE"
        )
        active_modules = data.get("active_modules")
        failed_modules = data.get("failed_modules")
        active_modules = active_modules if isinstance(active_modules, list) else []
        failed_modules = failed_modules if isinstance(failed_modules, list) else []
        lines.extend([
            f"System: {self._value(data.get('system_status'))}",
            f"Mode: {self._value(data.get('runtime_mode'))}",
            f"Cycle: {self._value(data.get('cycle_id'))}",
            f"Cycle State: {cycle_state}",
            "Heartbeat Flag: " + ("OK" if data.get("heartbeat_ok") else "FAILED"),
            f"Heartbeat Time: {self._value(data.get('heartbeat_timestamp'))}",
            f"Cycle Duration: {self._value(data.get('cycle_duration_seconds'))}",
            "",
            f"Active Modules: {len(active_modules)}",
            f"Failed Modules: {len(failed_modules)}",
        ])
        if failed_modules:
            lines.extend(str(module) for module in failed_modules)
        if data.get("last_error"):
            lines.extend(["", f"Last Error: {data['last_error']}"])
        return "\n".join(lines)

    def _positions(self) -> str:
        positions = self.providers.positions()
        reconciliation = self.providers.reconciliation()
        runtime = self.providers.runtime()
        lines = ["OPEN POSITIONS", ""]

        if not positions.available:
            lines.extend(self._source_unavailable("Local Positions", positions))
        elif not positions.data:
            lines.append("No open local positions.")
        else:
            for index, position in enumerate(positions.data):
                if index:
                    lines.append("")
                lines.extend([
                    f"{self._value(position.get('asset'))} · "
                    f"{self._value(position.get('direction'))}",
                    f"Size: {self._value(position.get('position_size'))}",
                    f"Entry: {self._value(position.get('entry_price'))}",
                    f"Current: {self._value(position.get('current_price'))}",
                    "Unrealized PnL: "
                    f"{self._value(position.get('unrealized_pnl'))}",
                    f"Realized PnL: {self._value(position.get('realized_pnl'))}",
                    f"Opened: {self._value(position.get('opened_at'))}",
                    f"Updated: {self._value(position.get('updated_at'))}",
                ])
                for label, field in (
                    ("Exchange Order ID", "exchange_order_id"),
                    ("Stop Loss Order ID", "stop_loss_order_id"),
                    ("Take Profit Order ID", "take_profit_order_id"),
                ):
                    if field in position:
                        lines.append(f"{label}: {self._value(position.get(field))}")

        lines.extend(["", "Reconciliation:"])
        if not reconciliation.available:
            lines.append("UNAVAILABLE")
            lines.append("Exchange Confirmation: UNAVAILABLE")
        else:
            data = reconciliation.data
            lines.append(self._value(data.get("state")))
            lines.extend([
                "",
                "Capability:",
                self._value(data.get("capability")),
            ])
            cycle_mismatch = (
                runtime.available
                and str(runtime.data.get("cycle_id"))
                != str(data.get("cycle_id"))
            )
            if cycle_mismatch:
                lines.append(
                    "Cycle Mismatch: "
                    f"runtime={runtime.data.get('cycle_id')}, "
                    f"reconciliation={data.get('cycle_id')}"
                )
                lines.append("Exchange Confirmation: CYCLE MISMATCH")
            elif data.get("expired"):
                lines.append("Exchange Confirmation: EXPIRED")
            elif data.get("state") == "CONFIRMED":
                lines.append("Exchange Confirmation: CURRENT")
            else:
                lines.append("Exchange Confirmation: NOT CONFIRMED")
        return "\n".join(lines)

    def _risk(self) -> str:
        kill_switch = self.providers.kill_switch()
        portfolio_health = self.providers.portfolio_health()
        lines = ["MORPHO RISK", ""]

        if kill_switch.available:
            data = kill_switch.data
            lines.append(
                "Kill Switch: "
                + ("ACTIVE" if data.get("kill_switch_active") else "INACTIVE")
            )
            for label, field in (
                ("Reason", "reason"),
                ("Activation Time", "activation_timestamp"),
                ("Deactivation Time", "deactivation_timestamp"),
                ("Activated By (reported)", "activated_by"),
                ("Deactivated By (reported)", "deactivated_by"),
            ):
                if data.get(field) is not None:
                    lines.append(f"{label}: {data[field]}")
        else:
            lines.extend(self._source_unavailable("Kill Switch", kill_switch))

        lines.append("")
        if portfolio_health.available:
            data = portfolio_health.data
            metrics = data["metrics"]
            lines.extend([
                f"Portfolio Health: {self._value(data.get('status'))}",
                f"Health Score: {self._value(data.get('health_score'))}",
                f"Position Count: {self._value(metrics.get('position_count'))}",
                "Deployment Efficiency: "
                f"{self._value(metrics.get('deployment_efficiency'))}",
                f"Directional Bias: {self._value(metrics.get('directional_bias'))}",
                "Max Asset Concentration: "
                f"{self._value(metrics.get('max_asset_concentration'))}",
                f"Snapshot: {self._value(data.get('timestamp'))}",
            ])
            alerts = data.get("alerts")
            if isinstance(alerts, list) and alerts:
                lines.append("Alerts: " + "; ".join(str(item) for item in alerts))
        else:
            lines.extend(
                self._source_unavailable("Portfolio Health", portfolio_health)
            )
        return "\n".join(lines)

    @staticmethod
    def _help() -> str:
        return "\n".join([
            "MORPHO OPS CONSOLE",
            "",
            "/status",
            "/health",
            "/positions",
            "/risk",
            "/help",
            "",
            "Read-only operational console.",
            "No trading actions are available.",
        ])
