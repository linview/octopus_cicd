"""Unit tests for runner module."""

import sys

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
    assert runner.get_config() == config


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
