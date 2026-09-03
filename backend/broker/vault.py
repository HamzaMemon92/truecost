from __future__ import annotations

from cryptography.fernet import Fernet, MultiFernet


class TokenVault:
    def __init__(self, keys: str) -> None:
        parsed = [Fernet(value.strip().encode()) for value in keys.split(",") if value.strip()]
        if not parsed:
            raise RuntimeError("BROKER_VAULT_ENCRYPTION_KEYS is required")
        self._cipher = MultiFernet(parsed)

    def seal(self, value: str | None) -> bytes | None:
        return self._cipher.encrypt(value.encode()) if value else None

    def open(self, value: bytes | None) -> str | None:
        return self._cipher.decrypt(value).decode() if value else None
