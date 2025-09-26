# 📚 rag-on-me — Minimal RAG API (FastAPI • LangGraph • pgvector)

*A small, clean Retrieval-Augmented Generation (RAG) service I built to show end-to-end RAG: ingestion → retrieval → generation, with conversation state stored in Postgres.*

---

## 🚀 Introduction

I built **rag-on-me** to learn (and show) how the moving parts of a RAG system fit together without tons of framework magic. It wires **FastAPI** to a **LangGraph** pipeline, stores embeddings in **Postgres + pgvector**, and uses **OpenAI** for chat + embeddings.

What it demonstrates:

* Ingesting markdown into a vector store
* A simple **retrieve → generate** graph with LangGraph
* **Checkpointed conversations** (multi-turn state in Postgres)

It’s intentionally compact and easy to read so you can follow the flow from HTTP request to LLM response.

---

## 🌐 Live Demo

👉 **[SOON]**

---

## 🎯 Features

* **RAG in under 1K lines** — minimal glue, maximum clarity
* **Markdown ingestion** — load `cv.md` into pgvector (easy to swap sources)
* **Threaded chat** — each `thread_id` keeps its own conversation state
* **Postgres-backed checkpoints** — resume conversations reliably
* **Batteries-included HTTP** — `POST /initialize`, `POST /chat`, `GET /graph/state`

---

## 🧭 How It Works (High Level)

**Client → FastAPI → LangGraph → Vector Store + LLM → Postgres (checkpoints)**

Key modules:

* `app/main.py` — FastAPI app, startup lifecycle, graph compile
* `app/modules/rag/graph_runtime.py` — graph wiring (retrieve → generate)
* `app/modules/rag/nodes.py` — retrieval + generation nodes
* `app/modules/rag/adapters.py` — singletons for LLM, embeddings, vector store
* `app/modules/ingest/ingest.py` — markdown ingestion utilities

---

## 🛠️ Setup (Local)

**Requirements:** Python 3.12, Docker (for Postgres + pgvector)

1. Start the database

```bash
docker compose --profile local -f docker/compose.yaml up -d
```

2. Configure environment

```bash
cp .env.example .env
# fill in: OPENAI_API_KEY, POSTGRES_* …
```

3. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. (Optional) Ingest the sample CV

```bash
curl -X POST "http://localhost:8000/initialize" \
  -H "Content-Type: application/json" \
  -d '{"file_name":"cv.md"}'
```

5. Chat with the graph

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"human","content":"Who is Jose?"}], "thread_id":"demo-1"}'
```

---

## ⚙️ Configuration

* `OPENAI_API_KEY` — your OpenAI key
* `OPENAI_CHAT_MODEL` — default chat model **[NEEDS CONFIRMATION: e.g., gpt-5-nano]**
* `OPENAI_EMBEDDING_MODEL` — default embeddings (currently `text-embedding-3-large`)
* `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`
* `LANGSMITH_TRACING`, `LANGSMITH_API_KEY` — optional tracing **[NEEDS CONFIRMATION]**

---

## 🖥️ API (Quick Reference)

* `POST /health` → `{ "status": "healthy" }`
* `POST /initialize` → `{ "file_name": "cv.md" }` (ingests the doc into pgvector)
* `POST /chat` → send messages + optional `thread_id`

**Example request**

```json
{
  "messages": [
    { "role": "human", "content": "Tell me about the CV." }
  ],
  "thread_id": "demo-1"
}
```

**Example response** (**shape simplified**)

```json
{
  "output": {
    "message": "Jose is a software engineer with..."
  }
}
```

> **[NEEDS CONFIRMATION]** The code may currently return `{"output": {"messages": "<string>"}}`. I plan to standardize on `{"message": "<string>"}` in a near-term update.

---

## 📂 Project Structure

```
├── app/
│   ├── main.py                 # FastAPI app
│   ├── core/config.py          # env + DB helpers
│   ├── modules/
│   │   ├── ingest/             # ingestion utilities
│   │   └── rag/                # graph, nodes, adapters, schemas
│   └── sources/                # sample docs (cv.md)
├── docker/compose.yaml         # local Postgres + pgvector
├── requirements.txt
├── backlogs.md                 # improvement plan
└── README.md
```

---

## 🔎 Notes & Conventions

* **Singleton clients** via `@lru_cache` for LLM, embeddings, and vector store
* **LangGraph `StateGraph`** using `MessagesState` (messages live at `"messages"`)
* **Checkpointing** via LangGraph `PostgresSaver` (psycopg-style DSN)
* **Ingestion defaults**: chunk size ~1000, overlap 100 **[NEEDS CONFIRMATION]**

---

## 🔭 Roadmap

Short, high-impact updates I plan to tackle next:

* **Input validation & response shape** — normalize roles, cap sizes, and standardize `{"message": ...}`
* **History trimming** — rolling window + (optional) summary for long chats
* **Async end-to-end** — convert handlers + clients to async for better concurrency
* **Streaming** — `/chat/stream` with SSE for token-by-token replies
* **Retrieval tuning** — `k`, namespace filters, dedupe + pre-formatted context
* **Idempotent ingestion** — prevent duplicate vectors on re-runs
* **Security & ops** — tighter CORS, optional API key, basic rate limits **[NEEDS CONFIRMATION]**
* **Observability** — request IDs in logs; tokens/latency metrics **[NEEDS CONFIRMATION: Prometheus + OpenTelemetry]**

---

## 📄 License

MIT

---

## ✨ Recruiter-Friendly Closing Note

I built **rag-on-me** to show that I can **design and ship** more than a notebook demo. It’s a production-flavored RAG slice: clean API, clear data flow, and deliberate trade-offs. The value isn’t just that it answers questions—it’s that the code makes it easy to **extend** (streaming, better retrieval, stricter validation) and **operate** (checkpoints, logs, config).

If you’re evaluating me for a role that touches **LLM apps, platform, or ML tooling**, this repo reflects how I think: start simple, keep it readable, measure what matters, and iterate with intent.