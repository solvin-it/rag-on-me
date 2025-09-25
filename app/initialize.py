from langchain_postgres import PGEngine

from .core.config import Settings
from .modules.rag.adapters import get_vector_size

settings = Settings()

engine = PGEngine.from_connection_string(url=settings.get_database_url())
vector_size = get_vector_size()

async def initialize_database():
    await engine.ainit_vectorstore_table(
        table_name="documents",
        vector_size=vector_size
    )
    

if __name__ == "__main__":
    print("Initializing database...")
    initialize_database()
    print("Database initialized.")