"""
Notification Manager for Delta VTuber.
Dispatches internal companion notifications to EventBus without coupling directly to TTS.
"""

import logging
from typing import Any, Callable, List, Optional, Set
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.presence.schemas import NotificationEvent, NotificationType

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages internal notification dispatching and history.
    """

    def __init__(self, event_bus: Optional[VTuberEventBus] = None):
        self.event_bus = event_bus or vtuber_event_bus
        self._listeners: Set[Callable[[NotificationEvent], Any]] = set()
        self._history: List[NotificationEvent] = []

    def add_listener(self, listener: Callable[[NotificationEvent], Any]) -> Callable[[], None]:
        self._listeners.add(listener)

        def _unsub():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    def notify(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> NotificationEvent:
        """
        Record and dispatch an internal companion notification event.
        """
        event = NotificationEvent(
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {},
        )
        self._history.append(event)
        if len(self._history) > 50:
            self._history = self._history[-50:]

        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception as exc:
                logger.error("Error executing notification listener: %s", exc)

        return event

    def get_recent_notifications(self, limit: int = 10) -> List[NotificationEvent]:
        return self._history[-limit:]
