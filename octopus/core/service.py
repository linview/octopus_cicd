from octopus.core.container import Container


class Service(Container):
    """Service"""

    def __init__(self, name: str, image: str):
        super().__init__(name, image)

    def start(self) -> None:
        """Start the service"""
        pass
