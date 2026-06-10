"""Punto de entrada de FastAPI.

Configura la aplicacion HTTP, habilita CORS y monta las rutas versionadas del
backend para el flujo de ingestion y preguntas sobre documentos.
"""

from fastapi import FastAPI
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
    allow_origins=[
        "https://knowledgefront-production.up.railway.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "*"    # para desarrollo local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Todas las rutas del negocio quedan bajo /api/v1.
app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint liviano para healthchecks de Docker y monitoreo."""
    return {"status": "ok"}
