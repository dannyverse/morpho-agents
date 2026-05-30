import logging
import structlog
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Crear carpeta logs
Path("logs").mkdir(exist_ok=True)

# Configurar logging tradicional
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            "logs/system.log",
            maxBytes=5_000_000,
            backupCount=3
        )
    ]
)

# Configurar structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
