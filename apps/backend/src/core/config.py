from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = ""

    redis_url: str = ""

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""

    fernet_key: str = ""  # ini buat encrypt github token
    jwt_secret: str = ""  # ini buat sign jwt

    chroma_host: str = "chroma" # service name di docker-compose, "localhost" untuk lokal
    chroma_port: int = 8000  # port di docker network, 8000 untuk lokal


settings = Settings()