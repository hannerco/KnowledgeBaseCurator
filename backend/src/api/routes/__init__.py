"""Agregador principal de rutas versionadas de la API."""

from fastapi import APIRouter, Depends

from utils.security import get_current_user

from .auth import router as auth_router
from .documents import router as documents_router
from .qa import router as qa_router
from .users import router as users_router
from .message import router as message_router

router = APIRouter()
# Endpoints protegidos por JWT Bearer.
router.include_router(documents_router, dependencies=[Depends(get_current_user)])
router.include_router(qa_router, dependencies=[Depends(get_current_user)])
router.include_router(message_router, dependencies=[Depends(get_current_user)])

# Endpoints publicos.
router.include_router(users_router)
router.include_router(auth_router)
