"""Test cases for DslConfig class."""

from pathlib import Path

import pytest

from octopus.dsl.dsl_config import DslConfig


@pytest.fixture
def sample_config_path() -> Path:
    """Fixture for sample config file path."""
    return Path(__file__).parent.parent / "test_data" / "config_sample_v0.1.0.yaml"


@pytest.fixture
def valid_config() -> dict:
    """Fixture for valid config data."""
    return {
        "version": "0.1.0",
        "name": "test_config",
        "desc": "Test configuration",
        "inputs": [
            {"service_name": "service1"},
            {"$cntr_name": "service_container"},
            {"$HOST_HTTP_PORT": "8080"},
            {"$ENV_LOG_SETTING": "NIM_LOG=debug"},
        ],
        "services": [
            {
                "name": "service_simple",
                "desc": "simple service verify container start",
                "image": "nginx:latest",
                "args": [
                    "--ulimit nofile=1024:1024",
                    "--device all",
                    "--privileged",
                    "-m 512m",
                ],
                "ports": ["80:80"],
                "envs": ["DEBUG_LOG=debug"],
                "vols": ["~/data:/data"],
            },
            {
                "name": "service1",
                "desc": "service verify lazy-var in service name",
                "depends_on": ["service2"],
                "image": "nginx:latest",
                "args": ["--name service1"],
                "ports": ["8080:80"],
                "envs": ["ENV=test", "NIM_LOG=debug"],
                "vols": ["~/data:/data"],
            },
        ],
        "tests": [
            {
                "name": "test_shell",
                "desc": "test in shell cmd",
                "mode": "shell",
                "runner": {
                    "cmd": ["echo", "'Hello, World!'"],
                },
                "expect": {
                    "exit_code": 0,
                    "stdout": "Hello, World!",
                    "stderr": "",
                },
            },
            {
                "name": "test_http",
                "desc": "test via http client",
                "mode": "http",
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
            },
        ],
    }


@pytest.mark.smoke
def test_load_valid_config_file(sample_config_path: Path):
    """Test loading a valid config file."""
    config = DslConfig.from_yaml_file(sample_config_path)
    assert config.version == "0.1.0"
    assert config.name == "config_sample"
    assert len(config.inputs) > 0
    assert len(config.services) > 0
    assert len(config.tests) > 0


def test_load_invalid_config_file(tmp_path: Path):
    """Test loading an invalid config file."""
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("invalid: yaml: content: [")
    config = DslConfig.from_yaml_file(invalid_yaml)
    assert config is None


def test_load_nonexistent_config_file(tmp_path: Path):
    """Test loading a non-existent config file."""
    nonexistent_yaml = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        DslConfig.from_yaml_file(nonexistent_yaml)


@pytest.mark.TODO("missing required 'inputs' shall be handled by pydantic")
@pytest.mark.xfail(reason="missing required 'inputs' shall be handled by pydantic")
def test_missing_required_fields(tmp_path: Path):
    """Test config with missing required fields."""
    invalid_config = {
        "version": "0.1.0",
        "name": "test_config",
        "desc": "Test configuration",
        "services": [],
        "tests": [],
    }
    # DslConfig.from_dict(invalid_config)
    with pytest.raises(ValueError, match="Missing required fields"):
        DslConfig.from_dict(invalid_config)


def test_invalid_service_config(valid_config: dict):
    """Test config with invalid service name."""
    valid_config["services"].append(
        {
            "desc": "Invalid service",
            "image": "nginx:latest",
        }
    )
    with pytest.raises(ValueError, match="Service name is required"):
        DslConfig.from_dict(valid_config)


def test_invalid_test_config(valid_config: dict):
    """Test config with invalid test configuration."""
    valid_config["tests"].append(
        {
            "desc": "Invalid test",
            "mode": "shell",
        }
    )
    with pytest.raises(ValueError, match="Test name is required"):
        DslConfig.from_dict(valid_config)


@pytest.mark.TODO("need to implement lazy-var in service name")
def test_variable_replacement(valid_config: dict):
    """Test variable replacement in config."""
    config = DslConfig.from_dict(valid_config)
    service = config.services[1]  # service1
    assert service.name == "service1"
    assert "8080:80" in service.ports
    assert "NIM_LOG=debug" in service.envs


def test_test_mode_validation(valid_config: dict):
    """Test test mode validation."""
    valid_config["tests"].append(
        {
            "name": "invalid_mode",
            "desc": "Invalid mode test",
            "mode": "invalid_mode",
            "runner": {
                "cmd": ["echo", "test"],
            },
            "expect": {
                "exit_code": 0,
                "stdout": "test",
            },
        }
    )
    with pytest.raises(ValueError, match="'invalid_mode' is not a valid TestMode"):
        DslConfig.from_dict(valid_config)


@pytest.mark.TODO(reason="kw 'depends_on' is not implemented")
@pytest.mark.xfail(reason="kw 'depends_on' is not implemented")
def test_service_dependencies(valid_config: dict):
    """Test service dependency validation."""
    valid_config["services"].append(
        {
            "name": "service3",
            "desc": "Service with invalid dependency",
            "depends_on": ["non_existent_service"],
            "image": "nginx:latest",
        }
    )
    # DslConfig.from_dict(valid_config)
    # TODO: shall xfail when 'depends_on' is implemented
    with pytest.raises(ValueError, match="Invalid service dependency"):
        DslConfig.from_dict(valid_config)


@pytest.mark.TODO("need to implement 'needs' kw")
@pytest.mark.xfail(reason="kw 'needs' is not implemented")
def test_test_dependencies(valid_config: dict):
    """Test test dependency validation."""
    valid_config["tests"].append(
        {
            "name": "dependent_test",
            "desc": "Dependent test",
            "mode": "shell",
            "needs": ["non_existent_test"],  # TODO: shall xfail when 'needs' is implemented
            "runner": {
                "cmd": ["echo", "test"],
            },
            "expect": {
                "exit_code": 0,
                "stdout": "test",
            },
        }
    )
    with pytest.raises(ValueError, match="Invalid test dependency"):
        DslConfig.from_dict(valid_config)
