"""
Módulo para validación de inputs.
"""

from typing import Tuple, Optional
from .regex_utils import normalize_text, contains_pattern
from .patterns import PROFANITY_PATTERNS
from .contextual import is_academic_context, has_malicious_intent
from .contextual import is_academic_context, has_malicious_intent, is_academic_question

def validate_input(user_input: str) -> Tuple[bool, str, Optional[str]]:
    """
    Valida el input del usuario.

    Args:
        user_input: Texto ingresado por el usuario.

    Returns:
        Tuple (is_valid, validated_text, error_message):
        - is_valid: True si el input pasa la validación
        - validated_text: Input validado y limpio
        - error_message: Mensaje de error si falla la validación, None si es válido
    """
    normalized_input = normalize_text(user_input)

    if not normalized_input:
        return (
            False,
            user_input,
            "El input no puede estar vacío."
        )

    if len(normalized_input) > 2000:
        return (
            False,
            user_input,
            "El input es demasiado largo (máximo 2000 caracteres)."
        )

    if contains_pattern(normalized_input, PROFANITY_PATTERNS):
        return (
            False,
            user_input,
            "El input contiene lenguaje inapropiado."
        )

    if has_malicious_intent(normalized_input) and not is_academic_context(normalized_input):
        return (
            False,
            user_input,
            "El input contiene solicitudes que incumplen las políticas de seguridad."
        )
    if not is_academic_question(normalized_input):
        return (
            False,
            user_input,
            "Esta consulta no está relacionada con temas académicos. "
            "Por favor haz preguntas sobre el contenido del curso."
        )

    return (
        True,
        normalized_input,
        None
    )