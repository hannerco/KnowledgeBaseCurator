"""Endpoints de gestion de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.sql.database import get_db
from db.sql.models import User
from db.sql.schemas import UserCreate
from utils.security import hash_password

router = APIRouter(tags=["Usuarios"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Crea un usuario nuevo validando que el email no exista."""

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    hashed_password = hash_password(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuario registrado exitosamente"}
