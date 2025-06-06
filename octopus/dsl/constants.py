"""
Constants used in the DSL configuration.
"""

from enum import Enum


class TestMode(str, Enum):
    """Test execution modes."""

    SHELL = "shell"
    HTTP = "http"
    GRPC = "grpc"
    PYTEST = "pytest"
    DOCKER = "docker"
    NONE = "none"

    def __str__(self) -> str:
        """Return the string representation of the test mode."""
        return self.value

    def __repr__(self) -> str:
        """Return the string representation of the test mode."""
        return self.value


class HttpMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class Keywords:
    """Reserved keywords in the DSL."""

    # Common keywords
    DESC = "desc"
    NAME = "name"

    # Config keywords
    VERSION = "version"
    INPUTS = "inputs"
    SERVICES = "services"
    TESTS = "tests"

    # Service keywords
    IMAGE = "image"
    ARGS = "args"
    ENVS = "envs"
    PORTS = "ports"
    VOLS = "vols"

    # Graph keywords
    NEXT = "next"
    DEPENDS_ON = "depends_on"
    TRIGGER = "trigger"
    NEEDS = "needs"

    # Test keywords
    MODE = "mode"
    RUNNER = "runner"
    EXPECT = "expect"

    # Runner keywords
    CMD = "cmd"
    HEADER = "header"
    METHOD = "method"
    PAYLOAD = "payload"
    ENDPOINT = "endpoint"
    ROOT_DIR = "root_dir"
    TEST_ARGS = "test_args"
    PROTO = "proto"
    FUNCTION = "function"

    # Checker(Expect) keywords
    EXIT_CODE = "exit_code"
    STDOUT = "stdout"
    STDERR = "stderr"
    STATUS_CODE = "status_code"
    RESPONSE = "response"


# Required fields for each test mode
TEST_RUNNER_FIELDS = {
    TestMode.SHELL: ["cmd"],
    TestMode.HTTP: ["header", "method", "payload", "endpoint"],
    TestMode.GRPC: ["function", "endpoint", "payload"],
    TestMode.PYTEST: ["root_dir", "test_args"],
    TestMode.DOCKER: ["cmd"],
}

# Expected fields for each test mode
TEST_EXPECT_FIELDS = {
    TestMode.SHELL: ["exit_code", "stdout", "stderr"],
    TestMode.HTTP: ["status_code", "response"],
    TestMode.GRPC: ["exit_code", "response"],
    TestMode.PYTEST: ["exit_code"],
    TestMode.DOCKER: ["exit_code", "stdout", "stderr"],
    #    TestMode.NONE: [],     # will fail if test mode is not specified
}

SUPPORTED_VERSION = ["0.1.0"]
