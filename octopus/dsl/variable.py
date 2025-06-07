from pydantic import BaseModel, Field


class Variable(BaseModel):
    """Input variable configuration.

    Since the input format in YAML is key-value pairs like:
    - service_name: service1
    - $cntr_name: service_container

    We need to handle this structure dynamically at runtime.
    """

    key: str = Field(description="Input variable name")
    value: str = Field(description="Input variable value")
