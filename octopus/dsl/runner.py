"""
Test runner implementations.
"""

import sys
from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from octopus.dsl.constants import TEST_RUNNER_FIELDS, HttpMethod, TestMode
from octopus.dsl.interface import RunnerInterface

logger.remove()
logger.add(sys.stdout, level="DEBUG")


class BaseRunner(BaseModel, RunnerInterface):
    """Base class for all test runners."""

    def __init__(self, **data: Any):
        """Initialize the runner with configuration.

        Args:
            **data: Runner configuration data
        """
        super().__init__(**data)
        self._config = data

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

    def __repr__(self) -> str:
        """Return the string representation of the runner instance."""
        attrs = []
        for field in self.model_fields:
            value = getattr(self, field)
            if value is not None:
                attrs.append(f"{field}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"


class ShellRunner(BaseRunner):
    """Shell command test runner."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    cmd: list[str] = Field(description="Shell command")

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._config = self.model_dump()

    def get_config(self) -> dict[str, Any]:
        self._config.update({"cmd": self.cmd})
        return self._config

    def get_command(self) -> str:
        """Get the shell command string.

        Returns:
            str: The shell command string
        """
        return " ".join(self.cmd)


class HttpRunner(BaseRunner):
    """HTTP request test runner."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    header: str = Field(description="HTTP header")
    method: HttpMethod = Field(default=HttpMethod.GET, description="HTTP method")
    payload: str | None = Field(default=None, description="HTTP payload")
    endpoint: str = Field(description="HTTP endpoint")

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._config = self.model_dump()

    def get_config(self) -> dict[str, Any]:
        self._config.update(
            {"header": self.header, "method": self.method, "payload": self.payload, "endpoint": self.endpoint}
        )
        return self._config

    def get_command(self) -> str:
        """Get the HTTP request command string.

        Returns:
            str: The curl command string
        """
        required = TEST_RUNNER_FIELDS[TestMode.HTTP]
        if not all(field in self.get_config() for field in required):
            raise ValueError(f"HTTP runner requires fields: {required}")

        cmd = ["curl"]
        if self.header:
            cmd.extend(["-H", f"""'{self.header}'"""])
        cmd.extend(["-X", self.method])
        if self.payload and self.method not in [HttpMethod.GET, HttpMethod.DELETE]:
            cmd.extend(["-d", f"'{self.payload}'"])
        cmd.append(f"'{self.endpoint}'")
        return " ".join(cmd)


class GrpcRunner(BaseRunner):
    """gRPC request test runner."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    proto: str | None = Field(default=None, description="gRPC proto file")
    function: str = Field(description="gRPC function")
    endpoint: str = Field(description="gRPC endpoint")
    payload: str = Field(description="gRPC payload")

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._config = self.model_dump()

    def get_config(self) -> dict[str, Any]:
        self._config.update({"function": self.function, "endpoint": self.endpoint, "payload": self.payload})
        return self._config

    def get_command(self) -> str:
        """Get the gRPC request command string.

        Returns:
            str: The grpcurl command string
        """
        required = TEST_RUNNER_FIELDS[TestMode.GRPC]
        if not all(field in self.get_config() for field in required):
            raise ValueError(f"gRPC runner requires fields: {required}")

        cmd = ["grpcurl"]
        cmd.extend(["-proto", self.proto]) if self.proto else None
        cmd.extend(["-d", f"'{self.payload}'"])
        cmd.extend(["-plaintext", self.endpoint])
        cmd.append(self.function)
        return " ".join(cmd)


class PytestRunner(BaseRunner):
    """Pytest test runner."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    root_dir: str | None = Field(default=None, description="Pytest root directory")
    test_args: list[str] = Field(description="Pytest test arguments")

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._config = self.model_dump()

    def get_config(self) -> dict[str, Any]:
        self._config.update({"root_dir": self.root_dir, "test_args": self.test_args})
        return self._config

    def get_command(self) -> str:
        """Get the pytest command string.

        Returns:
            str: The pytest command string
        """
        required = TEST_RUNNER_FIELDS[TestMode.PYTEST]
        if not all(field in self.get_config() for field in required):
            raise ValueError(f"Pytest runner requires fields: {required}")

        cmd = ["pytest"]
        if self.root_dir:
            cmd.extend(["--rootdir", self.root_dir])
        if self.test_args:
            cmd.extend(self.test_args)
        return " ".join(cmd)


class DockerRunner(BaseRunner):
    """Docker command test runner."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    cntr_name: str = Field(description="Docker container name to run command")
    cmd: list[str] = Field(description="Execute command in docker container")

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._config = self.model_dump()

    def get_config(self) -> dict[str, Any]:
        self._config.update({"cmd": self.cmd, "cntr_name": self.cntr_name})
        return self._config

    def get_command(self) -> str:
        """Get the docker command string.

        Returns:
            str: The docker command string
        """
        if "cntr_name" not in self.get_config():
            raise ValueError("Docker runner requires 'cntr_name' in config")
        if "cmd" not in self.get_config():
            raise ValueError("Docker runner requires 'cmd' in config")
        return "docker exec " + self.cntr_name + " " + " ".join(self.cmd)


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

    return runners[mode](**config)
