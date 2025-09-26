from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..rag.adapters import get_vector_store

# TODO: Add error handling and logging
# TODO: Make chunk size and overlap configurable
# TODO: Handle duplicates in the vector store
def ingest_markdown_file(file_path: str) -> None:
    """
    Ingests a markdown file into the vector store.

    Args:
        file_path (str): The path to the markdown file.
    """
    # Load the markdown file
    loader = UnstructuredMarkdownLoader(file_path)
    documents = loader.load()

    # Split documents into smaller chunks if necessary
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    document_splits = splitter.split_documents(documents)

    # Add metadata (source) to each document split
    file_name = file_path.split("/")[-1]
    for i, doc in enumerate(document_splits, 1):
        if not doc.metadata:
            doc.metadata = {}
        doc.metadata["source"] = f"{file_name}-chunk-{i}"

    # Get the vector store
    vector_store = get_vector_store()

    # Remove existing documents from the same source to avoid duplicates
    try:
        vector_store.delete(source=file_name)
    except Exception as e:
        print(f"Warning: Failed to delete existing documents from source '{file_name}': {e}")

    # Add documents to the vector store with the specified source
    vector_store.add_documents(documents=document_splits)

# TODO: Add more file type support (e.g., PDF, DOCX)