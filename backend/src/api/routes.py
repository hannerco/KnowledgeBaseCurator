import logging
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from rag.ingest import ingest_pdf
from rag.graph import rag_chain
from db.chroma_client import get_vectorstore

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class QuestionRequest(BaseModel):
    """Payload de entrada para preguntas al sistema RAG."""

    question: str
    model_config = {"json_schema_extra": {"example": {"question": "¿De qué trata el documento?"}}}


class AnswerResponse(BaseModel):
    """Respuesta final devuelta al cliente luego del grafo RAG."""

    question: str
    answer: str


class UploadResponse(BaseModel):
    """Resultado de la indexacion de un archivo PDF."""

    filename: str
    chunks_indexed: int
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Subir y indexar un PDF",
    tags=["Documentos"],
)
async def upload_document(file: UploadFile = File(...)):
    """Valida, parsea e indexa un PDF en la base vectorial."""

    # Validacion basica del tipo de archivo antes de procesar bytes.
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF (.pdf)")

    try:
        # Se lee en memoria para pasarlo al pipeline de ingestion.
        file_bytes = await file.read()
        chunks_count = ingest_pdf(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Error en /upload:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

    return UploadResponse(
        filename=file.filename,
        chunks_indexed=chunks_count,
        message=f"'{file.filename}' indexado correctamente en {chunks_count} fragmentos.",
    )


@router.post(
    "/ask",
    response_model=AnswerResponse,
    summary="Hacer una pregunta sobre los documentos",
    tags=["Preguntas"],
)
async def ask_question(request: QuestionRequest):
    """Ejecuta el flujo retrieve -> generate para responder una pregunta."""

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    try:
        # Estado inicial requerido por el grafo de LangGraph.
        result = rag_chain.invoke({
            "question": request.question,
            "context": [],
            "answer": "",
        })
    except Exception as e:
        logger.error("Error en /ask:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al procesar la pregunta: {str(e)}")

    return AnswerResponse(
        question=request.question,
        answer=result["answer"],
    )


@router.get(
    "/documents",
    summary="Listar documentos indexados en ChromaDB",
    tags=["Debug"],
)
async def list_documents():
    """
    Muestra cuántos chunks hay por documento en la colección.
    Útil para verificar qué PDFs están indexados.
    """
    try:
        vs = get_vectorstore()
        collection = vs._collection
        result = collection.get(include=["metadatas"])

        # Agrupar chunks por archivo de origen
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
    except Exception as e:
        logger.error("Error en /documents:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/documents/{filename}",
    summary="Eliminar un documento de ChromaDB",
    tags=["Debug"],
)
async def delete_document(filename: str):
    """
    Elimina todos los chunks de un documento específico por nombre de archivo.
    """
    try:
        vs = get_vectorstore()
        collection = vs._collection
        collection.delete(where={"source": filename})
        return {"message": f"Documento '{filename}' eliminado correctamente."}
    except Exception as e:
        logger.error("Error en /documents DELETE:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
