from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings

from .modules.ingest.ingest import ingest_markdown_file
from pathlib import Path
from fastapi import HTTPException

app = FastAPI()

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

    namespace = "default"

    try:
        ingest_markdown_file(file_path=str(file_path), namespace=namespace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return {"status": "initialization complete"}
