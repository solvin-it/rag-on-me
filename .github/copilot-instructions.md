## Purpose

Short, focused guidance for coding agents working on rag-on-me. Use these notes to make small, safe edits and to implement features that fit existing conventions.

## Big-picture architecture (what to read first)
- Entry: `app/main.py` — FastAPI app, lifespan that compiles a LangGraph `StateGraph` and attaches a `PostgresSaver` checkpointer.
- RAG graph: `app/modules/rag/graph_runtime.py` builds the graph (nodes: `query_or_respond`, `retrieve`, `generate`).
- Node implementations: `app/modules/rag/nodes.py` — contains the retrieval tool, the tool-wiring pattern, and the generator node.
- Adapters: `app/modules/rag/adapters.py` — singletons for LLM, embeddings and PGVector store (use `lru_cache` for singletons).
- Ingestion: `app/modules/ingest/ingest.py` — markdown ingestion using `UnstructuredMarkdownLoader` and `RecursiveCharacterTextSplitter`.

Read those four files in order to understand the main control flow: incoming HTTP -> graph.invoke -> nodes -> vector store / llm -> checkpointer.

## Developer workflows & commands
- Local DB (dev): `docker/compose.yaml` contains a `db` service. Start it for local testing:

  docker compose --profile local -f docker/compose.yaml up -d

- Run the app (from repo root, using the provided `env/` venv or your environment):

  env/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

- Useful endpoints:
  - `POST /health` — quick liveness check.
  - `POST /initialize` — expects `file_name` (currently only `cv.md`) and will call `ingest_markdown_file`.
  - `POST /chat` — accepts `ChatRequest` (see `app/modules/rag/schemas.py`) and returns `ChatResponse`.
  - `GET /graph/state` — debug endpoint to inspect the current LangGraph snapshot for a `thread_id`.

## Data shapes & examples (concrete)
- `ChatRequest` (see `app/modules/rag/schemas.py`) = { "messages": [ { "role": "human", "content": "..." }, ... ], "thread_id": "optional" }
- `POST /initialize` body: application/json or form param `file_name: "cv.md"` — only `app/sources/cv.md` is supported today.
- Note: `ChatResponse.output` currently contains `{"messages": <string>}` (code returns a single string), so code that consumes it may expect a string rather than a list.

## Project-specific conventions & patterns
- Singletons: `get_llm()`, `get_embeddings()`, `get_vector_store()` use `@lru_cache` to return process-singleton clients. Preserve this pattern when adding clients.
- LangGraph usage:
  - Graph is a `StateGraph(MessagesState)`; nodes accept/return dictionaries where the key `"messages"` is the canonical message list.
  - Tool pattern: `retrieve_tool` returns `(serialized_content, artifact)` and is wrapped with `ToolNode` in `nodes.py`.
- Checkpointing: `PostgresSaver.from_conn_string(settings.get_checkpoint_url())` is used at startup. There are two DB URL helpers in `app/core/config.py`: one for SQLAlchemy (`get_database_url`) and one for the psycopg checkpointer (`get_checkpoint_url`). Use the correct one depending on the library.
- Ingestion: `ingest_markdown_file()` splits docs with chunk_size=1000, chunk_overlap=100 and adds `metadata['source']` with `filename-chunk-i`.

## Integration points & external deps
- OpenAI (models configured in `app/core/config.py` via `OPENAI_*` env vars).
- Postgres + pgvector (docker/compose.yaml uses `pgvector/pgvector:pg17-trixie`).
- LangGraph / LangChain / LangChain Postgres adapters: see `requirements.txt` for pinned packages.

## Quick debugging tips
- If startup fails, logs from the `lifespan` block in `app/main.py` will show graph compilation errors.
- Use `GET /graph/state?thread_id=<id>` to inspect messages, last_role and checkpoint id.
- Be careful with blocking I/O in endpoints — many libs have async variants (the README contains guidance about switching to async endpoints).

## When you change behavior, update these files
- `app/main.py` — HTTP API surface & lifecycle.
- `app/modules/rag/nodes.py` and `graph_runtime.py` — core RAG behavior.
- `app/modules/rag/adapters.py` — client creation (LLM/embeddings/vector store).
- `app/modules/ingest/ingest.py` and `app/sources/` — ingestion behavior and supported source files.

If anything above is unclear or you want more examples (sample `curl` bodies, typical logs, or a small unit test harness), tell me which area to expand and I'll iterate.
