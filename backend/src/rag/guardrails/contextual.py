"""
Módulo para validación contextual.
"""

from .regex_utils import contains_pattern
from .patterns import SAFE_ACADEMIC_CONTEXTS, DANGEROUS_REQUEST_PATTERNS
from .patterns import ACADEMIC_TOPIC_PATTERNS, NON_ACADEMIC_PATTERNS

def is_academic_context(text: str) -> bool:
    """
    Verifica si el texto tiene un contexto académico seguro.

    Args:
        text: Texto a validar.

    Returns:
        True si el texto tiene un contexto académico seguro, False en caso contrario.
    """
    return contains_pattern(text, SAFE_ACADEMIC_CONTEXTS)

def has_malicious_intent(text: str) -> bool:
    """
    Verifica si el texto tiene intención maliciosa.

    Args:
        text: Texto a validar.

    Returns:
        True si el texto tiene intención maliciosa, False en caso contrario.
    """
    return contains_pattern(text, DANGEROUS_REQUEST_PATTERNS)

def is_academic_question(text: str) -> bool:
    """
    Determina si la pregunta es de dominio académico.
    
    Lógica:
    1. Si coincide con ACADEMIC_TOPIC_PATTERNS → siempre válido
    2. Si coincide con NON_ACADEMIC_PATTERNS → bloqueado
    3. Si no coincide con ninguno → se permite (beneficio de la duda)
    """
    # Prioridad 1: si es claramente académico, pasa siempre
    if contains_pattern(text, ACADEMIC_TOPIC_PATTERNS):
        return True
    
    # Prioridad 2: si es claramente no académico, se bloquea
    if contains_pattern(text, NON_ACADEMIC_PATTERNS):
        return False
    
    # Prioridad 3: tema neutro o desconocido → permitir
    return True