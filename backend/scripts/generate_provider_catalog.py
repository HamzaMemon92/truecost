from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "app" / "provider_catalog.json"
TARGET = ROOT / "mobile" / "catalog" / "providerManifest.generated.ts"


def render() -> str:
    catalog = json.loads(SOURCE.read_text(encoding="utf-8"))
    providers = [provider["id"] for provider in catalog["providers"]]
    return "// Generated from backend/app/provider_catalog.json. Do not edit.\n" + f"export const PROVIDERS = {json.dumps(providers, separators=(',', ':'))} as const;\n" + f"export const PROVIDER_CATALOG_VERSION = {catalog['version']} as const;\n" + f"export const CATEGORY_DEFINITIONS = {json.dumps(catalog['categories'], separators=(',', ':'))} as const;\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        return 0 if TARGET.exists() and TARGET.read_text(encoding="utf-8") == expected else 1
    TARGET.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
