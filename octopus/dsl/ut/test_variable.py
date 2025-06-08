"""Unit tests for Variable class."""

import pytest

from octopus.dsl.variable import Variable


@pytest.fixture
def normal_variable():
    """Create a normal variable."""
    return Variable(key="service_name", value="service1")


@pytest.fixture
def lazy_variable():
    """Create a lazy variable."""
    return Variable(key="$cntr_name", value="service_container")


def test_variable_creation(normal_variable, lazy_variable):
    """Test variable creation."""
    # Test normal variable
    assert normal_variable.key == "service_name"
    assert normal_variable.value == "service1"
    assert not normal_variable.is_lazy

    # Test lazy variable
    assert lazy_variable.key == "$cntr_name"
    assert lazy_variable.value == "service_container"
    assert lazy_variable.is_lazy


def test_variable_value_setter(normal_variable, lazy_variable):
    """Test variable value setter."""
    # Test lazy variable value setting
    lazy_variable.value = "new_container"
    assert lazy_variable.value == "new_container"

    # Test normal variable value setting (should raise error)
    with pytest.raises(ValueError, match="Cannot reassign value for non-lazy variable"):
        normal_variable.value = "new_service"


def test_variable_validation():
    """Test variable validation."""
    # Test valid variable creation
    var = Variable(key="valid_key", value="valid_value")
    assert var.key == "valid_key"
    assert var.value == "valid_value"

    # Test invalid variable creation (missing required fields)
    with pytest.raises(ValueError):
        var.key = "frozen_key"

    with pytest.raises(ValueError):
        var.value = "immutable_value"

    lazy_var = Variable(key="$lazy_var", value="lazy_value")
    with pytest.raises(ValueError):
        lazy_var.key = "$new_lazy_key"
    lazy_var.value = "new_lazy_value"
    assert lazy_var.value == "new_lazy_value"


def test_variable_from_dict():
    """Test variable creation from dictionary."""
    # Test normal variable
    var_dict = {"key": "service_name", "value": "service1"}
    var = Variable(**var_dict)
    assert var.key == "service_name"
    assert var.value == "service1"
    assert not var.is_lazy

    # Test lazy variable
    lazy_dict = {"key": "$cntr_name", "value": "service_container"}
    lazy_var = Variable(**lazy_dict)
    assert lazy_var.key == "$cntr_name"
    assert lazy_var.value == "service_container"
    assert lazy_var.is_lazy


def test_variable_to_dict(normal_variable, lazy_variable):
    """Test variable to dictionary conversion."""
    # Test normal variable
    var_dict = normal_variable.to_dict()
    assert var_dict == {"key": "service_name", "value": "service1"}

    # Test lazy variable
    lazy_dict = lazy_variable.to_dict()
    assert lazy_dict == {"key": "$cntr_name", "value": "service_container"}


def test_variable_str_representation(normal_variable, lazy_variable):
    """Test variable string representation."""
    # Test normal variable string representation
    assert str(normal_variable) == "service_name: service1"
    assert repr(normal_variable) == "Variable(key='service_name', value='service1')"

    # Test lazy variable string representation
    assert str(lazy_variable) == "$cntr_name: service_container"
    assert repr(lazy_variable) == "Variable(key='$cntr_name', value='service_container')"
