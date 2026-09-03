from pydantic import BaseModel
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "decision-advisor-backend"
    app_env: str = "development"
    database_url: str = "sqlite:///./decision_advisor.db"
    redis_url: str | None = None
    openai_api_key: str | None = None
    sms_provider: str = "console"
    sms_fallback_provider: str = "none"
    sms_request_timeout_seconds: float = 10.0
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None
    auth_secret_key: str = "secret"
    password_pbkdf2_iterations: int = 600_000
    access_token_minutes: int = 60
    refresh_token_days: int = 7
    admin_emails: str = ""
    otp_max_requests_per_10_minutes: int = 5
    otp_max_attempts: int = 3
    otp_ttl_minutes: int = 5
    otp_resend_seconds: int = 30
    task_execution_mode: str = "inline"
    auto_create_schema: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:8081,http://127.0.0.1:5173"
    trusted_hosts: str = "localhost,127.0.0.1,0.0.0.0,testserver,*.local"
    expo_access_token: str | None = None
    provider_connection_broker_url: str | None = None
    provider_connection_broker_secret: str | None = None
    provider_connection_attempt_minutes: int = 15
    provider_preview_enabled: bool = False
    sentry_dsn: str | None = None
    otel_exporter_otlp_endpoint: str | None = None
    price_watch_interval_seconds: int = 300
    entity_resolution_mode: str = "shadow"
    entity_resolution_rollback_to_legacy: bool = False
    entity_resolution_llm_extraction_enabled: bool = False
    shopping_model: str = "gpt-4o-mini"
    flipkart_affiliate_id: str | None = None
    flipkart_affiliate_token: str | None = None

    # QuickCommerce API (real grocery provider — Blinkit, Zepto, Swiggy Instamart)
    # Sign up free at https://quickcommerceapi.com
    quickcommerce_api_key: str | None = None
    quickcommerce_lat: float = 12.9716   # default: Bengaluru
    quickcommerce_lon: float = 77.5946
    quickcommerce_timeout_s: float = 8.0

    @model_validator(mode="after")
    def validate_production_profile(self) -> "Settings":
        env = (self.app_env or "").strip().lower()
        prod_like = env in {"production", "prod", "staging"}

        sms = (self.sms_provider or "").strip().lower()
        if sms == "twilio":
            missing_twilio = [
                name
                for name in ("twilio_account_sid", "twilio_auth_token", "twilio_from_number")
                if not getattr(self, name)
            ]
            if missing_twilio:
                raise ValueError(f"Twilio SMS provider requires: {', '.join(missing_twilio)}")
        elif sms not in {"console", "msg91", "twilio"}:
            raise ValueError("sms_provider must be one of: console, msg91, twilio")

        if not prod_like:
            return self

        errors: list[str] = []
        if not self.database_url.startswith(("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
            errors.append("production database_url must use PostgreSQL")
        if not self.redis_url or not self.redis_url.startswith(("redis://", "rediss://")):
            errors.append("production redis_url is required")
        if not self.auth_secret_key or self.auth_secret_key == "secret" or len(self.auth_secret_key) < 32:
            errors.append("production auth_secret_key must be a strong secret")
        if self.auto_create_schema:
            errors.append("production auto_create_schema must be false; use Alembic migrations")
        if self.task_execution_mode != "celery":
            errors.append("production task_execution_mode must be celery")
        if self.provider_preview_enabled:
            errors.append("production provider_preview_enabled must be false")
        if not self.expo_access_token:
            errors.append("production expo_access_token is required")
        if not self.provider_connection_broker_url or not self.provider_connection_broker_url.startswith("https://"):
            errors.append("production provider_connection_broker_url must be HTTPS")
        if not self.provider_connection_broker_secret or len(self.provider_connection_broker_secret) < 32:
            errors.append("production provider_connection_broker_secret must be a strong secret")
        if "*" in {origin.strip() for origin in self.cors_origins.split(",")}:
            errors.append("production cors_origins cannot include wildcard origins")
        if "*" in {host.strip() for host in self.trusted_hosts.split(",")}:
            errors.append("production trusted_hosts cannot include wildcard hosts")
        if sms != "twilio":
            errors.append("production sms_provider must be twilio")

        if errors:
            raise ValueError("; ".join(errors))
        return self


class DeepReasoningPolicy(BaseModel):
    moderate_keywords: list[str] = Field(
        default_factory=lambda: [
            "best",
            "compare",
            "budget",
            "under",
            "battery",
            "camera",
            "offer",
            "credit card",
            "emi",
        ]
    )
    complex_keyword_multiplier: int = 3
    long_query_tokens: int = 9


settings = Settings()
policy = DeepReasoningPolicy()
