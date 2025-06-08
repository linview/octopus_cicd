"""Base classes for CI platform adapters."""

from abc import ABC, abstractmethod
from typing import Any


class CIAdapter(ABC):
    """Base class for CI platform adapters."""

    def __init__(self, api_url: str, token: str):
        """Initialize the CI adapter.

        Args:
            api_url: The API endpoint URL
            token: Authentication token
        """
        self.api_url = api_url
        self.token = token

    @abstractmethod
    def get_pipeline_status(self, pipeline_id: str) -> dict[str, Any]:
        """Get pipeline status."""
        pass

    @abstractmethod
    def trigger_pipeline(self, config: dict[str, Any]) -> str:
        """Trigger a new pipeline."""
        pass

    @abstractmethod
    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline."""
        pass

    @abstractmethod
    def get_job_logs(self, job_id: str) -> str:
        """Get job logs."""
        pass
