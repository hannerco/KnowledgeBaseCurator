"""Endpoints relacionados con carga e indexacion de documentos."""

import logging
import traceback

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from db.chroma_client import get_vectorstore
from db.sql.database import get_db
from db.sql.models import Document, User
from db.sql.schemas import DocumentResponse
from rag.ingest import ingest_pdf
from utils.security import get_current_user

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
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Valida, parsea e indexa un PDF en la base vectorial."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF (.pdf)")

    try:
        file_bytes = await file.read()
        chunks_count = ingest_pdf(file_bytes, file.filename, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Error en /upload:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al procesar el archivo.")

    # Persist document record in PostgreSQL
    db_document = Document(
        user_id=current_user.id,
        filename=file.filename,
        chunks_indexed=chunks_count,
        document_type="user_upload"
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return UploadResponse(
        filename=file.filename,
        chunks_indexed=chunks_count,
        message=f"'{file.filename}' indexado correctamente en {chunks_count} fragmentos.",
    )


@router.post(
    "/upload/base",
    response_model=UploadResponse,
    summary="Subir e indexar un PDF como fuente de verdad (base_knowledge)",
)
async def upload_base_document(
    file: UploadFile = File(...),
    knowledge_base: str = "general",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Valida, parsea e indexa un PDF como base de conocimiento."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF (.pdf)")

    try:
        file_bytes = await file.read()
        chunks_count = ingest_pdf(
            file_bytes, 
            file.filename, 
            document_type="base_knowledge", 
            knowledge_base=knowledge_base, 
            book=file.filename,
            user_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Error en /upload/base:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al procesar el archivo.")

    # Persist document record in PostgreSQL
    db_document = Document(
        user_id=current_user.id,
        filename=file.filename,
        chunks_indexed=chunks_count,
        document_type="base_knowledge"
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return UploadResponse(
        filename=file.filename,
        chunks_indexed=chunks_count,
        message=f"'{file.filename}' indexado como base de verdad correctamente en {chunks_count} fragmentos.",
    )


@router.get(
    "/documents",
    response_model=List[DocumentResponse],
    summary="Listar documentos del usuario",
)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna los documentos del usuario desde PostgreSQL."""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents


@router.get(
    "/documents/base",
    summary="Listar todas las fuentes de verdad (base_knowledge)",
)
async def list_base_documents(
    current_user: User = Depends(get_current_user),
):
    """
    Retorna la lista de archivos globales consultando directamente a ChromaDB.
    Esto garantiza que se muestren tanto los subidos por API como los cargados por script.
    """
    try:
        vs = get_vectorstore()
        collection = vs._collection
        result = collection.get(
            where={
                "$and": [
                    {"document_type": "base_knowledge"},
                    {"user_id": current_user.id}
                ]
            },
            include=["metadatas"]
        )

        sources: dict[str, dict] = {}
        for meta in result["metadatas"]:
            if not meta: continue
            source = meta.get("source", "desconocido")
            if source not in sources:
                sources[source] = {
                    "id": source, # Usamos el nombre como ID único temporal
                    "filename": source,
                    "chunks_indexed": 1,
                    "document_type": "base_knowledge",
                    "scope": "global"
                }
            else:
                sources[source]["chunks_indexed"] += 1

        return list(sources.values())
    except Exception:
        logger.error("Error en /documents/base:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al consultar libros base en ChromaDB.")


@router.delete(
    "/documents/{document_id}",
    summary="Eliminar un documento de ChromaDB y PostgreSQL",
)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Elimina el documento en ambos sistemas:
    1. Chunks en ChromaDB (para que el agente deje de usarlo)
    2. Registro en PostgreSQL (para que desaparezca del listado del usuario)
    """
    # Verificar que el documento existe y pertenece al usuario
    db_document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not db_document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    # 1. Borrar chunks de ChromaDB
    try:
        vs = get_vectorstore()
        collection = vs._collection
        collection.delete(where={"source": db_document.filename})
    except Exception:
        logger.error("Error en /documents DELETE:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al eliminar el documento de ChromaDB.")

    # 2. Borrar registro de PostgreSQL
    db.delete(db_document)
    db.commit()

    return {"message": f"Documento '{db_document.filename}' eliminado correctamente."}


@router.get(
    "/documents/chroma-debug",
    summary="Ver chunks en ChromaDB (debug)",
    tags=["Debug"],
)
async def chroma_debug(current_user: User = Depends(get_current_user)):
    """Muestra todos los chunks en ChromaDB — útil para verificar borrados."""
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
    except Exception:
        logger.error("Error en chroma-debug:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error al consultar ChromaDB.")