"""Punto de entrada de FastAPI.

Configura la aplicacion HTTP, habilita CORS y monta las rutas versionadas del
backend para el flujo de ingestion y preguntas sobre documentos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from db.sql.database import Base, engine
from db.sql.models import User


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG MVP",
    description="API para responder preguntas sobre documentos PDF usando RAG + LangGraph + ChromaDB",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    # En produccion conviene reemplazar * por una lista explicita de dominios.
    allow_origins=["*"],
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
