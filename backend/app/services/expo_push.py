from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings, settings

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
EXPO_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"


@dataclass(frozen=True)
class PushMessage:
    to: str
    title: str
    body: str
    data: dict


class ExpoPushService:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config

    def send(self, messages: list[PushMessage]) -> list[dict]:
        if not messages:
            return []
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.config.expo_access_token:
            headers["Authorization"] = f"Bearer {self.config.expo_access_token}"
        payload = [
            {
                "to": message.to,
                "title": message.title,
                "body": message.body,
                "sound": "default",
                "channelId": "truecost-alerts",
                "data": message.data,
            }
            for message in messages
        ]
        response = httpx.post(EXPO_PUSH_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json().get("data", [])
        return result if isinstance(result, list) else [result]

    def receipts(self, ticket_ids: list[str]) -> dict[str, dict]:
        if not ticket_ids:
            return {}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.config.expo_access_token:
            headers["Authorization"] = f"Bearer {self.config.expo_access_token}"
        response = httpx.post(EXPO_RECEIPTS_URL, headers=headers, json={"ids": ticket_ids}, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", {})
        return data if isinstance(data, dict) else {}
