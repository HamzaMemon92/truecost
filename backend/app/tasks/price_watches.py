from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select

from app.config import settings
from app.db import SessionLocal
from app.models import Notification, NotificationOutbox, PushDevice
from app.services.expo_push import ExpoPushService, PushMessage
from app.services.price_watcher import evaluate_active_price_watches
from app.tasks.celery_app import celery_app

logger = logging.getLogger("truecost.worker")


@celery_app.task(name="truecost.evaluate_price_watches", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def evaluate_price_watches() -> dict:
    from redis import Redis
    lock = Redis.from_url(settings.redis_url).lock("lock:truecost:price-watch-evaluation", timeout=max(settings.price_watch_interval_seconds - 1, 30), blocking_timeout=0)
    if not lock.acquire(blocking=False):
        return {"skipped": "already_running"}
    try:
        return evaluate_active_price_watches().__dict__
    finally:
        lock.release()


@celery_app.task(name="truecost.deliver_notification_outbox")
def deliver_notification_outbox(batch_size: int = 100) -> dict:
    from redis import Redis
    lock = Redis.from_url(settings.redis_url).lock("lock:truecost:notification-outbox", timeout=120, blocking_timeout=0)
    if not lock.acquire(blocking=False):
        return {"skipped": "already_running"}
    now = datetime.now(timezone.utc)
    delivered = failed = 0
    service = ExpoPushService()
    try:
        with SessionLocal() as db:
            rows = db.scalars(
                select(NotificationOutbox)
                .where(
                    NotificationOutbox.status.in_(("pending", "retrying")),
                    or_(NotificationOutbox.next_attempt_at.is_(None), NotificationOutbox.next_attempt_at <= now),
                )
                .order_by(NotificationOutbox.created_at)
                .limit(batch_size)
            ).all()
            for row in rows:
                notification = db.get(Notification, row.notification_id)
                devices = db.scalars(select(PushDevice).where(PushDevice.user_id == row.user_id, PushDevice.active.is_(True))).all()
                if notification is None or not devices:
                    row.status = "delivered"
                    row.delivered_at = now
                    delivered += 1
                    continue
                try:
                    messages = [PushMessage(device.expo_push_token, notification.title, notification.body, {"deepLink": notification.deep_link}) for device in devices]
                    tickets = service.send(messages)
                    row.attempts += 1
                    row.ticket_ids = [ticket["id"] for ticket in tickets if ticket.get("status") == "ok" and ticket.get("id")]
                    row.delivery_targets = [{"ticket_id": ticket.get("id"), "device_id": device.id} for device, ticket in zip(devices, tickets) if ticket.get("id")]
                    invalid_tokens = {
                        device.expo_push_token for device, ticket in zip(devices, tickets)
                        if ticket.get("details", {}).get("error") == "DeviceNotRegistered"
                    }
                    for device in devices:
                        if device.expo_push_token in invalid_tokens:
                            device.active = False
                    row.status = "sent" if row.ticket_ids else "invalid_device" if invalid_tokens else "failed"
                    row.sent_at = now
                    delivered += 1
                except Exception as exc:
                    row.attempts += 1
                    row.last_error_code = type(exc).__name__
                    row.status = "failed" if row.attempts >= 5 else "retrying"
                    row.next_attempt_at = now + timedelta(seconds=min(30 * 2 ** row.attempts, 3600))
                    failed += 1
                    logger.exception("Notification outbox delivery failed id=%s", row.id)
            db.commit()
        return {"processed": len(rows), "delivered": delivered, "failed": failed}
    finally:
        lock.release()


@celery_app.task(name="truecost.reconcile_expo_receipts")
def reconcile_expo_receipts(batch_size: int = 100) -> dict:
    service = ExpoPushService()
    reconciled = 0
    with SessionLocal() as db:
        rows = db.scalars(select(NotificationOutbox).where(NotificationOutbox.status == "sent").limit(batch_size)).all()
        ticket_ids = [ticket for row in rows for ticket in row.ticket_ids]
        receipts = service.receipts(ticket_ids)
        for row in rows:
            states = [receipts.get(ticket) for ticket in row.ticket_ids]
            if not states or any(state is None for state in states):
                continue
            errors = [state for state in states if state.get("status") == "error"]
            invalid_ticket_ids = {ticket for ticket, state in zip(row.ticket_ids, states) if state.get("details", {}).get("error") == "DeviceNotRegistered"}
            invalid_device_ids = {target.get("device_id") for target in row.delivery_targets if target.get("ticket_id") in invalid_ticket_ids}
            for device_id in invalid_device_ids:
                device = db.get(PushDevice, device_id)
                if device:
                    device.active = False
            row.status = "invalid_device" if errors and len(invalid_ticket_ids) == len(row.ticket_ids) else "failed" if errors else "delivered"
            row.last_error_code = errors[0].get("details", {}).get("error") if errors else None
            row.delivered_at = datetime.now(timezone.utc) if not errors else None
            reconciled += 1
        db.commit()
    return {"reconciled": reconciled}
