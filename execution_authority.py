"""
Execution Authority

Responsabilidad:
- Controlar si Morpho puede enviar órdenes reales.
- Por defecto, toda ejecución live está bloqueada.
- Respeta kill switch global.
"""

from kill_switch_manager import get_kill_switch_state


LIVE_EXECUTION_AUTHORIZED = False


def can_execute_live():

    if not LIVE_EXECUTION_AUTHORIZED:
        return False

    kill_switch_state = get_kill_switch_state()

    if kill_switch_state.get("kill_switch_active"):
        return False

    return True
