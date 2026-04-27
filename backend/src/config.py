"""Configuracion central del backend.

Este modulo define todas las variables de entorno que usa la aplicacion y
expone una unica instancia (`settings`) para que el resto del codigo evite
valores hardcodeados.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Mapa tipado de variables de entorno del proyecto."""

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ChromaDB
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    COLLECTION_NAME: str = "documents"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Retrieval
    RETRIEVER_K: int = 4

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        # En local se leen valores desde .env; en Docker tambien pueden
        # inyectarse por variables de entorno del contenedor.
        env_file = ".env"


# Instancia unica reutilizable en todos los modulos.
settings = Settings()
