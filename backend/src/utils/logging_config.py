"""Configuracion centralizada de logging usando loguru.

Configura dos sinks JSON persistentes:
  - logs/app.log   : INFO y superior, rotacion diaria, retencion 14 dias.
  - logs/errors.log: ERROR y superior, retencion 30 dias.

Intercepta el modulo logging estandar de Python para que FastAPI,
LangChain y SQLAlchemy pasen por el mismo pipeline.

Uso en cualquier modulo:
    from loguru import logger
    logger.info("mensaje", key=value)

Para anotar un trace_id en un bloque:
    with logger.contextualize(trace_id="abc123"):
        logger.info("dentro del trace")
"""

import logging
import sys
from pathlib import Path

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Puente entre logging stdlib y loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


_FORMATO = (
    "{time:YYYY-MM-DDTHH:mm:ss.SSS}Z | {level:<8} | "
    "{name}:{function}:{line} | trace={extra[trace_id]} | {message}"
)


def setup_logging() -> None:
    """Inicializa loguru y redirige el logging estandar.

    Debe llamarse UNA SOLA VEZ al inicio de la aplicacion, antes de
    importar cualquier modulo que use logging.
    """
    Path("logs").mkdir(exist_ok=True)

    logger.remove()
    logger.configure(extra={"trace_id": "-"})

    # Sink 1: app.log (INFO+) en JSON estructurado
    logger.add(
        "logs/app.log",
        format=_FORMATO,
        level="INFO",
        rotation="00:00",
        retention="14 days",
        serialize=True,
        encoding="utf-8",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    # Sink 2: errors.log (ERROR+) con traceback completo
    logger.add(
        "logs/errors.log",
        format=_FORMATO,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        serialize=True,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Sink 3: stderr coloreado para desarrollo
    logger.add(
        sys.stderr,
        format=_FORMATO,
        level="INFO",
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # Interceptar logging estandar de Python
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Silenciar loggers muy verbosos de terceros
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger.info("logging_initialized", sinks=["app.log", "errors.log", "stderr"])