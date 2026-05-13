from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""

    redis_url: str = ""

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""
    langfuse_base_url: str = ""

    fernet_key: str = ""  # ini buat encrypt github token

    # Docker / sandbox settings for agent containers
    docker_agent_image: str = "patch/agent:latest"
    agent_memory_limit: str = "2g"
    agent_cpus: float = 1.0
    agent_pids_limit: int = 512
    agent_max_wall_time_sec: int = 900


settings = Settings()
