import re
from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field


class Variable(BaseModel):
    """Input variable configuration.

    Since the input format in YAML is key-value pairs like:
    - service_name: service1
    - $cntr_name: service_container

    We need to handle this structure dynamically at runtime.
    """

    model_config = ConfigDict(extra="ignore")

    key: str = Field(description="Input variable name", frozen=True)
    # value: str = Field(description="value")
    _value: str = PrivateAttr(default=None)

    def __init__(self, **data: dict[str, Any]):
        super().__init__(**data)
        self._value = data.get("value", None)

    @computed_field
    @property
    def value(self) -> str:
        """Get the value of the variable."""
        # use computed_field to avoid pydantic validation error
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set the value of the variable.

        Args:
            new_value: The new value to set

        Raises:
            ValueError: If trying to set value for non-lazy variable
        """
        if not self.key.startswith("$"):
            raise ValueError(f"Cannot reassign value to non-lazy variable: {self.key}")
        logger.debug(f"Reassign lazy variable {self.key}: {self.value} -> {new_value}")
        self._value = new_value

    @property
    def is_lazy(self) -> bool:
        """Check if the variable is lazy."""
        return self.key.startswith("$")

    def __repr__(self) -> str:
        return f"Variable(key='{self.key}', value='{self.value}')"

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Dump the model to a dictionary.

        Returns:
            dict[str, Any]: The model as a dictionary with key and value fields
        """
        return {"key": self.key, "value": self._value}

    def to_dict(self) -> dict[str, str]:
        """Convert the variable to a dictionary.

        Returns:
            dict[str, str]: The variable as a dictionary with key and value fields
        """
        return self.model_dump()


class VariableEvaluator:
    """Variable evaluator"""

    @staticmethod
    def evaluate_value(value: Any, variables: dict[str, Any]) -> Any:
        """evaluate value with given variables"""
        if isinstance(value, str):
            pattern = r"\${([^}]+)}"
            matches = re.finditer(pattern, value)
            for match in matches:
                var_key = match.group(1)
                if var_key in variables:
                    value = value.replace(match.group(0), str(variables[var_key]))
        return value

    @staticmethod
    def evaluate_dict(data: dict[str, Any], variables: dict[str, Any]) -> None:
        """evaluate dict with given variables"""
        for key, value in data.items():
            if isinstance(value, dict | list):
                VariableEvaluator.evaluate_collection(value, variables)
            else:
                data[key] = VariableEvaluator.evaluate_value(value, variables)

    @staticmethod
    def evaluate_collection(collection: Any, variables: dict[str, Any]) -> None:
        """evaluate collection with given variables"""
        if isinstance(collection, dict):
            VariableEvaluator.evaluate_dict(collection, variables)
        elif isinstance(collection, list):
            for i, item in enumerate(collection):
                if isinstance(item, dict | list):
                    VariableEvaluator.evaluate_collection(item, variables)
                else:
                    collection[i] = VariableEvaluator.evaluate_value(item, variables)
