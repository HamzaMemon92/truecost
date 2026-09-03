from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BROKER_", extra="ignore")
    database_url: str = "postgresql+psycopg://truecost_broker:broker@postgres/truecost"
    redis_url: str = "redis://redis:6379/1"
    public_url: str = "http://localhost:8010"
    callback_secret: str = ""
    vault_encryption_keys: str = ""
    enabled_providers: str = ""
    allowed_mobile_redirects: str = "truecost://provider-connect"

    @property
    def enabled_provider_ids(self) -> set[str]:
        return {value.strip() for value in self.enabled_providers.split(",") if value.strip()}

    @property
    def redirect_allowlist(self) -> set[str]:
        return {value.strip() for value in self.allowed_mobile_redirects.split(",") if value.strip()}


settings = BrokerSettings()
