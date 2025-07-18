"""
Test environment manager implementation

Container test scheduling execution based on DslConfig
Supports DAG dependencies and sequential execution
"""

import time
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel

from octopus.core.container import Container
from octopus.core.service import Service
from octopus.dsl.dsl_config import DslConfig
from octopus.dsl.dsl_service import DslService
from octopus.dsl.dsl_test import DslTest


class ExecutionStatus(Enum):
    """Execution status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionNode(BaseModel):
    """Execution node"""

    name: str
    node_type: str  # "service" or "test"
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: float | None = None
    end_time: float | None = None
    error_message: str | None = None
    container: Container | None = None
    dsl_service: DslService | None = None
    dsl_test: DslTest | None = None


class TestManager:
    """Test manager based on DSL config

    Main features:
    1. Get DAG (execution plan) from DslConfig
    2. Execute in order according to DAG dependencies
    3. Manage container deployment and test execution
    4. Handle dependencies and trigger relationships
    """

    def __init__(self, config: DslConfig):
        """Initialize test manager

        Args:
            config: DslConfig configuration instance
        """
        self.config = config
        self.execution_nodes: dict[str, ExecutionNode] = {}
        self.running_containers: dict[str, Container] = {}
        self.execution_plan: list[str] = []
        self.execution_history: list[dict[str, Any]] = []

        # Validate configuration
        self._validate_config()

        # Initialize execution nodes
        self._init_execution_nodes()

        # Get execution plan (reuse DslConfig's DAG manager)
        self._generate_execution_plan()

    def _validate_config(self):
        """Validate configuration validity"""
        try:
            # Use DslConfig's validation functionality
            self.config.verify()
            logger.info("Configuration validation passed")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def _init_execution_nodes(self):
        """Initialize execution nodes"""
        # Initialize service nodes
        for service in self.config.services:
            node = ExecutionNode(name=service.name, node_type="service", dsl_service=service)
            self.execution_nodes[service.name] = node

        # Initialize test nodes
        for test in self.config.tests:
            node = ExecutionNode(name=test.name, node_type="test", dsl_test=test)
            self.execution_nodes[test.name] = node

    def _generate_execution_plan(self):
        """Generate execution plan (reuse DslConfig's DAG manager)"""
        try:
            # Use DslConfig's DAG manager to generate execution plan
            self.execution_plan = self.config._dag_manger.generate_execution_plan()
            logger.info(f"Generated execution plan using DslConfig DAG: {self.execution_plan}")
        except Exception as e:
            logger.error(f"DAG execution plan generation failed: {e}")
            raise

    def _get_node_dependencies(self, node_name: str) -> list[str]:
        """Get node dependencies (reuse DslConfig's DAG functionality)"""
        # Get dependencies from DAG manager's graph
        dag_graph = self.config._dag_manger._gen_subgraph()

        # Get node's predecessor nodes (dependencies)
        predecessors = list(dag_graph.predecessors(node_name))
        return predecessors

    def _get_node_dependents(self, node_name: str) -> list[str]:
        """Get node dependents (reuse DslConfig's DAG functionality)"""
        # Get dependents from DAG manager's graph
        dag_graph = self.config._dag_manger._gen_subgraph()

        # Get node's successor nodes (dependents)
        successors = list(dag_graph.successors(node_name))
        return successors

    def _can_execute_node(self, node_name: str) -> bool:
        """Check if node can be executed"""
        # Get node dependencies
        dependencies = self._get_node_dependencies(node_name)

        # Check if all dependencies are completed
        for dep_name in dependencies:
            if dep_name not in self.execution_nodes:
                logger.warning(f"Dependency node {dep_name} does not exist in execution nodes")
                continue

            dep_node = self.execution_nodes[dep_name]
            if dep_node.status not in [ExecutionStatus.SUCCESS]:
                return False

        return True

    def _create_container_from_service(self, service: DslService) -> Container:
        """Create Container instance from DslService"""
        # Convert parameter format
        envs = [f"-e {env}" for env in service.envs] if service.envs else []
        ports = [f"-p {port}" for port in service.ports] if service.ports else []
        volumes = [f"-v {vol}" for vol in service.vols] if service.vols else []
        run_args = service.args or []

        container = Service(
            name=service.name, image=service.image, envs=envs, ports=ports, volumes=volumes, run_args=run_args
        )

        return container

    def _execute_service(self, service_name: str) -> bool:
        """Execute service node"""
        node = self.execution_nodes[service_name]
        service = node.dsl_service

        try:
            logger.info(f"Starting service deployment: {service_name}")
            node.status = ExecutionStatus.RUNNING
            node.start_time = time.time()

            # Create and start container
            container = self._create_container_from_service(service)
            container_id = container.run()
            logger.info(f"Container '{container_id}' started")

            # Wait for container to start
            time.sleep(2)

            # Check container status
            if container.is_healthy():
                node.container = container
                self.running_containers[service_name] = container
                node.status = ExecutionStatus.SUCCESS
                node.end_time = time.time()
                logger.info(f"Service {service_name} deployed successfully")
                return True
            else:
                node.status = ExecutionStatus.FAILED
                node.error_message = "Container startup failed or health check failed"
                logger.error(f"Service {service_name} deployment failed")
                return False

        except Exception as e:
            node.status = ExecutionStatus.FAILED
            node.error_message = str(e)
            node.end_time = time.time()
            logger.error(f"Service {service_name} execution exception: {e}")
            return False

    def _execute_test(self, test_name: str) -> bool:
        """Execute test node"""
        node = self.execution_nodes[test_name]
        test = node.dsl_test

        try:
            logger.info(f"Starting test execution: {test_name}")
            node.status = ExecutionStatus.RUNNING
            node.start_time = time.time()

            # Get runner and execute test
            runner = test.runner
            command = runner.get_command()

            logger.info(f"Executing test command: {command}")

            # Here should actually execute the test command
            # Temporarily simulate success
            import subprocess

            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            # Check test result
            if result.returncode == test.expect.exit_code:
                node.status = ExecutionStatus.SUCCESS
                node.end_time = time.time()
                logger.info(f"Test {test_name} executed successfully")
                return True
            else:
                node.status = ExecutionStatus.FAILED
                node.error_message = (
                    f"Test failed, expected exit code: {test.expect.exit_code}, actual: {result.returncode}"
                )
                node.end_time = time.time()
                logger.error(f"Test {test_name} execution failed")
                return False

        except Exception as e:
            node.status = ExecutionStatus.FAILED
            node.error_message = str(e)
            node.end_time = time.time()
            logger.error(f"Test {test_name} execution exception: {e}")
            return False

    def _execute_node(self, node_name: str) -> bool:
        """Execute single node"""
        node = self.execution_nodes[node_name]

        if node.node_type == "service":
            return self._execute_service(node_name)
        elif node.node_type == "test":
            return self._execute_test(node_name)
        else:
            logger.error(f"Unknown node type: {node.node_type}")
            return False

    def execute(self) -> bool:
        """Execute entire test flow"""
        logger.info("Starting test flow execution")
        logger.info(f"Execution plan: {self.execution_plan}")

        success_count = 0
        total_count = len(self.execution_plan)

        for node_name in self.execution_plan:
            # Check if can execute
            if not self._can_execute_node(node_name):
                logger.warning(f"Node {node_name} dependencies not satisfied, skipping")
                self.execution_nodes[node_name].status = ExecutionStatus.SKIPPED
                continue

            # Execute node
            success = self._execute_node(node_name)
            if success:
                success_count += 1

            # Record execution history
            node = self.execution_nodes[node_name]
            self.execution_history.append(
                {
                    "node_name": node_name,
                    "node_type": node.node_type,
                    "status": node.status.value,
                    "start_time": node.start_time,
                    "end_time": node.end_time,
                    "error_message": node.error_message,
                }
            )

        logger.info(f"Test flow execution completed: {success_count}/{total_count} successful")
        return success_count == total_count

    def cleanup(self):
        """Clean up resources"""
        logger.info("Starting resource cleanup")

        # Stop and remove all containers
        for container_name, container in self.running_containers.items():
            try:
                logger.info(f"Cleaning up container: {container_name}")
                container.stop()
                container.remove()
            except Exception as e:
                logger.error(f"Failed to cleanup container {container_name}: {e}")

        self.running_containers.clear()
        logger.info("Resource cleanup completed")

    def get_execution_status(self) -> dict[str, Any]:
        """Get execution status"""
        status_summary = {
            "total_nodes": len(self.execution_nodes),
            "execution_plan": self.execution_plan,
            "node_status": {},
            "summary": {"pending": 0, "running": 0, "success": 0, "failed": 0, "skipped": 0},
        }

        for name, node in self.execution_nodes.items():
            # Get dependencies (reuse DslConfig's DAG functionality)
            dependencies = self._get_node_dependencies(name)
            dependents = self._get_node_dependents(name)

            status_summary["node_status"][name] = {
                "type": node.node_type,
                "status": node.status.value,
                "dependencies": dependencies,
                "dependents": dependents,
                "start_time": node.start_time,
                "end_time": node.end_time,
                "error_message": node.error_message,
            }
            status_summary["summary"][node.status.value] += 1

        return status_summary

    def get_dag_info(self) -> dict[str, Any]:
        """Get DAG information (reuse DslConfig's DAG functionality)"""
        dag_manager = self.config._dag_manger

        return {
            "is_valid_dag": dag_manager.is_valid_dag(),
            "total_nodes": len(dag_manager._full_graph.nodes),
            "total_edges": len(dag_manager._full_graph.edges),
            "topological_order": dag_manager.get_topological_order(),
            "execution_plan": self.execution_plan,
        }

    def print_dag_visualization(self):
        """Print DAG visualization (reuse DslConfig's DAG functionality)"""
        self.config.print_execution_dag()

    def get_service_logs(self, service_name: str) -> list[str]:
        """Get service logs"""
        if service_name in self.running_containers:
            return self.running_containers[service_name].get_logs()
        return []

    def get_service(self, name: str) -> Container | None:
        """Get service instance"""
        return self.running_containers.get(name)


# quick function
def create_test_manager_from_config(config_path: str | Path) -> TestManager:
    """Create test manager from configuration file

    Args:
        config_path: Configuration file path

    Returns:
        TestManager instance
    """
    config = DslConfig.from_yaml_file(Path(config_path))
    return TestManager(config)


def execute_test_from_config(config_path: str | Path) -> bool:
    """Execute local container test from DSL file

    Args:
        config_path: Configuration file path

    Returns:
        Whether execution was successful
    """
    manager = create_test_manager_from_config(config_path)
    try:
        return manager.execute()
    finally:
        manager.cleanup()


if __name__ == "__main__":
    # Test code
    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if config_path:
        print(f"Using configuration file: {config_path}")
        success = execute_test_from_config(config_path)
        print(f"Test execution result: {'Success' if success else 'Failed'}")
    else:
        print("Configuration file not found")
