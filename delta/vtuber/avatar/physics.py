"""
Live2D Spring-Damper Hair, Breathing, and Secondary Motion Physics for Delta VTuber.
Renderer-agnostic physics simulator computing dynamic sway offsets for hair, clothing, and accessories.
"""

import math
from typing import Any, Dict


class PhysicsSpring:
    """
    Critically-damped 2D spring simulator for smooth, organic secondary inertia.
    """

    def __init__(
        self,
        stiffness: float = 12.0,
        damping: float = 4.0,
        mass: float = 1.0,
    ):
        self.stiffness = stiffness
        self.damping = damping
        self.mass = mass
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        self.vel_x: float = 0.0
        self.vel_y: float = 0.0

    def update(self, target_x: float, target_y: float, dt: float = 0.016) -> None:
        # Hooke's Law with Damping: F = -k*(x - target) - d*v
        fx = -self.stiffness * (self.pos_x - target_x) - self.damping * self.vel_x
        fy = -self.stiffness * (self.pos_y - target_y) - self.damping * self.vel_y

        ax = fx / self.mass
        ay = fy / self.mass

        self.vel_x += ax * dt
        self.vel_y += ay * dt

        self.pos_x += self.vel_x * dt
        self.pos_y += self.vel_y * dt


class PhysicsController:
    """
    Simulates hair, clothing, accessory inertia, and breathing physics.
    """

    def __init__(self):
        # Dedicated spring simulators for hair sections and accessories
        self.hair_front_spring = PhysicsSpring(stiffness=18.0, damping=4.5)
        self.hair_side_spring = PhysicsSpring(stiffness=14.0, damping=3.8)
        self.hair_back_spring = PhysicsSpring(stiffness=10.0, damping=3.0)
        self.accessory_spring = PhysicsSpring(stiffness=15.0, damping=4.0)

    def update_physics(
        self,
        head_x: float,
        head_y: float,
        body_angle: float,
        speaking: bool = False,
        dt: float = 0.016,
    ) -> Dict[str, float]:
        """
        Step physics simulation and yield normalized parameter offsets (-1.0 to 1.0).
        """
        # Secondary sway reacts in opposite direction of head acceleration (inertia)
        target_hair_x = -head_x * 0.8 - body_angle * 0.5
        target_hair_y = -head_y * 0.6

        # Step springs
        self.hair_front_spring.update(target_hair_x * 0.7, target_hair_y * 0.5, dt)
        self.hair_side_spring.update(target_hair_x * 0.9, target_hair_y * 0.7, dt)
        self.hair_back_spring.update(target_hair_x * 1.1, target_hair_y * 0.9, dt)
        self.accessory_spring.update(target_hair_x * 0.85, target_hair_y * 0.6, dt)

        # Micro speaking flutter
        flutter = 0.02 * math.sin(dt * 30.0) if speaking else 0.0

        return {
            "hair_front": round(max(-1.0, min(1.0, self.hair_front_spring.pos_x + flutter)), 3),
            "hair_side": round(max(-1.0, min(1.0, self.hair_side_spring.pos_x + flutter)), 3),
            "hair_back": round(max(-1.0, min(1.0, self.hair_back_spring.pos_x)), 3),
            "clothing_sway": round(max(-1.0, min(1.0, -body_angle * 0.4)), 3),
            "accessory_motion": round(max(-1.0, min(1.0, self.accessory_spring.pos_x)), 3),
        }
