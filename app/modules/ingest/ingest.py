import uuid
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..rag.adapters import get_vector_store
import logging

# TODO: Make chunk size and overlap configurable
# TODO: Add more file type support (e.g., PDF, DOCX)
logger = logging.getLogger(__name__)


def ingest_markdown_file(file_path: str) -> None:
    """
    Ingests a markdown file into the vector store.

    Args:
        file_path (str): The path to the markdown file.
    """
    loader = UnstructuredMarkdownLoader(file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    document_splits = splitter.split_documents(documents)

    ids = []
    file_name = file_path.split("/")[-1]
    for i, doc in enumerate(document_splits, 1):
        chunk_id = f"{file_name}-chunk-{i}"
        doc.metadata = doc.metadata or {}
        doc.metadata["source"] = file_name

        ids.append(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id).hex)

    vector_store = get_vector_store()

    try:
        vector_store.delete(ids=ids, collection_only=True)
        logging.info("Deleted existing docs using where filter")
    except Exception as e:
        logging.warning(f"Unexpected error while attempting to delete prior docs for source '{file_name}': {e}")

    vector_store.add_documents(documents=document_splits, ids=ids)

# TODO: Add more file type support (e.g., PDF, DOCX)