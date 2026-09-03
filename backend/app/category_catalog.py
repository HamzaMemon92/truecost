from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CategoryDefinition(BaseModel):
    id: str
    name: str
    engine_category: str
    family: str
    capability: str
    requires_location: bool
    description: str


class ProviderDefinition(BaseModel):
    id: str
    name: str
    category_id: str
    aliases: list[str] = Field(default_factory=list)
    freshness_sla_seconds: int = Field(gt=0)
    source_mode: Literal["ingestion"] = "ingestion"
    rollout_state: Literal["catalogued", "testing", "verified", "degraded", "disabled"] = "catalogued"
    handoff_capability: Literal["observed_url"] = "observed_url"
    account_family: str | None = None
    account_connection_state: Literal["pending_approval", "enabled", "unavailable"] = "pending_approval"


class ProviderCatalog(BaseModel):
    version: int
    categories: list[CategoryDefinition]
    providers: list[ProviderDefinition]

    @model_validator(mode="after")
    def validate_catalog(self) -> "ProviderCatalog":
        category_ids = {category.id for category in self.categories}
        provider_ids = [provider.id for provider in self.providers]
        if len(provider_ids) != 32 or len(provider_ids) != len(set(provider_ids)):
            raise ValueError("Provider catalog must contain exactly 32 unique providers")
        if any(provider.category_id not in category_ids for provider in self.providers):
            raise ValueError("Every provider must reference a known category")
        alias_owners: dict[str, str] = {}
        for provider in self.providers:
            for raw_alias in {provider.id, provider.name, *provider.aliases}:
                alias = raw_alias.casefold().strip()
                previous_owner = alias_owners.get(alias)
                if previous_owner is not None and previous_owner != provider.id:
                    raise ValueError(f"Provider alias {raw_alias!r} belongs to multiple providers")
                alias_owners[alias] = provider.id
        return self


@lru_cache(maxsize=1)
def get_provider_catalog() -> ProviderCatalog:
    path = Path(__file__).with_name("provider_catalog.json")
    return ProviderCatalog.model_validate(json.loads(path.read_text(encoding="utf-8")))


CATALOG = get_provider_catalog()
PROVIDERS_BY_ID = {provider.id: provider for provider in CATALOG.providers}
PROVIDER_ALIAS_MAP = {alias.casefold().strip(): provider.id for provider in CATALOG.providers for alias in [provider.id, provider.name, *provider.aliases]}
KNOWN_PROVIDER_IDS = tuple(provider.id for provider in CATALOG.providers)


def normalize_provider_key(value: str) -> str:
    normalized = value.casefold().strip()
    return PROVIDER_ALIAS_MAP.get(normalized, normalized.replace(" ", "_"))


def provider_ids_for_engine_category(category: str) -> tuple[str, ...]:
    """Return canonical providers for a mobile/engine category name."""
    normalized = category.casefold().strip()
    category_ids = {
        item.id
        for item in CATALOG.categories
        if item.id.casefold() == normalized
        or item.name.casefold() == normalized
        or item.engine_category.casefold() == normalized
    }
    return tuple(provider.id for provider in CATALOG.providers if provider.category_id in category_ids)


def category_projection() -> list[dict]:
    by_category: dict[str, list[str]] = {category.id: [] for category in CATALOG.categories}
    for provider in CATALOG.providers:
        by_category[provider.category_id].append(provider.name)
    return [{"id": category.id, "name": category.name, "engine_category": category.engine_category, "capability": category.capability, "providers": by_category[category.id]} for category in CATALOG.categories]


CATEGORY_CATALOG = category_projection()
SUPPORTED_CATEGORY_NAMES = {item["name"] for item in CATEGORY_CATALOG}
