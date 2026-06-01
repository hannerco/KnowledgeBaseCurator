"""Repository para operaciones de mensajes conversacionales.

Responsable de recuperar historial conversacional desde PostgreSQL
sin vectorización ni summarization.
"""

from sqlalchemy.orm import Session
from db.sql.models import Message
from typing import Optional


def get_recent_messages(
    chat_id: int,
    limit: int = 10,
    db: Optional[Session] = None
) -> list[dict]:
    """
    Recupera los últimos N mensajes de un chat, en orden cronológico.

    Args:
        chat_id: ID del chat
        limit: Cantidad máxima de mensajes a recuperar
        db: Sesión de SQLAlchemy (opcional para inyección de dependencia)

    Returns:
        Lista de dicts: [{"sender": "user|assistant", "content": str}, ...]
        Ordenados de más antiguo a más reciente.
    """
    try:
        if db is None:
            from db.sql.database import SessionLocal
            db = SessionLocal()

        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(
            Message.timestamp.asc()  # más antiguo primero
        ).limit(limit).all()

        return [
            {
                "sender": msg.sender,
                "content": msg.content
            }
            for msg in messages
        ]

    except Exception as e:
        print(f"[message_repository] Error recuperando historial: {e}")
        return []
