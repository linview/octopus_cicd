"""
Test configuration DSL definition
"""

from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Container service configuration"""

    name: str
    image: str
    ports: list[str] | None = None
    environment: dict[str, str] | None = None
    volumes: list[str] | None = None
    depends_on: list[str] | None = None


@dataclass
class TestConfig:
    """Test environment configuration"""

    services: dict[str, ServiceConfig]

    @classmethod
    def from_yaml(cls, path: str) -> "TestConfig":
        """Load configuration from YAML file"""
        # TODO: Implement YAML loading
        pass
