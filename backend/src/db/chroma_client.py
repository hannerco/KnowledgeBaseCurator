"""Utilidades de acceso a ChromaDB.

Centraliza la creacion de embeddings y del vectorstore para que ingestion y
retrieval usen exactamente la misma configuracion.
"""

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings

# El modelo de embeddings se instancia una sola vez (es pesado cargarlo repetidamente)
_embeddings: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Crea (una sola vez) el modelo de embeddings usado por todo el backend."""

    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    """
    Retorna un vectorstore de LangChain conectado al servicio ChromaDB via HTTP.
    Usar esta función siempre que se necesite leer o escribir en ChromaDB.
    """
    # Cliente HTTP hacia ChromaDB (soporta local o Chroma Cloud).
    http_client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        ssl=settings.CHROMA_SSL,
        headers={"x-chroma-token": settings.CHROMA_API_KEY} if settings.CHROMA_API_KEY else {},
        tenant=settings.CHROMA_TENANT,
        database=settings.CHROMA_DATABASE,
    )

    # Coleccion logica donde se almacenan y consultan los embeddings.
    return Chroma(
        client=http_client,
        collection_name=settings.COLLECTION_NAME,
        embedding_function=get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"},
    )
