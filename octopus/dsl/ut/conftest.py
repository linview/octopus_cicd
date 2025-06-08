"""Test fixtures for DSL module."""

from typing import Any

import pytest

from octopus.dsl.constants import HttpMethod, TestMode
from octopus.dsl.runner import (
    DockerRunner,
    GrpcRunner,
    HttpRunner,
    PytestRunner,
    ShellRunner,
)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "runner: mark test to use specific runner type")


def pytest_sessionstart(session):
    """Initialize global resources before test session starts."""
    # TODO: add global resources initialization
    pass


def pytest_sessionfinish(session, exitstatus):
    """Clean up global resources after test session ends."""
    # TODO: add global resources cleanup
    pass


# Session-scoped fixtures
@pytest.fixture(scope="session")
def test_mode() -> TestMode:
    """Fixture for test mode."""
    return TestMode.SHELL


# Module-scoped fixtures
@pytest.fixture(scope="module")
def shell_runner_config() -> dict[str, Any]:
    """Fixture for shell runner configuration."""
    return {"cmd": ["echo", "hello world"]}


@pytest.fixture(scope="module")
def http_runner_config() -> dict[str, Any]:
    """Fixture for HTTP runner configuration."""
    return {
        "header": "Content-Type: application/json",
        "method": HttpMethod.POST,
        "payload": '{"key": "value"}',
        "endpoint": "http://localhost:8080/api",
    }


@pytest.fixture(scope="module")
def grpc_runner_config() -> dict[str, Any]:
    """Fixture for gRPC runner configuration."""
    return {
        "proto": "hello.proto",
        "function": "HelloService.SayHello",
        "endpoint": "localhost:50051",
        "payload": '{"name": "world"}',
    }


@pytest.fixture(scope="module")
def runner_pytest_config() -> dict[str, Any]:
    """Fixture for pytest runner configuration."""
    return {"root_dir": "/path/to/tests", "test_args": ["-v", "test_file.py"]}


@pytest.fixture(scope="module")
def docker_runner_config() -> dict[str, Any]:
    """Fixture for docker runner configuration."""
    return {"cntr_name": "container_name", "cmd": ["echo", "hello world"]}


# Function-scoped fixtures
@pytest.fixture
def shell_runner(shell_runner_config: dict[str, Any]) -> ShellRunner:
    """Fixture for shell runner instance."""
    return ShellRunner(**shell_runner_config)


@pytest.fixture
def http_runner(http_runner_config: dict[str, Any]) -> HttpRunner:
    """Fixture for HTTP runner instance."""
    return HttpRunner(**http_runner_config)


@pytest.fixture
def grpc_runner(grpc_runner_config: dict[str, Any]) -> GrpcRunner:
    """Fixture for gRPC runner instance."""
    return GrpcRunner(**grpc_runner_config)


@pytest.fixture
def runner_pytest(runner_pytest_config: dict[str, Any]) -> PytestRunner:
    """Fixture for pytest runner instance."""
    return PytestRunner(**runner_pytest_config)


@pytest.fixture
def docker_runner(docker_runner_config: dict[str, Any]) -> DockerRunner:
    """Fixture for docker runner instance."""
    return DockerRunner(**docker_runner_config)
