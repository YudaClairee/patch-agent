from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""

    redis_url: str = ""

    # --- LLM (provider-agnostic, via LiteLLM model-id prefix) ---
    # Examples:
    #   openrouter/google/gemini-2.0-flash-001   (default)
    #   openai/gpt-4o-mini
    #   anthropic/claude-3-5-sonnet-20241022
    #   gemini/gemini-2.0-flash
    #   groq/llama-3.3-70b-versatile
    llm_model_id: str = "openrouter/google/gemini-2.0-flash-001"
    llm_api_key: str = ""
    llm_base_url: str = ""  # blank → LiteLLM picks the provider default

    # Legacy / deprecated — kept so existing .env files keep working.
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""
    langfuse_base_url: str = ""

    fernet_key: str = ""  # ini buat encrypt github token
    jwt_secret: str = ""  # ini buat sign jwt

    # Session cookie / JWT
    session_cookie_name: str = "patch_session"
    session_ttl_hours: int = 24 * 7
    environment: str = "development"  # set to "production" to enable Secure cookies

    # GitHub OAuth App credentials
    github_oauth_client_id: str = ""
    github_oauth_client_secret: str = ""
    github_oauth_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Docker / sandbox settings for agent containers
    docker_agent_image: str = "patch/agent:latest"
    agent_database_url: str = ""
    agent_redis_url: str = ""
    agent_memory_limit: str = "2g"
    agent_cpus: float = 1.0
    agent_pids_limit: int = 512
    agent_max_wall_time_sec: int = 900
    agent_max_steps: int = 40
    agent_duplicate_streak_limit: int = 3
    agent_max_tool_output_chars: int = 4000
    agent_shell_network_enabled: bool = False
    agent_allow_host_gateway: bool = False
    patch_runtime: str = "backend"

    # --- Embedding / VDB settings ---
    embedding_model_id: str = "openrouter/openai/text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 64

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]
        frontend_origin = self.frontend_url.strip().rstrip("/")
        if frontend_origin and frontend_origin not in origins:
            origins.append(frontend_origin)
        return origins

    @model_validator(mode="after")
    def resolve_legacy_llm_and_validate_required(self) -> "Settings":
        if not self.llm_api_key and self.openrouter_api_key:
            self.llm_api_key = self.openrouter_api_key
        if not self.llm_base_url and self.openrouter_base_url:
            self.llm_base_url = self.openrouter_base_url

        required = {
            "DATABASE_URL": self.database_url,
            "REDIS_URL": self.redis_url,
            "LLM_API_KEY": self.llm_api_key,
        }
        if self.patch_runtime != "agent":
            required.update(
                {
                    "FERNET_KEY": self.fernet_key,
                    "JWT_SECRET": self.jwt_secret,
                }
            )
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            missing_names = ", ".join(missing)
            raise ValueError(f"Missing required backend environment variables: {missing_names}")

        return self

    # --- Auto-Review settings ---
    # Model used for the reviewer LLM call. Defaults to the main model if blank.
    llm_reviewer_model_id: str = ""
    # Set to False to disable automatic post-PR review for every developer run.
    auto_review_enabled: bool = True


settings = Settings()
