"""
Definición de patrones de validación.

IMPORTANTE:
- Los patrones deben minimizar falsos positivos académicos.
- NO bloquear términos educativos, históricos o científicos por sí solos.
- Solo bloquear intenciones claramente peligrosas, ofensivas o maliciosas.
"""

# -------------------------------------------------------------------
# Lenguaje ofensivo REAL
# Evitamos términos médicos o académicos.
# -------------------------------------------------------------------

PROFANITY_PATTERNS = [
    # Español
    r"\bmierda\b",
    r"\bputa\b",
    r"\bcabr[oó]n\b",
    r"\bzorra\b",
    r"\bpendej[o|a]\b",
    r"\bidiota\b",

    # Inglés
    r"\bfuck\b",
    r"\bshit\b",
    r"\bbitch\b",
    r"\basshole\b",
    r"\bmotherfucker\b",
]

# -------------------------------------------------------------------
# Solicitudes peligrosas ESPECÍFICAS
# No usar frases genéricas tipo "cómo crear".
# -------------------------------------------------------------------

DANGEROUS_REQUEST_PATTERNS = [

    # Hacking / acceso ilegal
    r"\bhackear\s+(wifi|cuentas?|servidores?|correos?)\b",
    r"\brobar\s+contraseñas?\b",
    r"\bphishing\b",
    r"\bkeylogger\b",
    r"\bcrear\s+malware\b",
    r"\bdesarrollar\s+ransomware\b",

    # Explosivos / armas
    r"\bfabricar\s+explosivos\b",
    r"\bcrear\s+una?\s+bomba\b",
    r"\bmanual\s+para\s+explosivos\b",

    # Terrorismo / violencia explícita
    r"\bc[oó]mo\s+unirme\s+a\s+(terroristas?|isis|al-qaeda)\b",
    r"\bc[oó]mo\s+atacar\s+a\s+personas\b",

    # Fraude
    r"\bclonar\s+tarjetas\b",
    r"\bfraude\s+bancario\b",
]

# -------------------------------------------------------------------
# Contenido de odio SOLO cuando implica intención dañina.
# NO bloquear palabras históricas por sí solas.
# -------------------------------------------------------------------

HATEFUL_INTENT_PATTERNS = [

    # Superioridad racial explícita
    r"\bla\s+raza\s+\w+\s+es\s+superior\b",
    r"\bodio\s+a\s+los\s+\w+\b",
    r"\bexpulsar\s+a\s+los\s+\w+\b",

    # Incitación
    r"\bviolencia\s+contra\s+\w+\b",
    r"\beliminar\s+a\s+los\s+\w+\b",

    # Glorificación extremista
    r"\bapoyo\s+al\s+nazismo\b",
    r"\bglorificar\s+terroristas\b",
]

# -------------------------------------------------------------------
# Contextos académicos seguros
# Permiten análisis históricos, educativos y científicos.
# -------------------------------------------------------------------

SAFE_ACADEMIC_CONTEXTS = [

    # Explicación / análisis
    r"\bexplica\b",
    r"\banaliza\b",
    r"\bdescribe\b",
    r"\bdefine\b",
    r"\bresumen\b",

    # Educación / investigación
    r"\binvestigaci[oó]n\b",
    r"\bcontexto\s+hist[oó]rico\b",
    r"\ban[aá]lisis\s+acad[eé]mico\b",

    # Preguntas educativas
    r"\bqu[eé]\s+es\b",
    r"\bpor\s+qu[eé]\b",
    r"\bc[oó]mo\s+funciona\b",

    # Historia / política
    r"\bhistoria\s+del\s+nazismo\b",
    r"\ban[aá]lisis\s+del\s+terrorismo\b",
    r"\bfascismo\b",
    r"\bsegunda\s+guerra\s+mundial\b",

    # Tecnología legítima
    r"\bc[oó]mo\s+crear\s+una\s+api\b",
    r"\bc[oó]mo\s+hacer\s+embeddings\b",
    r"\bmachine\s+learning\b",
]

# -------------------------------------------------------------------
# Temas NO académicos — se bloquean en el input
# -------------------------------------------------------------------

NON_ACADEMIC_PATTERNS = [
    # Deportes
    r"\b(mundial|copa del mundo|liga|Champions League|premier league)\b",
    r"\b(gol|portero|delantero|fútbol|soccer|NBA|NFL|MLB)\b",
    r"\b(quién ganó|resultado del partido|marcador)\b",

    # Entretenimiento / farándula
    r"\b(película|serie|netflix|spotify|canción|álbum|concierto)\b",
    r"\b(famoso|celebridad|actor|actriz|cantante)\b",

    # Apuestas / juegos
    r"\b(casino|apuesta|lotería|ruleta|póker)\b",

    # Chismes / redes sociales
    r"\b(tiktok|instagram|twitter|meme|viral|trending)\b",
]

# -------------------------------------------------------------------
# Temas académicos válidos — si coincide, siempre se permite
# (tiene prioridad sobre NON_ACADEMIC_PATTERNS)
# -------------------------------------------------------------------

ACADEMIC_TOPIC_PATTERNS = [
    r"\b(matemática|cálculo|álgebra|estadística|probabilidad)\b",
    r"\b(física|química|biología|anatomía|genética)\b",
    r"\b(historia|geografía|filosofía|sociología|psicología)\b",
    r"\b(programación|algoritmo|base de datos|redes|software)\b",
    r"\b(economía|administración|contabilidad|finanzas)\b",
    r"\b(literatura|gramática|redacción|lingüística)\b",
    r"\b(investigación|tesis|ensayo|metodología|hipótesis)\b",
]