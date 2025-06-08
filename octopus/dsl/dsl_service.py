"""
Service configuration models.
"""

import copy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from octopus.dsl.variable import VariableEvaluator


class DslService(BaseModel):
    """Service configuration.

    This model represents the configuration of a service.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(description="Service name")
    desc: str = Field(description="Service description")

    image: str = Field(description="Service image")
    args: list[str] | None = Field(default_factory=list, description="container run args ")
    envs: list[str] | None = Field(default_factory=list, description="container env variables")
    ports: list[str] | None = Field(default_factory=list, description="container port maps")
    vols: list[str] | None = Field(default_factory=list, description="container volume maps")
    next: list[str] = Field(default_factory=list, description="the container run next after current one")
    depends_on: list[str] | None = Field(
        default_factory=list, description="the living container that current one depends on"
    )
    trigger: list[str] | None = Field(default_factory=list, description="the tests that current one triggers")

    def __init__(self, **data):
        """Initialize service configuration.

        Args:
            **data: Service configuration data
        """
        super().__init__(**data)
        # Store original data for evaluate
        self.__origin_data = copy.deepcopy(data)

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "DslService":
        """Create a Service instance from a dictionary.

        Args:
            body: Dictionary containing service configuration
        """
        return cls(**body)

    def evaluate(self, variables: dict[str, Any]) -> None:
        """Evaluate the service with given variables.

        This method is idempotent, meaning it can be called multiple times with the same
        variables and produce the same result. It achieves this by:
        1. Restoring the original data from __origin_data
        2. Evaluating variables in the restored data
        3. Updating the model with evaluated values

        Args:
            variables: A dictionary of variables to evaluate the service with
        """
        # Restore original data
        data = copy.deepcopy(self.__origin_data)

        # Evaluate variables in the data
        VariableEvaluator.evaluate_dict(data, variables)

        # Update model with evaluated values
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Convert the service instance to a dictionary."""
        return {k: v for k, v in self.model_dump().items() if v is not None}

    def get_depends_on(self) -> list[str]:
        """Get the dependencies of the service."""
        return self.depends_on or []

    def get_trigger(self) -> list[str]:
        """Get the triggers of the service."""
        return self.trigger or []

    def get_next(self) -> list[str]:
        """Get the next of the service."""
        return self.next or []

    def __repr__(self) -> str:
        """Return the string representation of the service instance."""
        attrs = []
        for field in self.model_fields:
            value = getattr(self, field)
            if value is not None:
                attrs.append(f"{field}={value!r}")
        return f"DslService({', '.join(attrs)})"
