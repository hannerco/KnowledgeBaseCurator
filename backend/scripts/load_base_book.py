"""Script genérico para cargar libros base en ChromaDB.

Este script indexa libros académicos como "base_knowledge" con metadata
académica (knowledge_base, book, capítulos, secciones).

Uso:
    python scripts/load_base_book.py --book sedra_smith --knowledge_base electronics
"""

import argparse
import os
import sys
from pathlib import Path

# Agregar /app al path para importar módulos del proyecto.
# Dentro de Docker: /app es el directorio de trabajo (mapea a ./src del host).
# Localmente: necesitamos agregar ./src al path.
_app_dir = Path(__file__).parent.parent / "src"
if _app_dir.exists():
    sys.path.insert(0, str(_app_dir))
else:
    sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from rag.ingest import ingest_pdf
from config import settings


def is_book_already_indexed(book: str) -> bool:
    """
    Verifica si un libro ya está indexado en ChromaDB.

    Consulta la colección para ver si existen documentos con
    metadata book={book}.

    Args:
        book: Identificador del libro (ej: "sedra_smith").

    Returns:
        True si el libro ya está indexado, False en caso contrario.
    """
    try:
        http_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            ssl=settings.CHROMA_SSL,
            headers={"x-chroma-token": settings.CHROMA_API_KEY} if settings.CHROMA_API_KEY else {},
            tenant=settings.CHROMA_TENANT,
            database=settings.CHROMA_DATABASE,
        )
        collection = http_client.get_collection(name=settings.COLLECTION_NAME)

        # Consultar si existe algún documento con book={book}
        results = collection.get(
            where={"book": book},
            limit=1,
        )

        return len(results["ids"]) > 0
    except Exception as e:
        print(f"Error al verificar si el libro ya está indexado: {e}")
        return False


def load_base_book(
    book: str,
    knowledge_base: str,
    filename: str | None = None,
) -> None:
    """
    Carga un libro base en ChromaDB con metadata académica.

    Args:
        book: Identificador del libro (ej: "sedra_smith", "serway").
        knowledge_base: Área de conocimiento (ej: "electronics", "signals").
        filename: Nombre del archivo PDF (opcional). Si no se especifica,
                  se usa {book}.pdf.
    """
    # Determinar nombre del archivo
    pdf_filename = filename or f"{book}.pdf"
    book_path = Path(__file__).parent.parent / "data" / "books" / pdf_filename

    # Verificar que el archivo existe
    if not book_path.exists():
        print(f"❌ Error: No se encontró el archivo en {book_path}")
        print(f"   Coloca el PDF en backend/data/books/{pdf_filename}")
        sys.exit(1)

    # Verificar si ya está indexado
    if is_book_already_indexed(book):
        print(f"✅ El libro '{book}' ya está indexado en ChromaDB.")
        print("   No es necesario re-indexar. Si deseas forzar una re-indexación,")
        print("   elimina los documentos existentes de ChromaDB y ejecuta este script nuevamente.")
        return

    # Leer el archivo PDF
    print(f"📖 Leyendo {pdf_filename} desde {book_path}...")
    with open(book_path, "rb") as f:
        file_bytes = f.read()

    # Indexar como base_knowledge
    print(f"🔄 Indexando '{book}' como base_knowledge (knowledge_base={knowledge_base})...")
    try:
        num_chunks = ingest_pdf(
            file_bytes=file_bytes,
            filename=pdf_filename,
            document_type="base_knowledge",
            knowledge_base=knowledge_base,
            book=book,
        )
        print(f"✅ Libro indexado exitosamente.")
        print(f"   Book: {book}")
        print(f"   Knowledge base: {knowledge_base}")
        print(f"   Chunks indexados: {num_chunks}")
    except Exception as e:
        print(f"❌ Error al indexar el libro: {e}")
        sys.exit(1)


def main():
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Carga un libro base en ChromaDB con metadata académica."
    )
    parser.add_argument(
        "--book",
        required=True,
        help="Identificador del libro (ej: sedra_smith, serway)",
    )
    parser.add_argument(
        "--knowledge-base",
        required=True,
        dest="knowledge_base",
        help="Área de conocimiento (ej: electronics, signals, control_systems)",
    )
    parser.add_argument(
        "--filename",
        help="Nombre del archivo PDF si difiere del identificador del libro",
    )

    args = parser.parse_args()

    load_base_book(
        book=args.book,
        knowledge_base=args.knowledge_base,
        filename=args.filename,
    )


if __name__ == "__main__":
    main()
