from fastapi import APIRouter, Depends, HTTPException
from typing import List
from db.sql.schemas import MessageCreate, MessageResponse, MessagePairResponse
from db.sql.models import Message, Chat
from utils.security import get_current_user
from db.sql.database import get_db
from sqlalchemy.orm import Session
from rag.graph import rag_chain, detect_intent, MODE_CHAT, MODE_QA, MODE_CURATE
from db.sql.repositories.message_repository import get_recent_messages


router = APIRouter(tags=["messages"], prefix="/chats/{chat_id}/messages")

@router.post("/", response_model=MessagePairResponse)
async def create_message(
    chat_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Crea un nuevo mensaje en el chat especificado."""

    # Verificar que el chat pertenece al usuario actual
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_message = Message(
        chat_id=chat_id,
        content=message.content,
        sender="user"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Detectar intención para decidir qué historial usar
    detected_mode = detect_intent(message.content)

    # Recuperar historial según el modo
    conversation_history = []
    if detected_mode == MODE_CHAT:
        # CHAT: historial completo (últimos 10 mensajes)
        conversation_history = get_recent_messages(chat_id, limit=10, db=db)
    elif detected_mode == MODE_QA:
        # QA: historial más completo (últimos 8 mensajes = 4 intercambios)
        # para que preguntas sueltas/vagas puedan encontrar contexto real
        # Ejemplos: "¿por qué?", "¿y eso?", "¿aplica aquí?" necesitan historia
        conversation_history = get_recent_messages(chat_id, limit=8, db=db)
    # MODE_CURATE: sin historial (keep empty)

    try:
        result = rag_chain.invoke({
                "question": message.content,
                "user_files": message.sources or [],
                "base_files": message.base_sources or [],
                "user_id": current_user.id,
                "base_context": [],
                "user_context": [],
                "suggestions": [],
                "analysis_error": None,
                "answer": "",
                "mode": "",
                "rag_similarity_score": 0.0,
                "web_results": [],
                "used_web_fallback": False,
                "input_error": None,
                "conversation_history": conversation_history,
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error interno al procesar la pregunta.")

    assistant_message = Message(
        chat_id=chat_id,
        content=result["answer"],
        sender="assistant"
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return {
        "user_message": user_message,
        "assistant_message": assistant_message
    }

@router.get("/", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene todos los mensajes de un chat específico."""
    
    # Verificar que el chat pertenece al usuario actual
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    return messages
