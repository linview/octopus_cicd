"""Unit tests for DAGManager class."""

import tempfile
from pathlib import Path

import pytest

from octopus.dsl.checker import Expect
from octopus.dsl.constants import TestMode
from octopus.dsl.dag_manager import DAGManager
from octopus.dsl.dsl_config import DslConfig
from octopus.dsl.dsl_service import DslService
from octopus.dsl.dsl_test import DslTest
from octopus.dsl.runner import ShellRunner


@pytest.fixture
def valid_config():
    """Create a valid test configuration."""
    services = [
        DslService(
            name="service_1",
            desc="Service 1",
            next=["service_2"],
            trigger=["test_1"],
            image="nginx:latest",
            args=[],
            ports=["80:80"],
            envs=[],
            vols=[],
        ),
        DslService(
            name="service_2",
            desc="Service 2",
            next=["service_3"],
            trigger=["test_2"],
            image="nginx:latest",
            args=[],
            ports=["80:80"],
            envs=[],
            vols=[],
        ),
        DslService(
            name="service_3",
            desc="Service 3",
            next=[],
            trigger=["test_3"],
            image="nginx:latest",
            args=[],
            ports=["80:80"],
            envs=[],
            vols=[],
        ),
    ]
    tests = [
        DslTest(
            name="test_1",
            desc="Test 1",
            mode=TestMode.SHELL,
            needs=["service_1"],
            runner=ShellRunner(cmd=["echo", "test1"]),
            expect=Expect(
                mode=TestMode.SHELL,
                exit_code=0,
                stdout="test1",
                stderr="",
            ),
        ),
        DslTest(
            name="test_2",
            desc="Test 2",
            mode=TestMode.SHELL,
            needs=["service_2"],
            runner=ShellRunner(cmd=["echo", "test2"]),
            expect=Expect(
                mode=TestMode.SHELL,
                exit_code=0,
                stdout="test2",
                stderr="",
            ),
        ),
        DslTest(
            name="test_3",
            desc="Test 3",
            mode=TestMode.SHELL,
            needs=["service_3"],
            runner=ShellRunner(cmd=["echo", "test3"]),
            expect=Expect(
                mode=TestMode.SHELL,
                exit_code=0,
                stdout="test3",
                stderr="",
            ),
        ),
    ]
    return DslConfig(
        version="0.1.0",
        name="test_config",
        desc="Test configuration",
        services=services,
        tests=tests,
    )


@pytest.fixture
def cyclic_config():
    """Create a configuration with circular dependency."""
    services = [
        DslService(
            name="service_1",
            desc="Service 1",
            next=["service_2"],
            trigger=[],
            image="nginx:latest",
            args=[],
            ports=["80:80"],
            envs=[],
            vols=[],
        ),
        DslService(
            name="service_2",
            desc="Service 2",
            next=["service_1"],
            trigger=[],
            image="nginx:latest",
            args=[],
            ports=["80:80"],
            envs=[],
            vols=[],
        ),
    ]
    return DslConfig(
        version="0.1.0",
        name="cyclic_config",
        desc="Configuration with circular dependency",
        services=services,
        tests=[],
    )


def test_dag_construction(valid_config):
    """Test basic DAG construction."""
    dag_manager = DAGManager(valid_config)

    # Test node creation
    assert "service_1" in dag_manager._full_graph.nodes
    assert "service_2" in dag_manager._full_graph.nodes
    assert "service_3" in dag_manager._full_graph.nodes
    assert "test_1" in dag_manager._full_graph.nodes
    assert "test_2" in dag_manager._full_graph.nodes
    assert "test_3" in dag_manager._full_graph.nodes

    # Test edge creation
    assert dag_manager._full_graph.has_edge("service_1", "service_2")
    assert dag_manager._full_graph.has_edge("service_2", "service_3")
    assert dag_manager._full_graph.has_edge("service_1", "test_1")
    assert dag_manager._full_graph.has_edge("service_2", "test_2")
    assert dag_manager._full_graph.has_edge("service_3", "test_3")
    assert dag_manager._full_graph.has_edge("test_1", "service_1")
    assert dag_manager._full_graph.has_edge("test_2", "service_2")
    assert dag_manager._full_graph.has_edge("test_3", "service_3")


def test_dag_validation(valid_config, cyclic_config):
    """Test DAG validation."""
    # Test valid DAG
    dag_manager = DAGManager(valid_config)
    assert dag_manager.is_valid_dag()

    # Test cyclic DAG
    dag_manager = DAGManager(cyclic_config)
    assert not dag_manager.is_valid_dag()


def test_topological_sort(valid_config):
    """Test topological sorting."""
    dag_manager = DAGManager(valid_config)
    order = dag_manager.get_topological_order()

    # Verify service order
    service_1_index = order.index("service_1")
    service_2_index = order.index("service_2")
    service_3_index = order.index("service_3")
    assert service_1_index < service_2_index
    assert service_2_index < service_3_index


def test_execution_plan(valid_config):
    """Test execution plan generation."""
    dag_manager = DAGManager(valid_config)
    plan = dag_manager.generate_execution_plan()

    # Verify deployment order
    assert plan["deploy"] == ["service_1", "service_2", "service_3"]

    # Verify execution order
    assert plan["execute"] == ["test_1", "test_2", "test_3"]


def test_invalid_dag_topological_sort(cyclic_config):
    """Test topological sort on invalid DAG."""
    dag_manager = DAGManager(cyclic_config)
    with pytest.raises(ValueError, match="Cannot perform topological sort on a graph with cycles"):
        dag_manager.get_topological_order()


def test_yaml_config():
    """Test DAGManager with config loaded from YAML."""
    yaml_content = """
    version: "0.1.0"
    name: yaml_config
    desc: Configuration loaded from YAML
    inputs:
    services:
      - name: service_1
        desc: Service 1
        next: [service_2]
        trigger: [test_1]
        image: nginx:latest
        args: []
        ports: ["80:80"]
        envs: []
        vols: []
      - name: service_2
        desc: Service 2
        trigger: [test_2]
        image: nginx:latest
        args: []
        ports: ["80:80"]
        envs: []
        vols: []
    tests:
      - name: test_1
        desc: Test 1
        mode: shell
        needs: [service_1]
        runner:
          cmd: ["echo", "test1"]
        expect:
          mode: shell
          exit_code: 0
          stdout: "test1"
          stderr: ""
      - name: test_2
        desc: Test 2
        mode: shell
        needs: [service_2]
        runner:
          cmd: ["echo", "test2"]
        expect:
          mode: shell
          exit_code: 0
          stdout: "test2"
          stderr: ""
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_yaml_path = f.name

    try:
        config = DslConfig.from_yaml_file(Path(temp_yaml_path))
        dag_manager = DAGManager(config)

        # Verify graph structure
        assert "service_1" in dag_manager._full_graph.nodes
        assert "service_2" in dag_manager._full_graph.nodes
        assert "test_1" in dag_manager._full_graph.nodes
        assert "test_2" in dag_manager._full_graph.nodes
        assert dag_manager._full_graph.has_edge("service_1", "service_2")
        assert dag_manager._full_graph.has_edge("service_1", "test_1")
        assert dag_manager._full_graph.has_edge("service_2", "test_2")

        # Test execution plan
        plan = dag_manager.generate_execution_plan()
        assert plan["deploy"] == ["service_1", "service_2"]
        assert plan["execute"] == ["test_1", "test_2"]
    finally:
        Path(temp_yaml_path).unlink()
