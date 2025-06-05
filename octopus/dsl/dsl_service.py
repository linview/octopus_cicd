"""
Service configuration models.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DslService(BaseModel):
    """Service configuration.

    This model represents the configuration of a service.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(description="Service name")
    desc: str = Field(description="Service description")

    image: str = Field(description="Service image")
    args: list[str] | None = Field(default_factory=list, description="Service arguments")
    envs: list[str] | None = Field(default_factory=list, description="Service environment variables")
    ports: list[str] | None = Field(default_factory=list, description="Service ports")
    vols: list[str] | None = Field(default_factory=list, description="Service volumes")
    depends_on: list[str] | None = Field(default_factory=list, description="Service depends on other Services")
    trigger: list[str] | None = Field(default_factory=list, description="Service triggers Tests")

    def __init__(self, **data):
        """Initialize service configuration.

        Args:
            **data: Service configuration data
        """
        super().__init__(**data)
        self._name = data.get("name", "")
        self._desc = data.get("desc", "")

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "DslService":
        """Create a Service instance from a dictionary.

        Args:
            body: Dictionary containing service configuration
        """
        return cls(**body)

    def to_dict(self) -> dict[str, Any]:
        """Convert the service instance to a dictionary."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
