from dotenv import load_dotenv
import os

load_dotenv()

LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-5-nano")
OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "change_me_locally")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app_db")
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))


class Settings:
    
    def __init__(self):
        self.langsmith_tracing = LANGSMITH_TRACING
        self.langsmith_api_key = LANGSMITH_API_KEY
        self.openai_api_key = OPENAI_API_KEY
        self.openai_chat_model = OPENAI_CHAT_MODEL
        self.openai_embedding_model = OPENAI_EMBEDDING_MODEL
        self.allowed_origins = ["*"]  # Adjust this in production for security

        self.database_settings = {
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD,
            "database": POSTGRES_DB,
            "port": POSTGRES_PORT,
            "host": POSTGRES_HOST
        }
        
    def get_database_url(self) -> str:
        return f"postgresql+psycopg://{self.database_settings['user']}:{self.database_settings['password']}@{self.database_settings['host']}:{self.database_settings['port']}/{self.database_settings['database']}"
    
settings = Settings()
    
# TODO: Add logging configuration settings