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
    # Modelo para intent classification
    GROQ_CLASSIFIER_MODEL: str = "llama-3.1-8b-instant"

    # PostgreSQL
    DATABASE_URL: str

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_SSL: bool = False
    CHROMA_API_KEY: str | None = None
    CHROMA_TENANT: str = "default_tenant"
    CHROMA_DATABASE: str = "default_database"
    COLLECTION_NAME: str = "documents_v2"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # Retrieval
    RETRIEVER_K: int = 6
    RETRIEVER_FETCH_K: int = 20
    RETRIEVER_MMR_LAMBDA: float = 0.5
    
    # Web Search (fallback cuando el RAG no encuentra contexto suficiente)
    TAVILY_API_KEY: str = ""
    WEB_SEARCH_SIMILARITY_THRESHOLD: float = 0.4  # Score mínimo del RAG para evitar búsqueda web
    WEB_SEARCH_MAX_RESULTS: int = 8               # Resultados brutos que pide a Tavily
    WEB_SEARCH_TOP_K: int = 3                     # Snippets filtrados que llegan al prompt
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Grading
    GRADING_CONFIDENCE_THRESHOLD: float = 0.7

    # Langfuse — observabilidad local
    # Las llaves se generan en http://localhost:3001 al primer arranque.
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://langfuse-server:3000"
    LANGFUSE_ENABLED: bool = True

    class Config:
        # En local se leen valores desde .env; en Docker tambien pueden
        # inyectarse por variables de entorno del contenedor.
        env_file = ".env"


# Instancia unica reutilizable en todos los modulos.
settings = Settings()
