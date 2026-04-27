"""Endpoints de autenticacion."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from config import settings
from db.sql.database import get_db
from db.sql.models import User
from utils.security import create_access_token, get_current_user, verify_password

router = APIRouter(tags=["Auth"])


class LoginRequest(BaseModel):
    """Credenciales minimas para login."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Token de acceso JWT para consumir endpoints protegidos."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Perfil basico del usuario autenticado."""

    id: int
    name: str
    email: EmailStr


@router.post("/login", response_model=LoginResponse, summary="Iniciar sesion y obtener JWT")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Valida credenciales y genera un token JWT firmado."""

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return LoginResponse(access_token=access_token)


@router.get("/me", response_model=MeResponse, summary="Obtener perfil autenticado")
async def read_me(current_user: User = Depends(get_current_user)):
    """Retorna el usuario resuelto desde el token Bearer."""

    return MeResponse(id=current_user.id, name=current_user.name, email=current_user.email)
