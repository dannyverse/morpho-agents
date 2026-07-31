"""
Execution Authority

Responsabilidad:
- Controlar si Morpho puede enviar órdenes reales.
- Por defecto, toda ejecución live está bloqueada.
"""


LIVE_EXECUTION_AUTHORIZED = False


def can_execute_live():
    return LIVE_EXECUTION_AUTHORIZED
