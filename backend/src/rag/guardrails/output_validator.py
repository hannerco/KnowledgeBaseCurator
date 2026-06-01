"""
Módulo para validación de outputs.
"""

from typing import Tuple, Optional
from .regex_utils import normalize_text, contains_pattern
from .patterns import PROFANITY_PATTERNS, DANGEROUS_REQUEST_PATTERNS, HATEFUL_INTENT_PATTERNS

def validate_output(model_output: str) -> Tuple[bool, str, Optional[str]]:
    """
    Valida el output generado por el modelo.

    Args:
        model_output: Texto generado por el modelo.

    Returns:
        Tuple (is_valid, validated_text, error_message):
        - is_valid: True si el output pasa la validación
        - validated_text: Output validado y limpio
        - error_message: Mensaje de error si falla la validación, None si es válido
    """
    normalized_output = normalize_text(model_output)

    if not normalized_output:
        return (
            False,
            model_output,
            "La respuesta no puede estar vacía."
        )

    if len(normalized_output) > 10000:
        return (
            False,
            model_output,
            "La respuesta es demasiado larga (máximo 10000 caracteres)."
        )

    if contains_pattern(normalized_output, PROFANITY_PATTERNS):
        return (
            False,
            model_output,
            "La respuesta contiene lenguaje inapropiado."
        )

    if contains_pattern(normalized_output, DANGEROUS_REQUEST_PATTERNS):
        return (
            False,
            model_output,
            "La respuesta contiene instrucciones peligrosas."
        )

    if contains_pattern(normalized_output, HATEFUL_INTENT_PATTERNS):
        return (
            False,
            model_output,
            "La respuesta contiene contenido de odio."
        )

    return (
        True,
        normalized_output,
        None
    )