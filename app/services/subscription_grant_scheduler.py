"""Cron scheduler for monthly subscription token grants."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from threading import Event, Thread

from app.core.config import settings
from app.db.subscription_queries import process_due_subscription_grants
from app.utils.log_safety import sanitize_for_log

logger = logging.getLogger(__name__)


class SubscriptionGrantScheduler:
    def __init__(
        self,
        *,
        interval_minutes: int,
        cron_hour_utc: int,
        run_on_start: bool = False,
    ) -> None:
        self._interval_seconds = max(1, interval_minutes) * 60
        self._cron_hour_utc = max(0, min(23, int(cron_hour_utc)))
        self._run_on_start = run_on_start
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_run_date: datetime | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = Thread(target=self._run_loop, name="subscription-grant-scheduler", daemon=True)
        self._thread.start()
        logger.info(
            "subscription grant scheduler started interval_minutes=%s cron_hour_utc=%s run_on_start=%s",
            self._interval_seconds // 60,
            self._cron_hour_utc,
            self._run_on_start,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("subscription grant scheduler stopped")

    def _run_loop(self) -> None:
        if self._run_on_start and self._in_cron_window(datetime.now(timezone.utc)):
            self._run_once_safe()
        while not self._stop_event.wait(self._interval_seconds):
            now = datetime.now(timezone.utc)
            if not self._in_cron_window(now):
                continue
            if self._last_run_date and self._last_run_date.date() == now.date():
                continue
            self._run_once_safe()
            self._last_run_date = now

    def _in_cron_window(self, now: datetime) -> bool:
        return now.hour == self._cron_hour_utc

    def _run_once_safe(self) -> None:
        try:
            result = process_due_subscription_grants()
            logger.info(
                "subscription grant batch complete granted_count=%s",
                result.get("granted_count"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "subscription grant batch failed error=%s",
                sanitize_for_log(str(exc)),
            )
