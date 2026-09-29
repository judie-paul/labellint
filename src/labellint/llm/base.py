"""Bounded text-provider protocol."""

from typing import Protocol


class Provider(Protocol):
    """A provider returns plain text, never executable actions."""

    def complete(self, prompt: str) -> str: ...
