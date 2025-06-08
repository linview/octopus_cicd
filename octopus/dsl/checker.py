from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from octopus.dsl.constants import TEST_EXPECT_FIELDS, TestMode


class Expect(BaseModel):
    """Test expectations configuration."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    mode: TestMode = Field(default=TestMode.NONE, description="Test mode")
    exit_code: int | str | None = Field(default=None, description="Exit code")
    stdout: str | None = Field(default=None, description="Standard output")
    stderr: str | None = Field(default=None, description="Standard error")
    status_code: int | str | None = Field(default=None, description="Status code")
    response: str | None = Field(default=None, description="Response")

    def __init__(self, **data: Any):
        """Initialize expectations with mode-specific fields.

        Args:
            mode: Test mode
            **data: Expectation data
        """
        super().__init__(**data)
        #        self.mode = mode
        self._validate_fields()

    def _validate_fields(self):
        """Validate that all required fields are present."""
        required = TEST_EXPECT_FIELDS[self.mode]
        missing = [field for field in required if getattr(self, field) is None]
        if missing:
            raise ValueError(f"Missing required fields for {self.mode}: {missing}")

    def to_dict(self) -> dict[str, str]:
        """Convert the expect instance to a dictionary."""
        return {k: v for k, v in self.model_dump().items() if v is not None}

    def __repr__(self) -> str:
        """Return the string representation of the expect instance."""
        attrs = []
        for field in self.model_fields:
            value = getattr(self, field)
            if value is not None:
                attrs.append(f"{field}={value!r}")
        return f"Expect({', '.join(attrs)})"
