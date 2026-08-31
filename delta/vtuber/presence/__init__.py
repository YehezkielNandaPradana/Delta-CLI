"""
Personal Presence & Companion Subpackage for Delta VTuber.
"""

from delta.vtuber.presence.schemas import (
    PresenceActivity,
    PresenceState,
    NotificationType,
    NotificationEvent,
)
from delta.vtuber.presence.reactions import (
    MicroReactionEngine,
)
from delta.vtuber.presence.notifications import (
    NotificationManager,
)
from delta.vtuber.presence.scheduler import (
    PresenceScheduler,
)
from delta.vtuber.presence.manager import (
    PresenceManager,
    presence_manager,
)

__all__ = [
    "PresenceActivity",
    "PresenceState",
    "NotificationType",
    "NotificationEvent",
    "MicroReactionEngine",
    "NotificationManager",
    "PresenceScheduler",
    "PresenceManager",
    "presence_manager",
]
