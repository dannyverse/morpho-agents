# Morpho Agents

## Estado actual
- VPS Vultr operativo
- Ubuntu 24
- tmux persistente funcionando
- master_runner.py operativo
- sistema modular desplegado

## Arquitectura
- master_runner.py = loop principal
- safe_runner.py = protección
- risk_engine.py = control riesgo
- opportunity_engine.py = detección oportunidades
- signal_memory.py = memoria señales

## Infraestructura
- VPS: Vultr
- Python 3.12
- SQLite
- tmux
- backup local + VPS

## Próximas fases
- .env
- gitignore
- observabilidad
- métricas
- systemd
- dashboards

## Comandos importantes

### entrar VPS
ssh root@IP

### reattach tmux
tmux attach

### activar entorno
source venv/bin/activate

### lanzar sistema
python master_runner.py