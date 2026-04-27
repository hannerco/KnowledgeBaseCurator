"""Endpoints de autenticacion."""

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter(tags=["Auth"])


class LoginRequest(BaseModel):
    """Credenciales minimas para login."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Respuesta temporal del login para pruebas de integracion."""

    email: EmailStr
    password: str


@router.post("/login", response_model=LoginResponse, summary="Login basico")
async def login(payload: LoginRequest):
    """Retorna las credenciales recibidas mientras se implementa auth real."""

    return LoginResponse(email=payload.email, password=payload.password)
