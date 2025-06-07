"""
Constants used in the DSL configuration.
"""

import inspect
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

    __CURRENT_VERSION = "0.1.0"

    # Common keywords
    KW_DESC = "desc"
    KW_NAME = "name"

    # Config keywords
    KW_VERSION = "version"
    KW_INPUTS = "inputs"
    KW_SERVICES = "services"
    KW_TESTS = "tests"

    # Service keywords
    KW_IMAGE = "image"
    KW_ARGS = "args"
    KW_ENVS = "envs"
    KW_PORTS = "ports"
    KW_VOLS = "vols"

    # Graph keywords
    KW_NEXT = "next"
    KW_DEPENDS_ON = "depends_on"
    KW_TRIGGER = "trigger"
    KW_NEEDS = "needs"

    # Test keywords
    KW_MODE = "mode"
    KW_RUNNER = "runner"
    KW_EXPECT = "expect"

    # Runner keywords
    KW_CMD = "cmd"
    KW_HEADER = "header"
    KW_METHOD = "method"
    KW_PAYLOAD = "payload"
    KW_ENDPOINT = "endpoint"
    KW_ROOT_DIR = "root_dir"
    KW_TEST_ARGS = "test_args"
    KW_PROTO = "proto"
    KW_FUNCTION = "function"
    KW_CNTR_NAME = "cntr_name"

    # Checker(Expect) keywords
    KW_EXIT_CODE = "exit_code"
    KW_STDOUT = "stdout"
    KW_STDERR = "stderr"
    KW_STATUS_CODE = "status_code"
    KW_RESPONSE = "response"

    @classmethod
    def is_support_version(cls, version: str) -> bool:
        """Check if the version is valid."""
        return version in SUPPORTED_VERSION

    @classmethod
    def is_valid_keyword(cls, key: str) -> bool:
        """Check if the keyword is valid."""

        def _get_kw_collection(cls):
            return [
                v
                for k, v in cls.__dict__.items()
                if not (
                    k.startswith("_")
                    or inspect.ismethod(v)
                    or inspect.isfunction(v)
                    or isinstance(v, classmethod)
                    or k in ["model_config", "model_fields"]
                )
            ]

        return key in _get_kw_collection(cls)


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
