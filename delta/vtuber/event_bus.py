"""
Asynchronous Event Bus for Delta VTuber Event System.
"""

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Union
from delta.vtuber.events import VTuberEvent, VTuberEventType

logger = logging.getLogger(__name__)

SubscriberCallable = Callable[[VTuberEvent], Any]


class VTuberEventBus:
    """
    Thread-safe & async-friendly Event Bus with subscriber error isolation.
    Supports subscribing to specific VTuberEventType or all events via wildcard (None).
    """

    def __init__(self):
        self._subscribers: Dict[Optional[VTuberEventType], List[SubscriberCallable]] = {}

    def subscribe(
        self,
        handler: SubscriberCallable,
        event_type: Optional[Union[VTuberEventType, str]] = None,
    ) -> Callable[[], None]:
        """
        Subscribe a sync or async handler to an event type (or all events if event_type is None).
        Returns an unsubscribe callback function for convenience.
        """
        target_type: Optional[VTuberEventType] = None
        if event_type is not None:
            target_type = (
                event_type
                if isinstance(event_type, VTuberEventType)
                else VTuberEventType(event_type)
            )

        if target_type not in self._subscribers:
            self._subscribers[target_type] = []

        if handler not in self._subscribers[target_type]:
            self._subscribers[target_type].append(handler)

        def _unsub():
            self.unsubscribe(handler, target_type)

        return _unsub

    def unsubscribe(
        self,
        handler: SubscriberCallable,
        event_type: Optional[Union[VTuberEventType, str]] = None,
    ) -> bool:
        """
        Unsubscribe a handler from a specific event type or from all registrations.
        """
        target_type: Optional[VTuberEventType] = None
        if event_type is not None:
            target_type = (
                event_type
                if isinstance(event_type, VTuberEventType)
                else VTuberEventType(event_type)
            )

        removed = False
        if target_type is not None:
            if target_type in self._subscribers and handler in self._subscribers[target_type]:
                self._subscribers[target_type].remove(handler)
                removed = True
        else:
            for subs in self._subscribers.values():
                if handler in subs:
                    subs.remove(handler)
                    removed = True

        return removed

    async def emit(self, event: VTuberEvent) -> None:
        """
        Emit an event asynchronously to all matching subscribers with error isolation.
        """
        handlers_to_call: Set[SubscriberCallable] = set()

        # Collect type-specific subscribers
        if event.type in self._subscribers:
            handlers_to_call.update(self._subscribers[event.type])

        # Collect wildcard/global subscribers (None key)
        if None in self._subscribers:
            handlers_to_call.update(self._subscribers[None])

        for handler in handlers_to_call:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as exc:
                logger.error(
                    "Error executing VTuber event handler %s for event %s: %s",
                    getattr(handler, "__name__", str(handler)),
                    event.type,
                    exc,
                    exc_info=True,
                )

    def clear(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()


# Default singleton instance
vtuber_event_bus = VTuberEventBus()
