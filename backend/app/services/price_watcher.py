from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db import SessionLocal
from app.models import Notification, NotificationOutbox, PriceObservation, PriceWatch, PriceWatchTrigger, PushDevice, UserActivity
from app.services.expo_push import ExpoPushService, PushMessage

logger = logging.getLogger("truecost.price_watcher")


@dataclass(frozen=True)
class PriceCheck:
    price: float
    observation_key: str
    provider: str | None = None


class PricingEngine(Protocol):
    def check(self, db: Session, watch: PriceWatch) -> PriceCheck | None: ...


class StoredObservationPricingEngine:
    """Uses trusted prices already persisted by the ingestion pipeline.

    The scheduled worker intentionally does not scrape providers. A future authorized
    pricing adapter can implement PricingEngine without changing alert semantics.
    """

    def check(self, db: Session, watch: PriceWatch) -> PriceCheck | None:
        observation = db.scalar(
            select(PriceObservation)
            .where(PriceObservation.watch_id == watch.id)
            .order_by(PriceObservation.observed_at.desc(), PriceObservation.id.desc())
            .limit(1)
        )
        if observation:
            return PriceCheck(observation.price, f"observation:{observation.id}", observation.provider)
        if watch.current_price is None:
            return None
        changed_at = watch.updated_at
        if changed_at.tzinfo is None:
            changed_at = changed_at.replace(tzinfo=timezone.utc)
        return PriceCheck(watch.current_price, f"current:{changed_at.isoformat()}:{watch.current_price:g}", watch.provider)


@dataclass
class WatchRunSummary:
    checked: int = 0
    triggered: int = 0
    skipped: int = 0
    failures: int = 0


def evaluate_active_price_watches(
    session_factory: sessionmaker = SessionLocal,
    pricing_engine: PricingEngine | None = None,
    push_service: ExpoPushService | None = None,
) -> WatchRunSummary:
    engine = pricing_engine or StoredObservationPricingEngine()
    pushes = push_service
    summary = WatchRunSummary()

    with session_factory() as lookup:
        watch_ids = list(lookup.scalars(select(PriceWatch.id).where(PriceWatch.active.is_(True))))

    for watch_id in watch_ids:
        with session_factory() as db:
            try:
                watch = db.get(PriceWatch, watch_id)
                if watch is None or not watch.active:
                    summary.skipped += 1
                    continue
                check = engine.check(db, watch)
                summary.checked += 1
                if check is None or check.price > watch.target_price:
                    summary.skipped += 1
                    continue

                previous_trigger = db.scalar(
                    select(PriceWatchTrigger)
                    .where(PriceWatchTrigger.watch_id == watch.id)
                    .order_by(PriceWatchTrigger.created_at.desc(), PriceWatchTrigger.id.desc())
                    .limit(1)
                )
                if previous_trigger is not None:
                    # Observation time is the domain clock. A trigger is committed
                    # after its observation, so comparing later observations with
                    # trigger.created_at can miss a rapid above-target rearm.
                    triggered_observation_id = (
                        previous_trigger.observation_key.removeprefix("observation:")
                        if previous_trigger.observation_key.startswith("observation:")
                        else None
                    )
                    boundary = previous_trigger.created_at
                    if triggered_observation_id:
                        boundary = db.scalar(
                            select(PriceObservation.observed_at)
                            .where(
                                PriceObservation.watch_id == watch.id,
                                PriceObservation.id == triggered_observation_id,
                            )
                        ) or boundary
                    rearmed = db.scalar(
                        select(PriceObservation.id)
                        .where(
                            PriceObservation.watch_id == watch.id,
                            PriceObservation.observed_at >= boundary,
                            PriceObservation.id != triggered_observation_id if triggered_observation_id else True,
                            PriceObservation.price > watch.target_price,
                        )
                        .limit(1)
                    )
                    if rearmed is None:
                        summary.skipped += 1
                        continue

                trigger = PriceWatchTrigger(
                    watch_id=watch.id,
                    observation_key=check.observation_key,
                    observed_price=check.price,
                )
                db.add(trigger)
                db.flush()

                preferences = (watch.user.profile.preferences or {}) if watch.user.profile else {}
                notifications = preferences.get("notification_preferences", {})
                notification = None
                if notifications.get("price_drops") is not False:
                    notification = Notification(
                        user_id=watch.user_id,
                        category="price",
                        title=f"Target reached: {watch.title}",
                        body=f"Observed at {watch.currency} {check.price:g}, at or below your {watch.currency} {watch.target_price:g} target.",
                        deep_link="Watchlist",
                    )
                    db.add(notification)
                    db.flush()
                    db.add(NotificationOutbox(notification_id=notification.id, user_id=watch.user_id))
                    trigger.notification_id = notification.id
                    db.add(UserActivity(
                        user_id=watch.user_id,
                        event_type="price_watch.triggered",
                        title=f"Target reached for {watch.title}",
                        details={"price_watch_id": watch.id, "observed_price": check.price, "target_price": watch.target_price},
                    ))
                db.commit()
                summary.triggered += 1

                # Tests may inject a delivery seam. Production delivery is exclusively
                # handled by the transactional outbox worker after this commit.
                if notification and pushes is not None:
                    devices = db.scalars(select(PushDevice).where(PushDevice.user_id == watch.user_id, PushDevice.active.is_(True))).all()
                    messages = [PushMessage(device.expo_push_token, notification.title, notification.body, {"deepLink": "Watchlist", "watchId": watch.id}) for device in devices]
                    if messages:
                        try:
                            tickets = pushes.send(messages)
                            for device, ticket in zip(devices, tickets):
                                if ticket.get("status") == "error" and ticket.get("details", {}).get("error") == "DeviceNotRegistered":
                                    device.active = False
                            db.commit()
                        except Exception:
                            logger.exception("Push delivery failed for price watch %s", watch.id)
            except IntegrityError:
                db.rollback()
                summary.skipped += 1
            except Exception:
                db.rollback()
                summary.failures += 1
                logger.exception("Price watch evaluation failed for %s", watch_id)
    return summary


class PriceWatchScheduler:
    def __init__(self, interval_seconds: int | None = None) -> None:
        self.interval_seconds = interval_seconds or settings.price_watch_interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="truecost-price-watcher", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            summary = evaluate_active_price_watches()
            logger.info("Price watch cycle checked=%s triggered=%s skipped=%s failures=%s", summary.checked, summary.triggered, summary.skipped, summary.failures)

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None
