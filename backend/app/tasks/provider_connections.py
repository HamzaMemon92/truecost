from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select

from app.db import SessionLocal
from app.models import BrokerRevocationOutbox, ProviderConnection
from app.services.provider_broker import ProviderBrokerClient
from app.tasks.celery_app import celery_app


@celery_app.task(name="truecost.retry_broker_revocations")
def retry_broker_revocations(batch_size: int = 50) -> dict:
    now = datetime.now(timezone.utc)
    completed = failed = 0
    with SessionLocal() as db:
        rows = db.scalars(select(BrokerRevocationOutbox).where(BrokerRevocationOutbox.status.in_(("pending", "retrying")), or_(BrokerRevocationOutbox.next_attempt_at.is_(None), BrokerRevocationOutbox.next_attempt_at <= now)).limit(batch_size)).all()
        for row in rows:
            connection = db.get(ProviderConnection, row.connection_id)
            subject_ref = connection.broker_subject_ref if connection and connection.broker_subject_ref else row.subject_ref
            if not subject_ref:
                row.status = "completed"
                completed += 1
                continue
            try:
                ProviderBrokerClient().revoke(subject_ref, row.provider_id)
                if connection:
                    db.delete(connection)
                row.status = "completed"
                completed += 1
            except Exception as exc:
                row.attempts += 1
                row.last_error_code = type(exc).__name__
                row.status = "failed" if row.attempts >= 10 else "retrying"
                row.next_attempt_at = now + timedelta(seconds=min(60 * 2 ** row.attempts, 21600))
                failed += 1
        db.commit()
    return {"completed": completed, "failed": failed}
