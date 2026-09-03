import json
import logging
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger("decision_advisor")
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_event(event: str, **data: Any) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **data,
    }
    logger.info(json.dumps(payload, ensure_ascii=True))
