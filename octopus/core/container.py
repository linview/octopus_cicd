"""
Base container service implementation
"""

from abc import ABC, abstractmethod


class Container(ABC):
    """Abstract base class for container services"""

    name: str
    image: str
    container_id: str | None

    def __init__(self, name: str, image: str):
        """Initialize the container"""
        self.name = name
        self.image = image
        self.container_id: str | None = None

    @abstractmethod
    def run(self) -> str:
        """Run container and return the container ID"""
        ...

    @abstractmethod
    def start(self) -> None:
        """Start the container"""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the container"""
        ...

    @abstractmethod
    def pause(self) -> None:
        """Pause the container"""
        ...

    @abstractmethod
    def remove(self) -> None:
        """Remove the container"""
        ...

    @abstractmethod
    def get_logs(self) -> list[str]:
        """Get container logs"""
        ...

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the container is healthy"""
        ...

    @abstractmethod
    def get_container_info(self) -> dict[str, str]:
        """Get container information"""
        ...
