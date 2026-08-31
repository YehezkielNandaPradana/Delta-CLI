"""
Live2D Parameter & Expression Mapper for Delta VTuber.
Translates renderer-agnostic AvatarState and physics simulations into standard Cubism 4 / Live2D parameter values.
"""

from typing import Any, Dict
from delta.vtuber.avatar.physics import PhysicsController
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.emotion.schemas import VTuberExpression


# Standard Cubism 4 Parameter IDs (Standard Live2D model convention)
PARAM_ANGLE_X = "ParamAngleX"          # -30.0 to 30.0
PARAM_ANGLE_Y = "ParamAngleY"          # -30.0 to 30.0
PARAM_ANGLE_Z = "ParamAngleZ"          # -30.0 to 30.0
PARAM_BODY_ANGLE_X = "ParamBodyAngleX"  # -10.0 to 10.0
PARAM_EYE_L_OPEN = "ParamEyeLOpen"      # 0.0 to 1.0
PARAM_EYE_R_OPEN = "ParamEyeROpen"      # 0.0 to 1.0
PARAM_EYE_L_SMILE = "ParamEyeLSmile"    # 0.0 to 1.0
PARAM_EYE_R_SMILE = "ParamEyeRSmile"    # 0.0 to 1.0
PARAM_EYE_BALL_X = "ParamEyeBallX"      # -1.0 to 1.0 (Gaze)
PARAM_EYE_BALL_Y = "ParamEyeBallY"      # -1.0 to 1.0 (Gaze)
PARAM_MOUTH_OPEN_Y = "ParamMouthOpenY"  # 0.0 to 1.0
PARAM_MOUTH_FORM = "ParamMouthForm"      # -1.0 to 1.0
PARAM_BROW_L_Y = "ParamBrowLY"          # -1.0 to 1.0
PARAM_BROW_R_Y = "ParamBrowRY"          # -1.0 to 1.0
PARAM_CHEEK = "ParamCheek"              # 0.0 to 1.0
PARAM_HAIR_FRONT = "ParamHairFront"      # -1.0 to 1.0 (Physics)
PARAM_HAIR_SIDE = "ParamHairSide"        # -1.0 to 1.0 (Physics)
PARAM_HAIR_BACK = "ParamHairBack"        # -1.0 to 1.0 (Physics)
PARAM_BREATH = "ParamBreath"            # 0.0 to 1.0


class Live2DExpressionMapper:
    """
    Maps generic VTuberExpression to standard Live2D Cubism facial parameter adjustments.
    """

    @classmethod
    def get_expression_parameters(
        cls,
        expression: VTuberExpression,
        intensity: float = 0.5,
    ) -> Dict[str, float]:
        clamped_intensity = max(0.0, min(1.0, float(intensity)))
        params: Dict[str, float] = {
            PARAM_EYE_L_OPEN: 1.0,
            PARAM_EYE_R_OPEN: 1.0,
            PARAM_EYE_L_SMILE: 0.0,
            PARAM_EYE_R_SMILE: 0.0,
            PARAM_EYE_BALL_X: 0.0,
            PARAM_EYE_BALL_Y: 0.0,
            PARAM_MOUTH_FORM: 0.0,
            PARAM_BROW_L_Y: 0.0,
            PARAM_BROW_R_Y: 0.0,
            PARAM_CHEEK: 0.0,
        }

        if expression == VTuberExpression.SMILE:
            params[PARAM_EYE_L_SMILE] = round(0.8 * clamped_intensity, 2)
            params[PARAM_EYE_R_SMILE] = round(0.8 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = round(0.9 * clamped_intensity, 2)
            params[PARAM_CHEEK] = round(0.6 * clamped_intensity, 2)

        elif expression == VTuberExpression.EXCITED:
            params[PARAM_EYE_L_OPEN] = 1.0
            params[PARAM_EYE_R_OPEN] = 1.0
            params[PARAM_EYE_L_SMILE] = round(0.9 * clamped_intensity, 2)
            params[PARAM_EYE_R_SMILE] = round(0.9 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = 1.0
            params[PARAM_CHEEK] = round(0.9 * clamped_intensity, 2)
            params[PARAM_BROW_L_Y] = round(0.5 * clamped_intensity, 2)
            params[PARAM_BROW_R_Y] = round(0.5 * clamped_intensity, 2)

        elif expression == VTuberExpression.THINKING:
            params[PARAM_EYE_L_OPEN] = round(max(0.6, 1.0 - 0.3 * clamped_intensity), 2)
            params[PARAM_EYE_R_OPEN] = round(max(0.6, 1.0 - 0.3 * clamped_intensity), 2)
            params[PARAM_EYE_BALL_X] = round(0.35 * clamped_intensity, 2)  # Glance away while thinking
            params[PARAM_EYE_BALL_Y] = round(0.25 * clamped_intensity, 2)
            params[PARAM_BROW_L_Y] = round(-0.3 * clamped_intensity, 2)
            params[PARAM_BROW_R_Y] = round(0.4 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = round(-0.2 * clamped_intensity, 2)

        elif expression == VTuberExpression.CONFUSED:
            params[PARAM_BROW_L_Y] = round(-0.6 * clamped_intensity, 2)
            params[PARAM_BROW_R_Y] = round(0.6 * clamped_intensity, 2)
            params[PARAM_EYE_BALL_X] = round(-0.3 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = round(-0.5 * clamped_intensity, 2)
            params[PARAM_EYE_L_OPEN] = 0.8
            params[PARAM_EYE_R_OPEN] = 0.9

        elif expression == VTuberExpression.SURPRISED:
            params[PARAM_EYE_L_OPEN] = 1.0
            params[PARAM_EYE_R_OPEN] = 1.0
            params[PARAM_BROW_L_Y] = round(0.8 * clamped_intensity, 2)
            params[PARAM_BROW_R_Y] = round(0.8 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = 0.0

        elif expression == VTuberExpression.SAD:
            params[PARAM_EYE_L_OPEN] = round(max(0.5, 1.0 - 0.4 * clamped_intensity), 2)
            params[PARAM_EYE_R_OPEN] = round(max(0.5, 1.0 - 0.4 * clamped_intensity), 2)
            params[PARAM_BROW_L_Y] = round(-0.7 * clamped_intensity, 2)
            params[PARAM_BROW_R_Y] = round(-0.7 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = round(-0.8 * clamped_intensity, 2)

        elif expression == VTuberExpression.ANGRY:
            params[PARAM_BROW_L_Y] = round(-0.9 * clamped_intensity, 2)
            params[PARAM_BROW_R_Y] = round(-0.9 * clamped_intensity, 2)
            params[PARAM_MOUTH_FORM] = round(-0.6 * clamped_intensity, 2)

        return params


class Live2DParameterMapper:
    """
    Transforms generic AvatarState into fully resolved Live2D Cubism parameters including secondary physics.
    """
    _physics_engine = PhysicsController()

    @classmethod
    def to_live2d_parameters(cls, state: AvatarState) -> Dict[str, float]:
        """
        Convert AvatarState to Live2D parameter key-values.
        """
        # 1. Base head and body posture scaling
        angle_x = round(state.head_x * 30.0, 2)
        angle_y = round(state.head_y * 30.0, 2)
        body_angle_x = round(state.body_angle * 10.0, 2)

        # 2. Base expression parameters
        expr_params = Live2DExpressionMapper.get_expression_parameters(
            expression=state.expression,
            intensity=state.expression_intensity,
        )

        # 3. Mouth parameters
        mouth_open = round(state.mouth_open, 2)
        mouth_form = round(state.mouth_form if abs(state.mouth_form) > 0.01 else expr_params.get(PARAM_MOUTH_FORM, 0.0), 2)

        # 4. Secondary Physics simulation
        phys = cls._physics_engine.update_physics(
            head_x=state.head_x,
            head_y=state.head_y,
            body_angle=state.body_angle,
            speaking=state.speaking,
        )

        # Eye and Gaze values if provided in state metadata or default
        eye_l_open = state.metadata.get("eye_l_open", expr_params.get(PARAM_EYE_L_OPEN, 1.0))
        eye_r_open = state.metadata.get("eye_r_open", expr_params.get(PARAM_EYE_R_OPEN, 1.0))
        eye_x = state.metadata.get("eye_x", expr_params.get(PARAM_EYE_BALL_X, 0.0))
        eye_y = state.metadata.get("eye_y", expr_params.get(PARAM_EYE_BALL_Y, 0.0))
        breath_val = state.metadata.get("breath", round(0.5 + 0.5 * phys["hair_front"], 2))

        result: Dict[str, float] = {
            PARAM_ANGLE_X: angle_x,
            PARAM_ANGLE_Y: angle_y,
            PARAM_ANGLE_Z: round(angle_x * 0.3, 2),
            PARAM_BODY_ANGLE_X: body_angle_x,
            PARAM_MOUTH_OPEN_Y: mouth_open,
            PARAM_MOUTH_FORM: mouth_form,
            PARAM_HAIR_FRONT: phys["hair_front"],
            PARAM_HAIR_SIDE: phys["hair_side"],
            PARAM_HAIR_BACK: phys["hair_back"],
            PARAM_BREATH: breath_val,
            PARAM_EYE_L_OPEN: eye_l_open,
            PARAM_EYE_R_OPEN: eye_r_open,
            PARAM_EYE_BALL_X: eye_x,
            PARAM_EYE_BALL_Y: eye_y,
            **expr_params,
        }

        result[PARAM_EYE_L_OPEN] = eye_l_open
        result[PARAM_EYE_R_OPEN] = eye_r_open
        result[PARAM_EYE_BALL_X] = eye_x
        result[PARAM_EYE_BALL_Y] = eye_y
        result[PARAM_MOUTH_FORM] = mouth_form
        result[PARAM_MOUTH_OPEN_Y] = mouth_open
        result[PARAM_BREATH] = breath_val

        return result
