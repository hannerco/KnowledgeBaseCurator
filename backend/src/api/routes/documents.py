"""Endpoints relacionados con carga e indexacion de documentos."""

import logging
import traceback

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from db.chroma_client import get_vectorstore
from rag.ingest import ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Documentos"])


class UploadResponse(BaseModel):
    """Resultado de la indexacion de un archivo PDF."""

    filename: str
    chunks_indexed: int
    message: str


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Subir y indexar un PDF",
)
async def upload_document(file: UploadFile = File(...)):
    """Valida, parsea e indexa un PDF en la base vectorial."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF (.pdf)")

    try:
        file_bytes = await file.read()
        chunks_count = ingest_pdf(file_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Error en /upload:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al procesar el archivo.")

    return UploadResponse(
        filename=file.filename,
        chunks_indexed=chunks_count,
        message=f"'{file.filename}' indexado correctamente en {chunks_count} fragmentos.",
    )


@router.get(
    "/documents",
    summary="Listar documentos indexados en ChromaDB",
    tags=["Debug"],
)
async def list_documents():
    """
    Muestra cuantos chunks hay por documento en la coleccion.
    Util para verificar que PDFs estan indexados.
    """
    try:
        vs = get_vectorstore()
        collection = vs._collection
        result = collection.get(include=["metadatas"])

        sources: dict[str, int] = {}
        for meta in result["metadatas"]:
            source = meta.get("source", "desconocido")
            sources[source] = sources.get(source, 0) + 1

        return {
            "total_chunks": len(result["metadatas"]),
            "documents": [
                {"filename": name, "chunks": count}
                for name, count in sorted(sources.items())
            ],
        }
    except Exception as exc:
        logger.error("Error en /documents:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al listar los documentos.")


@router.delete(
    "/documents/{filename}",
    summary="Eliminar un documento de ChromaDB",
    tags=["Debug"],
)
async def delete_document(filename: str):
    """
    Elimina todos los chunks de un documento especifico por nombre de archivo.
    """
    try:
        vs = get_vectorstore()
        collection = vs._collection
        collection.delete(where={"source": filename})
        return {"message": f"Documento '{filename}' eliminado correctamente."}
    except Exception as exc:
        logger.error("Error en /documents DELETE:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al eliminar el documento.")
