"""
Configuration DSL (Domain Specific Language) definition for test orchestration.
This module defines the data models for parsing and validating test configuration YAML files.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from octopus.dsl.service import Service
from octopus.dsl.test import Test


class Variable(BaseModel):
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
    desc: str = Field(description="Configuration description")
    inputs: list[Variable] = Field(default_factory=list, description="List of input variables")
    services: list[Service] = Field(default_factory=list, description="List of service configurations")
    tests: list[Test] = Field(default_factory=list, description="List of test case configurations")

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"  # Forbid extra fields not defined in the model
        frozen = True  # Make the model immutable after instantiation

    @staticmethod
    def _transform_inputs(inputs_data: list) -> list[dict]:
        """Transform input data to Variable objects.

        Args:
            inputs_data: List of input data from YAML

        Returns:
            list[dict]: List of transformed input data
        """
        inputs = []
        for item in inputs_data:
            if isinstance(item, dict):
                for k, v in item.items():
                    inputs.append({"key": k, "value": str(v)})
        return inputs

    @staticmethod
    def _transform_tests(tests_data: list) -> list[Test]:
        """Transform test data to Test objects.

        Args:
            tests_data: List of test data from YAML

        Returns:
            list[Test]: List of Test instances

        Raises:
            ValueError: If test name is missing
        """
        tests = []
        for test_data in tests_data:
            if isinstance(test_data, dict):
                if test_data.get("name", None) is None:
                    raise ValueError("Test name is required")
                tests.append(Test.from_dict(test_data))
        return tests

    @staticmethod
    def _transform_services(services_data: list) -> list[Service]:
        """Transform service data to Service objects.

        Args:
            services_data: List of service data from YAML

        Returns:
            list[Service]: List of Service instances

        Raises:
            ValueError: If service name is missing
        """
        services = []
        for service_data in services_data:
            if isinstance(service_data, dict):
                if service_data.get("name", None) is None:
                    raise ValueError("Service name is required")
                services.append(Service.from_dict(service_data))
        return services

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
            yaml_data["inputs"] = cls._transform_inputs(yaml_data["inputs"])

        # Transform tests from list to Test objects
        if "tests" in yaml_data:
            yaml_data["tests"] = cls._transform_tests(yaml_data["tests"])

        # Transform services from list to Service objects
        if "services" in yaml_data:
            yaml_data["services"] = cls._transform_services(yaml_data["services"])

        return cls(**yaml_data)


if __name__ == "__main__":
    test_yaml_file = Path(__file__).parent / "test_data" / "config_sample_v0.1.0.yaml"
    with open(test_yaml_file) as f:
        yaml_data = yaml.load(f, Loader=yaml.FullLoader)
        config = DslConfig.from_yaml(yaml_data)
        print(config)
