"""
Parameter mapper between AvatarState and VTube Studio injection payloads.
"""

from typing import Dict, List, Optional
from delta.vtuber.avatar.live2d_mapper import Live2DParameterMapper
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.avatar.vts.protocol import (
    VTSInjectParameterData,
    VTSMessage,
    VTSMessageType,
    VTSParameterValue,
)


class VTSMapper:
    """
    Translates generic AvatarState into VTube Studio parameter injection requests.
    """

    @classmethod
    def to_vts_inject_message(
        cls,
        state: AvatarState,
        request_id: str = "DeltaAvatarState",
        supported_parameters: Optional[List[str]] = None,
    ) -> VTSMessage:
        live2d_dict: Dict[str, float] = Live2DParameterMapper.to_live2d_parameters(state)

        param_values: List[VTSParameterValue] = []
        for k, v in live2d_dict.items():
            if supported_parameters is not None and k not in supported_parameters:
                # Safe fallback: filter out parameters not supported by detected model
                continue
            param_values.append(VTSParameterValue(id=k, value=float(v), weight=1.0))

        inject_data = VTSInjectParameterData(
            mode="set",
            faceFound=False,
            parameterValues=param_values,
        )

        return VTSMessage(
            requestID=request_id,
            messageType=VTSMessageType.INJECT_PARAMETER_DATA_REQUEST,
            data=inject_data.model_dump(),
        )
