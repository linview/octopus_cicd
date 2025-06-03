"""
Service configuration models.
"""

from pydantic import BaseModel, Field, PrivateAttr


class Service(BaseModel):
    """Service configuration.

    This model represents the configuration of a service.
    """

    _name: str = PrivateAttr(description="Service name")
    _desc: str = PrivateAttr(description="Service description")

    image: str = Field(description="Service image")
    args: list[str] | None = Field(default_factory=list, description="Service arguments")
    envs: list[str] | None = Field(default_factory=list, description="Service environment variables")
    ports: list[str] | None = Field(default_factory=list, description="Service ports")
    vols: list[str] | None = Field(default_factory=list, description="Service volumes")
    depends_on: list[str] | None = Field(default_factory=list, description="Service dependencies")
    trigger: list[str] | None = Field(default_factory=list, description="Service triggers")

    def __init__(self, **data):
        """Initialize service configuration.

        Args:
            **data: Service configuration data
        """
        super().__init__(**data)
        self._name = data.get("name", "")
        self._desc = data.get("desc", "")

    @property
    def name(self) -> str:
        """Get service name.

        Returns:
            str: Service name
        """
        return self._name

    @property
    def desc(self) -> str:
        """Get service description.

        Returns:
            str: Service description
        """
        return self._desc

    class Config:
        """Pydantic model configuration"""

        extra = "forbid"
