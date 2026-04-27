"""Endpoints para consultas al flujo RAG."""

import logging
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag.graph import rag_chain

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Preguntas"])


class QuestionRequest(BaseModel):
    """Payload de entrada para preguntas al sistema RAG."""

    question: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "¿De que trata el documento?"
            }
        }
    }


class AnswerResponse(BaseModel):
    """Respuesta final devuelta al cliente luego del grafo RAG."""

    question: str
    answer: str


@router.post(
    "/ask",
    response_model=AnswerResponse,
    summary="Hacer una pregunta sobre los documentos",
)
async def ask_question(request: QuestionRequest):
    """Ejecuta el flujo retrieve -> generate para responder una pregunta."""

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacia.")

    try:
        result = rag_chain.invoke({
            "question": request.question,
            "context": [],
            "answer": "",
        })
    except Exception as exc:
        logger.error("Error en /ask:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno al procesar la pregunta.")

    return AnswerResponse(
        question=request.question,
        answer=result["answer"],
    )
