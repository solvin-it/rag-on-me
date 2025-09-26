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
    # Startup code
    try:
        logging.info("Starting up and compiling the graph...")
        with PostgresSaver.from_conn_string(settings.get_checkpoint_url()) as saver:
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

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/initialize")
def initialize(file_name: str):
    """
    Initializes the vector store by ingesting a markdown file located in the app/sources folder.
    Only 'cv.md' is supported at the moment.
    """

    if file_name != "cv.md":
        raise HTTPException(status_code=400, detail="Only 'cv.md' is supported at the moment.")

    app_dir = Path(__file__).resolve().parent
    sources_dir = app_dir / "sources"
    file_path = sources_dir / file_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found in app/sources: {file_name}")

    try:
        ingest_markdown_file(file_path=str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return {"status": "initialization complete"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Handles chat requests through LangGraph, persisted with PostgresSaver.
    """
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
    last_message = snap.values.get("messages", [])[-1] if snap.values.get("messages") else None

    logging.info(f"Chat processed with thread ID: {request.thread_id}, checkpoint ID: {checkpoint_id}")

    response = ChatResponse(
        output={"messages": last_message.content} if last_message else {"messages": []},
        checkpoint_id=checkpoint_id,
        num_messages=len(snap.values.get("messages", []))
    )

    return response

@app.get("/graph/state")
def get_graph_state(thread_id: str | None = None):
    """
    Returns the current state of the graph for debugging purposes.
    """
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