"""Definicion del grafo RAG con LangGraph.

Flujo QA:     START -> retrieve -> generate -> END
Flujo Curate: START -> retrieve -> analyze -> generate -> END

Observabilidad:
    - Cada invocacion crea un trace en Langfuse con spans por nodo.
    - Las llamadas LLM se registran como Generation (tokens + latencia).
    - Los errores se marcan en el span sin interrumpir el flujo.
    - Todos los logs incluyen trace_id para correlacion con Langfuse.
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

# ---------------------------------------------------------------------------
# Constantes de modo
# ---------------------------------------------------------------------------
MODE_CHAT = "chat"
MODE_QA = "qa"
MODE_CURATE = "curate"


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
    base_context: list[str]
    user_context: list[str]
    user_files: list[str]
    suggestions: list[dict]
    analysis_error: Optional[str]
    answer: str
    mode: str
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
def _retrieve_by_type(
    question: str,
    document_type: str,
    k: int,
    user_files: list[str] = None,
) -> list[str]:
    try:
        vectorstore = get_vectorstore()

        filter_dict = {"document_type": document_type}
        if document_type == "user_upload" and user_files:
            if len(user_files) == 1:
                filter_dict = {
                    "$and": [
                        {"document_type": document_type},
                        {"source": user_files[0]},
                    ]
                }
            else:
                filter_dict = {
                    "$and": [
                        {"document_type": document_type},
                        {"source": {"$in": user_files}},
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
        return [doc.page_content for doc in docs]

    except Exception as exc:
        logger.warning("retrieve_warning", document_type=document_type, error=str(exc))
        return []


# ---------------------------------------------------------------------------
# Nodo 1 — Recuperacion
# ---------------------------------------------------------------------------
def retrieve(state: RAGState) -> dict:
    """Crea el trace raiz y el span de recuperacion."""
    t0 = time.monotonic()
    question = state["question"]

    trace = create_trace(name="rag_pipeline", metadata={"question": question})
    trace_id = trace.id if trace else None

    with logger.contextualize(trace_id=trace_id or "-"):
        span = trace.span(name="retrieve", input={"question": question}) if trace else None

        try:
            mode = detect_intent(question, trace=trace)

            if mode == MODE_CHAT:
                base_chunks, user_chunks = [], []
            else:
                base_chunks = _retrieve_by_type(question, "base_knowledge", settings.RETRIEVER_K)
                user_chunks = _retrieve_by_type(
                    question, "user_upload", settings.RETRIEVER_K,
                    user_files=state.get("user_files", []),
                )

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
        "_trace_id": trace_id,
    }


# ---------------------------------------------------------------------------
# Nodo 2 — Analisis de inconsistencias
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
    """Nodo 2 — Analisis con span Langfuse."""
    if not state.get("user_context"):
        return {"suggestions": [], "analysis_error": None}

    if not state.get("base_context"):
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
            validated = []
            for s in parsed.get("suggestions", []):
                if not isinstance(s, dict):
                    continue
                validated.append({
                    "type": s.get("type", "no_support"),
                    "description": s.get("description", "Sin descripcion"),
                    "action": s.get("action", "Revisar manualmente"),
                    "severity": s.get("severity", "medium"),
                    "base_reference": s.get("base_reference", ""),
                })

            logger.info(
                "analyze_ok",
                suggestions_count=len(validated),
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
                        metadata={"latency_ms": latency_ms, "suggestions_count": len(validated)},
                    )
                except Exception as lf_exc:
                    logger.warning("langfuse_generation_failed", node="analyze", error=str(lf_exc))

            if span:
                span.end(output={"suggestions_count": len(validated), "latency_ms": latency_ms})

            return {"suggestions": validated, "analysis_error": None}

        except json.JSONDecodeError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            error_msg = f"Error al parsear respuesta del analisis: {exc}"
            logger.error("analyze_json_error", error=error_msg, latency_ms=latency_ms)
            if span:
                span.end(level="ERROR", status_message=error_msg)
            return {"suggestions": [], "analysis_error": error_msg}

        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            error_msg = f"Error inesperado durante el analisis: {exc}"
            logger.error("analyze_error", error=error_msg, latency_ms=latency_ms)
            if span:
                span.end(level="ERROR", status_message=error_msg)
            return {"suggestions": [], "analysis_error": error_msg}


# ---------------------------------------------------------------------------
# Nodo 3 — Generacion de respuesta final
# ---------------------------------------------------------------------------
def _build_qa_prompt(question, base_context, user_context) -> str:
    base_text = "\n\n---\n\n".join(base_context) if base_context else "Sin contenido base."
    user_text = "\n\n---\n\n".join(user_context) if user_context else "Sin documentos del usuario."

    return f"""
Eres un asistente academico inteligente y util.

Tu tarea es responder preguntas usando:
1. Los documentos del usuario como fuente principal.
2. Los libros base como referencia academica de apoyo.

Reglas:
- Prioriza el documento del usuario cuando la pregunta sea sobre su archivo.
- Usa los libros base para complementar o contextualizar.
- No inventes informacion.

=== LIBROS BASE ===
{base_text}

=== DOCUMENTOS DEL USUARIO ===
{user_text}

Pregunta:
{question}

Respuesta:
"""


def _build_curate_prompt(question, base_context, user_context, suggestions, analysis_error) -> str:
    base_text = "\n\n---\n\n".join(base_context) if base_context else "Sin contenido de libros base."
    user_text = "\n\n---\n\n".join(user_context)

    if suggestions:
        suggestions_text = "\n".join([
            f"- [{s['type'].upper()} / severidad {s['severity']}] {s['description']} -> Accion: {s['action']}"
            for s in suggestions
        ])
    elif analysis_error:
        suggestions_text = f"No se pudo completar el analisis automatico: {analysis_error}"
    else:
        suggestions_text = "No se detectaron inconsistencias ni sugerencias relevantes."

    return f"""Eres un curador academico experto y amigable.

        El usuario hizo esta solicitud: "{question}"

        Analiza si es CONVERSACIONAL (mejoras, consejos) o FORMAL (reporte, analisis completo).

        Si es CONVERSACIONAL: responde directo, tono amigable, sin estructura rigida.
        Si es FORMAL: organiza en secciones con emojis como separadores.

        REGLAS:
        - Basa siempre tus sugerencias en el contenido real de los libros base.
        - NO uses asteriscos (**texto**), usa texto plano.
        - Escribe en espanol.

        === ANALISIS AUTOMATICO ===
        {suggestions_text}

        === LIBROS BASE ===
        {base_text}

        === DOCUMENTO DEL USUARIO ===
        {user_text}

        Respuesta:"""


def generate(state: RAGState) -> dict:
    """Nodo 3 — Generacion con Generation Langfuse.
    Registra prompt, completion, tokens de Groq y latencia.
    Cierra el trace con el resultado final.
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
            mode = state["mode"]

            if mode == MODE_CHAT:
                prompt = f"Eres un asistente conversacional amigable.\nResponde naturalmente al usuario.\nMensaje:\n{state['question']}"
            elif mode == MODE_CURATE:
                prompt = _build_curate_prompt(
                    question=state["question"],
                    base_context=state["base_context"],
                    user_context=state["user_context"],
                    suggestions=state.get("suggestions", []),
                    analysis_error=state.get("analysis_error"),
                )
            else:
                prompt = _build_qa_prompt(
                    question=state["question"],
                    base_context=state["base_context"],
                    user_context=state["user_context"],
                )

            llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY, temperature=0)
            response = llm.invoke([HumanMessage(content=prompt)])
            latency_ms = int((time.monotonic() - t0) * 1000)
            usage = response.response_metadata.get("token_usage", {})

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
                        output=response.content,
                        usage=ModelUsage(
                            input=usage.get("prompt_tokens", 0),
                            output=usage.get("completion_tokens", 0),
                        ),
                        metadata={"latency_ms": latency_ms, "mode": mode},
                    )
                    trace.update(
                        output={"answer": response.content},
                        metadata={"total_latency_ms": latency_ms, "mode": mode},
                    )
                except Exception as lf_exc:
                    logger.warning("langfuse_generation_failed", node="generate", error=str(lf_exc))

            flush_langfuse()
            return {"answer": response.content}

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
    if state["mode"] == MODE_CURATE and state.get("user_context"):
        return "analyze"
    return "generate"


def build_rag_graph():
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("analyze", analyze)
    graph.add_node("generate", generate)
    graph.set_entry_point("retrieve")
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"analyze": "analyze", "generate": "generate"},
    )
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


rag_chain = build_rag_graph()