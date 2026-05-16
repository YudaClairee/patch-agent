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

    # Docker / sandbox settings for agent containers
    docker_agent_image: str = "patch/agent:latest"
    agent_memory_limit: str = "2g"
    agent_cpus: float = 1.0
    agent_pids_limit: int = 512
    agent_max_wall_time_sec: int = 900
    agent_max_steps: int = 40
    agent_duplicate_streak_limit: int = 3
    agent_max_tool_output_chars: int = 4000

    # --- Auto-Review settings ---
    # Model used for the reviewer LLM call. Defaults to the main model if blank.
    llm_reviewer_model_id: str = ""
    # Set to False to disable automatic post-PR review for every developer run.
    auto_review_enabled: bool = True


settings = Settings()

# Back-compat: if only legacy OPENROUTER_* vars are set, use them for the LLM.
if not settings.llm_api_key and settings.openrouter_api_key:
    settings.llm_api_key = settings.openrouter_api_key
if not settings.llm_base_url and settings.openrouter_base_url:
    settings.llm_base_url = settings.openrouter_base_url