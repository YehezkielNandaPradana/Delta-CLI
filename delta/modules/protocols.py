# delta/modules/protocols.py
"""Protocol contract for delta.modules namespace."""
from typing import Protocol, runtime_checkable


@runtime_checkable
class ModuleBase(Protocol):
    """Contract for all command modules."""

    name: str
    description: str

    def execute(self, args: list[str]) -> str: ...

    def validate_args(self, args: list[str]) -> bool: ...