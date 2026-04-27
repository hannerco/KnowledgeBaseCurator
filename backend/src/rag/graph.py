"""Definicion del grafo RAG con LangGraph.

El pipeline tiene dos nodos principales:
1) retrieve: recupera contexto relevante desde ChromaDB,
2) generate: construye el prompt y genera la respuesta con Groq.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from db.chroma_client import get_vectorstore
from config import settings


# ---------------------------------------------------------------------------
# Estado del grafo
# Cada nodo recibe este estado y retorna un dict con los campos que modifica.
# ---------------------------------------------------------------------------
class RAGState(TypedDict):
    """Estado compartido entre nodos del grafo RAG."""

    question: str
    context: list[str]
    answer: str


# ---------------------------------------------------------------------------
# Nodos del grafo
# ---------------------------------------------------------------------------
def retrieve(state: RAGState) -> dict:
    """
    Nodo 1 — Recuperación.
    Busca en ChromaDB los chunks más relevantes para la pregunta del usuario.
    """
    # Se reutiliza la configuracion de retrieval centralizada en settings.
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": settings.RETRIEVER_K}
    )
    # Cada documento recuperado aporta un fragmento de contexto textual.
    docs = retriever.invoke(state["question"])
    return {"context": [doc.page_content for doc in docs]}


def generate(state: RAGState) -> dict:
    """
    Nodo 2 — Generación.
    Construye el prompt con el contexto recuperado y llama a Groq.
    """
    # Unifica los chunks recuperados en un solo bloque para el prompt.
    context_text = "\n\n---\n\n".join(state["context"])
    print("Contexto recuperado para la pregunta:\n", context_text)  # Debug: muestra el contexto antes de generar la respuesta.

    prompt = f"""Eres un asistente experto. Responde la pregunta basándote ÚNICAMENTE en el los datos proporcionados en el contexto el cual te pasaré a continuación.
    Si no encuentras una respuesta clara en el contexto, responde: "No encontré información suficiente en los documentos para responder esa pregunta."

Contexto:
{context_text}

Pregunta: {state["question"]}"""

    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )
    # Se usa HumanMessage para invocar el chat model de forma explicita.
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"answer": response.content}


# ---------------------------------------------------------------------------
# Construcción del grafo
# Flujo: START → retrieve → generate → END
# ---------------------------------------------------------------------------
def build_rag_graph():
    """Crea y compila el grafo con el orden fijo retrieve -> generate."""

    graph = StateGraph(RAGState)

    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# Se compila una sola vez al importar el modulo para reducir overhead por request.
rag_chain = build_rag_graph()
