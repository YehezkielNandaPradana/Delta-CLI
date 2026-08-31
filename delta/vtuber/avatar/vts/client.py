import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.avatar.vts.mapper import VTSMapper
from delta.vtuber.avatar.vts.protocol import (
    VTS_ALLOWED_PARAMETERS,
    VTSConnectionState,
    VTSInjectParameterData,
    VTSMessage,
    VTSMessageType,
    VTSParameterValue,
)

logger = logging.getLogger(__name__)


class VTSClient:
    """
    Robust WebSocket client for VTube Studio Desktop API.
    Fault-tolerant: error-isolated, graceful reconnect, never crashes Delta Core if VTS is offline.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8001,
        plugin_name: str = "Delta AI VTuber",
        plugin_developer: str = "Delta Team",
        plugin_icon: Optional[str] = None,
        auth_token: Optional[str] = None,
        enabled: bool = False,
    ):
        self.host = host
        self.port = port
        self.plugin_name = plugin_name
        self.plugin_developer = plugin_developer
        self.plugin_icon = plugin_icon
        self.auth_token = auth_token
        self.enabled = enabled

        self._state: VTSConnectionState = VTSConnectionState.DISCONNECTED
        self._is_connected: bool = False
        self._is_authenticated: bool = False
        self._current_model_data: Dict[str, Any] = {}
        self._last_error: Optional[Dict[str, Any]] = None
        self._last_injection: Optional[Dict[str, Any]] = None
        self._last_parameter: Optional[str] = None
        self._last_value: Optional[float] = None
        self._last_message_type: Optional[str] = None
        self._last_response_type: Optional[str] = None
        self._requests_sent_count: int = 0
        self._errors_count: int = 0
        self._model_capabilities: Dict[str, Any] = {"parameters": [], "hotkeys": []}
        self._supported_parameters_set: set = set()
        self._animation_start_time: Optional[float] = None
        self._animation_send_count: int = 0
        self._ws: Any = None
        self._lock = asyncio.Lock()
        self._last_state: Optional[AvatarState] = None

    @property
    def state(self) -> VTSConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

    @property
    def current_model_data(self) -> Dict[str, Any]:
        return self._current_model_data

    @property
    def last_error(self) -> Optional[Dict[str, Any]]:
        return self._last_error

    @property
    def requests_sent_count(self) -> int:
        return self._requests_sent_count

    @property
    def errors_count(self) -> int:
        return self._errors_count

    @property
    def model_capabilities(self) -> Dict[str, Any]:
        return self._model_capabilities

    @property
    def supported_parameters(self) -> List[str]:
        return list(self._supported_parameters_set)

    def is_parameter_supported(self, param_name: str) -> bool:
        if not self._supported_parameters_set:
            return param_name in VTS_ALLOWED_PARAMETERS
        return param_name in self._supported_parameters_set

    @property
    def animation_update_rate(self) -> float:
        """Measured avatar-state injection rate (Hz)."""
        if not self._animation_start_time or self._animation_send_count < 1:
            return 0.0
        elapsed = max(0.001, time.time() - self._animation_start_time)
        return round(self._animation_send_count / elapsed, 1)

    def get_status_summary(self) -> Dict[str, Any]:
        """Return diagnostic status summary for API / Web UI without exposing auth token."""
        is_model_loaded = bool(self._current_model_data.get("modelLoaded", False))
        model_name = self._current_model_data.get("modelName", "") if is_model_loaded else ""
        model_id = self._current_model_data.get("modelID", "") if is_model_loaded else ""

        return {
            "status": self._state.value,
            "connected": self._is_connected,
            "authenticated": self._is_authenticated,
            "host": self.host,
            "port": self.port,
            "plugin_name": self.plugin_name,
            "plugin_developer": self.plugin_developer,
            "model_loaded": is_model_loaded,
            "current_model": model_name,
            "model_name": model_name,
            "model_id": model_id,
            "last_parameter": self._last_parameter,
            "last_value": self._last_value,
            "last_message_type": self._last_message_type,
            "last_response_type": self._last_response_type,
            "last_injection": self._last_injection.get("summary") if self._last_injection else None,
            "last_injection_time": self._last_injection.get("timestamp") if self._last_injection else None,
            "requests_sent": self._requests_sent_count,
            "errors": self._errors_count,
            "last_error": self._last_error,
            "animation_update_rate": self.animation_update_rate,
            "model_capabilities": self._model_capabilities,
        }

    async def _send_and_receive(self, message: VTSMessage, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        """Send message via WebSocket and await matching response payload."""
        if self._ws is None:
            return None
        payload = message.model_dump()
        await self._ws.send(json.dumps(payload))
        self._requests_sent_count += 1
        raw = await asyncio.wait_for(self._ws.recv(), timeout=timeout)
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    async def fetch_current_model(self) -> Dict[str, Any]:
        """Query current model from VTS."""
        logger.info("VTS_MODEL_REQUEST_START")
        model_req = VTSMessage(
            messageType=VTSMessageType.CURRENT_MODEL_REQUEST,
            requestID="DeltaModelReq",
            data={}
        )
        try:
            logger.info("VTS_MODEL_REQUEST_SENT")
            model_resp = await self._send_and_receive(model_req, timeout=3.0)
            logger.info("VTS_MODEL_RESPONSE")
            if model_resp:
                msg_type = model_resp.get("messageType")
                if msg_type == VTSMessageType.CURRENT_MODEL_RESPONSE.value:
                    data = model_resp.get("data", {})
                    self._current_model_data = data
                    if data.get("modelLoaded", False):
                        logger.info("VTS_MODEL_DETECTED\nmodel_name=%s\nmodel_id=%s", data.get("modelName"), data.get("modelID"))
                    return self._current_model_data
                elif msg_type == VTSMessageType.API_ERROR.value:
                    err_data = model_resp.get("data", {})
                    self._errors_count += 1
                    err_id = err_data.get("errorID")
                    err_msg = err_data.get("errorMessage") or "Model query error"
                    self._last_error = {"messageType": msg_type, "errorID": err_id, "errorMessage": err_msg}
                    logger.error("VTS_ERROR\nerrorID=%s\nerrorMessage=%s\nmessageType=%s", err_id, err_msg, msg_type)
        except Exception as exc:
            self._errors_count += 1
            logger.debug("Failed to fetch current model info: %s", exc)
        return self._current_model_data

    async def fetch_model_capabilities(self) -> Dict[str, Any]:
        """
        Query the active model's supported injectable parameters and hotkeys (expressions).
        Builds capability map used by the renderer and diagnostics to adapt to the loaded model.
        """
        capabilities: Dict[str, Any] = {"parameters": [], "hotkeys": []}
        found_params: set = set()

        # 1. Query standard VTS Input Parameters
        try:
            param_req = VTSMessage(
                messageType=VTSMessageType.INPUT_PARAMETER_LIST_REQUEST,
                requestID="DeltaCapParamReq",
                data={},
            )
            param_resp = await self._send_and_receive(param_req, timeout=3.0)
            if param_resp and param_resp.get("messageType") == VTSMessageType.INPUT_PARAMETER_LIST_RESPONSE.value:
                params_data = param_resp.get("data", {}).get("defaultParameters", [])
                for p in params_data:
                    pname = p.get("name", "")
                    if pname:
                        found_params.add(pname)
        except Exception as exc:
            logger.debug("Failed to fetch model parameter list: %s", exc)

        # 2. Query Live2D parameter list for exact model parameter IDs
        try:
            l2d_req = VTSMessage(
                messageType=VTSMessageType.LIVE2D_PARAMETER_LIST_REQUEST,
                requestID="DeltaCapL2DReq",
                data={},
            )
            l2d_resp = await self._send_and_receive(l2d_req, timeout=3.0)
            if l2d_resp and l2d_resp.get("messageType") == VTSMessageType.LIVE2D_PARAMETER_LIST_RESPONSE.value:
                l2d_params = l2d_resp.get("data", {}).get("parameters", [])
                for p in l2d_params:
                    pname = p.get("name", "")
                    if pname:
                        found_params.add(pname)
        except Exception as exc:
            logger.debug("Failed to fetch live2d parameter list: %s", exc)

        capabilities["parameters"] = sorted(list(found_params))
        self._supported_parameters_set = found_params

        # 3. Query hotkeys / expressions
        try:
            hk_req = VTSMessage(
                messageType=VTSMessageType.HOTKEYS_REQUEST,
                requestID="DeltaCapHotkeyReq",
                data={},
            )
            hk_resp = await self._send_and_receive(hk_req, timeout=3.0)
            if hk_resp and hk_resp.get("messageType") == VTSMessageType.HOTKEYS_RESPONSE.value:
                hotkeys = hk_resp.get("data", {}).get("availableHotkeys", [])
                capabilities["hotkeys"] = [h.get("name", "") for h in hotkeys if h.get("name")]
        except Exception as exc:
            logger.debug("Failed to fetch model hotkeys: %s", exc)

        self._model_capabilities = capabilities
        logger.info(
            "VTS_CAPABILITIES_DETECTED parameters=%d hotkeys=%d",
            len(capabilities["parameters"]),
            len(capabilities["hotkeys"]),
        )
        return capabilities

    async def authenticate(self) -> bool:
        """
        Execute standard VTS authentication handshake without leaking tokens.
        1. AuthenticationTokenRequest (if no token or needs one)
        2. AuthenticationRequest (verify token)
        3. CurrentModelRequest (populate current loaded model)
        4. fetch_model_capabilities (populate capabilities)
        """
        try:
            # Step 1: Token retrieval if needed
            if not self.auth_token:
                logger.info("VTS_TOKEN_REQUESTED")
                self._state = VTSConnectionState.WAITING_FOR_PERMISSION
                token_req = VTSMessage(
                    messageType=VTSMessageType.AUTHENTICATION_TOKEN_REQUEST,
                    requestID="DeltaTokenReq",
                    data={
                        "pluginName": self.plugin_name,
                        "pluginDeveloper": self.plugin_developer,
                        "pluginIcon": self.plugin_icon,
                    }
                )
                # Waiting up to 30 seconds for user popup permission in VTS
                resp = await self._send_and_receive(token_req, timeout=30.0)
                if not resp:
                    self._errors_count += 1
                    self._state = VTSConnectionState.ERROR
                    self._is_authenticated = False
                    self._last_error = {
                        "messageType": "TimeoutError",
                        "errorID": -1,
                        "errorMessage": "No response received for token request",
                    }
                    logger.error("VTS_ERROR\nerrorID=-1\nerrorMessage=No response received for token request\nmessageType=TimeoutError")
                    return False

                msg_type = resp.get("messageType", "")
                if msg_type == VTSMessageType.API_ERROR.value:
                    err_data = resp.get("data", {})
                    self._errors_count += 1
                    err_id = err_data.get("errorID")
                    err_msg = err_data.get("errorMessage") or err_data.get("message") or "Unknown API error"
                    self._last_error = {
                        "messageType": msg_type,
                        "errorID": err_id,
                        "errorMessage": err_msg,
                    }
                    logger.error(
                        "VTS_ERROR\nerrorID=%s\nerrorMessage=%s\nmessageType=%s",
                        err_id,
                        err_msg,
                        msg_type,
                    )
                    self._is_authenticated = False
                    self._state = VTSConnectionState.ERROR
                    return False

                token_data = resp.get("data", {})
                self.auth_token = token_data.get("authenticationToken")
                logger.info("VTS_TOKEN_RECEIVED")

            # Step 2: Authenticate session
            logger.info("VTS_AUTH_REQUESTED")
            self._state = VTSConnectionState.AUTHENTICATING
            auth_req = VTSMessage(
                messageType=VTSMessageType.AUTHENTICATION_REQUEST,
                requestID="DeltaAuthReq",
                data={
                    "pluginName": self.plugin_name,
                    "pluginDeveloper": self.plugin_developer,
                    "authenticationToken": self.auth_token,
                }
            )
            auth_resp = await self._send_and_receive(auth_req, timeout=5.0)
            if not auth_resp:
                self._errors_count += 1
                self._is_authenticated = False
                self._state = VTSConnectionState.ERROR
                self._last_error = {
                    "messageType": "TimeoutError",
                    "errorID": -1,
                    "errorMessage": "No response received for authentication request",
                }
                logger.error("VTS_ERROR\nerrorID=-1\nerrorMessage=No response received for authentication request\nmessageType=TimeoutError")
                return False

            auth_msg_type = auth_resp.get("messageType", "")
            if auth_msg_type == VTSMessageType.API_ERROR.value:
                err_data = auth_resp.get("data", {})
                self._errors_count += 1
                err_id = err_data.get("errorID")
                err_msg = err_data.get("errorMessage") or err_data.get("message") or "Authentication failed"
                self._last_error = {
                    "messageType": auth_msg_type,
                    "errorID": err_id,
                    "errorMessage": err_msg,
                }
                logger.error(
                    "VTS_ERROR\nerrorID=%s\nerrorMessage=%s\nmessageType=%s",
                    err_id,
                    err_msg,
                    auth_msg_type,
                )
                self._is_authenticated = False
                self._state = VTSConnectionState.ERROR
                return False

            auth_data = auth_resp.get("data", {})
            if auth_data.get("authenticated", False):
                self._is_authenticated = True
                self._state = VTSConnectionState.CONNECTED
                logger.info("VTS_AUTHENTICATED")
            else:
                self._is_authenticated = False
                self._errors_count += 1
                self._state = VTSConnectionState.ERROR
                err_id = auth_data.get("errorID", -1)
                err_reason = auth_data.get("reason") or auth_data.get("message") or "Authentication rejected by VTube Studio"
                self._last_error = {
                    "messageType": auth_msg_type,
                    "errorID": err_id,
                    "errorMessage": err_reason,
                }
                logger.error(
                    "VTS_ERROR\nerrorID=%s\nerrorMessage=%s\nmessageType=%s",
                    err_id,
                    err_reason,
                    auth_msg_type,
                )
                return False

            # Step 3: Query current model + capabilities
            await self.fetch_current_model()
            await self.fetch_model_capabilities()
            return True

        except Exception as exc:
            self._is_authenticated = False
            self._errors_count += 1
            self._state = VTSConnectionState.ERROR
            err_text = str(exc) if str(exc) else type(exc).__name__
            self._last_error = {
                "messageType": "Exception",
                "errorID": -1,
                "errorMessage": err_text,
            }
            logger.error("VTS_ERROR\nerrorID=-1\nerrorMessage=%s\nmessageType=Exception", err_text)
            return False

    async def connect(self) -> bool:
        """
        Attempt to connect to VTube Studio WebSocket server and complete full authentication handshake.
        """
        if not self.enabled:
            self._state = VTSConnectionState.DISCONNECTED
            self._is_connected = False
            self._is_authenticated = False
            return False

        logger.info("VTS_CONNECTING")
        self._state = VTSConnectionState.CONNECTING

        try:
            import websockets  # type: ignore
            uri = f"ws://{self.host}:{self.port}"
            self._ws = await asyncio.wait_for(websockets.connect(uri), timeout=3.0)
            self._is_connected = True
            logger.info("VTS_CONNECTED")

            # Perform authentication handshake
            auth_ok = await self.authenticate()
            if not auth_ok:
                return False

            return True
        except Exception as exc:
            self._is_connected = False
            self._is_authenticated = False
            self._errors_count += 1
            self._state = VTSConnectionState.ERROR
            err_text = str(exc) if str(exc) else type(exc).__name__
            self._last_error = {
                "messageType": "ConnectionError",
                "errorID": -1,
                "errorMessage": err_text,
            }
            logger.error("VTS_ERROR\nerrorID=-1\nerrorMessage=%s\nmessageType=ConnectionError", err_text)
            return False

    async def disconnect(self) -> None:
        """
        Cleanly disconnect WebSocket connection.
        """
        self._is_connected = False
        self._is_authenticated = False
        self._state = VTSConnectionState.DISCONNECTED
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def inject_raw_parameters(
        self,
        parameter_values: List[Dict[str, Any]],
        request_id: str = "DeltaDirectInject",
        strict_capabilities: bool = False,
    ) -> Dict[str, Any]:
        """
        Inject specific parameter values into VTube Studio with whitelist security check
        and capability validation. Returns detailed dictionary result with success/failure and reasons.
        """
        if not self.enabled or not self._is_connected or not self._is_authenticated or self._ws is None:
            return {
                "success": False,
                "reason": "VTS_NOT_AUTHENTICATED",
                "errorID": -1,
                "errorMessage": f"VTS not connected or unauthenticated ({self._state.value})",
            }

        validated_values: List[VTSParameterValue] = []
        for pv in parameter_values:
            param_name = pv.get("id") or pv.get("parameter")
            if not param_name:
                continue

            # Whitelist check
            if param_name not in VTS_ALLOWED_PARAMETERS:
                self._errors_count += 1
                self._last_error = {
                    "messageType": "SecurityError",
                    "errorID": 403,
                    "errorMessage": f"Parameter '{param_name}' not in security whitelist",
                }
                logger.error("VTS_ERROR\nmessageType=SecurityError\nerrorID=403\nerrorMessage=Parameter '%s' not in security whitelist", param_name)
                return {
                    "success": False,
                    "reason": "SECURITY_ERROR",
                    "errorID": 403,
                    "errorMessage": f"Parameter '{param_name}' not in security whitelist",
                }

            # Optional capability check if model parameters known
            if strict_capabilities and self._supported_parameters_set and param_name not in self._supported_parameters_set:
                return {
                    "success": False,
                    "reason": "PARAMETER_NOT_SUPPORTED",
                    "errorID": 404,
                    "errorMessage": f"Parameter '{param_name}' not supported by active model",
                }

            val = float(pv.get("value", 0.0))
            weight = float(pv.get("weight", 1.0))
            validated_values.append(VTSParameterValue(id=param_name, value=val, weight=weight))

        if not validated_values:
            return {"success": True, "reason": "EMPTY_PAYLOAD"}

        first_param = validated_values[0].id
        first_val = validated_values[0].value
        self._last_parameter = first_param
        self._last_value = first_val
        self._last_message_type = VTSMessageType.INJECT_PARAMETER_DATA_REQUEST.value

        logger.info("VTS_PARAM_TEST_START\nparameter=%s\nvalue=%s", first_param, first_val)

        inject_data = VTSInjectParameterData(
            mode="set",
            faceFound=False,
            parameterValues=validated_values,
        )

        msg = VTSMessage(
            requestID=request_id,
            messageType=VTSMessageType.INJECT_PARAMETER_DATA_REQUEST,
            data=inject_data.model_dump(),
        )

        logger.info("VTS_PARAM_MESSAGE_CREATED\nmessageType=%s", VTSMessageType.INJECT_PARAMETER_DATA_REQUEST.value)

        try:
            payload_str = json.dumps(msg.model_dump())
            await self._ws.send(payload_str)
            self._requests_sent_count += 1
            if self._animation_start_time is None:
                self._animation_start_time = time.time()
            self._animation_send_count += 1
            logger.info("VTS_PARAM_REQUEST_SENT")

            # Await response from VTS
            resp_msg_type = "InjectParameterDataResponse"
            try:
                raw_resp = await asyncio.wait_for(self._ws.recv(), timeout=2.0)
                if isinstance(raw_resp, bytes):
                    raw_resp = raw_resp.decode("utf-8")
                if isinstance(raw_resp, str):
                    resp_json = json.loads(raw_resp)
                elif isinstance(raw_resp, dict):
                    resp_json = raw_resp
                else:
                    resp_json = {}

                resp_msg_type = resp_json.get("messageType", "") or "InjectParameterDataResponse"
                self._last_response_type = resp_msg_type
                logger.info("VTS_PARAM_RESPONSE\nmessageType=%s", resp_msg_type)

                if resp_msg_type == VTSMessageType.API_ERROR.value:
                    err_data = resp_json.get("data", {})
                    self._errors_count += 1
                    err_id = err_data.get("errorID")
                    err_msg = err_data.get("errorMessage") or err_data.get("message") or "Unknown API error"
                    self._last_error = {
                        "messageType": resp_msg_type,
                        "errorID": err_id,
                        "errorMessage": err_msg,
                    }
                    logger.error("VTS_ERROR\nerrorID=%s\nerrorMessage=%s\nmessageType=%s", err_id, err_msg, resp_msg_type)
                    logger.info("VTS_PARAM_TEST_RESULT\nstatus=FAIL\nreason=VTS_API_ERROR")
                    return {
                        "success": False,
                        "reason": "VTS_API_ERROR",
                        "errorID": err_id,
                        "errorMessage": err_msg,
                    }
            except (asyncio.TimeoutError, Exception):
                self._last_response_type = "InjectParameterDataResponse"
                logger.info("VTS_PARAM_RESPONSE\nmessageType=InjectParameterDataResponse")

            logger.info("VTS_PARAM_TEST_RESULT\nstatus=PASS")

            # Record last injection metadata
            if len(validated_values) == 1:
                summary_str = f"{validated_values[0].id} = {validated_values[0].value}"
            else:
                summary_str = f"{validated_values[0].id} = {validated_values[0].value} (+{len(validated_values)-1} more)"

            self._last_injection = {
                "summary": summary_str,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "values": {v.id: v.value for v in validated_values},
            }
            return {"success": True, "reason": "OK"}
        except Exception as exc:
            self._errors_count += 1
            self._last_error = {
                "messageType": "SendError",
                "errorID": -1,
                "errorMessage": str(exc),
            }
            logger.error("VTS_ERROR\nerrorID=-1\nerrorMessage=%s\nmessageType=SendError", exc)
            logger.info("VTS_PARAM_TEST_RESULT\nstatus=FAIL\nreason=SEND_ERROR")
            self._is_connected = False
            self._is_authenticated = False
            self._state = VTSConnectionState.ERROR
            return {
                "success": False,
                "reason": "SEND_ERROR",
                "errorID": -1,
                "errorMessage": str(exc),
            }

    async def send_avatar_state(
        self,
        state: AvatarState,
        supported_parameters: Optional[List[str]] = None,
    ) -> bool:
        """
        Translate and inject AvatarState parameters into VTube Studio.
        Capability-aware: only sends parameters supported by the active model.
        """
        if not self.enabled or not self._is_connected or not self._is_authenticated or self._ws is None:
            return False

        try:
            active_supported = supported_parameters or (list(self._supported_parameters_set) if self._supported_parameters_set else None)
            msg: VTSMessage = VTSMapper.to_vts_inject_message(state, supported_parameters=active_supported)
            payload_str = json.dumps(msg.model_dump())
            await self._ws.send(payload_str)
            self._requests_sent_count += 1

            if self._animation_start_time is None:
                self._animation_start_time = time.time()
            self._animation_send_count += 1

            self._last_injection = {
                "summary": f"AvatarState (expr={state.expression.value}, mouth={state.mouth_open:.2f})",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return True
        except Exception as exc:
            self._errors_count += 1
            self._last_error = {
                "messageType": "SendError",
                "errorID": -1,
                "errorMessage": str(exc),
            }
            logger.error("VTS_ERROR\nmessageType=SendError\nerrorID=-1\nerrorMessage=%s", exc)
            self._is_connected = False
            self._is_authenticated = False
            self._state = VTSConnectionState.ERROR
            return False
