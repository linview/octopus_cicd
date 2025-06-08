from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class Variable(BaseModel):
    """Input variable configuration.

    Since the input format in YAML is key-value pairs like:
    - service_name: service1
    - $cntr_name: service_container

    We need to handle this structure dynamically at runtime.
    """

    model_config = ConfigDict(extra="ignore")

    key: str = Field(description="Input variable name", frozen=True)
    _value: str = PrivateAttr(default=None)

    def __init__(self, **data: dict[str, Any]):
        super().__init__(**data)
        self._value = data.get("value", None)

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        if not self.key.startswith("$"):
            raise ValueError(f"Cannot reassign value to non-lazy variable: {self.key}")
        logger.debug(f"Reassign lazy variable {self.key}: {self.value} -> {new_value}")
        self._value = new_value

    @property
    def is_lazy(self) -> bool:
        return self.key.startswith("$")

    def __repr__(self) -> str:
        return f"Variable(key='{self.key}', value='{self.value}')"

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        return {"key": self.key, "value": self._value}

    def to_dict(self) -> dict[str, str]:
        return self.model_dump()
