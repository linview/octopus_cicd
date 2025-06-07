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
                "next": ["service1"],
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
                "next": ["service2"],
                "depends_on": ["service2"],
                "image": "nginx:latest",
                "args": ["--name service1"],
                "ports": ["8080:80"],
                "envs": ["ENV=test", "NIM_LOG=debug"],
                "vols": ["~/data:/data"],
            },
            {
                "name": "service2",
                "desc": "service with empty next",
                "next": [],
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
    with pytest.raises(ValueError, match="semantic check failed"):
        DslConfig.from_dict(valid_config)


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
                "stderr": "",
            },
        }
    )
    with pytest.raises(ValueError, match="semantic check failed"):
        DslConfig.from_dict(valid_config)


def test_duplicate_service_name(valid_config: dict):
    """Test duplicate service name detection."""
    valid_config["services"].append(
        {
            "name": "service_simple",  # duplicated service name
            "desc": "duplicate service",
            "image": "nginx:latest",
        }
    )
    with pytest.raises(ValueError, match="Duplicate service name found: service_simple"):
        DslConfig.from_dict(valid_config)


def test_duplicate_test_name(valid_config: dict):
    """Test duplicate test name detection."""
    valid_config["tests"].append(
        {
            "name": "test_shell",  # duplicated test name
            "desc": "duplicate test",
            "mode": "shell",
            "runner": {
                "cmd": ["echo", "test"],
            },
            "expect": {
                "exit_code": 0,
                "stdout": "test",
                "stderr": "",
            },
        }
    )
    with pytest.raises(ValueError, match="Duplicate test name found: test_shell"):
        DslConfig.from_dict(valid_config)


def test_unsupported_version(valid_config: dict):
    """Test unsupported version validation."""
    valid_config["version"] = "999.999.999"
    with pytest.raises(ValueError, match="Unsupported version: 999.999.999"):
        DslConfig.from_dict(valid_config)


def test_service_depends_validation(valid_config: dict):
    """Test service dependency validation."""
    # depends on non-existent service
    valid_config["services"].append(
        {
            "name": "service3",
            "desc": "Service with invalid dependency",
            "depends_on": ["non_existent_service"],
            "image": "nginx:latest",
        }
    )
    with pytest.raises(ValueError, match="semantic check"):
        config = DslConfig.from_dict(valid_config)
        assert not config.verify()


def test_test_needs_validation(valid_config: dict):
    """Test test dependency validation."""
    # needs non-existent service
    valid_config["tests"].append(
        {
            "name": "test_docker",
            "desc": "Test with invalid dependency",
            "mode": "docker",
            "needs": ["non_existent_service"],
            "runner": {
                "cntr_name": "test_container",
                "cmd": ["echo", "test"],
            },
            "expect": {
                "exit_code": 0,
                "stdout": "test",
                "stderr": "",
            },
        }
    )
    with pytest.raises(ValueError, match="semantic check"):
        config = DslConfig.from_dict(valid_config)
        assert not config.verify()


def test_service_trigger_validation(valid_config: dict):
    """Test service trigger validation."""
    # trigger non-existent test
    valid_config["services"].append(
        {
            "name": "service4",
            "desc": "Service with invalid trigger",
            "trigger": ["non_existent_test"],
            "image": "nginx:latest",
        }
    )
    with pytest.raises(ValueError, match="semantic check"):
        config = DslConfig.from_dict(valid_config)
        assert not config.verify()


def test_get_service_by_name(valid_config: dict):
    """Test getting service by name."""
    config = DslConfig.from_dict(valid_config)
    service = config.get_service_by_name("service_simple")
    assert service is not None
    assert service.name == "service_simple"
    assert service.image == "nginx:latest"


def test_get_test_by_name(valid_config: dict):
    """Test getting test by name."""
    config = DslConfig.from_dict(valid_config)
    test = config.get_test_by_name("test_shell")
    assert test is not None
    assert test.name == "test_shell"
    assert test.mode == "shell"


def test_get_nonexistent_service(valid_config: dict):
    """Test getting non-existent service."""
    config = DslConfig.from_dict(valid_config)
    service = config.get_service_by_name("non_existent_service")
    assert service is None


def test_get_nonexistent_test(valid_config: dict):
    """Test getting non-existent test."""
    config = DslConfig.from_dict(valid_config)
    test = config.get_test_by_name("non_existent_test")
    assert test is None


def test_service_next_validation(valid_config: dict):
    """Test service next validation."""
    # next to invalida service will fail semantic check
    valid_config["services"].append(
        {
            "name": "service3",
            "desc": "Service with invalid next",
            "next": ["non_existent_service"],
            "image": "nginx:latest",
        }
    )
    with pytest.raises(ValueError, match="semantic check"):
        config = DslConfig.from_dict(valid_config)
        assert not config.verify()


def test_service_next_validation_empty_list(valid_config: dict):
    """Test service next validation with empty list."""
    # next is empty list, no subsequent services to deploy
    valid_config["services"].append(
        {
            "name": "service3",
            "desc": "Service with empty next",
            "next": [],
            "image": "nginx:latest",
        }
    )
    config = DslConfig.from_dict(valid_config)
    assert config.verify()


def test_service_next_validation_valid_service(valid_config: dict):
    """Test service next validation with valid service."""
    # next to valid service
    valid_config["services"].append(
        {
            "name": "service3",
            "desc": "Service with valid next",
            "next": ["service_simple"],  # next to valid service
            "image": "nginx:latest",
        }
    )
    config = DslConfig.from_dict(valid_config)
    assert config.verify()


def test_service_next_validation_cycle(valid_config: dict):
    """Test service next validation with cycle."""
    # create cycle dependency, pass semantic check, will fail at DAG validation
    valid_config["services"].append(
        {
            "name": "service3",
            "desc": "Service with cycle",
            "next": ["service4"],
            "image": "nginx:latest",
        }
    )
    valid_config["services"].append(
        {
            "name": "service4",
            "desc": "Service with cycle",
            "next": ["service3"],
            "image": "nginx:latest",
        }
    )
    config = DslConfig.from_dict(valid_config)
    # note: here we only verify service existence, not cycle dependency
    assert config.verify()
