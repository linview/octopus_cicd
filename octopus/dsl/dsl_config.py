"""
Configuration DSL (Domain Specific Language) definition for test orchestration.
This module defines the data models for parsing and validating test configuration YAML files.
"""

from pydantic import BaseModel, Field

from octopus.dsl.service import Service
from octopus.dsl.test import Test


class Input(BaseModel):
    """Input variable configuration.

    Since the input format in YAML is key-value pairs like:
    - service_name: service1
    - $cntr_name: service_container

    We need to handle this structure dynamically at runtime.
    """

    key: str = Field(description="Input variable name")
    value: str = Field(description="Input variable value")


class DslConfig(BaseModel):
    """Top-level dsl configuration structure.

    This model represents the root structure of the DSL configuration YAML file.
    It includes version information, basic metadata, and collections of services and tests.
    """

    version: str = Field(description="DSL version number")
    name: str = Field(description="Configuration name")
    description: str = Field(description="Configuration description")
    inputs: list[Input] = Field(default_factory=list, description="List of input variables")
    services: dict[str, Service] = Field(default_factory=dict, description="Dictionary of service configurations")
    tests: dict[str, Test] = Field(default_factory=dict, description="Dictionary of test case configurations")

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"  # Forbid extra fields not defined in the model
        frozen = True  # Make the model immutable after instantiation

    @classmethod
    def from_yaml(cls, yaml_data: dict) -> "DslConfig":
        """Create a configuration instance from YAML data.

        This method handles the conversion of raw YAML data into a structured Config instance.
        It performs necessary transformations on the input data before instantiation.

        Args:
            yaml_data: The parsed YAML data as a dictionary

        Returns:
            DslConfig: An instance of the configuration model
        """
        # Transform inputs from key-value pairs to Input objects
        if "inputs" in yaml_data:
            inputs = []
            for item in yaml_data["inputs"]:
                if isinstance(item, dict):
                    for k, v in item.items():
                        inputs.append({"key": k, "value": str(v)})
            yaml_data["inputs"] = inputs

        return cls(**yaml_data)
