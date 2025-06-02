"""
Base container service implementation
"""

from abc import ABC, abstractmethod


class Container(ABC):
    """Abstract base class for container services"""

    def __init__(self, name: str, image: str):
        self.name = name
        self.image = image
        self.container_id: str | None = None

    @abstractmethod
    def start(self) -> None:
        """Start the container"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the container"""
        pass

    @abstractmethod
    def get_logs(self) -> list[str]:
        """Get container logs"""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the container is healthy"""
        pass

    @abstractmethod
    def get_container_info(self) -> dict[str, str]:
        """Get container information"""
        pass
