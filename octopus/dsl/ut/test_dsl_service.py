"""Unit tests for DslService class."""

import copy

import pytest
from pydantic import ValidationError

from octopus.dsl.dsl_service import DslService


@pytest.fixture
def valid_service_data():
    """Fixture providing valid service data."""
    return {
        "name": "test_service",
        "desc": "Test service description",
        "image": "nginx:latest",
        "args": ["--port", "8080"],
        "envs": ["ENV1=value1", "ENV2=value2"],
        "ports": ["8080:8080", "8081:8081"],
        "vols": ["/host/path:/container/path"],
        "depends_on": ["service_a", "service_b"],
        "trigger": ["test_a", "test_b"],
        "next": ["service_d"],
    }


@pytest.fixture
def sample_service_data():
    """Create a sample service configuration for testing."""
    return {
        "name": "service1",
        "desc": "Test service",
        "image": "nginx:latest",
        "args": ["--name", "test_container"],
        "envs": ["ENV=test"],
        "ports": ["80:80"],
        "vols": ["~/data:/data"],
        "next": ["service2"],
        "depends_on": ["service0"],
        "trigger": ["test1"],
    }


def test_dsl_service_initialization(valid_service_data):
    """Test DslService initialization with valid data."""
    service = DslService(**valid_service_data)
    assert service.name == valid_service_data["name"]
    assert service.desc == valid_service_data["desc"]
    assert service.image == valid_service_data["image"]
    assert service.args == valid_service_data["args"]
    assert service.envs == valid_service_data["envs"]
    assert service.ports == valid_service_data["ports"]
    assert service.vols == valid_service_data["vols"]
    assert service.depends_on == valid_service_data["depends_on"]
    assert service.trigger == valid_service_data["trigger"]


def test_dsl_service_from_dict(valid_service_data):
    """Test DslService.from_dict method."""
    service = DslService.from_dict(valid_service_data)
    assert service.name == valid_service_data["name"]
    assert service.image == valid_service_data["image"]
    assert service.depends_on == valid_service_data["depends_on"]


def test_dsl_service_validation():
    """Test DslService validation."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        DslService()

    # Test missing required name
    with pytest.raises(ValidationError):
        DslService(
            desc="test",
            image="nginx:latest",
        )

    # Test missing required desc
    with pytest.raises(ValidationError):
        DslService(
            name="test",
            image="nginx:latest",
        )

    # Test missing required image
    with pytest.raises(ValidationError):
        DslService(
            name="test",
            desc="test",
        )


def test_dsl_service_optional_fields():
    """Test DslService optional fields."""
    # Test with minimal required fields
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
    )
    assert service.args == []
    assert service.envs == []
    assert service.ports == []
    assert service.vols == []
    assert service.depends_on == []
    assert service.trigger == []

    # Test with empty optional fields
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
        args=[],
        envs=[],
        ports=[],
        vols=[],
        depends_on=[],
        trigger=[],
    )
    assert service.args == []
    assert service.envs == []
    assert service.ports == []
    assert service.vols == []
    assert service.depends_on == []
    assert service.trigger == []


def test_dsl_service_extra_fields():
    """Test DslService extra fields validation."""
    # Test with extra fields
    with pytest.raises(ValidationError):
        DslService(
            name="test",
            desc="test",
            image="nginx:latest",
            extra_field="value",
        )


def test_dsl_service_to_dict_with_all_fields(valid_service_data):
    """Test DslService.to_dict() with all fields set."""
    service = DslService(**valid_service_data)
    result = service.to_dict()

    # Verify all fields are correctly included in the result
    assert result == valid_service_data


def test_dsl_service_to_dict_with_empty_lists():
    """Test DslService.to_dict() with empty lists."""
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
        args=[],
        envs=[],
        ports=[],
        vols=[],
        depends_on=[],
        trigger=[],
        next=[],
    )
    result = service.to_dict()

    # Verify empty list fields are included in the result
    assert result == {
        "name": "test",
        "desc": "test",
        "image": "nginx:latest",
        "args": [],
        "envs": [],
        "ports": [],
        "vols": [],
        "depends_on": [],
        "trigger": [],
        "next": [],
    }


def test_dsl_service_to_dict_with_none_values():
    """Test DslService.to_dict() with None values."""
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
        args=None,
        envs=None,
        ports=None,
        vols=None,
        depends_on=None,
        trigger=None,
        next=[],
    )
    result = service.to_dict()

    # Verify fields with None values are excluded from the result
    assert result == {
        "name": "test",
        "desc": "test",
        "image": "nginx:latest",
        "next": [],
    }


def test_dsl_service_to_dict_with_mixed_values():
    """Test DslService.to_dict() with mixed values."""
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
        args=["--port", "8080"],
        envs=None,
        ports=["8080:8080"],
        vols=[],
        depends_on=None,
        trigger=["test_a"],
        next=["service_d"],
    )
    result = service.to_dict()

    # Verify mixed value handling (some fields have values, some are None, some are empty lists)
    assert result == {
        "name": "test",
        "desc": "test",
        "image": "nginx:latest",
        "args": ["--port", "8080"],
        "ports": ["8080:8080"],
        "vols": [],
        "trigger": ["test_a"],
        "next": ["service_d"],
    }


def test_dsl_service_next_empty_list():
    """Test DslService with empty next list (no subsequent services)."""
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
        next=[],  # no subsequent services to deploy
    )
    assert service.next == []
    assert service.to_dict()["next"] == []


def test_dsl_service_next_invalid_service():
    """Test DslService with invalid service in next list."""
    # invalid service name
    service = DslService(
        name="test",
        desc="test",
        image="nginx:latest",
        next=["non_existent_service"],  # invalid service name
    )
    assert service.next == ["non_existent_service"]
    assert service.to_dict()["next"] == ["non_existent_service"]


def test_dsl_service_variable_evaluation(sample_service_data):
    """Test variable evaluation in service configuration."""
    # Add variables to service data
    sample_service_data["name"] = "${service_name}"
    sample_service_data["args"] = ["--name", "${container_name}"]
    sample_service_data["envs"] = ["ENV=${env_value}"]

    service = DslService.from_dict(sample_service_data)

    # Evaluate with variables
    variables = {
        "service_name": "new_service",
        "container_name": "new_container",
        "env_value": "prod",
    }
    service.evaluate(variables)

    # Check variable replacement
    assert service.name == "new_service"
    assert service.args == ["--name", "new_container"]
    assert service.envs == ["ENV=prod"]


def test_dsl_service_idempotent_evaluation(sample_service_data):
    """Test that multiple evaluations produce the same result."""
    service = DslService.from_dict(sample_service_data)

    # First evaluation
    variables = {"service_name": "service1"}
    service.evaluate(variables)
    first_result = copy.deepcopy(service.model_dump())

    # Second evaluation with different variables
    variables = {"service_name": "service2"}
    service.evaluate(variables)
    second_result = service.model_dump()
    print(first_result)
    print(second_result)

    # Third evaluation with original variables
    variables = {"service_name": "service1"}
    service.evaluate(variables)
    third_result = service.model_dump()

    # First and third results should be identical
    assert first_result == third_result


def test_dsl_service_get_command(sample_service_data):
    """Test getting service command."""
    service = DslService.from_dict(sample_service_data)
    expected_cmd = (
        "docker run  --name service1 --name test_container -e ENV=test -p 80:80 -v ~/data:/data  nginx:latest"
    )
    assert service.get_command() == expected_cmd


def test_dsl_service_get_depends_on(sample_service_data):
    """Test getting service dependencies."""
    service = DslService.from_dict(sample_service_data)
    assert service.get_depends_on() == ["service0"]

    # Test with empty depends_on
    service.depends_on = None
    assert service.get_depends_on() == []


def test_dsl_service_get_trigger(sample_service_data):
    """Test getting service triggers."""
    service = DslService.from_dict(sample_service_data)
    assert service.get_trigger() == ["test1"]

    # Test with empty trigger
    service.trigger = None
    assert service.get_trigger() == []


def test_dsl_service_get_next(sample_service_data):
    """Test getting service next."""
    service = DslService.from_dict(sample_service_data)
    assert service.get_next() == ["service2"]

    # Test with empty next
    service.next = []
    assert service.get_next() == []


def test_dsl_service_to_dict(sample_service_data):
    """Test converting service to dictionary."""
    service = DslService.from_dict(sample_service_data)
    service_dict = service.to_dict()

    assert service_dict["name"] == "service1"
    assert service_dict["image"] == "nginx:latest"
    assert service_dict["args"] == ["--name", "test_container"]
    assert service_dict["envs"] == ["ENV=test"]
    assert service_dict["ports"] == ["80:80"]
    assert service_dict["vols"] == ["~/data:/data"]
    assert service_dict["next"] == ["service2"]
    assert service_dict["depends_on"] == ["service0"]
    assert service_dict["trigger"] == ["test1"]


def test_dsl_service_minimal_config():
    """Test service with minimal configuration."""
    minimal_data = {
        "name": "minimal_service",
        "desc": "Minimal service",
        "image": "nginx:latest",
    }
    service = DslService.from_dict(minimal_data)

    assert service.name == "minimal_service"
    assert service.image == "nginx:latest"
    assert service.args == []
    assert service.envs == []
    assert service.ports == []
    assert service.vols == []
    assert service.next == []
    assert service.depends_on == []
    assert service.trigger == []
