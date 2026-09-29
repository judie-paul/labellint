"""Validated, environment-aware defaults with no network requirements."""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings; environment variables use the LABELLINT_ prefix."""

    model_config = SettingsConfigDict(env_prefix="LABELLINT_", env_file=".env", extra="forbid")
    seed: int = Field(default=42, ge=0)
    items: int = Field(default=100, ge=1)
    annotators: int = Field(default=50, ge=1)
    raters_per_item: int = Field(default=3, ge=1)
    provider: Literal["mock", "openai", "anthropic"] = "mock"

    @model_validator(mode="after")
    def validate_overlap(self) -> "Settings":
        """Prevent requests for more distinct raters than the pool contains."""
        if self.raters_per_item > self.annotators:
            raise ValueError("raters_per_item cannot exceed annotators")
        return self
