"""Cliente Langfuse para observabilidad del pipeline RAG.

Patron singleton con graceful-degradation: si Langfuse no esta disponible
todas las operaciones son no-ops silenciosos y la app sigue funcionando.
"""

from loguru import logger

_client = None
_init_attempted = False


def get_langfuse_client():
    """Retorna el cliente Langfuse inicializado, o None si no esta disponible."""
    global _client, _init_attempted

    if _client is not None:
        return _client
    if _init_attempted:
        return None

    _init_attempted = True

    from config import settings

    if not settings.LANGFUSE_ENABLED:
        logger.info("langfuse_disabled", reason="LANGFUSE_ENABLED=false")
        return None

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.warning(
            "langfuse_skipped",
            reason="LANGFUSE_PUBLIC_KEY o LANGFUSE_SECRET_KEY no configuradas",
        )
        return None

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info("langfuse_initialized", host=settings.LANGFUSE_HOST)
        return _client

    except Exception as exc:
        logger.warning(
            "langfuse_init_failed",
            error=str(exc),
            hint="La app continua sin observabilidad Langfuse",
        )
        return None


def create_trace(name: str, user_id: str = None, session_id: str = None, input: dict = None, metadata: dict = None):
    lf = get_langfuse_client()
    if not lf:
        return None
    try:
        return lf.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            input=input,
            metadata=metadata or {},
        )
    except Exception as exc:
        import traceback
        logger.warning(f"langfuse_trace_failed: {str(exc)} | {traceback.format_exc()}")
        return None

def flush_langfuse() -> None:
    lf = get_langfuse_client()
    if not lf:
        return
    try:
        lf.flush(timeout=2)  # máximo 2 segundos
    except Exception as exc:
        logger.warning("langfuse_flush_failed", error=str(exc))