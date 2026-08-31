"""
VTube Studio WebSocket API Protocol Schemas for Delta VTuber.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VTSMessageType(str, Enum):
    API_STATE_REQUEST = "APIStateRequest"
    API_STATE_RESPONSE = "APIStateResponse"
    AUTHENTICATION_TOKEN_REQUEST = "AuthenticationTokenRequest"
    AUTHENTICATION_TOKEN_RESPONSE = "AuthenticationTokenResponse"
    AUTHENTICATION_REQUEST = "AuthenticationRequest"
    AUTHENTICATION_RESPONSE = "AuthenticationResponse"
    INJECT_PARAMETER_DATA_REQUEST = "InjectParameterDataRequest"
    INJECT_PARAMETER_DATA_RESPONSE = "InjectParameterDataResponse"
    CURRENT_MODEL_REQUEST = "CurrentModelRequest"
    CURRENT_MODEL_RESPONSE = "CurrentModelResponse"
    INPUT_PARAMETER_LIST_REQUEST = "InputParameterListRequest"
    INPUT_PARAMETER_LIST_RESPONSE = "InputParameterListResponse"
    LIVE2D_PARAMETER_LIST_REQUEST = "Live2DParameterListRequest"
    LIVE2D_PARAMETER_LIST_RESPONSE = "Live2DParameterListResponse"
    HOTKEYS_REQUEST = "HotkeysInCurrentModelRequest"
    HOTKEYS_RESPONSE = "HotkeysInCurrentModelResponse"
    HOTKEY_TRIGGER_REQUEST = "HotkeyTriggerRequest"
    HOTKEY_TRIGGER_RESPONSE = "HotkeyTriggerResponse"
    API_ERROR = "APIError"


class VTSConnectionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    AUTHENTICATING = "AUTHENTICATING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


VTS_ALLOWED_PARAMETERS = {
    "ParamAngleX",
    "ParamAngleY",
    "ParamAngleZ",
    "ParamBodyAngleX",
    "ParamBodyAngleY",
    "ParamBodyAngleZ",
    "ParamMouthOpenY",
    "ParamMouthForm",
    "ParamEyeLOpen",
    "ParamEyeROpen",
    "ParamEyeLSmile",
    "ParamEyeRSmile",
    "ParamEyeBallX",
    "ParamEyeBallY",
    "ParamBrowLY",
    "ParamBrowRY",
    "ParamCheek",
    "ParamHairFront",
    "ParamHairSide",
    "ParamHairBack",
    "ParamBreath",
}


class VTSParameterValue(BaseModel):
    id: str
    value: float
    weight: float = 1.0


class VTSInjectParameterData(BaseModel):
    mode: str = "set"
    faceFound: bool = False
    parameterValues: List[VTSParameterValue] = Field(default_factory=list)


class VTSMessage(BaseModel):
    apiName: str = "VTubeStudioPublicAPI"
    apiVersion: str = "1.0"
    requestID: str = "DeltaVTuber"
    messageType: VTSMessageType
    data: Dict[str, Any] = Field(default_factory=dict)
