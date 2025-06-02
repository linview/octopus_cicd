"""
Test configuration DSL definition
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ServiceConfig:
    """Container service configuration"""
    name: str
    image: str
    ports: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    volumes: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None

@dataclass
class TestConfig:
    """Test environment configuration"""
    services: Dict[str, ServiceConfig]
    
    @classmethod
    def from_yaml(cls, path: str) -> "TestConfig":
        """Load configuration from YAML file"""
        # TODO: Implement YAML loading
        pass 