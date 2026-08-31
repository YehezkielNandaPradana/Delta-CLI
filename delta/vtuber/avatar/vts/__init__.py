"""
VTube Studio Desktop API Subpackage for Delta VTuber.
"""

from delta.vtuber.avatar.vts.protocol import (
    VTS_ALLOWED_PARAMETERS,
    VTSConnectionState,
    VTSMessage,
    VTSMessageType,
    VTSParameterValue,
    VTSInjectParameterData,
)
from delta.vtuber.avatar.vts.mapper import (
    VTSMapper,
)
from delta.vtuber.avatar.vts.client import (
    VTSClient,
)

__all__ = [
    "VTS_ALLOWED_PARAMETERS",
    "VTSConnectionState",
    "VTSMessage",
    "VTSMessageType",
    "VTSParameterValue",
    "VTSInjectParameterData",
    "VTSMapper",
    "VTSClient",
]
