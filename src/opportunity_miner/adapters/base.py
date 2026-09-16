"""Base contract and data schemas for pluggable source adapters."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class NormalizedSignal(BaseModel):
    """Standardized representation of a public signal collected from any source."""
    source: str = Field(..., description="Source name (e.g., 'hackernews', 'reddit', 'upwork')")
    source_id: str = Field(..., description="Unique post ID or external ID within the source")
    source_url: str = Field(..., description="Canonical URL to the original post or listing")
    title: str = Field(..., description="Title of the post or job")
    author: str | None = Field(default=None, description="Username or organization name")
    body: str = Field(..., description="Full text body or description")
    published_at: datetime = Field(..., description="Publication timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")


class SourceAdapter(ABC):
    """Abstract base class for all OpportunityMiner source adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Identifier for the source adapter."""
        pass

    @abstractmethod
    def health_check(self) -> tuple[bool, str]:
        """Verify connectivity and credentials.
        Returns:
            (is_available: bool, diagnostic_message: str)
        """
        pass

    @abstractmethod
    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        """Collect and normalize signals from the source platform.
        Must handle network errors gracefully without crashing the pipeline.
        """
        pass
