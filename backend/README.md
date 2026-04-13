# RAG MVP — FastAPI + LangGraph + ChromaDB + Groq

API para responder preguntas sobre documentos PDF usando Retrieval-Augmented Generation.

## Stack

| Capa | Tecnología |
|---|---|
| API | FastAPI |
| Orquestación RAG | LangGraph |
| Vector DB | ChromaDB (contenedor) |
| LLM | Groq (`llama-3.1-8b-instant`) |
| Embeddings | `all-MiniLM-L6-v2` (local, gratis) |
| Contenedores | Docker + Docker Compose |

## Estructura del proyecto

```
backend/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── src/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py           ← FastAPI app
    ├── config.py         ← Configuración centralizada
    ├── api/
    │   └── routes.py     ← Endpoints: /upload, /ask
    ├── rag/
    │   ├── ingest.py     ← Parseo PDF → chunks → ChromaDB
    │   └── graph.py      ← Grafo LangGraph: retrieve → generate
    └── db/
        └── chroma_client.py  ← Conexión a ChromaDB
```

## Setup inicial (una sola vez por integrante)

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd backend
```

### 2. Obtener una API Key de Groq (gratis)

1. Ir a [console.groq.com](https://console.groq.com)
2. Crear cuenta → **API Keys** → **Create API Key**
3. Copiar la key

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y reemplazar `your_groq_api_key_here` con tu key real:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **NUNCA** subas el archivo `.env` al repositorio. Ya está en `.gitignore`.

### 4. Levantar los servicios

```bash
docker compose up --build
```

> La primera vez tarda varios minutos porque:
> - Instala todas las dependencias de Python
> - Descarga el modelo de embeddings (~90 MB) dentro de la imagen
>
> Las veces siguientes es mucho más rápido gracias al caché de Docker.

### 5. Verificar que todo está corriendo

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

También puedes abrir la documentación interactiva en:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Uso de la API

### Subir un PDF

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@mi_documento.pdf"
```

Respuesta:
```json
{
  "filename": "mi_documento.pdf",
  "chunks_indexed": 42,
  "message": "'mi_documento.pdf' indexado correctamente en 42 fragmentos."
}
```

### Hacer una pregunta

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿De qué trata el documento?"}'
```

Respuesta:
```json
{
  "question": "¿De qué trata el documento?",
  "answer": "El documento trata sobre..."
}
```

---

## Comandos útiles

| Comando | Descripción |
|---|---|
| `docker compose up --build` | Primera vez o tras cambiar requirements.txt |
| `docker compose up` | Levantar servicios (sin rebuild) |
| `docker compose down` | Detener y eliminar contenedores |
| `docker compose down -v` | Detener y **borrar** también los datos de ChromaDB |
| `docker compose logs -f backend` | Ver logs del backend en tiempo real |
| `docker compose logs -f chromadb` | Ver logs de ChromaDB |

> 💡 El código del backend tiene **hot-reload** activado. Al guardar un archivo `.py`, FastAPI se reinicia automáticamente sin necesidad de reconstruir la imagen.

---

## Flujo del RAG

```
Usuario sube PDF
      │
      ▼
  parse_pdf()          ← pypdf extrae el texto
      │
      ▼
split_into_chunks()    ← RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
      │
      ▼
  embeddings           ← all-MiniLM-L6-v2 (local)
      │
      ▼
   ChromaDB            ← almacenamiento vectorial persistente

─────────────────────────────────────────────

Usuario hace pregunta
      │
      ▼
 [Nodo: retrieve]      ← busca top-4 chunks más similares en ChromaDB
      │
      ▼
 [Nodo: generate]      ← construye prompt con contexto y llama a Groq
      │
      ▼
   Respuesta
```

---

## Variables de entorno disponibles

Todas tienen valores por defecto excepto `GROQ_API_KEY`.

| Variable | Por defecto | Descripción |
|---|---|---|
| `GROQ_API_KEY` | — | **Requerida.** API key de Groq |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Modelo de Groq a usar |
| `CHROMA_HOST` | `chromadb` | Host del servicio ChromaDB |
| `CHROMA_PORT` | `8000` | Puerto del servicio ChromaDB |
| `COLLECTION_NAME` | `documents` | Nombre de la colección en ChromaDB |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Modelo de embeddings |
| `CHUNK_SIZE` | `1000` | Tamaño de cada chunk en caracteres |
| `CHUNK_OVERLAP` | `200` | Overlap entre chunks |
| `RETRIEVER_K` | `4` | Número de chunks a recuperar por query |
