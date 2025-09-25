from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..rag.adapters import get_vector_store

# TODO: Add error handling and logging
# TODO: Make chunk size and overlap configurable
# TODO: Handle duplicates in the vector store
# TODO: Add metadata support
def ingest_markdown_file(file_path: str, namespace: str) -> None:
    """
    Ingests a markdown file into the vector store.

    Args:
        file_path (str): The path to the markdown file.
        namespace (str): The namespace to use in the vector store.
    """
    # Load the markdown file
    loader = UnstructuredMarkdownLoader(file_path)
    documents = loader.load()

    # Split documents into smaller chunks if necessary
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    document_splits = splitter.split_documents(documents)

    # Get the vector store
    vector_store = get_vector_store()

    # Add documents to the vector store with the specified namespace
    vector_store.add_documents(documents=document_splits, namespace=namespace)

# TODO: Add more file type support (e.g., PDF, DOCX)