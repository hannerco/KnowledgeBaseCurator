from fastapi import APIRouter, Depends
from typing import List
from db.sql.schemas import MessageCreate, MessageResponse
from db.sql.models import Message
from utils.security import get_current_user
from db.sql.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["messages"], prefix="/messages")

@router.post("/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
): 
    """Crea un nuevo mensaje asociado al usuario autenticado."""
    
    new_message = Message(
        user_id=current_user.id,
        content=message.content,
        sender=message.sender
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.get("/", response_model=List[MessageResponse])
async def get_messages(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene todos los mensajes del usuario autenticado."""
    messages = db.query(Message).filter(Message.user_id == current_user.id).all()
    return messages
