"""Unit tests for checker module."""

from typing import Any

import pytest

from octopus.dsl.checker import Expect
from octopus.dsl.constants import TestMode


@pytest.fixture
def expect_config() -> dict[str, Any]:
    """Fixture for expect configuration."""
    return {
        "mode": TestMode.SHELL,
        "exit_code": 0,
        "stdout": "hello world",
        "stderr": "",
    }


@pytest.fixture
def expect(expect_config: dict[str, Any]) -> Expect:
    """Fixture for expect instance."""
    return Expect(**expect_config)


def test_expect_init(expect: Expect):
    """Test Expect initialization."""
    assert expect.mode == TestMode.SHELL
    assert expect.exit_code == 0
    assert expect.stdout == "hello world"
    assert expect.stderr == ""


def test_expect_validate_fields():
    """Test Expect field validation."""
    # Test with missing required fields
    with pytest.raises(ValueError):
        Expect(mode=TestMode.SHELL)

    # Test with all required fields
    expect = Expect(
        mode=TestMode.SHELL,
        exit_code=0,
        stdout="test",
        stderr="",
    )
    assert expect.mode == TestMode.SHELL
    assert expect.exit_code == 0
    assert expect.stdout == "test"
    assert expect.stderr == ""


def test_expect_http_mode():
    """Test Expect with HTTP mode."""
    expect = Expect(
        mode=TestMode.HTTP,
        status_code=200,
        response="OK",
    )
    assert expect.mode == TestMode.HTTP
    assert expect.status_code == 200
    assert expect.response == "OK"


def test_expect_grpc_mode():
    """Test Expect with gRPC mode."""
    expect = Expect(
        mode=TestMode.GRPC,
        exit_code=0,
        response="OK",
    )
    assert expect.mode == TestMode.GRPC
    assert expect.exit_code == 0
    assert expect.response == "OK"


def test_expect_pytest_mode():
    """Test Expect with Pytest mode."""
    expect = Expect(
        mode=TestMode.PYTEST,
        exit_code=0,
        stdout="test passed",
        stderr="",
    )
    assert expect.mode == TestMode.PYTEST
    assert expect.exit_code == 0
    assert expect.stdout == "test passed"
    assert expect.stderr == ""


def test_expect_docker_mode():
    """Test Expect with Docker mode."""
    expect = Expect(
        mode=TestMode.DOCKER,
        exit_code=0,
        stdout="container output",
        stderr="",
    )
    assert expect.mode == TestMode.DOCKER
    assert expect.exit_code == 0
    assert expect.stdout == "container output"
    assert expect.stderr == ""
