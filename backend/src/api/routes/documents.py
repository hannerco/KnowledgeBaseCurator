"""Endpoints relacionados con carga e indexacion de documentos."""

import logging
import traceback

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

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
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(exc)}")

    return UploadResponse(
        filename=file.filename,
        chunks_indexed=chunks_count,
        message=f"'{file.filename}' indexado correctamente en {chunks_count} fragmentos.",
    )
