"""
Configuration DSL (Domain Specific Language) definition for test orchestration.
This module defines the data models for parsing and validating test configuration YAML files.
"""

from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationInfo, field_validator

from octopus.dsl.constants import SUPPORTED_VERSION, Keywords
from octopus.dsl.dag_manager import DAGManager
from octopus.dsl.dsl_service import DslService
from octopus.dsl.dsl_test import DslTest
from octopus.dsl.variable import Variable


class DslConfig(BaseModel):
    """Top-level dsl configuration structure.

    This model represents the root structure of the DSL configuration YAML file.
    It includes version information, basic metadata, and collections of services and tests.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    version: str = Field(description="DSL version number")
    name: str = Field(description="Configuration name")
    desc: str = Field(description="Configuration description")
    inputs: list[Variable] = Field(default_factory=list, description="List of input variables")
    services: list[DslService] = Field(default_factory=list, description="List of service configurations")
    tests: list[DslTest] = Field(default_factory=list, description="List of test case configurations")

    # Private fields for internal use
    _services_dict: dict[str, DslService] = PrivateAttr(default_factory=dict)
    _tests_dict: dict[str, DslTest] = PrivateAttr(default_factory=dict)
    _dag_manger: DAGManager = PrivateAttr(default=None)
    _inputs_dict: dict[str, Variable] = PrivateAttr(default_factory=dict)
    _lazy_vars: dict[str, Variable] = PrivateAttr(default_factory=dict)

    def __init__(self, **data: Any):
        """Initialize configuration.

        Args:
            **data: Configuration data

        Raises:
            ValueError: If duplicate service or test names are found
        """
        super().__init__(**data)
        # Initialize inputs mapping
        for input in self.inputs:
            if input.key in self._inputs_dict:
                logger.warning(f"Duplicate input key found: {input.key}")
            self._inputs_dict[input.key] = input
            if input.is_lazy:
                self._lazy_vars[input.key] = input

        # Initialize services mapping with duplicate check
        self._services_dict = {}
        for service in self.services:
            if service.name in self._services_dict:
                raise ValueError(f"Duplicate service name found: {service.name}")
            self._services_dict[service.name] = service

        # Initialize tests mapping with duplicate check
        self._tests_dict = {}
        for test in self.tests:
            if test.name in self._tests_dict:
                raise ValueError(f"Duplicate test name found: {test.name}")
            self._tests_dict[test.name] = test

        self._init_dag()

    def _init_dag(self):
        """Init DAG with self"""
        self.verify()
        self._dag_manger = DAGManager(self)

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str, info: ValidationInfo) -> str:
        """Validate the version of the configuration."""
        if v not in SUPPORTED_VERSION:
            raise ValueError(f"Unsupported version: {v}")
        return v

    @field_validator("inputs")
    @classmethod
    def _validate_inputs(cls, v: list[Variable]) -> list[Variable]:
        """Validate the inputs of the configuration."""
        return v

    def get_service_by_name(self, name: str) -> DslService | None:
        """Get service by name.

        Args:
            name: Service name

        Returns:
            DslService | None: Service instance if found, None otherwise
        """
        return self._services_dict.get(name)

    def get_test_by_name(self, name: str) -> DslTest | None:
        """Get test by name.

        Args:
            name: Test name

        Returns:
            DslTest | None: Test instance if found, None otherwise
        """
        return self._tests_dict.get(name)

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
    def _transform_tests(tests_data: list) -> list[DslTest]:
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
                tests.append(DslTest.from_dict(test_data))
        return tests

    @staticmethod
    def _transform_services(services_data: list) -> list[DslService]:
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
                services.append(DslService.from_dict(service_data))
        return services

    @classmethod
    def from_dict(cls, data: dict) -> "DslConfig":
        """Create a configuration instance from a dictionary.

        This method handles the conversion of raw data into a structured Config instance.
        It performs necessary transformations on the input data before instantiation.

        Args:
            data: The configuration data as a dictionary

        Returns:
            DslConfig: An instance of the configuration model
        """
        # Transform inputs from key-value pairs to Input objects
        if "inputs" in data:
            data["inputs"] = cls._transform_inputs(data["inputs"])

        # Transform tests from list to Test objects
        if "tests" in data:
            data["tests"] = cls._transform_tests(data["tests"])

        # Transform services from list to Service objects
        if "services" in data:
            data["services"] = cls._transform_services(data["services"])

        return cls(**data)

    @classmethod
    def _syntax_check(cls, data: dict):
        """Syntax check for config yaml data"""
        if isinstance(data, dict):
            for key in data:
                if key in [Keywords.KW_INPUTS]:
                    continue
                if not Keywords.is_valid_keyword(key):
                    raise ValueError(f"Syntax error: invalid keyword '{key}'")
                cls._syntax_check(data[key])
        elif isinstance(data, list):
            for item in data:
                cls._syntax_check(item)
        else:
            return

    @classmethod
    def from_yaml_file(cls, yaml_path: Path) -> "DslConfig":
        """Create a configuration instance from a YAML file.

        This method reads a YAML file and creates a configuration instance from its contents.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            DslConfig: An instance of the configuration model

        Raises:
            ValueError: If the YAML file is invalid
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")

        with open(yaml_path) as f:
            try:
                yaml_data = yaml.load(f, Loader=yaml.FullLoader)
            except yaml.YAMLError:
                logger.exception("Failed to load YAML file")
                return None

        if not Keywords.is_support_version(yaml_data.get("version", None)):
            raise ValueError(f"Unsupported version: {yaml_data.get('version', None)}")

        cls._syntax_check(yaml_data)
        return cls.from_dict(yaml_data)

    def _collect_verification_errors(self) -> list[str]:
        """Collect all verification errors.

        Returns:
            list[str]: List of error messages, empty if no errors found
        """
        errors = []

        # Verify next references
        nexts_ok, nexts_err = self._verify_nexts()
        if not nexts_ok:
            errors.append(f"Services with invalid 'next': {nexts_err}")

        # Verify dependencies
        deps_ok, deps_err = self._verify_dependencies()
        if not deps_ok:
            errors.append(f"Services with invalid 'depends_on': {deps_err}")

        # Verify triggers
        trig_ok, trig_err = self._verify_triggers()
        if not trig_ok:
            errors.append(f"Services with invalid 'trigger': {trig_err}")

        # Verify needs
        needs_ok, needs_err = self._verify_needs()
        if not needs_ok:
            errors.append(f"Tests with invalid 'needs': {needs_err}")

        # Verify inputs
        inputs_ok, inputs_err = self._verify_inputs()
        if not inputs_ok:
            errors.append(f"Invalid input references: {inputs_err}")

        return errors

    def verify(self) -> bool:
        """Verify the configuration by semantic check.

        Raises:
            ValueError: If any semantic check fails, with detailed error messages
        """
        errors = self._collect_verification_errors()
        if errors:
            raise ValueError("semantic check failed:\n" + "\n".join(errors))
        return True

    def _verify_nexts(self) -> tuple[bool, list[dict[str, str]]]:
        """Semantic check: Verify the service next of the configuration."""
        missing_nexts: list[dict[str, str]] = []
        for service in self.services:
            for svc in service.get_next():
                if svc not in self._services_dict:
                    err_info = {"service": service.name, "next": svc, "info": f"{svc} not found"}
                    missing_nexts.append(err_info)
        if len(missing_nexts) > 0:
            logger.error(f"Missing nexts: {missing_nexts}")
            return False, missing_nexts
        return True, []

    def _verify_dependencies(self) -> tuple[bool, list[dict[str, str]]]:
        """Semantic check: Verify the service dependencies of the configuration."""
        missing_deps: list[dict[str, str]] = []
        for service in self.services:
            if len(service.get_depends_on()) == 0:
                continue
            for svc in service.get_depends_on():
                if svc not in self._services_dict:
                    err_info = {"service": service.name, "dependency": svc, "info": f"{svc} not found"}
                    missing_deps.append(err_info)
        if len(missing_deps) > 0:
            logger.error(f"Missing dependencies: {missing_deps}")
            return False, missing_deps
        return True, []

    def _verify_triggers(self) -> tuple[bool, list[dict[str, str]]]:
        """Semantic check: Verify the service triggers of the configuration."""
        missing_triggers: list[dict[str, str]] = []
        for service in self.services:
            for test in service.get_trigger():
                if test not in self._tests_dict:
                    err_info = {"service": service.name, "trigger": test, "info": f"{test} not found"}
                    missing_triggers.append(err_info)
        if len(missing_triggers) > 0:
            logger.error(f"Missing triggers: {missing_triggers}")
            return False, missing_triggers
        return True, []

    def _verify_needs(self) -> bool:
        """Semantic check: Verify the test needs of the configuration."""
        missing_needs: list[dict[str, str]] = []
        for test in self.tests:
            for svc in test.get_needs():
                if svc not in self._services_dict:
                    err_info = {"test": test.name, "needs": svc, "info": f"{svc} not found"}
                    missing_needs.append(err_info)
        if len(missing_needs) > 0:
            logger.error(f"Missing needs: {missing_needs}")
            return False, missing_needs
        return True, []

    def _verify_inputs(self) -> tuple[bool, list[dict[str, str]]]:
        """Verify the inputs of the configuration."""
        return True, []

    def to_dict(self) -> dict[str, Any]:
        """Convert the configuration instance to a dictionary.

        Returns:
            dict: The configuration instance as a dictionary
        """
        return {k: v for k, v in self.model_dump().items() if v is not None}

    def is_valid_service(self, service_name: str) -> bool:
        """Check if the service name is valid."""
        self.verify()
        return service_name in self._services_dict

    def is_valid_test(self, test_name: str) -> bool:
        """Check if the test name is valid."""
        self.verify()
        return test_name in self._tests_dict

    def gen_execution_plan(self) -> dict[str, list[str]]:
        """generate execution plan by DAG"""
        self.verify()
        return self._dag_manger.generate_execution_plan()

    def print_execution_dag(self):
        """generate execution DAG by DAG"""
        self.verify()
        if not self._dag_manger.is_valid_dag():
            raise ValueError("Current config failed DAG check")
        self._dag_manger.visualize_with_rich()

    def visualize_execution_dag(self):
        """visualize execution DAG by DAG"""
        self.verify()
        if not self._dag_manger.is_valid_dag():
            raise ValueError("Current config failed DAG check")
        self._dag_manger.visualize_with_plt()

    def __repr__(self) -> str:
        """Custom string representation."""
        attrs = []
        for field in self.model_fields:
            value = getattr(self, field)
            if value is not None:
                attrs.append(f"{field}={value!r}")
        return f"DslConfig({', '.join(attrs)})"


if __name__ == "__main__":
    test_yaml_file = Path(__file__).parent / "test_data" / "config_sample_v0.1.0.yaml"
    config = DslConfig.from_yaml_file(test_yaml_file)
    try:
        print(config)
    except TypeError:
        logger.exception("Failed to print config")
    print(config.gen_execution_plan())
    config.print_execution_dag()
    config.visualize_execution_dag()
