"""Pipeline de ingestion de documentos PDF.

Convierte un PDF en texto, extrae metadata académica (capítulos, secciones),
lo divide en chunks y los indexa en ChromaDB para retrieval.
"""

import re
import io
from typing import Optional, Dict, Any
from pypdf import PdfReader

# Intentar import con compatibilidad para diferentes versiones de LangChain
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.schema import Document
from db.chroma_client import get_vectorstore
from config import settings


# ---------------------------------------------------------------------------
# Extracción de metadata académica (capítulos, secciones)
# ---------------------------------------------------------------------------

def extract_academic_metadata(text: str) -> Dict[str, Any]:
    """
    Extrae capítulos y secciones del texto usando heurísticas regex.

    Detecta patrones comunes en libros académicos:
    - "Chapter 8: Amplificadores Operacionales"
    - "8.2 Configuración Inversora"
    - "Capítulo 8 - Amplificadores"

    Returns:
        Dict con chapter, chapter_number, section, section_number (si se detectan).
    """
    metadata: Dict[str, Any] = {
        "chapter": None,
        "chapter_number": None,
        "section": None,
        "section_number": None,
    }

    # Patrones para capítulos (Chapter 8, Capítulo 8, CH. 8, etc.)
    chapter_patterns = [
        r"(?:Chapter|Capítulo|CH\.|Ch\.|Cap\.?)\s*(\d+(?:\.\d+)*)\s*[:\.-]\s*(.+)",
        r"Capítulo\s*(\d+(?:\.\d+)*)\s*[:\.-]\s*(.+)",
        r"(\d+)\s+[Cc]hapter\s*[:\.-]\s*(.+)",
    ]

    for pattern in chapter_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata["chapter_number"] = match.group(1)
            metadata["chapter"] = match.group(2).strip()
            break

    # Patrones para secciones (8.2, 8.2.1, etc.)
    section_patterns = [
        r"(\d+(?:\.\d+){1,2})\s+(.+)",  # 8.2 Configuración Inversora
        r"Section\s+(\d+(?:\.\d+){1,2})\s*[:\.-]\s*(.+)",  # Section 8.2: ...
    ]

    for pattern in section_patterns:
        match = re.search(pattern, text)
        if match:
            # Solo considerar sección si no parece ser un capítulo
            section_num = match.group(1)
            if "." in section_num:  # Secciones tienen punto (8.2, 8.2.1)
                metadata["section_number"] = section_num
                metadata["section"] = match.group(2).strip()
                break

    return metadata


def parse_pdf(
    file_bytes: bytes,
    source_filename: str,
    document_type: str = "user_upload",
    knowledge_base: Optional[str] = None,
    book: Optional[str] = None,
    user_id: Optional[int] = None,
) -> list[Document]:
    """
    Extrae texto por página y retorna documentos con metadatos académicos.

    Args:
        file_bytes: Bytes del PDF a procesar.
        source_filename: Nombre original del archivo.
        document_type: Tipo de documento ("base_knowledge" o "user_upload").
                       Por defecto "user_upload" para mantener compatibilidad.
        knowledge_base: Área de conocimiento (ej: "electronics", "signals").
                       Solo para base_knowledge.
        book: Identificador del libro (ej: "sedra_smith", "serway").
              Solo para base_knowledge.

    Returns:
        Lista de documentos con metadata académica extraída.
    """

    # PdfReader trabaja sobre un stream en memoria, sin guardar archivos en disco.
    reader = PdfReader(io.BytesIO(file_bytes))
    documents: list[Document] = []

    # Estado contextual para propagar metadata a chunks
    current_context: Dict[str, Any] = {
        "chapter": None,
        "chapter_number": None,
        "section": None,
        "section_number": None,
    }

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue

        # Extraer metadata académica de esta página
        academic_metadata = extract_academic_metadata(text)

        # Actualizar contexto si se detecta nuevo capítulo o sección
        if academic_metadata["chapter"]:
            current_context["chapter"] = academic_metadata["chapter"]
            current_context["chapter_number"] = academic_metadata["chapter_number"]
        if academic_metadata["section"]:
            current_context["section"] = academic_metadata["section"]
            current_context["section_number"] = academic_metadata["section_number"]

        # Construir metadata base
        base_metadata: Dict[str, Any] = {
            "source": source_filename,
            "page": page_index,
            "document_type": document_type,
        }

        # Agregar metadata de knowledge base si es base_knowledge
        if document_type == "base_knowledge":
            if knowledge_base:
                base_metadata["knowledge_base"] = knowledge_base
            if book:
                base_metadata["book"] = book

        if user_id is not None:
            base_metadata["user_id"] = user_id

        # Agregar metadata académica contextual (solo si se detectó algo)
        if current_context["chapter"]:
            base_metadata["chapter"] = current_context["chapter"]
        if current_context["chapter_number"]:
            base_metadata["chapter_number"] = current_context["chapter_number"]
        if current_context["section"]:
            base_metadata["section"] = current_context["section"]
        if current_context["section_number"]:
            base_metadata["section_number"] = current_context["section_number"]

        documents.append(
            Document(
                page_content=text,
                metadata=base_metadata,
            )
        )

    return documents


def split_into_chunks(documents: list[Document]) -> list[Document]:
    """
    Divide documentos por página en chunks con overlap.

    LangChain's RecursiveCharacterTextSplitter preserva automáticamente
    la metadata de los documentos originales en cada chunk generado,
    lo que permite que chapter, section, etc. se propaguen a los chunks.
    """
    # RecursiveCharacterTextSplitter intenta respetar separadores naturales
    # antes de cortar por longitud pura.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)


def ingest_pdf(
    file_bytes: bytes,
    filename: str,
    document_type: str = "user_upload",
    knowledge_base: Optional[str] = None,
    book: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    """
    Pipeline completo de ingestión:
    1. Parsea el PDF con extracción de metadata académica
    2. Divide en chunks (propagando metadata)
    3. Genera embeddings y guarda en ChromaDB

    Args:
        file_bytes: Bytes del PDF a procesar.
        filename: Nombre del archivo.
        document_type: Tipo de documento ("base_knowledge" o "user_upload").
                       Por defecto "user_upload" para mantener compatibilidad.
        knowledge_base: Área de conocimiento (ej: "electronics", "signals").
                       Solo para base_knowledge.
        book: Identificador del libro (ej: "sedra_smith", "serway").
              Solo para base_knowledge.

    Retorna el número de chunks indexados.
    """
    page_documents = parse_pdf(
        file_bytes,
        filename,
        document_type,
        knowledge_base,
        book,
        user_id,
    )

    if not page_documents:
        raise ValueError("El PDF no contiene texto extraíble (puede ser un PDF escaneado).")

    documents = split_into_chunks(page_documents)
    vectorstore = get_vectorstore()

    # add_documents dispara el calculo de embeddings y la insercion en Chroma.
    vectorstore.add_documents(documents)

    return len(documents)
