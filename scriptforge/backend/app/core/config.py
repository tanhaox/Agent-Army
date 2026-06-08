from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://scriptforge:dev@localhost:5432/scriptforge"

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    EMBEDDING_PROVIDER: str = "bge"
    VECTOR_STORE: str = "pgvector"

    WHISPER_MODEL_PATH: str = "./models/whisper"
    SENSITIVE_WORDS_PATH: str = "./data/sensitive_words.txt"

    SECRET_KEY: str = ""
    DEBUG: bool = True

    # Auth (empty = disabled, set to enable API-level auth)
    API_AUTH_KEY: str = ""

    # Disk usage thresholds (GB)
    DISK_USAGE_WARNING_GB: int = 50
    DISK_USAGE_CRITICAL_GB: int = 100

    # ASR batch retranscribe concurrency
    ASR_CONCURRENT_WORKERS: int = 0  # 0 = auto (min(4, cpu_count))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Generate a random SECRET_KEY if not configured
if not settings.SECRET_KEY:
    import secrets
    settings.SECRET_KEY = secrets.token_urlsafe(32)
