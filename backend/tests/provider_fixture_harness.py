from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "grocery"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def fixture_entries(*, provider: str | None = None) -> list[dict[str, Any]]:
    entries = load_manifest()["fixtures"]
    if provider:
        return [entry for entry in entries if entry["provider"] == provider]
    return entries


def load_fixture_payload(entry: dict[str, Any]) -> dict[str, Any]:
    path = FIXTURE_ROOT / entry["payload_file"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["payload"] if "payload" in raw else raw


def expected_product(entry: dict[str, Any]) -> dict[str, Any]:
    return entry["expected_products"][0]
