"""Pipeline de ingestion de documentos PDF.

Convierte un PDF en texto, lo divide en chunks y los indexa en ChromaDB para
que luego puedan recuperarse durante la fase de preguntas.
"""

import io
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from db.chroma_client import get_vectorstore
from config import settings


def parse_pdf(file_bytes: bytes) -> str:
    """Extrae el texto plano de un PDF en memoria."""

    # PdfReader trabaja sobre un stream en memoria, sin guardar archivos en disco.
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages_text)


def split_into_chunks(text: str, source_filename: str) -> list[Document]:
    """
    Divide el texto en chunks con overlap para no perder contexto en los bordes.
    Cada chunk conserva metadatos del archivo de origen.
    """
    # RecursiveCharacterTextSplitter intenta respetar separadores naturales
    # antes de cortar por longitud pura.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [
        Document(
            page_content=chunk,
            metadata={"source": source_filename},
        )
        for chunk in chunks
    ]


def ingest_pdf(file_bytes: bytes, filename: str) -> int:
    """
    Pipeline completo de ingestión:
    1. Parsea el PDF
    2. Divide en chunks
    3. Genera embeddings y guarda en ChromaDB

    Retorna el número de chunks indexados.
    """
    text = parse_pdf(file_bytes)

    if not text.strip():
        raise ValueError("El PDF no contiene texto extraíble (puede ser un PDF escaneado).")

    documents = split_into_chunks(text, filename)
    vectorstore = get_vectorstore()

    # add_documents dispara el calculo de embeddings y la insercion en Chroma.
    vectorstore.add_documents(documents)

    return len(documents)
