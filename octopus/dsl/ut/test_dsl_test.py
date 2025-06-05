"""Unit tests for DslTest class."""

import sys

import pytest
from loguru import logger
from pydantic import ValidationError

from octopus.dsl.checker import Expect
from octopus.dsl.constants import HttpMethod, TestMode
from octopus.dsl.dsl_test import DslTest
from octopus.dsl.runner import (
    DockerRunner,
    GrpcRunner,
    HttpRunner,
    PytestRunner,
    ShellRunner,
)

# loguru config
logger.remove()  # remove default handler
logger.add(
    "test_dsl_test.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    rotation="1 MB",
)
logger.add(sys.stdout, level="INFO")


@pytest.fixture
def valid_shell_test_data():
    """Fixture providing valid shell test data."""
    return {
        "name": "test_shell",
        "desc": "test in shell cmd",
        "mode": TestMode.SHELL,
        "runner": {
            "cmd": ["echo", "'Hello, World!'"],
        },
        "expect": {
            "mode": TestMode.SHELL,
            "exit_code": 0,
            "stdout": "Hello, World!",
            "stderr": "",
        },
    }


@pytest.fixture
def valid_http_test_data():
    """Fixture providing valid HTTP test data."""
    return {
        "name": "test_http",
        "desc": "test via http client",
        "mode": TestMode.HTTP,
        "runner": {
            "header": "",
            "method": "POST",
            "payload": '{"greeting": "Hello, World!"}',
            "endpoint": "http://localhost:8080",
        },
        "expect": {
            "status_code": 201,
            "response": '{"data": "Hello, World!"}',
        },
    }


@pytest.fixture
def valid_pytest_test_data():
    """Fixture providing valid pytest test data."""
    return {
        "name": "test_pytest",
        "desc": "test run by pytest cli",
        "mode": TestMode.PYTEST,
        "runner": {
            "root_dir": "./octopus/dsl/ut",
            "test_args": ["octopus/dsl/ut/test_runner.py", "-v", "-s", "-k", "test_docker_runner_"],
        },
        "expect": {
            "exit_code": 0,
        },
    }


@pytest.fixture
def valid_docker_test_data():
    """Fixture providing valid docker test data."""
    return {
        "name": "test_docker",
        "desc": "test run in docker container",
        "mode": TestMode.DOCKER,
        "needs": ["test_container"],
        "runner": {
            "cntr_name": "test_container",
            "cmd": ["echo", "Hello, World!"],
        },
        "expect": {
            "exit_code": 0,
            "stdout": "Hello, World!",
            "stderr": "",
        },
    }


@pytest.fixture
def valid_grpc_test_data():
    """Fixture providing valid gRPC test data."""
    return {
        "name": "test_grpc",
        "desc": "test run by grpc client",
        "mode": TestMode.GRPC,
        "runner": {
            "proto": "hello.proto",
            "function": "hello.Greeter/SayHello",
            "endpoint": "localhost:50051",
            "payload": '{"name": "World"}',
        },
        "expect": {
            "exit_code": 201,
            "response": "Hello, World!",
        },
    }


def test_dsl_test_initialization(valid_shell_test_data):
    """Test DslTest initialization with valid shell test data."""
    test = DslTest(**valid_shell_test_data)
    assert test.name == valid_shell_test_data["name"]
    assert test.desc == valid_shell_test_data["desc"]
    assert test.mode == valid_shell_test_data["mode"]
    assert isinstance(test.runner, ShellRunner)
    assert test.expect.exit_code == valid_shell_test_data["expect"]["exit_code"]
    assert test.expect.stdout == valid_shell_test_data["expect"]["stdout"]
    assert test.expect.stderr == valid_shell_test_data["expect"]["stderr"]


def test_dsl_test_from_dict(valid_http_test_data):
    """Test DslTest.from_dict method with HTTP test data."""
    test = DslTest.from_dict(valid_http_test_data)
    assert test.name == valid_http_test_data["name"]
    assert test.mode == valid_http_test_data["mode"]
    assert isinstance(test.runner, HttpRunner)
    assert test.expect.status_code == valid_http_test_data["expect"]["status_code"]
    assert test.expect.response == valid_http_test_data["expect"]["response"]


def test_dsl_test_validation():
    """Test DslTest validation."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        DslTest()

    # Test missing required name
    with pytest.raises(ValidationError):
        DslTest(
            desc="test",
            mode=TestMode.HTTP,
            runner={
                "method": "GET",
                "endpoint": "http://localhost",
            },
            expect={"mode": TestMode.SHELL, "status_code": 200},
        )

    # Test missing required desc
    with pytest.raises(ValidationError):
        DslTest(
            name="test",
            mode=TestMode.HTTP,
            runner={
                "method": "GET",
                "endpoint": "http://localhost",
            },
            expect={"mode": TestMode.HTTP, "status_code": 200},
        )

    # Test missing required mode
    with pytest.raises(KeyError):
        DslTest(
            name="test",
            desc="test",
            runner={
                "method": "GET",
                "endpoint": "http://localhost",
            },
            expect={"status_code": 200},
        )

    # Test missing required runner
    with pytest.raises(ValidationError):
        DslTest(
            name="test",
            desc="test",
            mode=TestMode.HTTP,
            expect={"mode": TestMode.HTTP, "status_code": 200},
        )

    # Test missing required expect
    with pytest.raises(ValidationError):
        DslTest(
            name="test",
            desc="test",
            mode=TestMode.HTTP,
            runner={
                "method": "GET",
                "endpoint": "http://localhost",
            },
        )


def test_dsl_test_optional_fields():
    """Test DslTest optional fields: needs"""
    # Test with minimal required fields
    test = DslTest(
        name="test",
        desc="test",
        mode=TestMode.HTTP,
        runner={
            "header": "",
            "method": HttpMethod.GET,
            "endpoint": "http://localhost",
        },
        expect={"mode": TestMode.HTTP, "status_code": 200, "response": '{"data": "Hello, World!"}'},
    )
    assert test.needs == []

    # Test with empty needs
    test = DslTest(
        name="test",
        desc="test",
        mode=TestMode.HTTP,
        needs=[],
        runner={
            "header": "",
            "method": HttpMethod.GET,
            "endpoint": "http://localhost",
        },
        expect={"mode": TestMode.HTTP, "status_code": 200, "response": '{"data": "Hello, World!"}'},
    )
    assert test.needs == []


def test_dsl_test_runner_type_validation():
    """Test runner type validation for different modes."""
    logger.debug("Starting runner type validation test")
    test_cases = [
        (
            TestMode.SHELL,
            {
                "cmd": ["echo", "test"],
            },
        ),
        (
            TestMode.HTTP,
            {
                "header": "",
                "method": HttpMethod.GET,
                "endpoint": "http://localhost",
            },
        ),
        (
            TestMode.GRPC,
            {
                "function": "hello.Greeter/SayHello",
                "endpoint": "localhost:50051",
                "payload": '{"name": "World"}',
            },
        ),
        (
            TestMode.PYTEST,
            {
                "root_dir": "./octopus/dsl/ut",
                "test_args": ["test_runner.py"],
            },
        ),
        (
            TestMode.DOCKER,
            {
                "cntr_name": "test_container",
                "cmd": ["echo", "test"],
            },
        ),
    ]

    default_expect = {
        "exit_code": 0,
        "stdout": "",
        "stderr": "",
        "status_code": 200,
        "response": "",
    }

    for mode, runner_config in test_cases:
        logger.info(f"Testing mode: {mode}")
        logger.debug(f"Runner config: {runner_config}")

        default_expect["mode"] = mode
        logger.debug(f"Expect config: {default_expect}")

        test = DslTest(name="test", desc="test", mode=mode, runner=runner_config, expect=default_expect)

        logger.debug(f"Successfully created DslTest for mode {mode}")
        expected_runner_type = {
            TestMode.SHELL: ShellRunner,
            TestMode.HTTP: HttpRunner,
            TestMode.GRPC: GrpcRunner,
            TestMode.PYTEST: PytestRunner,
            TestMode.DOCKER: DockerRunner,
        }[mode]

        logger.debug(f"Expected runner type: {expected_runner_type.__name__}")
        logger.debug(f"Actual runner type: {type(test.runner).__name__}")

        assert isinstance(test.runner, expected_runner_type)
        logger.debug(f"Runner type validation passed for mode {mode}")


def test_dsl_test_expect_validation():
    """Test expect validation and initialization."""
    # Test expect initialization with mode
    test = DslTest(
        name="test",
        desc="test",
        mode=TestMode.HTTP,
        runner={
            "header": "",
            "method": "GET",
            "endpoint": "http://localhost",
        },
        expect={"mode": TestMode.HTTP, "status_code": 200, "response": '{"data": "Hello, World!"}'},
    )
    assert test.expect.mode == TestMode.HTTP

    # Test expect update with mode
    test.mode = TestMode.GRPC
    assert test.expect.mode == TestMode.GRPC


def test_dsl_test_extra_fields():
    """Test DslTest extra fields validation."""
    # Test with extra fields
    with pytest.raises(ValidationError):
        DslTest(
            name="test",
            desc="test",
            mode=TestMode.HTTP,
            runner={
                "method": "GET",
                "endpoint": "http://localhost",
            },
            expect={"mode": TestMode.HTTP, "status_code": 200},
            extra_field="value",
        )


def test_dsl_test_to_dict():
    """Test to_dict method of DslTest class."""
    # Create a test instance
    test = DslTest(
        name="test_shell",
        desc="test in shell cmd",
        mode=TestMode.SHELL,
        runner={
            "cmd": ["echo", "'Hello, World!'"],
        },
        expect={
            "mode": TestMode.SHELL,
            "exit_code": 0,
            "stdout": "Hello, World!",
            "stderr": "",
        },
    )

    # Convert to dict
    test_dict = test.to_dict()

    # Verify that the result is a dictionary
    assert isinstance(test_dict, dict)

    # Verify that all fields are present and have correct values
    assert test_dict["name"] == "test_shell"
    assert test_dict["desc"] == "test in shell cmd"
    assert test_dict["mode"] == TestMode.SHELL
    assert test_dict["runner"] == {
        "cmd": ["echo", "'Hello, World!'"],
    }
    assert test_dict["expect"] == {
        "mode": TestMode.SHELL,
        "exit_code": 0,
        "stdout": "Hello, World!",
        "stderr": "",
    }

    # Test with modified values
    test.name = "new_name"
    test.desc = "new_desc"
    test.mode = TestMode.HTTP
    test.runner = HttpRunner(
        header="Content-Type: application/json",
        method="POST",
        payload='{"greeting": "Hello, World!"}',
        endpoint="http://localhost:8080",
    )
    test.expect = Expect(
        mode=TestMode.HTTP,
        status_code=201,
        response='{"data": "Hello, World!"}',
    )

    # Convert to dict again
    test_dict = test.to_dict()

    # Verify that the updated values are correctly represented in the dictionary
    assert test_dict["name"] == "new_name"
    assert test_dict["desc"] == "new_desc"
    assert test_dict["mode"] == TestMode.HTTP
    assert test_dict["runner"] == {
        "header": "Content-Type: application/json",
        "method": "POST",
        "payload": '{"greeting": "Hello, World!"}',
        "endpoint": "http://localhost:8080",
    }
    assert test_dict["expect"] == {
        "mode": TestMode.HTTP,
        "status_code": 201,
        "response": '{"data": "Hello, World!"}',
    }
