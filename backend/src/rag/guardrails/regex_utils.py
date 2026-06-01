"""
Módulo de utilidades para manejo seguro de regex.
"""

import re
from typing import List

def normalize_text(text: str) -> str:
    """
    Normaliza el texto para validaciones:
    - Convierte a minúsculas.
    - Elimina espacios duplicados.
    - Hace strip de espacios iniciales y finales.

    Args:
        text: Texto a normalizar.

    Returns:
        Texto normalizado.
    """
    return re.sub(r"\s+", " ", text.strip().lower())

def contains_pattern(text: str, patterns: List[str]) -> bool:
    """
    Verifica si el texto contiene alguno de los patrones dados.

    Args:
        text: Texto a validar.
        patterns: Lista de patrones regex.

    Returns:
        True si algún patrón coincide, False en caso contrario.
    """
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

def contains_whole_word(text: str, word: str) -> bool:
    """
    Verifica si el texto contiene una palabra completa.

    Args:
        text: Texto a validar.
        word: Palabra a buscar.

    Returns:
        True si la palabra completa está presente, False en caso contrario.
    """
    pattern = rf"\b{re.escape(word)}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))

def match_contextual_pattern(text: str, patterns: List[str]) -> bool:
    """
    Verifica si el texto coincide con patrones contextuales específicos.

    Args:
        text: Texto a validar.
        patterns: Lista de patrones regex contextuales.

    Returns:
        True si algún patrón contextual coincide, False en caso contrario.
    """
    return contains_pattern(text, patterns)