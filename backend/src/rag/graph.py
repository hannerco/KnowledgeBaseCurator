"""Definicion del grafo RAG con LangGraph.
 
El pipeline tiene cuatro nodos principales:
1) retrieve     : valida el input con guardrails ANTES de tocar ChromaDB o internet.
                  Si el input es inválido (tema no académico, lenguaje inapropiado,
                  intención maliciosa), corta el flujo inmediatamente y va a generate
                  con input_error seteado.
                  Si el input es válido, recupera contexto desde ChromaDB y calcula
                  el similarity score promedio.
2) web_search   : [FALLBACK] se activa cuando el score de similitud del RAG está
                  por debajo del umbral configurado (WEB_SEARCH_SIMILARITY_THRESHOLD).
                  Busca en la web usando Tavily y filtra resultados no académicos.
3) analyze      : compara ambos contextos, detecta inconsistencias conceptuales
                  y construye sugerencias académicas estructuradas.
                  Solo se ejecuta cuando hay documentos del usuario en ChromaDB.
4) generate     : construye el prompt final y genera la respuesta con Groq.
                  Si retrieve detectó input_error, responde con el mensaje de error
                  directamente sin llamar al LLM.
                  Indica claramente la procedencia de cada fragmento (RAG vs web).
                  Valida el output con guardrails antes de retornar.
 
Flujo input inválido:
    START → retrieve (corta) → generate (retorna error) → END
 
Flujo QA sin fallback web:
    START → retrieve → generate → END
 
Flujo QA con fallback web:
    START → retrieve → web_search → generate → END
 
Flujo Curación:
    START → retrieve → analyze → generate → END
 
Flujo Curación con fallback web:
    START → retrieve → web_search → analyze → generate → END
"""

 
import json
import time
from typing import Optional, TypedDict

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from loguru import logger

from config import settings
from db.chroma_client import get_vectorstore
from observability.langfuse_client import create_trace, flush_langfuse
from config import settings
from rag.guardrails import validate_input, validate_output

 
# ---------------------------------------------------------------------------
# Tavily — cliente de búsqueda web
# ---------------------------------------------------------------------------
try:
    from tavily import TavilyClient
    _tavily_available = True
except ImportError:
    _tavily_available = False
    print("[web_search] Advertencia: tavily-python no instalado. pip install tavily-python")

# ---------------------------------------------------------------------------
# Constantes de modo
# ---------------------------------------------------------------------------
MODE_CHAT = "chat"
MODE_QA = "qa"
MODE_CURATE = "curate"


# ---------------------------------------------------------------------------
# Dominios académicos de confianza para el filtro post-búsqueda
# ---------------------------------------------------------------------------
TRUSTED_ACADEMIC_DOMAINS = [
    ".edu", ".gov", ".org",
    "scholar.google", "pubmed", "scielo", "redalyc",
    "researchgate", "academia.edu", "arxiv.org",
    "springer.com", "elsevier.com", "ieee.org",
    "jstor.org", "dialnet.unirioja.es",
    "wikipedia.org",  # Aceptable como punto de entrada académico
]

# ---------------------------------------------------------------------------
# Estado del grafo
# ---------------------------------------------------------------------------
class CurationSuggestion(TypedDict):
    type: str
    description: str
    action: str
    severity: str
    base_reference: str


class RAGState(TypedDict):
    question: str
    base_context: list[str]         # Chunks recuperados de libros base
    user_context: list[str]         # Chunks recuperados de documentos del usuario
    user_files: list[str]           # Lista de nombres de archivos a consultar (user)
    base_files: list[str]           # Lista de nombres de archivos a consultar (base_knowledge)
    user_id: int                    # ID del usuario para aislar consultas
    suggestions: list[dict]         # Lista de CurationSuggestion (solo en modo curate)
    analysis_error: Optional[str]   # Error ocurrido durante el análisis (si hubo)
    answer: str
    mode: str                       # MODE_QA o MODE_CURATE
    rag_similarity_score: float      # Score promedio del contexto RAG recuperado
    web_results: list[dict]          # Snippets de búsqueda web [{title, url, content}]
    used_web_fallback: bool          # Flag: se usó búsqueda web en esta consulta
    input_error: Optional[str]       # Error de guardrail detectado en retrieve (corta el flujo)
    conversation_history: list[dict] # Historial reciente [{sender, content}] para contexto conversacional
    _trace_id: Optional[str]  # propaga el trace de Langfuse entre nodos


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
def _build_intent_classifier_prompt(question: str) -> str:
    return f"""
    Eres un clasificador de intencion para un sistema RAG academico.

    Debes clasificar el mensaje del usuario en UNA SOLA categoria:

    - chat
    -> conversacion casual, saludos, agradecimientos o charla general.

    - qa
    -> preguntas sobre contenido academico, libros o documentos.
    -> incluye preguntas sobre documentos del usuario.

    - curate
    -> solicitudes de analisis, comparacion, revision critica,
    deteccion de inconsistencias, evaluacion o validacion academica.

    IMPORTANTE:
    - Responde SOLO con una palabra: chat, qa o curate

    Mensaje del usuario:
    {question}
    """


# ---------------------------------------------------------------------------
# Deteccion de intencion
# ---------------------------------------------------------------------------
def detect_intent(question: str, trace=None) -> str:
    """Detecta la intencion con un LLM classifier.
    Registra la llamada como Generation en Langfuse si hay trace activo.
    """
    t0 = time.monotonic()
    try:
        llm = ChatGroq(
            model=settings.GROQ_CLASSIFIER_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        prompt = _build_intent_classifier_prompt(question)
        response = llm.invoke([HumanMessage(content=prompt)])

        latency_ms = int((time.monotonic() - t0) * 1000)
        usage = response.response_metadata.get("token_usage", {})

        intent = response.content.strip().lower().replace('"', "").replace(".", "")
        if intent not in {MODE_CHAT, MODE_QA, MODE_CURATE}:
            intent = MODE_QA

        logger.info(
            "intent_detected",
            intent=intent,
            latency_ms=latency_ms,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )

        if trace:
            try:
                from langfuse.model import ModelUsage
                trace.generation(
                    name="llm_detect_intent",
                    model=settings.GROQ_CLASSIFIER_MODEL,
                    input=prompt,
                    output=intent,
                    usage=ModelUsage(
                        input=usage.get("prompt_tokens", 0),
                        output=usage.get("completion_tokens", 0),
                    ),
                    metadata={"latency_ms": latency_ms},
                )
            except Exception as lf_exc:
                logger.warning("langfuse_generation_failed", node="detect_intent", error=str(lf_exc))

        return intent

    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.error("intent_detection_error", error=str(exc), latency_ms=latency_ms)
        return MODE_QA


# ---------------------------------------------------------------------------
# Helpers de recuperacion
# ---------------------------------------------------------------------------

def _retrieve_by_type(question: str, document_type: str, k: int, user_id: int, target_files: list[str] = None) -> list[str]:
    
    """
    Recupera chunks de ChromaDB filtrando por document_type, user_id y opcionalmente source.
 
    Args:
        question: Pregunta o tema a buscar.
        document_type: "base_knowledge" o "user_upload".
        k: Número de chunks a recuperar.
        user_id: ID del usuario actual.
        target_files: Lista de nombres de archivo a filtrar.
 
    Returns:
        Lista de strings con el contenido de los chunks.
        Retorna lista vacía si ocurre cualquier error (ChromaDB no disponible,
        colección vacía, etc.).
    """
    try:
        vectorstore = get_vectorstore()
        
        filter_dict = {
            "$and": [
                {"document_type": document_type},
                {"user_id": user_id}
            ]
        }
        
        if target_files:
            if len(target_files) == 1:
                filter_dict = {
                    "$and": [
                        {"document_type": document_type},
                        {"user_id": user_id},
                        {"source": target_files[0]}
                    ]
                }
            else:
                filter_dict = {
                    "$and": [
                        {"document_type": document_type},
                        {"user_id": user_id},
                        {"source": {"$in": target_files}}
                    ]
                }

        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
                "fetch_k": settings.RETRIEVER_FETCH_K,
                "lambda_mult": settings.RETRIEVER_MMR_LAMBDA,
                "filter": filter_dict,
            },
        )
        docs = retriever.invoke(question)
        chunks = [doc.page_content for doc in docs]
        if not chunks:
            return [], 0.0
 
        # Búsqueda separada solo para obtener el similarity score
        # No interrumpimos el flujo si falla; usamos 0.0 como fallback
        scored_results = vectorstore.similarity_search_with_score(
            question,
            k=k,
            filter=filter_dict,
        )
 
        if scored_results:
            avg_distance = sum(score for _, score in scored_results) / len(scored_results)
            avg_similarity = max(0.0, 1.0 - avg_distance)
        else:
            avg_similarity = 0.0
 
        return chunks, avg_similarity
    except Exception as e:
        # No interrumpimos el flujo; el nodo caller decide qué hacer.
        logger.warning("retrieve_warning", document_type=document_type, error=str(e))
        print(f"[retrieve] Advertencia al recuperar '{document_type}': {e}")
        return [], 0.0
    


# ---------------------------------------------------------------------------
# Nodo 1 — Recuperacion
# ---------------------------------------------------------------------------
def retrieve(state: RAGState) -> dict:
    """
    Nodo 1 — Recuperación con validación de guardrails al inicio.
 
    Orden de ejecución:
    1. Valida el input con guardrails ANTES de tocar ChromaDB o internet.
       Si falla → setea input_error y retorna con mode=MODE_CHAT para ir
       directo a generate sin pasar por web_search ni analyze.
    2. Detecta intención (chat / qa / curate).
    3. Recupera chunks de ChromaDB con MMR y calcula rag_similarity_score.
    """

    """Crea el trace raiz y el span de recuperacion."""
    t0 = time.monotonic()
    question = state["question"]
    
    # ------------------------------------------------------------------
    # GUARDRAIL DE INPUT — primer filtro, antes de cualquier búsqueda
    # ------------------------------------------------------------------
    is_input_valid, _, input_error = validate_input(question)
 
    if not is_input_valid:
        print(f"[guardrails][retrieve] Input rechazado: {input_error}")
        return {
            "base_context": [],
            "user_context": [],
            "mode": MODE_CHAT,          # Fuerza flujo directo a generate
            "suggestions": [],
            "analysis_error": None,
            "rag_similarity_score": 1.0,
            "web_results": [],
            "used_web_fallback": False,
            "input_error": input_error,
            "conversation_history": state.get("conversation_history", []),
        }

    trace = create_trace(name="rag_pipeline", metadata={"question": question})
    trace_id = trace.id if trace else None

    with logger.contextualize(trace_id=trace_id or "-"):
        span = trace.span(name="retrieve", input={"question": question}) if trace else None

        try:
            mode = detect_intent(question, trace=trace)

            # ---------------------------------------------------
            # CHAT → no hacer retrieval
            # ---------------------------------------------------
            if mode == MODE_CHAT:
                if span:
                    span.end(output={"mode": MODE_CHAT})
                return {
                    "base_context": [],
                    "user_context": [],
                    "mode": MODE_CHAT,
                    "suggestions": [],
                    "analysis_error": None,
                    "rag_similarity_score": 1.0,
                    "web_results": [],
                    "used_web_fallback": False,
                    "input_error": None,
                    "conversation_history": state.get("conversation_history", []),
                }

            # ---------------------------------------------------
            # QA o CURATE → sí hacer retrieval
            # ---------------------------------------------------
            base_chunks, base_score = _retrieve_by_type(
                question,
                "base_knowledge",
                settings.RETRIEVER_K,
                user_id=state["user_id"],
                target_files=state.get("base_files", [])
            )

            user_chunks, user_score = _retrieve_by_type(
                question,
                "user_upload",
                settings.RETRIEVER_K,
                user_id=state["user_id"],
                target_files=state.get("user_files", [])
            )

            # Score final: promedio ponderado.
            # Si no hay user_context usamos solo base_score.
            if user_chunks:
                avg_score = (base_score + user_score) / 2
            else:
                avg_score = base_score

            latency_ms = int((time.monotonic() - t0) * 1000)

            print(f"[retrieve] RAG similarity score: {avg_score:.3f} "
                f"(umbral: {settings.WEB_SEARCH_SIMILARITY_THRESHOLD})")
            


            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.info(
                "retrieve_ok",
                mode=mode,
                base_chunks=len(base_chunks),
                user_chunks=len(user_chunks),
                latency_ms=latency_ms,
            )

            if span:
                span.end(output={
                    "mode": mode,
                    "base_chunks_count": len(base_chunks),
                    "user_chunks_count": len(user_chunks),
                    "latency_ms": latency_ms,
                })

        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error("retrieve_error", error=str(exc), latency_ms=latency_ms)
            if span:
                span.end(level="ERROR", status_message=str(exc))
            base_chunks, user_chunks, mode = [], [], MODE_QA

    return {
        "base_context": base_chunks,
        "user_context": user_chunks,
        "mode": mode,
        "suggestions": [],
        "analysis_error": None,
        "rag_similarity_score": avg_score,
        "web_results": [],
        "used_web_fallback": False,
        "input_error": None,
        "conversation_history": state.get("conversation_history", []),
        "_trace_id": trace_id,
    }


# ---------------------------------------------------------------------------
# Nodo 2 — Web Search Fallback
# ---------------------------------------------------------------------------
def _is_academic_result(result: dict) -> bool:
    """
    Filtra resultados web: acepta solo fuentes académicas o de confianza.
 
    Criterios:
    - URL contiene un dominio de confianza, O
    - El score de relevancia de Tavily supera 0.5
    """
    url = result.get("url", "").lower()
    
    # Dominios explícitamente bloqueados (redes sociales, entretenimiento)
    BLOCKED_DOMAINS = [
        "tiktok.com", "instagram.com",
        "facebook.com", "twitter.com", "x.com",
        "pinterest.com",
    ]
    if any(blocked in url for blocked in BLOCKED_DOMAINS):
        return False
    
    is_trusted_domain = any(domain in url for domain in TRUSTED_ACADEMIC_DOMAINS)
    tavily_score = result.get("score", 0.0)
    is_high_relevance = tavily_score >= 0.5

    return is_trusted_domain or is_high_relevance
 
def web_search(state: RAGState) -> dict:
    """
    Nodo 2 — Búsqueda web como fallback académico.
 
    Se activa cuando rag_similarity_score < WEB_SEARCH_SIMILARITY_THRESHOLD.
    Consulta Tavily con contexto académico y filtra resultados de baja calidad.
 
    Modifica el estado con:
    - web_results: lista de snippets filtrados [{title, url, content, score}]
    - used_web_fallback: True
    """
    question = state["question"]
    print(f"[web_search] Activando búsqueda web para: '{question[:80]}...'")
 
    if not _tavily_available:
        print("[web_search] Tavily no disponible — omitiendo búsqueda web.")
        return {"web_results": [], "used_web_fallback": False}
 
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
 
        academic_query = f"{question} site:edu OR site:gov OR academic research"
 
        response = client.search(
            query=academic_query,
            search_depth="advanced",
            max_results=settings.WEB_SEARCH_MAX_RESULTS,
            include_answer=False,
            include_raw_content=False,
        )
 
        raw_results = response.get("results", [])
 
        # Filtro post-búsqueda: solo resultados académicos o de alta relevancia
        filtered = [r for r in raw_results if _is_academic_result(r)]
 
        # Ordenar por score y tomar los mejores
        top_results = sorted(
            filtered,
            key=lambda r: r.get("score", 0.0),
            reverse=True,
        )[:settings.WEB_SEARCH_TOP_K]
 
        web_results = [
            {
                "title": r.get("title", "Sin título"),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": round(r.get("score", 0.0), 3),
            }
            for r in top_results
        ]
 
        print(f"[web_search] {len(raw_results)} resultados brutos → "
              f"{len(filtered)} filtrados → {len(web_results)} seleccionados.")
 
        return {"web_results": web_results, "used_web_fallback": True}

    except Exception as e:
        print(f"[web_search] Error durante la búsqueda: {e}")
        return {"web_results": [], "used_web_fallback": False}
    
# ---------------------------------------------------------------------------
# Nodo 3 — Análisis y detección de inconsistencias
# ---------------------------------------------------------------------------
def _build_analysis_prompt(question, base_context, user_context) -> str:
    base_text = "\n\n---\n\n".join(base_context) if base_context else "Sin contenido de libros base disponible."
    user_text = "\n\n---\n\n".join(user_context)

    return f"""Eres un curador academico experto. Tu tarea es analizar un documento subido por un estudiante
    y compararlo con el contenido oficial de los libros base del curso.

    Debes identificar:
    1. REDUNDANCIA: El documento repite contenido que ya existe en los libros base.
    2. CONFLICTO: El documento contradice o es inconsistente con los libros base (esto es lo mas importante).
    3. COMPLEMENTO: El documento agrega informacion util que no esta en los libros base.
    4. SIN_RESPALDO: El documento contiene afirmaciones que no tienen respaldo en los libros base.

    Tema consultado: {question}

    === CONTENIDO DE LIBROS BASE ===
    {base_text}

    === CONTENIDO DEL DOCUMENTO DEL USUARIO ===
    {user_text}

    Responde UNICAMENTE con un JSON valido con esta estructura exacta, sin texto adicional, sin markdown:
    {{
    "suggestions": [
        {{
        "type": "conflict|redundancy|complement|no_support",
        "description": "Explicacion clara de que encontraste",
        "action": "Accion concreta recomendada al curador",
        "severity": "low|medium|high",
        "base_reference": "Fragmento breve del libro base relacionado, o vacio si no aplica"
        }}
    ]
    }}

    Si no encuentras ningun problema ni sugerencia relevante, retorna {{"suggestions": []}}.
    """


def analyze(state: RAGState) -> dict:
    """
    Nodo 3 — Análisis de inconsistencias (solo en modo curate).
 
    Compara user_context con base_context usando el LLM para detectar:
    - Redundancias
    - Conflictos conceptuales
    - Contenido complementario
    - Afirmaciones sin respaldo
 
    Maneja errores de parsing JSON y errores del LLM sin interrumpir el flujo.
    """
    # Validación: si no hay contexto del usuario, no hay nada que analizar.
    if not state.get("user_context"):
        return {"suggestions": [], "analysis_error": None}

    if not state.get("base_context"):
        print("[analyze] Advertencia: No hay contenido de libros base para comparar.")
        logger.warning("analyze_no_base_context")

    t0 = time.monotonic()
    trace_id = state.get("_trace_id")

    trace = None
    try:
        from observability.langfuse_client import get_langfuse_client
        lf = get_langfuse_client()
        if lf and trace_id:
            trace = lf.get_trace(trace_id)
    except Exception:
        pass

    span = trace.span(name="analyze", input={"question": state["question"]}) if trace else None

    with logger.contextualize(trace_id=trace_id or "-"):
        try:
            prompt = _build_analysis_prompt(
                question=state["question"],
                base_context=state["base_context"],
                user_context=state["user_context"],
            )
            llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY, temperature=0)
            response = llm.invoke([HumanMessage(content=prompt)])
            latency_ms = int((time.monotonic() - t0) * 1000)
            usage = response.response_metadata.get("token_usage", {})

            raw_content = response.content.strip()
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                raw_content = "\n".join(lines[1:-1])

            parsed = json.loads(raw_content)
            
            suggestions = parsed.get("suggestions", [])
            # Validar estructura de cada sugerencia
            validated_suggestions = []
            for s in suggestions:
                if not isinstance(s, dict):
                    continue
                validated_suggestions.append({
                    "type": s.get("type", "no_support"),
                    "description": s.get("description", "Sin descripción"),
                    "action": s.get("action", "Revisar manualmente"),
                    "severity": s.get("severity", "medium"),
                    "base_reference": s.get("base_reference", ""),
                })
            
            logger.info(
                "analyze_ok",
                suggestions_count=len(validated_suggestions),
                latency_ms=latency_ms,
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
            )

            if trace:
                try:
                    from langfuse.model import ModelUsage
                    trace.generation(
                        name="llm_analyze",
                        model=settings.GROQ_MODEL,
                        input=prompt,
                        output=raw_content,
                        usage=ModelUsage(
                            input=usage.get("prompt_tokens", 0),
                            output=usage.get("completion_tokens", 0),
                        ),
                        metadata={"latency_ms": latency_ms, "suggestions_count": len(validated_suggestions)},
                    )
                except Exception as lf_exc:
                    logger.warning("langfuse_generation_failed", node="analyze", error=str(lf_exc))

            if span:
                span.end(output={"suggestions_count": len(validated_suggestions), "latency_ms": latency_ms})

            return {"suggestions": validated_suggestions, "analysis_error": None}

        except json.JSONDecodeError as e:
        # El LLM no retornó JSON válido; registramos el error pero seguimos.
            latency_ms = int((time.monotonic() - t0) * 1000)
            error_msg = f"Error al parsear respuesta del analisis: {e}"
            logger.error("analyze_json_error", error=error_msg, latency_ms=latency_ms)
            if span:
                span.end(level="ERROR", status_message=error_msg)
            return {"suggestions": [], "analysis_error": error_msg}

        except Exception as e:
            latency_ms = int((time.monotonic() - t0) * 1000)
            error_msg = f"Error inesperado durante el analisis: {e}"
            logger.error("analyze_error", error=error_msg, latency_ms=latency_ms)
            if span:
                span.end(level="ERROR", status_message=error_msg)
            return {"suggestions": [], "analysis_error": error_msg}


# ---------------------------------------------------------------------------
# Nodo 4 — Generación de respuesta final
# ---------------------------------------------------------------------------
def _extract_main_topic(
    conversation_history: list[dict],
    base_context: list[str] = None,
    user_context: list[str] = None
) -> str:
    """Detecta el tema principal de la conversación.

    Prioridad:
    1. Si hay contexto del retrieval (base_context o user_context), extrae el tema de ahí
       (más preciso, ya que el retrieval ya identificó el tema académico)
    2. Si no hay retrieval, busca en el historial conversacional
    """
    # Opción 1: Usar contexto del retrieval (PRIORITARIO)
    retrieval_context = base_context or user_context
    if retrieval_context:
        # Tomar el primer chunk del retrieval
        first_chunk = retrieval_context[0] if retrieval_context else ""
        if first_chunk:
            # Extraer primer párrafo o primera oración
            lines = first_chunk.split("\n")
            first_paragraph = next((line for line in lines if line.strip()), "")

            if first_paragraph:
                # Buscar la primera oración completa
                sentences = first_paragraph.split(".")
                first_sentence = sentences[0].strip()

                # Extraer palabras clave (capitalizadas = sustantivos propios probables)
                words = first_sentence.split()
                capitalized = [w for w in words if w[0].isupper() and len(w) > 2]

                if capitalized:
                    # Tomar el primer sustantivo capitalizado (típicamente el tema)
                    topic = capitalized[0]
                    return topic

                # Fallback: primeras 100 chars del párrafo
                return first_paragraph[:100].rstrip(".")

    # Opción 2: Extraer del historial conversacional si no hay retrieval
    if not conversation_history:
        return ""

    # Buscar el primer mensaje del usuario que NO sea un saludo/pequeño
    topic_keywords = [
        "qué es", "define", "explica", "sobre", "hablar de",
        "tema de", "ley de", "teoría de", "concepto de",
        "analiza", "explica", "diferencia entre", "relación entre"
    ]

    # Buscar primer mensaje USER significativo (>20 chars)
    first_significant_msg = None
    for msg in conversation_history:
        if msg["sender"] == "user" and len(msg["content"]) > 20:
            first_significant_msg = msg["content"]
            break

    if not first_significant_msg:
        return ""

    # Si encontramos una palabra clave, extrae lo que viene después
    text_lower = first_significant_msg.lower()
    for keyword in topic_keywords:
        if keyword in text_lower:
            idx = text_lower.find(keyword) + len(keyword)
            # Tomar los próximos 100 chars
            topic_snippet = first_significant_msg[idx:idx+100].strip()
            # Limpiar puntuación
            topic_snippet = topic_snippet.rstrip("?.!,;:")
            return topic_snippet[:80]

    # Fallback: tomar primeros 80 chars del primer mensaje significativo
    return first_significant_msg[:80].rstrip("?.!,;:")


def _build_conversation_context_chat(conversation_history: list[dict]) -> str:
    """Formatea el historial conversacional completo para mode_chat."""
    if not conversation_history:
        return ""

    lines = ["CONTEXTO CONVERSACIONAL RECIENTE:", ""]
    for msg in conversation_history:
        sender_label = "Tú" if msg["sender"] == "user" else "Asistente"
        lines.append(f"{sender_label}: {msg['content']}")
        lines.append("")

    return "\n".join(lines)


def _build_conversation_context_qa(
    conversation_history: list[dict],
    base_context: list[str] = None,
    user_context: list[str] = None
) -> str:
    """Formatea el historial conversacional corto para mode_qa.

    CRÍTICO: Las preguntas que parecen sueltas o sin contexto son justamente
    las que necesitan este historial para ser entendidas correctamente.
    Ejemplos:
    - Usuario: "¿Por qué es importante?" → se refiere al tema anterior
    - Usuario: "¿Eso también aplica aquí?" → "eso" necesita contexto
    - Usuario: "¿Dame un ejemplo" → ejemplo de qué? → necesita contexto
    """
    if not conversation_history:
        return ""

    # Detectar tema principal usando retrieval context si disponible
    main_topic = _extract_main_topic(conversation_history, base_context, user_context)
    topic_reminder = f"\nTEMA PRINCIPAL DE LA CONVERSACIÓN: {main_topic}\n" if main_topic else ""

    lines = [f"CONTEXTO RECIENTE:{topic_reminder}", ""]
    for msg in conversation_history[-8:]:  # Últimos 4 intercambios (8 mensajes max)
        sender_label = "Tú" if msg["sender"] == "user" else "Asistente"
        content = msg['content']
        # Truncar pero preservar suficiente para contexto
        if len(content) > 250:
            content = content[:250] + "..."
        lines.append(f"{sender_label}: {content}")
        lines.append("")

    return "\n".join(lines)


def _build_web_snippet_block(web_results: list[dict]) -> str:
    """Formatea los snippets web para el prompt (solo contenido, sin URLs)."""
    if not web_results:
        return "Sin resultados web disponibles."
 
    lines = []
    for i, r in enumerate(web_results, 1):
        lines.append(
            f"[Fuente web {i}]\n"
            f"Título: {r['title']}\n"
            f"Contenido: {r['content']}\n"
        )
    return "\n---\n".join(lines)
 
 
def _build_references_block(web_results: list[dict]) -> str:
    """Genera el bloque de referencias al final de la respuesta."""
    if not web_results:
        return ""
 
    lines = ["\n📚 Fuentes consultadas en internet:\n"]
    for i, r in enumerate(web_results, 1):
        lines.append(f"  {i}. {r['title']}\n     {r['url']}")
    return "\n".join(lines)

def _build_qa_prompt(
    question: str,
    base_context: list[str],
    user_context: list[str],
    web_results: list[dict] = None,
    used_web_fallback: bool = False,
    rag_similarity_score: float = 0.0,
    conversation_history: list[dict] = None,
) -> str:

    base_text = (
        "\n\n---\n\n".join(base_context)
        if base_context
        else "Sin contenido base."
    )

    user_text = (
        "\n\n---\n\n".join(user_context)
        if user_context
        else "Sin documentos del usuario."
    )

    conversation_section = ""
    if conversation_history:
        conv_context = _build_conversation_context_qa(conversation_history, base_context, user_context)
        if conv_context:
            conversation_section = f"\n{conv_context}\n"

    web_section = ""
    references_block = ""
    provenance_rule = ""

    # Solo usar web si NO hay contexto en los documentos
    has_relevant_context = bool(base_context or user_context) and rag_similarity_score >= 0.25

    if used_web_fallback and web_results and not has_relevant_context:
        web_block = _build_web_snippet_block(web_results)
        references_block = _build_references_block(web_results)
        web_section = f"""
=== INFORMACIÓN COMPLEMENTARIA DE INTERNET ===
(Los documentos indexados no tenían suficiente contexto para esta consulta.
La siguiente información proviene de búsqueda web.)

{web_block}

"""
        provenance_rule = f"""- Escribe tu respuesta de forma fluida y natural, SIN mencionar URLs ni fuentes dentro del texto.
- Al final de tu respuesta, incluye exactamente este bloque de referencias sin modificarlo:
{references_block}
"""

    return f"""
INSTRUCCIÓN CRÍTICA: Debes escribir SIEMPRE con mayúsculas al inicio de cada oración. Nunca escribas todo en minúsculas. Esto es obligatorio.
Eres un asistente académico inteligente y útil.

Tu tarea es responder preguntas usando:
1. Los documentos del usuario como fuente principal.
2. Los libros base como referencia académica de apoyo.
3. Información web (solo si está disponible en la sección correspondiente).
4. El historial conversacional para entender referencias indirectas.

⚠️ REGLA CRÍTICA SOBRE CONTEXTO CONVERSACIONAL:
Las preguntas que parecen "sueltas" o sin mucho contexto son JUSTAMENTE las que más necesitan
que uses el historial para ser entendidas correctamente.

EJEMPLOS:
- Usuario pregunta: "¿Por qué es importante?" → SIN mencionar tema previo
  RESPUESTA CORRECTA: Usa el historial para saber qué tema se está discutiendo
                     (ej: ley de ohm, photosíntesis, etc.) y explica por qué ESO es importante.
  RESPUESTA INCORRECTA: Hablar genéricamente sobre "importancia de la investigación"

- Usuario pregunta: "¿Eso también aplica aquí?" → "eso" es ambiguo
  RESPUESTA CORRECTA: Usa historial para saber a qué "eso" se refiere exactamente.

- Usuario pregunta: "Dame un ejemplo" → muy vago
  RESPUESTA CORRECTA: Del contexto anterior, sabe qué concepto necesita ejemplo.

Reglas de precedencia IMPORTANTÍSIMAS:
- Los LIBROS BASE son la fuente de verdad para información académica.
- El historial conversacional SOLO ayuda a entender a qué se refiere el usuario.
- NO reemplaces búsquedas en los documentos con información del historial.
- Si el usuario pregunta algo que requiere conocimiento de los libros, prioriza siempre eso.
- MANTÉN COHERENCIA DE TEMA: Si llevas 5 mensajes hablando de "ley de ohm"
  y el usuario hace una pregunta breve, asume que sigue siendo sobre "ley de ohm"
  a menos que cambie explícitamente de tema.

Reglas de formato OBLIGATORIAS:
- Empieza siempre con mayúscula.
- Usa mayúsculas correctamente en toda la respuesta (nombres propios, inicio de oraciones).
- NO uses asteriscos para negrillas (**texto**). Usa texto plano.
- NO uses markdown de ningún tipo.
- Organiza las ideas con saltos de línea y numeración simple (1. 2. 3.) sin negrillas.
- NO menciones URLs ni fuentes dentro de los párrafos. Las fuentes van solo al final.
{provenance_rule}

Reglas de contenido:
- Responde de forma natural y útil.
- Prioriza la información del documento del usuario cuando la pregunta sea sobre su archivo.
- Usa los libros base para complementar, corregir o contextualizar.
- Si la pregunta es sobre contenido académico general, responde con libros base
  e ignora el documento del usuario si no es relevante.
- Si la pregunta es directamente sobre el documento del usuario, usa ambas fuentes
  y puedes mencionar diferencias con los libros base.
- NO generes reportes de curaduría ni listas de inconsistencias a menos que el usuario lo solicite.
- No inventes información.
{conversation_section}
=== LIBROS BASE ===
{base_text}

=== DOCUMENTOS DEL USUARIO ===
{user_text}
{web_section}
Pregunta:
{question}

Respuesta:
"""
 
def _build_curate_prompt(
    question: str,
    base_context: list[str],
    user_context: list[str],
    suggestions: list[dict],
    analysis_error: Optional[str],
    web_results: list[dict] = None,
    used_web_fallback: bool = False,
    ) -> str:
        """
        Prompt de curaduría adaptativo:
        - Si el usuario pide mejoras o consejos → respuesta conversacional y directa.
        - Si el usuario pide análisis formal o reporte → respuesta estructurada completa.
        Sin markdown con asteriscos, usando texto plano y emojis para organizar.
        """
        base_text = "\n\n---\n\n".join(base_context) if base_context else "Sin contenido de libros base."
        user_text = "\n\n---\n\n".join(user_context)
    
        # Formatear sugerencias para el prompt
        if suggestions:
            suggestions_text = "\n".join([
                f"- [{s['type'].upper()} / severidad {s['severity']}] {s['description']} → Acción: {s['action']}"
                for s in suggestions
            ])
        elif analysis_error:
            suggestions_text = f"No se pudo completar el análisis automático: {analysis_error}"
        else:
            suggestions_text = "No se detectaron inconsistencias ni sugerencias relevantes."
        
        web_section = ""
        if used_web_fallback and web_results:
            web_block = _build_web_snippet_block(web_results)
            web_section = f"""
    === INFORMACIÓN COMPLEMENTARIA DE INTERNET ===
    (Los documentos indexados no tenían suficiente contexto.
    La siguiente información proviene de búsqueda web y debe citarse como tal.)
    
    {web_block}
    
    """
        provenance_rule = (
            "- Indica claramente si algún dato proviene de Internet (cita título y URL). "
            "Diferéncialos de los documentos indexados.\n"
            if used_web_fallback and web_results else ""
        )
    
        return f"""Eres un curador académico experto y amigable.

        El usuario hizo esta solicitud: "{question}"

        Analiza si es CONVERSACIONAL (mejoras, consejos) o FORMAL (reporte, analisis completo).

        Si es CONVERSACIONAL:
        - Responde de forma directa y natural, como si fuera una conversación.
        - Da sugerencias concretas y puntuales sin estructuras rígidas.
        - Usa un tono amigable y constructivo.
        - Usa emojis para que la conversación sea más amena.
        - No hagas un reporte completo, solo responde lo que preguntó.
        
        Si es FORMAL:
        - Organiza la respuesta en secciones claras usando emojis como separadores.
        - Ejemplo: "📋 Resumen", "🔍 Hallazgos", "✅ Recomendacion"
        - Sé detallado y profesional.
        
        REGLAS DE CONTENIDO (aplican siempre):
        - SIEMPRE usa los libros base como referencia para tus sugerencias.
        - Si el documento del usuario y los libros tienen temas en común, compáralos directamente
        señalando diferencias, gaps o contradicciones concretas.
        - Si el documento del usuario NO tiene relación directa con los libros, dilo claramente
        pero aun así indica qué temas de los libros debería considerar el usuario para
        enriquecer su documento, citando ejemplos concretos del contenido de los libros.
        - Nunca des sugerencias genéricas sin basarlas en el contenido real de los libros base
        {provenance_rule}
        REGLAS DE FORMATO (aplican siempre):
        - NO uses asteriscos para negrillas ni markdown (**texto**).
        - NO uses numeracion con puntos seguidos de texto en negrilla.
        - Usa texto plano, emojis para organizar si es necesario, y saltos de linea.
        - Escribe en español.

        === ANALISIS AUTOMATICO ===
        {suggestions_text}

        === LIBROS BASE ===
        {base_text}

        === DOCUMENTO DEL USUARIO ===
        {user_text}
        {web_section}
        Respuesta:"""


def generate(state: RAGState) -> dict:
    """
    Nodo 4 — Generación final con guardrails.
 
    Si retrieve ya detectó un input_error, retorna el mensaje de error
    directamente sin llamar al LLM ni gastar tokens.
 
    Incorpora snippets web en el prompt cuando used_web_fallback=True,
    indicando la procedencia de cada fragmento.
    """
    t0 = time.monotonic()
    trace_id = state.get("_trace_id")

    trace = None
    try:
        from observability.langfuse_client import get_langfuse_client
        lf = get_langfuse_client()
        if lf and trace_id:
            trace = lf.get_trace(trace_id)
    except Exception:
        pass

    with logger.contextualize(trace_id=trace_id or "-"):
        try:
            # ---------------------------------------------------
            # Guardrail de input — si retrieve ya lo rechazó
            # ---------------------------------------------------
            input_error = state.get("input_error")
            if input_error:
                logger.warning("generate_input_error_passthrough", error=input_error)
                return {"answer": f"Tu mensaje no pudo ser procesado: {input_error}"}

            # ---------------------------------------------------
            # Validación de seguridad secundaria
            # ---------------------------------------------------
            is_input_valid, validated_question, val_error = validate_input(state["question"])
            if not is_input_valid:
                error_answer = f"Tu mensaje no pudo ser procesado: {val_error}"
                logger.warning("guardrails_input_rejected_generate", error=val_error)
                return {"answer": error_answer}

            web_results = state.get("web_results", [])
            used_web_fallback = state.get("used_web_fallback", False)
            mode = state["mode"]

            # ---------------------------------------------------
            # CHAT
            # ---------------------------------------------------
            if mode == MODE_CHAT:
                conversation_section = ""
                if state.get("conversation_history"):
                    conv_context = _build_conversation_context_chat(state["conversation_history"])
                    if conv_context:
                        conversation_section = f"\n{conv_context}\n"

                prompt = f"""
    Eres un asistente conversacional amigable.
    {conversation_section}
    Responde naturalmente al usuario.

    Mensaje:
    {validated_question}
    """

            # ---------------------------------------------------
            # CURATE
            # ---------------------------------------------------
            elif mode == MODE_CURATE:
                prompt = _build_curate_prompt(
                    question=validated_question,
                    base_context=state["base_context"],
                    user_context=state["user_context"],
                    suggestions=state.get("suggestions", []),
                    analysis_error=state.get("analysis_error"),
                    web_results=web_results,
                    used_web_fallback=used_web_fallback,
                )

            # ---------------------------------------------------
            # QA
            # ---------------------------------------------------
            else:
                prompt = _build_qa_prompt(
                    question=validated_question,
                    base_context=state["base_context"],
                    user_context=state["user_context"],
                    web_results=web_results,
                    used_web_fallback=used_web_fallback,
                    rag_similarity_score=state.get("rag_similarity_score", 0.0),
                    conversation_history=state.get("conversation_history"),
                )

            llm = ChatGroq(
                model=settings.GROQ_MODEL,
                api_key=settings.GROQ_API_KEY,
                temperature=0,
            )

            response = llm.invoke([HumanMessage(content=prompt)])
            latency_ms = int((time.monotonic() - t0) * 1000)
            usage = response.response_metadata.get("token_usage", {})

            # ---------------------------------------------------
            # Validar output con guardrails
            # ---------------------------------------------------
            is_output_valid, validated_answer, output_error = validate_output(response.content)

            if not is_output_valid:
                error_answer = f"La respuesta generada no pasó la validación: {output_error}\nPor favor reformula tu pregunta."
                logger.warning("guardrails_output_rejected", error=output_error, latency_ms=latency_ms)
                if trace:
                    try:
                        trace.update(level="ERROR", status_message=f"guardrail: {output_error}")
                    except Exception:
                        pass
                flush_langfuse()
                return {"answer": error_answer}

            logger.info(
                "generate_ok",
                mode=mode,
                latency_ms=latency_ms,
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
            )

            if trace:
                try:
                    from langfuse.model import ModelUsage
                    trace.generation(
                        name="llm_generate",
                        model=settings.GROQ_MODEL,
                        input=prompt,
                        output=validated_answer,
                        usage=ModelUsage(
                            input=usage.get("prompt_tokens", 0),
                            output=usage.get("completion_tokens", 0),
                        ),
                        metadata={"latency_ms": latency_ms, "mode": mode},
                    )
                    trace.update(
                        output={"answer": validated_answer},
                        metadata={"total_latency_ms": latency_ms, "mode": mode},
                    )
                except Exception as lf_exc:
                    logger.warning("langfuse_generation_failed", node="generate", error=str(lf_exc))

            flush_langfuse()
            return {"answer": validated_answer}

        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error("generate_error", error=str(exc), latency_ms=latency_ms)
            if trace:
                try:
                    trace.update(level="ERROR", status_message=str(exc))
                except Exception:
                    pass
            flush_langfuse()
            return {"answer": f"Error al generar la respuesta: {exc}\nPor favor intenta nuevamente."}
# ---------------------------------------------------------------------------
# Router y construccion del grafo
# ---------------------------------------------------------------------------
def route_after_retrieve(state: RAGState) -> str:
    """
   Decide el siguiente nodo después de retrieve.
 
    Lógica:
    - Si hay input_error → generate (responde el error directamente)
    - Si el score RAG está por debajo del umbral → web_search (fallback)
    - Si es modo CURATE con user_context → analyze
    - En cualquier otro caso → generate
    """
    
    

    # Input inválido: ir directo a generate sin búsquedas
    if state.get("input_error"):
        return "generate"
 
    mode = state["mode"]
    score = state.get("rag_similarity_score", 1.0)
    threshold = getattr(settings, "WEB_SEARCH_SIMILARITY_THRESHOLD", 0.4)
 
    # Chat nunca va a web
    if mode == MODE_CHAT:
        return "generate"
 
    # Score bajo → activar fallback web
    if score < threshold:
        print(f"[router] Score {score:.3f} < umbral {threshold} → activando web_search")
        return "web_search"
 
    # Score suficiente: routing normal
    if mode == MODE_CURATE and state.get("user_context"):
        return "analyze"
 
    return "generate"
 
def route_after_web_search(state: RAGState) -> str:
    """
    Decide el siguiente nodo después de web_search.
 
    - CURATE con user_context → analyze
    - QA / CURATE sin user_context → generate
    """
    if (
        state["mode"] == MODE_CURATE
        and state.get("user_context")
    ):
        return "analyze"
 
    return "generate"

# ---------------------------------------------------------------------------
# Construcción del grafo
# Flujo QA:     START → retrieve → generate → END
# Flujo Curate: START → retrieve → analyze → generate → END
# ---------------------------------------------------------------------------
def build_rag_graph():
    """
    Crea y compila el grafo con routing condicional + nodo de búsqueda web.
    
 
    El nodo retrieve determina el modo según si hay documentos del usuario
    en ChromaDB, y el router decide si pasar por analyze o ir directo a generate.
    """
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("web_search", web_search)
    graph.add_node("analyze", analyze)
    graph.add_node("generate", generate)
    graph.set_entry_point("retrieve")
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "web_search": "web_search",
            "analyze": "analyze",
            "generate": "generate",
        },
    )
    graph.add_conditional_edges(
        "web_search",
        route_after_web_search,
        {
            "analyze": "analyze",
            "generate": "generate",
        },
    )
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


rag_chain = build_rag_graph()