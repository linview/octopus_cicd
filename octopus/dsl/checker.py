from typing import Any

from pydantic import BaseModel

from octopus.dsl.constants import TEST_EXPECT_FIELDS, TestMode


class Expect(BaseModel):
    """Test expectations configuration."""

    def __init__(self, mode: TestMode, **data: Any):
        """Initialize expectations with mode-specific fields.

        Args:
            mode: Test mode
            **data: Expectation data
        """
        super().__init__(**data)
        self._mode = mode
        self._validate_fields()

    def _validate_fields(self):
        """Validate that all required fields are present."""
        required = TEST_EXPECT_FIELDS[self._mode]
        missing = [field for field in required if not hasattr(self, field)]
        if missing:
            raise ValueError(f"Missing required fields for {self._mode}: {missing}")
