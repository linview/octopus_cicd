"""
Interface definitions for test runners.
"""

from abc import ABC, abstractmethod
from typing import Any


class RunnerInterface(ABC):
    """Interface for test runners.

    All test runners must implement this interface to ensure consistent behavior.
    """

    @abstractmethod
    def get_command(self) -> str:
        """Get the executable command string.

        Returns:
            str: The command string that can be executed
        """
        pass

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get the runner's configuration.

        Returns:
            Dict[str, Any]: The runner's configuration dictionary
        """
        pass


class Evaluable(ABC):
    """Interface for evaluable objects.

    All evaluable objects must implement this interface to ensure consistent behavior.
    """

    @abstractmethod
    def evaluate(self, variables: dict[str, Any]) -> None:
        """Evaluate object with given variables.

        Args:
            variables: A dictionary of variables to evaluate the object with
        """
        pass
