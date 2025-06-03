"""
Test configuration models.
"""

from typing import Any

from pydantic import BaseModel, Field, validator

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


class Test(BaseModel):
    """Test configuration.

    This model represents the configuration of a test.
    """

    name: str = Field(description="Test name")
    desc: str = Field(description="Test description")
    mode: TestMode = Field(description="Test mode")
    needs: list[str] | None = Field(default_factory=list, description="Test dependencies")
    runner: ShellRunner | HttpRunner | GrpcRunner | PytestRunner | DockerRunner = Field(
        description="Test runner configuration"
    )
    expect: Expect = Field(description="Test expectations")

    @classmethod
    def from_dict(cls, name: str, body: dict[str, Any]) -> "Test":
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

        expect = Expect(mode=TestMode(mode), **expect_config)

        # Create and return Test instance
        return cls(name=name, mode=TestMode(mode), desc=desc, needs=needs, runner=runner, expect=expect)

    @validator("runner")
    def validate_runner_type(self, v: BaseRunner, values: dict) -> BaseRunner:
        """Validate that runner type matches the test mode.

        Args:
            v: The runner instance
            values: Other field values

        Returns:
            BaseRunner: The validated runner instance

        Raises:
            ValueError: If runner type doesn't match the mode
        """
        mode = values.get("mode")
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

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
