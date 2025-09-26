from ..rag.adapters import get_vector_store

# TODO: Add error handling and logging
def delete_source(source: str) -> None:
    """
    Deletes all documents in the specified source from the vector store.

    Args:
        source (str): The source to delete from the vector store.
    """
    # Get the vector store
    vector_store = get_vector_store()

    # Delete documents in the specified source
    vector_store.delete(source=source)