# delta/core/protocols.py
"""Protocol contracts for delta.core namespace.

These typing.Protocol classes define the public surface contract
for core components. They are typing-only and do not affect runtime behavior.
"""
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EngineProtocol(Protocol):
    """Contract for DeltaEngine-like components."""

    def run(self) -> None: ...

    def execute(self, command: str) -> str: ...


@runtime_checkable
class ConfigProtocol(Protocol):
    """Contract for DeltaConfig-like components."""

    def load(self, config_path: str | None = None) -> None: ...

    def save(self, config_path: str | None = None) -> None: ...

    def get(self, key: str, default: Any = None) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...