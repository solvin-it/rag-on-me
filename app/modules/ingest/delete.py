from ..rag.adapters import get_vector_store

# TODO: Add error handling and logging
def delete_namespace(namespace: str) -> None:
    """
    Deletes all documents in the specified namespace from the vector store.

    Args:
        namespace (str): The namespace to delete from the vector store.
    """
    # Get the vector store
    vector_store = get_vector_store()

    # Delete documents in the specified namespace
    vector_store.delete(namespace=namespace)