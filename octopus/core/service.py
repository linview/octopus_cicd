import atexit
import uuid
from enum import Enum

from docker import DockerClient
from docker.errors import DockerException
from loguru import logger
from pydantic import Field, field_validator

from octopus.core.container import Container


class ServiceStatus(Enum):
    """Service status"""

    NOT_STARTED = "not_started"
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    EXITED = "exited"
    REMOVED = "removed"


class Service(Container):
    """Service in Container"""

    envs: list[str] = Field(default_factory=list, description="Environment variables")
    ports: list[str] = Field(default_factory=list, description="Ports")
    volumes: list[str] = Field(default_factory=list, description="Volumes")
    run_args: list[str] = Field(default_factory=list, description="Run arguments")

    _registered_containers: set[str] = set()
    __uuid: str
    __docker_client: DockerClient = DockerClient.from_env()
    __status: ServiceStatus = ServiceStatus.NOT_STARTED

    def __init__(
        self,
        name: str,
        image: str,
        envs: list[str] | None,
        ports: list[str] | None,
        volumes: list[str] | None,
        run_args: list[str] | None,
    ):
        super().__init__(name, image)
        self.__uuid = str(uuid.uuid4())
        self.run_args = [
            "-d",
            "--name",
            self.name,
        ]
        if envs:
            self.envs = envs
        if ports:
            self.ports = ports
        if volumes:
            self.volumes = volumes
        if run_args:
            self.run_args.extend(run_args)
        self.__status = ServiceStatus.NOT_STARTED

    def _cleanup(self) -> None:
        """Internal cleanup method that will be called on exit"""
        if self.container_id is not None:
            try:
                self.remove()
            except DockerException:
                logger.error(f"Failed to remove container {self.container_id}")

    @property
    def uuid(self) -> str:
        """Get the container UUID"""
        return self.__uuid

    @property
    def status(self) -> ServiceStatus:
        """Get the service status"""
        return self.__status

    @field_validator("envs")
    @classmethod
    def validate_envs(cls, v: list[str]) -> list[str]:
        """Validate the environment variables"""
        if not isinstance(v, list):
            raise ValueError("Environment variables must be a list")
        for env in v:
            if "-e" not in env:
                raise ValueError("Environment variables must be in the format of -e KEY=VALUE")
        return v

    @field_validator("ports")
    @classmethod
    def validate_ports(cls, v: list[str]) -> list[str]:
        """Validate the ports"""
        if not isinstance(v, list):
            raise ValueError("Ports must be a list")
        for port in v:
            if ":" not in port or "-v" not in port:
                raise ValueError("Ports must be in the format of '-p HOST:CONTAINER'")
        return v

    @field_validator("volumes")
    @classmethod
    def validate_volumes(cls, v: list[str]) -> list[str]:
        """Validate the volumes"""
        if not isinstance(v, list):
            raise ValueError("Volumes must be a list")
        for volume in v:
            if "-v" not in volume or ":" not in volume:
                raise ValueError("Volumes must be in the format of '-v HOST:CONTAINER'")
        return v

    @field_validator("run_args")
    @classmethod
    def validate_run_args(cls, v: list[str]) -> list[str]:
        """Validate the run arguments"""
        if not isinstance(v, list):
            raise ValueError("Run arguments must be a list")
        return v

    def run(self) -> str:
        """Run the service in container, return the container ID"""
        try:
            if self.container_id is None and self.__docker_client.containers.get(self.container_id) is None:
                res = self.__docker_client.containers.run(
                    self.image,
                    self.envs,
                    self.ports,
                    self.volumes,
                    self.run_args,
                )
                if res.status_code == 200:
                    self.container_id = res.id
                    self.container_name = res.name
                    self.__status = ServiceStatus.RUNNING
                    self._registered_containers.add(self.container_id)
                    atexit.register(self._cleanup)
                else:
                    raise DockerException(f"Failed to start container {self.container_id}")
            elif self.container_id and self.__docker_client.containers.get(self.container_id) is None:
                logger.warning(f"Container {self.name} was removed unexpected, rerun it")
                self.container_id = None
                self.__status = ServiceStatus.NOT_STARTED
                return self.run()
            else:
                logger.warning(f"Container {self.name} is already running, id: {self.container_id}")
                self.__status = ServiceStatus.RUNNING
            return self.container_id
        except DockerException as e:
            logger.error(f"Failed to run container: {str(e)}")
            self.__status = ServiceStatus.EXITED
            raise

    def start(self) -> None:
        """Start the service"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            self.__docker_client.containers.start(self.container_id)
            self.__status = ServiceStatus.RUNNING

    def stop(self) -> None:
        """Stop the service"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            try:
                self.__docker_client.containers.stop(self.container_id)
                self.__status = ServiceStatus.STOPPED
            except DockerException as e:
                logger.error(f"Failed to stop container: {str(e)}")
                raise

    def pause(self) -> None:
        """Pause the service"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            self.__docker_client.containers.pause(self.container_id)
            self.__status = ServiceStatus.PAUSED

    def remove(self) -> None:
        """Remove the service"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            self.__docker_client.containers.remove(self.container_id)
            self.__status = ServiceStatus.REMOVED
            self._registered_containers.remove(self.container_id)
            self.container_id = None
            atexit.unregister(self._cleanup)

    def get_logs(self) -> list[str]:
        """Get servic log"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            return self.__docker_client.containers.get(self.container_id).logs()
        return []

    def is_healthy(self) -> bool:
        """Check if the service is healthy"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            try:
                return self.__docker_client.containers.get(self.container_id).health()
            except DockerException:
                return False
        return False

    def get_container_info(self) -> dict[str, str]:
        """Get container information by docker inspect"""
        if self.container_id and self.__docker_client.containers.get(self.container_id):
            return self.__docker_client.containers.get(self.container_id).inspect()
        return {}
