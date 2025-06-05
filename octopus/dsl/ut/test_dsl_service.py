"""Unit tests for DslService class."""

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
    )
    result = service.to_dict()

    # Verify fields with None values are excluded from the result
    assert result == {
        "name": "test",
        "desc": "test",
        "image": "nginx:latest",
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
    }
