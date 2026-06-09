"""Punto de entrada de FastAPI."""

import time

# Logging debe inicializarse ANTES de cualquier otro import del proyecto.
from utils.logging_config import setup_logging
setup_logging()

from loguru import logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from db.sql.database import init_db
from db.sql.models import User


init_db()

app = FastAPI(
    title="RAG MVP",
    description="API para responder preguntas sobre documentos PDF usando RAG + LangGraph + ChromaDB",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Todas las rutas del negocio quedan bajo /api/v1.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra cada request HTTP con metodo, ruta, status y latencia."""
    t0 = time.monotonic()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        logger.error(
            "http_request_error",
            method=request.method,
            path=request.url.path,
            error=str(exc),
        )
        raise

    latency_ms = int((time.monotonic() - t0) * 1000)
    level = "WARNING" if status >= 400 else "INFO"
    logger.log(
        level,
        "http_request",
        method=request.method,
        path=request.url.path,
        status=status,
        latency_ms=latency_ms,
    )
    return response


app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint liviano para healthchecks de Docker y monitoreo."""
    return {"status": "ok"}