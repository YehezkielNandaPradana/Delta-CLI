"""
Canonical Character Profile definitions for Delta Live2D / VTS integration.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from delta.vtuber.emotion.schemas import VTuberExpression


class CharacterProfile(BaseModel):
    """
    Canonical character configuration specifying model ID, parameter capabilities,
    expression mappings, and default visual / physical properties.
    """
    name: str = "Delta AI VTuber"
    model_id: str = "delta_cyber_v1"
    model_name: str = "Delta Cyber Live2D"
    supported_expressions: List[str] = Field(default_factory=lambda: [
        "neutral", "smile", "excited", "thinking", "confused", "surprised", "sad", "angry"
    ])
    supported_parameters: List[str] = Field(default_factory=lambda: [
        "ParamAngleX", "ParamAngleY", "ParamAngleZ",
        "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ",
        "ParamEyeLOpen", "ParamEyeROpen", "ParamEyeLSmile", "ParamEyeRSmile",
        "ParamEyeBallX", "ParamEyeBallY",
        "ParamMouthOpenY", "ParamMouthForm",
        "ParamBrowLY", "ParamBrowRY",
        "ParamCheek",
        "ParamHairFront", "ParamHairSide", "ParamHairBack",
        "ParamBreath"
    ])
    default_idle: Dict[str, float] = Field(default_factory=lambda: {
        "head_x": 0.0,
        "head_y": 0.0,
        "body_angle": 0.0,
        "mouth_open": 0.0,
        "mouth_form": 0.0,
        "expression_intensity": 0.5,
    })
    voice_profile: str = "id-ID-GadisNeural"
    voice_speed: float = 1.0
    physics_enabled: bool = True
    lip_sync_enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_expression_supported(self, expression: str) -> bool:
        return expression.lower().strip() in [e.lower() for e in self.supported_expressions]

    def is_parameter_supported(self, parameter: str) -> bool:
        return parameter in self.supported_parameters


# Default Canonical Profile instance
default_character_profile = CharacterProfile()
