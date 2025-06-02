from octopus.orchestration.manager import TestManager


class Composer:
    """Composer"""

    def __init__(self, manager: TestManager):
        self.manager = manager

    def compose(self) -> None:
        """Compose the test environment"""
        pass
