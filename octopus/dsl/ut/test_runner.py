"""Unit tests for runner module."""

import sys

import pydantic_core
import pytest
from loguru import logger

from octopus.dsl.constants import HttpMethod, TestMode
from octopus.dsl.runner import (
    BaseRunner,
    DockerRunner,
    GrpcRunner,
    HttpRunner,
    PytestRunner,
    ShellRunner,
    create_runner,
)

logger.remove()
logger.add(sys.stdout, level="DEBUG")


def test_base_runner_init():
    """Test BaseRunner initialization."""
    config = {"key": "value"}
    runner = BaseRunner(**config)
    # BaseRunner is abstract class, not model fields
    assert runner.get_config() == {}


def test_shell_runner_get_config(shell_runner: ShellRunner):
    """Test ShellRunner get_config method."""
    config = shell_runner.get_config()
    assert "cmd" in config
    assert config["cmd"] == ["echo", "hello world"]


def test_shell_runner_get_command(shell_runner: ShellRunner):
    """Test ShellRunner get_command method."""
    cmd = shell_runner.get_command()
    assert cmd == "echo hello world"


def test_http_runner_get_config(http_runner: HttpRunner):
    """Test HttpRunner get_config method."""
    http_runner.method = HttpMethod.POST
    config = http_runner.get_config()
    assert all(key in config for key in ["header", "method", "payload", "endpoint"])
    assert config["method"] == HttpMethod.POST
    http_runner.method = HttpMethod.GET
    config = http_runner.get_config()
    assert config["method"] == HttpMethod.GET


def test_http_runner_get_command(http_runner: HttpRunner):
    """Test HttpRunner get_command method."""
    if http_runner.method in [HttpMethod.GET, HttpMethod.DELETE]:
        assert "-d" not in http_runner.get_command()
    else:
        assert "-d" in http_runner.get_command()

    http_runner.method = HttpMethod.POST
    cmd = http_runner.get_command()
    logger.debug(cmd)
    assert "curl" in cmd
    assert "-H" in cmd
    assert "-X" in cmd
    assert "http://localhost:8080/api" in cmd
    http_runner.method = HttpMethod.GET
    cmd = http_runner.get_command()
    logger.debug(cmd)
    assert "-d" not in http_runner.get_command()


def test_grpc_runner_get_config(grpc_runner: GrpcRunner):
    """Test GrpcRunner get_config method."""
    config = grpc_runner.get_config()
    logger.debug(config)
    assert all(key in config for key in ["function", "endpoint", "payload"])


def test_grpc_runner_get_command(grpc_runner: GrpcRunner):
    """Test GrpcRunner get_command method."""
    cmd = grpc_runner.get_command()
    logger.debug(cmd)
    assert "grpcurl" in cmd
    assert "-d" in cmd
    assert "-plaintext" in cmd
    assert "localhost:50051" in cmd
    assert "HelloService.SayHello" in cmd


def test_pytest_runner_get_config(runner_pytest: PytestRunner):
    """Test PytestRunner get_config method."""
    config = runner_pytest.get_config()
    logger.debug(config)
    assert all(key in config for key in ["root_dir", "test_args"])


def test_pytest_runner_get_command(runner_pytest: PytestRunner):
    """Test PytestRunner get_command method."""
    cmd = runner_pytest.get_command()
    logger.debug(cmd)
    assert "pytest" in cmd
    assert "--rootdir" in cmd
    assert "/path/to/tests" in cmd
    assert "-v" in cmd
    assert "test_file.py" in cmd


def test_docker_runner_get_config(docker_runner: DockerRunner):
    """Test DockerRunner get_config method."""
    config = docker_runner.get_config()
    logger.debug(config)
    assert "cmd" in config
    assert "cntr_name" in config
    assert config["cntr_name"] == "container_name"
    assert config["cmd"] == ["echo", "hello world"]


def test_docker_runner_get_command(docker_runner: DockerRunner):
    """Test DockerRunner get_command method."""
    cmd = docker_runner.get_command()
    logger.debug(cmd)
    assert cmd == "docker exec container_name echo hello world"


def test_create_runner():
    """Test create_runner factory function."""
    # Test creating each type of runner
    runners = {
        TestMode.SHELL: (
            ShellRunner,
            [
                {"cmd": ["echo", "test2"]},
            ],
        ),
        TestMode.HTTP: (
            HttpRunner,
            [
                {
                    "header": "Content-Type: application/json",
                    "method": HttpMethod.GET,
                    "endpoint": "http://localhost:8080",
                },
                {
                    "header": "Content-Type: application/json",
                    "method": HttpMethod.POST,
                    "payload": '{"name": "Jack"}',
                    "endpoint": "http://localhost:8080",
                },
            ],
        ),
        TestMode.GRPC: (
            GrpcRunner,
            [
                {
                    "proto": "hello.proto",
                    "function": "Test",
                    "endpoint": "localhost:50051",
                    "payload": '{"name": "Jack"}',
                },
                {
                    "function": "Test",
                    "endpoint": "localhost:50051",
                    "payload": '{"name": "Worker"}',
                },
            ],
        ),
        TestMode.PYTEST: (
            PytestRunner,
            [
                {
                    "root_dir": "/test",
                    "test_args": ["test.py"],
                },
                {
                    "test_args": ["test.py"],
                },
            ],
        ),
        TestMode.DOCKER: (
            DockerRunner,
            [
                {
                    "cntr_name": "container_name",
                    "cmd": ["container", "echo", "test"],
                },
            ],
        ),
    }

    for mode, (runner_class, configs) in runners.items():
        for config in configs:
            runner = create_runner(mode, config)
            assert isinstance(runner, runner_class)

    # Test invalid mode
    with pytest.raises(ValueError):
        create_runner("invalid_mode", {})


@pytest.fixture
def shell_runner_data():
    """Create a sample shell runner configuration."""
    return {
        "cmd": ["echo", "test"],
    }


@pytest.fixture
def http_runner_data():
    """Create a sample HTTP runner configuration."""
    return {
        "method": "GET",
        "endpoint": "http://localhost:8080",
        "header": "",
        "payload": "",
    }


@pytest.fixture
def grpc_runner_data():
    """Create a sample gRPC runner configuration."""
    return {
        "function": "hello.Greeter/SayHello",
        "endpoint": "localhost:50051",
        "payload": '{"name": "World"}',
    }


@pytest.fixture
def pytest_runner_data():
    """Create a sample pytest runner configuration."""
    return {
        "root_dir": "./tests",
        "test_args": ["test_file.py"],
    }


@pytest.fixture
def docker_runner_data():
    """Create a sample docker runner configuration."""
    return {
        "cntr_name": "test_container",
        "cmd": ["echo", "test"],
    }


def test_shell_runner(shell_runner_data):
    """Test shell runner functionality."""
    runner = ShellRunner(**shell_runner_data)
    assert runner.cmd == ["echo", "test"]
    assert runner.get_command() == "echo test"


def test_http_runner(http_runner_data):
    """Test HTTP runner functionality."""
    runner = HttpRunner(**http_runner_data)
    assert runner.method == "GET"
    assert runner.endpoint == "http://localhost:8080"
    assert runner.header == ""
    assert runner.payload == ""
    assert runner.get_command() == "curl -X GET 'http://localhost:8080'"

    # Test with payload
    runner.payload = '{"data": "test"}'
    assert runner.get_command() == "curl -X GET 'http://localhost:8080'"

    # Test with header
    runner.header = "Content-Type: application/json"
    assert runner.get_command() == "curl -H 'Content-Type: application/json' -X GET 'http://localhost:8080'"


def test_grpc_runner(grpc_runner_data):
    """Test gRPC runner functionality."""
    runner = GrpcRunner(**grpc_runner_data)
    assert runner.function == "hello.Greeter/SayHello"
    assert runner.endpoint == "localhost:50051"
    assert runner.payload == '{"name": "World"}'
    assert runner.get_command() == 'grpcurl -d \'{"name": "World"}\' -plaintext localhost:50051 hello.Greeter/SayHello'


def test_pytest_runner(pytest_runner_data):
    """Test pytest runner functionality."""
    runner = PytestRunner(**pytest_runner_data)
    assert runner.root_dir == "./tests"
    assert runner.test_args == ["test_file.py"]
    assert runner.get_command() == "pytest --rootdir ./tests test_file.py"


def test_docker_runner(docker_runner_data):
    """Test docker runner functionality."""
    runner = DockerRunner(**docker_runner_data)
    assert runner.cntr_name == "test_container"
    assert runner.cmd == ["echo", "test"]
    assert runner.get_command() == "docker exec test_container echo test"


def test_runner_validation():
    """Test runner validation."""
    # Test shell runner validation
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation error for ShellRunner"):
        ShellRunner()

    # Test HTTP runner validation
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation errors for HttpRunner"):
        HttpRunner()
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation errors for HttpRunner"):
        HttpRunner(method="GET")

    # Test gRPC runner validation
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation errors for GrpcRunner"):
        GrpcRunner()
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation errors for GrpcRunner"):
        GrpcRunner(function="hello.Greeter/SayHello")

    # Test pytest runner validation
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation error for PytestRunner"):
        PytestRunner()
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation error for PytestRunner"):
        PytestRunner(root_dir="./tests")

    # Test docker runner validation
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation errors for DockerRunner"):
        DockerRunner()
    with pytest.raises(pydantic_core._pydantic_core.ValidationError, match="validation error for DockerRunner"):
        DockerRunner(cntr_name="test_container")
