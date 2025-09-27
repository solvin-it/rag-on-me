from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .modules.ingest.ingest import ingest_markdown_file
from .modules.rag.graph_runtime import build_graph
from .modules.rag.schemas import ChatRequest, ChatResponse, ChatMessage

from langgraph.checkpoint.postgres import PostgresSaver
from pathlib import Path
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Expose readiness state and return 503 until the graph compiles successfully.
    # Startup code
    try:
        logging.info("Starting up and compiling the graph...")
        with PostgresSaver.from_conn_string(settings.get_checkpoint_url()) as saver:
            # TODO: Add retention policy to prune old checkpoints per thread.
            # TODO: Document enabling LANGGRAPH_AES_KEY so checkpoint data can be encrypted at rest.
            saver.setup()  # create tables if missing
            graph = build_graph().compile(checkpointer=saver)
            app.state.checkpointer = saver
            app.state.graph = graph

            logging.info("Graph compiled successfully.")
            yield
    except Exception as e:
        logging.error(f"Failed to compile the graph: {e}")
        raise e
    # Shutdown code

openapi_tags = [
    {"name": "Health", "description": "Liveness and readiness endpoints."},
    {"name": "Initialization", "description": "Ingest and initialize vector store."},
    {"name": "Chat", "description": "Chat endpoints backed by LangGraph RAG pipeline."},
    {"name": "Debug", "description": "Debugging and inspection endpoints for the graph state."},
]

app = FastAPI(
    title="RAG-on-me",
    description=(
        "Lightweight Retrieval-Augmented-Generation (RAG) demo that wires a FastAPI HTTP "
        "surface to a LangGraph runtime, a Postgres+pgvector vector store, and OpenAI models."
    ),
    version="0.1.0",
    contact={"name": "Solvin", "url": "https://solvin.co", "email": "josefernando.a.gonzales@gmail.com"},
    license_info={"name": "MIT"},
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# TODO: Restrict default origins and require API key authentication in production deployments.

@app.post("/health", tags=["Health"], summary="Liveness check")
def health_check():
    # TODO: Surface readiness information (graph compiled, dependencies reachable) in the health response.
    return {"status": "healthy"}

@app.post("/initialize", tags=["Initialization"], summary="Ingest a source file into the vector store")
def initialize(file_name: str):
    """Initializes the vector store by ingesting a markdown file located in the app/sources folder.

    Only `cv.md` is supported at the moment.
    """

    if file_name not in ("cv.md", "faq.md"):
        raise HTTPException(status_code=400, detail="Only 'cv.md' and 'faq.md' are supported at the moment.")

    app_dir = Path(__file__).resolve().parent
    sources_dir = app_dir / "sources"
    file_path = sources_dir / file_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found in app/sources: {file_name}")

    try:
        # TODO: Make ingestion idempotent to avoid duplicate documents on repeated runs.
        ingest_markdown_file(file_path=str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return {"status": "initialization complete"}

@app.post("/chat", response_model=ChatResponse, tags=["Chat"], summary="Run a chat turn through the RAG graph")
def chat(request: ChatRequest):
    """Handles chat requests through LangGraph and persists checkpoints with PostgresSaver.

    The request expects a `ChatRequest` (see `app/modules/rag/schemas.py`). The response contains
    a `ChatResponse` with `output`, `checkpoint_id`, and `num_messages`.
    """
    # TODO: Convert to async FastAPI handler so downstream graph calls don't block the event loop.
    # TODO: Enforce input validation for payload size and message count before invoking the graph.
    # TODO: Normalize incoming roles (user/assistant/system) and reject unsupported values early.
    if not request.messages or request.messages[-1].role not in ("human", "user"):
        raise HTTPException(status_code=400, detail="The last message must be from the user.")
    
    # Prepare the config and thread ID
    config = {"configurable": {"thread_id": request.thread_id}}

    # Convert ChatMessage to the format expected by the graph
    state = {"messages": [ChatMessage(role=msg.role, content=msg.content).model_dump() for msg in request.messages]}

    try:
        app.state.graph.invoke(state, config=config)
    except Exception as e:
        logging.error(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {e}")

    # Save the checkpoint ID
    snap = app.state.graph.get_state(config)
    checkpoint_id = snap.config["configurable"].get("checkpoint_id")

    # Get the last AI message as the response
    # TODO: Trim or summarize older history before invoking the model to control token usage.
    # TODO: Implement helper that returns the most recent assistant response even with tool call interleaving.
    last_message = snap.values.get("messages", [])[-1] if snap.values.get("messages") else None

    logging.info(f"Chat processed with thread ID: {request.thread_id}, checkpoint ID: {checkpoint_id}")
    # TODO: Attach request-scoped IDs and structured metrics to logs and responses for observability.

    response = ChatResponse(
        # TODO: Standardize response shape to either a single message or a messages list.
        output={"messages": last_message.content} if last_message else {"messages": []},
        checkpoint_id=checkpoint_id,
        num_messages=len(snap.values.get("messages", []))
    )

    return response

# TODO: Add a /chat/stream endpoint using SSE to stream token-by-token responses.

@app.get("/graph/state", tags=["Debug"], summary="Inspect LangGraph state for a thread")
def get_graph_state(thread_id: str | None = None):
    """Returns the current state of the LangGraph for a `thread_id` for debugging and inspection."""
    try:
        snap = app.state.graph.get_state({"configurable": {"thread_id": thread_id}})
        checkpoint_id = snap.config["configurable"].get("checkpoint_id")
        return {
            "state": snap.values,
            "config": snap.config,
            "checkpoint_id": checkpoint_id,
            "num_messages": len(snap.values.get("messages", [])),
            "last_role": snap.values.get("messages", [])[-1].role if snap.values.get("messages") else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph state: {e}")