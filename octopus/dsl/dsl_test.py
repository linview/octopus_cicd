"""
Test configuration models.
"""

from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from octopus.dsl.checker import Expect
from octopus.dsl.constants import TestMode
from octopus.dsl.runner import (
    BaseRunner,
    DockerRunner,
    GrpcRunner,
    HttpRunner,
    PytestRunner,
    ShellRunner,
    create_runner,
)


class DslTest(BaseModel):
    """Test configuration.

    This model represents the configuration of a test.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str = Field(description="Test name")
    desc: str = Field(description="Test description")
    mode: TestMode = Field(description="Test mode")
    needs: list[str] | None = Field(default=[], description="Test's service dependencies")
    runner: ShellRunner | HttpRunner | GrpcRunner | PytestRunner | DockerRunner = Field(
        description="Test runner configuration"
    )
    expect: Expect = Field(description="Test expectations")

    def __init__(self, **data: Any):
        """Initialize the test configuration.

        Args:
            **data: Test configuration data
        """
        # initialize other fields first
        super().__init__(**data)

        # manually create expect instance, pass in mode
        if "expect" in data and isinstance(data["expect"], dict) and not isinstance(data["expect"], Expect):
            self.expect = Expect(**data["expect"])

    @field_validator("expect")
    @classmethod
    def validate_expect(cls, v: Expect, info: ValidationInfo) -> Expect:
        """Validate and initialize expect with test mode.

        Args:
            v: The expect instance
            info: Validation info containing other field values

        Returns:
            Expect: The validated expect instance
        """
        # Get current field name
        field_name = info.field_name  # Should be "expect"
        logger.debug(f"field_name: {field_name}")

        # Get all field values
        all_data = info.data  # Dictionary containing all fields

        # Get specific field value
        mode = all_data.get("mode")
        if mode is None:
            return v

        # if expect is a dictionary, create a new Expect instance
        if isinstance(v, dict):
            return Expect(mode=mode, **v)

        # if expect is already an Expect instance, update its mode
        v.mode = mode
        return v

    @model_validator(mode="after")
    def update_expect_mode(self) -> "DslTest":
        """Update co-related attributes after reassignment
        e.g. update test.expect.mode when test.mode changes.

        Returns:
            DslTest: The updated test instance
        """
        if self.expect:
            self.expect.mode = self.mode
        return self

    @classmethod
    def from_dict(cls, body: dict[str, Any]) -> "DslTest":
        """Create a Test instance from a dictionary.

        This method is used to create a Test instance from the YAML data structure
        where each test is represented as a key-value pair: <test_name>: <test_body>.

        Args:
            name: Test name from the YAML key
            body: Test configuration dictionary from the YAML value

        Returns:
            Test: A new Test instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not isinstance(body, dict):
            raise ValueError(f"Test body must be a dictionary, got {type(body)}")

        # Extract required fields
        name = body.get("name")
        if not name:
            raise ValueError("Test name is required")

        mode = body.get("mode")
        if not mode:
            raise ValueError(f"Test mode is required for test '{name}'")

        desc = body.get("desc", "")
        needs = body.get("needs", [])

        # Create runner instance
        runner_config = body.get("runner", {})
        if not isinstance(runner_config, dict):
            raise ValueError(f"Runner configuration must be a dictionary, got {type(runner_config)}")

        runner = create_runner(TestMode(mode), runner_config)

        # Create expect instance
        expect_config = body.get("expect", {})
        if not isinstance(expect_config, dict):
            raise ValueError(f"Expect configuration must be a dictionary, got {type(expect_config)}")
        expect_config.update({"mode": TestMode(mode)})

        # Create and return Test instance with all fields
        return cls(
            name=name,
            mode=TestMode(mode),
            desc=desc,
            needs=needs,
            runner=runner,
            expect=expect_config,  # Pass the dict directly, let __init__ handle it
        )

    @field_validator("runner")
    @classmethod
    def validate_runner_type(cls, v: BaseRunner, info: ValidationInfo) -> BaseRunner:
        """Validate that runner type matches the test mode.

        Args:
            v: The runner instance
            info: Validation info containing other field values

        Returns:
            BaseRunner: The validated runner instance

        Raises:
            ValueError: If runner type doesn't match the mode
        """
        # Get all field values
        all_data = info.data

        # Get specific field value
        mode = all_data.get("mode")
        if mode is None:
            return v

        runner_types = {
            TestMode.SHELL: ShellRunner,
            TestMode.HTTP: HttpRunner,
            TestMode.GRPC: GrpcRunner,
            TestMode.PYTEST: PytestRunner,
            TestMode.DOCKER: DockerRunner,
        }

        expected_type = runner_types[mode]
        if not isinstance(v, expected_type):
            raise ValueError(
                f"Invalid runner type for mode {mode}. " f"Expected {expected_type.__name__}, got {type(v).__name__}"
            )

        return v

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Convert the model to a dictionary.

        This method overrides the default model_dump to ensure nested Expect
        object uses its to_dict method.

        Returns:
            dict: The model as a dictionary
        """
        data = super().model_dump(**kwargs)
        if "expect" in data and isinstance(self.expect, Expect):
            data["expect"] = self.expect.to_dict()
        return data

    def to_dict(self) -> dict[str, Any]:
        """Convert the test instance to a dictionary.

        Returns:
            dict: The test instance as a dictionary
        """
        return {k: v for k, v in self.model_dump().items() if v is not None}

    def get_needs(self) -> list[str]:
        """Get the needs of the test."""
        return self.needs or []
