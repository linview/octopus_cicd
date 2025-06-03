"""Test cases for DslConfig class."""

from pathlib import Path

import pytest

from octopus.dsl.dsl_config import DslConfig


@pytest.fixture
def sample_config_path() -> Path:
    """Get the path to the sample config file."""
    return Path(__file__).parent.parent / "test_data" / "config_sample_v0.1.0.yaml"


@pytest.fixture
def valid_config() -> dict:
    """Get a valid config dictionary."""
    return {
        "version": "0.1.0",
        "name": "test_config",
        "desc": "Test configuration",
        "inputs": [
            {"service_name": "service1"},
            {"$cntr_name": "service_container"},
            {"$HOST_HTTP_PORT": "8080"},
        ],
        "services": {
            "service1": {
                "desc": "Test service",
                "image": "nginx:latest",
                "args": ["--name", "${$cntr_name}"],
                "ports": ["${$HOST_HTTP_PORT}:80"],
                "envs": ["ENV=test"],
                "vols": ["~/data:/data"],
            }
        },
        "tests": {
            "test_shell": {
                "desc": "Test shell command",
                "mode": "shell",
                "runner": {
                    "cmd": ["echo", "Hello, World!"],
                },
                "expect": {
                    "exit_code": 0,
                    "stdout": "Hello, World!",
                    "stderr": "",
                },
            }
        },
    }


def test_load_valid_config(sample_config_path: Path):
    """Test loading a valid config file."""
    config = DslConfig.from_yaml(sample_config_path)
    assert config.version == "0.1.0"
    assert config.name == "config_sample"
    assert config.desc == "Sample config DSL for v0.1.0"
    assert len(config.services) > 0
    assert len(config.tests) > 0


def test_load_invalid_config(tmp_path: Path):
    """Test loading an invalid config file."""
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text("invalid: yaml: content: [")

    with pytest.raises(ValueError, match="Failed to load YAML file"):
        DslConfig.from_yaml(invalid_config)


def test_missing_required_fields(tmp_path: Path):
    """Test config with missing required fields."""
    config_path = tmp_path / "missing_fields.yaml"
    config_path.write_text("""
    version: 0.1.0
    # missing name and desc
    services: {}
    tests: {}
    """)

    with pytest.raises(ValueError, match="Missing required fields"):
        DslConfig.from_yaml(config_path)


def test_invalid_service_config(valid_config: dict):
    """Test config with invalid service configuration."""
    valid_config["services"]["invalid_service"] = {
        "desc": "Invalid service",
        # missing required image field
    }

    with pytest.raises(ValueError, match="Invalid service configuration"):
        DslConfig(**valid_config)


def test_invalid_test_config(valid_config: dict):
    """Test config with invalid test configuration."""
    valid_config["tests"]["invalid_test"] = {
        "desc": "Invalid test",
        # missing required mode and runner fields
    }

    with pytest.raises(ValueError, match="Invalid test configuration"):
        DslConfig(**valid_config)


def test_variable_replacement(valid_config: dict):
    """Test variable replacement in config."""
    config = DslConfig(**valid_config)
    service = config.services["service1"]

    # Check if variables are replaced in service configuration
    assert "--name" in service.args
    assert "service_container" in service.args
    assert "8080:80" in service.ports


def test_test_mode_validation(valid_config: dict):
    """Test test mode validation."""
    valid_config["tests"]["invalid_mode"] = {
        "desc": "Invalid mode test",
        "mode": "invalid_mode",
        "runner": {
            "cmd": ["echo", "test"],
        },
        "expect": {
            "exit_code": 0,
        },
    }

    with pytest.raises(ValueError, match="Invalid test mode"):
        DslConfig(**valid_config)


def test_service_dependencies(valid_config: dict):
    """Test service dependency validation."""
    valid_config["services"]["service2"] = {
        "desc": "Dependent service",
        "image": "nginx:latest",
        "depends_on": ["non_existent_service"],
    }

    with pytest.raises(ValueError, match="Invalid service dependency"):
        DslConfig(**valid_config)


def test_test_dependencies(valid_config: dict):
    """Test test dependency validation."""
    valid_config["tests"]["dependent_test"] = {
        "desc": "Dependent test",
        "mode": "shell",
        "needs": ["non_existent_test"],
        "runner": {
            "cmd": ["echo", "test"],
        },
        "expect": {
            "exit_code": 0,
        },
    }

    with pytest.raises(ValueError, match="Invalid test dependency"):
        DslConfig(**valid_config)
