# from ...core.config import Settings
from core.config import Settings
from functools import lru_cache
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

settings = Settings()

@lru_cache
def get_llm():
    return init_chat_model(
        model=settings.openai_chat_model,
        model_provider="openai"
    )

@lru_cache
def get_embeddings():
    return OpenAIEmbeddings(model=settings.openai_embedding_model)

@lru_cache
def get_vector_store():
    engine = PGEngine.from_connection_string(url=settings.get_database_url())
    return PGVectorStore.create_sync(
        engine=engine,
        table_name="documents",
        embedding_service=get_embeddings()
    )

def get_vector_size() -> int:
    return len(get_embeddings().embed_query("dimension probe"))