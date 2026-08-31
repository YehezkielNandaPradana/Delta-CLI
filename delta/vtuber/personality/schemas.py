"""
Data schemas and models for Delta VTuber Personality, Persona, and Mood system.
"""

import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class PersonaProfile(BaseModel):
    """
    Measurable persona profile configuring AI VTuber tone, formality, and behavioral traits.
    """
    name: str = "Delta"
    role: str = "AI Developer / Security Assistant"
    description: str = "A sharp, supportive, and technically adept AI VTuber assistant."
    speaking_style: str = "casual_technical"
    language: str = "id-ID"
    formality: float = Field(default=0.3, ge=0.0, le=1.0)
    humor: float = Field(default=0.5, ge=0.0, le=1.0)
    enthusiasm: float = Field(default=0.6, ge=0.0, le=1.0)
    patience: float = Field(default=0.9, ge=0.0, le=1.0)
    technicality: float = Field(default=0.85, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("formality", "humor", "enthusiasm", "patience", "technicality", mode="before")
    @classmethod
    def clamp_trait(cls, v: Any) -> float:
        try:
            return max(0.0, min(1.0, float(v)))
        except (ValueError, TypeError):
            return 0.5


class MoodState(BaseModel):
    """
    Persistent character mood metrics with gradual decay toward baseline.
    """
    energy: float = Field(default=0.7, ge=0.0, le=1.0)
    happiness: float = Field(default=0.6, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    stress: float = Field(default=0.1, ge=0.0, le=1.0)
    curiosity: float = Field(default=0.75, ge=0.0, le=1.0)
    last_updated: float = Field(default_factory=time.time)

    @field_validator("energy", "happiness", "confidence", "stress", "curiosity", mode="before")
    @classmethod
    def clamp_metric(cls, v: Any) -> float:
        try:
            return max(0.0, min(1.0, float(v)))
        except (ValueError, TypeError):
            return 0.5

    def decay_towards_baseline(self, elapsed_sec: float, decay_rate: float = 0.05) -> None:
        """
        Gently decays mood values back toward natural baseline over time.
        """
        step = (elapsed_sec / 300.0) * decay_rate
        # Baseline targets
        target_energy = 0.65
        target_happiness = 0.60
        target_confidence = 0.75
        target_stress = 0.15
        target_curiosity = 0.70

        self.energy += (target_energy - self.energy) * step
        self.happiness += (target_happiness - self.happiness) * step
        self.confidence += (target_confidence - self.confidence) * step
        self.stress += (target_stress - self.stress) * step
        self.curiosity += (target_curiosity - self.curiosity) * step
        self.last_updated = time.time()
