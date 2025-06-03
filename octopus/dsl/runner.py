"""
Test runner implementations.
"""

from typing import Any

from pydantic import BaseModel

from octopus.dsl.constants import TEST_EXPECT_FIELDS, TEST_RUNNER_FIELDS, TestMode
from octopus.dsl.interface import RunnerInterface


class BaseRunner(RunnerInterface):
    """Base class for all test runners."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the runner with configuration.

        Args:
            config: Runner configuration dictionary
        """
        self._config = config

    def get_config(self) -> dict[str, Any]:
        """Get the runner's configuration.

        Returns:
            Dict[str, Any]: The runner's configuration dictionary
        """
        return self._config

    def get_command(self) -> str:
        """Get the executable command string.

        Returns:
            str: The command string that can be executed
        """
        raise NotImplementedError("Subclasses must implement get_command")


class ShellRunner(BaseRunner):
    """Shell command test runner."""

    def get_command(self) -> str:
        """Get the shell command string.

        Returns:
            str: The shell command string
        """
        if "cmd" not in self._config:
            raise ValueError("Shell runner requires 'cmd' in config")
        return " ".join(self._config["cmd"])


class HttpRunner(BaseRunner):
    """HTTP request test runner."""

    def get_command(self) -> str:
        """Get the HTTP request command string.

        Returns:
            str: The curl command string
        """
        required = TEST_RUNNER_FIELDS[TestMode.HTTP]
        if not all(field in self._config for field in required):
            raise ValueError(f"HTTP runner requires fields: {required}")

        cmd = ["curl"]
        if self._config.get("header"):
            cmd.extend(["-H", self._config["header"]])
        cmd.extend(["-X", self._config["method"]])
        if self._config.get("payload"):
            cmd.extend(["-d", self._config["payload"]])
        cmd.append(self._config["endpoint"])
        return " ".join(cmd)


class GrpcRunner(BaseRunner):
    """gRPC request test runner."""

    def get_command(self) -> str:
        """Get the gRPC request command string.

        Returns:
            str: The grpcurl command string
        """
        required = TEST_RUNNER_FIELDS[TestMode.GRPC]
        if not all(field in self._config for field in required):
            raise ValueError(f"gRPC runner requires fields: {required}")

        cmd = ["grpcurl"]
        cmd.extend(["-d", self._config["payload"]])
        cmd.extend(["-plaintext", self._config["endpoint"]])
        cmd.append(self._config["function"])
        return " ".join(cmd)


class PytestRunner(BaseRunner):
    """Pytest test runner."""

    def get_command(self) -> str:
        """Get the pytest command string.

        Returns:
            str: The pytest command string
        """
        required = TEST_RUNNER_FIELDS[TestMode.PYTEST]
        if not all(field in self._config for field in required):
            raise ValueError(f"Pytest runner requires fields: {required}")

        cmd = ["pytest"]
        cmd.extend(["--rootdir", self._config["root_dir"]])
        if self._config.get("test_args"):
            cmd.extend(self._config["test_args"])
        return " ".join(cmd)


class DockerRunner(BaseRunner):
    """Docker command test runner."""

    def get_command(self) -> str:
        """Get the docker command string.

        Returns:
            str: The docker command string
        """
        if "cmd" not in self._config:
            raise ValueError("Docker runner requires 'cmd' in config")
        return "docker exec " + " ".join(self._config["cmd"])


class Expect(BaseModel):
    """Test expectations configuration."""

    def __init__(self, mode: TestMode, **data: Any):
        """Initialize expectations with mode-specific fields.

        Args:
            mode: Test mode
            **data: Expectation data
        """
        super().__init__(**data)
        self._mode = mode
        self._validate_fields()

    def _validate_fields(self):
        """Validate that all required fields are present."""
        required = TEST_EXPECT_FIELDS[self._mode]
        missing = [field for field in required if not hasattr(self, field)]
        if missing:
            raise ValueError(f"Missing required fields for {self._mode}: {missing}")


def create_runner(mode: TestMode, config: dict[str, Any]) -> RunnerInterface:
    """Create a runner instance based on mode.

    Args:
        mode: Test execution mode
        config: Runner configuration

    Returns:
        RunnerInterface: A runner instance

    Raises:
        ValueError: If mode is not supported
    """
    runners: dict[TestMode, type[RunnerInterface]] = {
        TestMode.SHELL: ShellRunner,
        TestMode.HTTP: HttpRunner,
        TestMode.GRPC: GrpcRunner,
        TestMode.PYTEST: PytestRunner,
        TestMode.DOCKER: DockerRunner,
    }

    if mode not in runners:
        raise ValueError(f"Unsupported test mode: {mode}")

    return runners[mode](config)
