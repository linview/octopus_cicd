import sys

import networkx as nx
from loguru import logger

from octopus.dsl.dsl_config import DslConfig
from octopus.dsl.dsl_service import DslService
from octopus.dsl.dsl_test import DslTest

logger.remove()
logger.add(sys.stdout, level="DEBUG")

ALLOWED_EDGE_TYPES = ["next", "trigger", "depends_on", "needs"]


class DAGManager:
    """A manager class to handle DAG operations for DslConfig.

    Features:
    - Build graph from DslConfig services and tests
    - Check if the graph is a valid DAG (no cycles)
    - Generate topological order of nodes
    - Create execution plan based on dependencies
    - Visualize the dependency graph (optional)
    """

    dsl_config: DslConfig
    _full_graph: nx.Graph
    __edge_types_in_dag: list[str] = ["next", "trigger"]

    def __init__(self, dsl_config: DslConfig):
        """Initialize the DAGManager with a DslConfig instance.

        Args:
            dsl_config: A DslConfig instance containing service and test definitions
        """
        self.dsl_config = dsl_config
        self._full_graph = nx.DiGraph()
        self._build_graph()

    @property
    def allowed_edge_types(self):
        return self.__edge_types_in_dag

    @allowed_edge_types.setter
    def allowed_edge_types(self, types: list[str]):
        for t in types:
            if t not in ALLOWED_EDGE_TYPES:
                raise ValueError(f"Invalid edge type: {t}")
        self.__edge_types_in_dag = types

    def __build_service_edges(self, services: list[str]):
        # add depends_on, trigger edges
        for svc in services:
            for next_svc in svc.get_next():
                if next_svc not in self._full_graph:
                    logger.warning(f"Service '{svc.name}' next to non-existent service '{next_svc}'")
                    continue
                self._full_graph.add_edge(svc.name, next_svc, type="next")

            for dep in svc.depends_on:
                if dep not in self._full_graph:
                    logger.warning(f"Service '{svc.name}' depends on non-existent service '{dep}'")
                    continue
                self._full_graph.add_edge(dep, svc.name, type="depends_on")

            for test_name in svc.trigger:
                if not self.dsl_config.is_valid_test(test_name):
                    raise ValueError(f"Service {svc} triggers non-existent Test {test_name}")
                if test_name not in self._full_graph:
                    self._full_graph.add_node(test_name, type="test")
                else:
                    logger.info(f"Test '{test_name}' already exists in graph")
                self._full_graph.add_edge(svc.name, test_name, type="trigger")

    def __build_test_edges(self, tests: list[str]):
        # Add test edges
        for test in tests:
            for svc in test.needs:
                if not self.dsl_config.is_valid_service(svc):
                    raise ValueError(f"Test '{test.name}' needs non-existent service '{svc}'")
                if svc not in self._full_graph:
                    logger.warning(f"Test '{test.name}' needs non-existent service '{svc}'")
                    continue
                self._full_graph.add_edge(test.name, svc, type="needs")

    def _build_graph(self):
        """Build the graph structure from DslConfig data.

        This method adds nodes for services and tests, and creates edges based on:
        - Service deploy sequence (next)
        - Service dependencies (depends_on)
        - Service triggers Test (trigger)
        - Test require Service (needs)
        """
        services = self.dsl_config.services
        tests = self.dsl_config.tests

        # Add all service nodes
        for svc in services:
            self._full_graph.add_node(svc.name, type="service")

        # Add all test nodes
        for test in tests:
            self._full_graph.add_node(test.name, type="test")

        self.__build_service_edges(services)
        self.__build_test_edges(tests)

    def _gen_subgraph(self) -> nx.DiGraph:
        """
        Generate a subgraph with only the allowed edge types.``
        """
        subgraph = nx.DiGraph()
        for u, v, attrs in self._full_graph.edges(data=True):
            if attrs.get("type") in self.allowed_edge_types:
                subgraph.add_edge(u, v, **attrs)
                subgraph.add_node(u, **self._full_graph.nodes[u])
                subgraph.add_node(v, **self._full_graph.nodes[v])
        return subgraph

    def is_valid_dag(self) -> bool:
        """Check if the subgraph formed by specific edge types is a valid DAG.
        Returns:
            bool: True if the filtered subgraph is a valid DAG
        """

        # Build a subgraph with only the allowed edge types
        subgraph = self._gen_subgraph()

        # Empty graph is technically a DAG
        if len(subgraph.edges) == 0:
            return True

        try:
            return nx.is_directed_acyclic_graph(subgraph)
        except Exception as e:
            logger.exception(f"DAG check failed: {e}")
            return False

    def get_topological_order(self) -> list[str]:
        """Get the topological order of nodes in the graph.

        Returns:
            List of node names in topological order

        Raises:
            ValueError: If the graph contains cycles
        """
        if not self.is_valid_dag():
            raise ValueError("Cannot perform topological sort on a graph with cycles.")
        return list(nx.topological_sort(self._gen_subgraph()))

    def generate_execution_plan(self) -> dict[str, list[str]]:
        """Generate deployment and execution plans based on dependencies.

        The deployment plan includes services in the order they should be deployed.
        The execution plan includes tests in the order they should be executed,
        ensuring all required services are already deployed.

        Returns:
            Dictionary with 'deploy' and 'execute' keys containing ordered lists

        Raises:
            ValueError: If any test's required services are missing from deployment plan
        """
        order = self.get_topological_order()
        service_names = {s.name for s in self.dsl_config.services}
        test_names = {t.name for t in self.dsl_config.tests}

        plan = {"deploy": [], "execute": []}

        # Deployment order: only services
        for node in order:
            if node in service_names:
                plan["deploy"].append(node)

        executed_tests = set()
        for node in order:
            if node in test_names and node not in executed_tests:
                test_obj = next(t for t in self.dsl_config.tests if t.name == node)
                missing = [n for n in test_obj.needs if n not in plan["deploy"]]
                if missing:
                    raise ValueError(f"Test '{node}' cannot run because dependencies {missing} are missing.")
                plan["execute"].append(node)
                executed_tests.add(node)

        return plan

    def visualize_with_plt(self, output_file: str | None = None):
        """Visualize test execution DAG with matplotlib

        Args:
            output_file: Optional path to save the visualization. If not provided, displays the graph.
        """
        import matplotlib.pyplot as plt

        graph = self._gen_subgraph()

        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Graph is not a DAG")

        pos = nx.spring_layout(graph, k=1, iterations=50)

        plt.figure(figsize=(12, 8))
        #        ax = plt.gca()

        node_colors = {
            "service": "#FF9999",  # dark blue
            "test": "#306998",  # ligth blue
        }

        edge_colors = {
            "next": "#4B8BBE",  # red
            "trigger": "#99FF99",  # greed
            "depends_on": "#9999FF",  # cyan
            "needs": "#FFFF99",  # yellow
        }

        # get service, test nodes
        service_nodes, test_nodes = [], []
        for node, attr in graph.nodes(data=True):
            node_type = attr.get("type", "")
            if node_type == "service":
                service_nodes.append(node)
            elif node_type == "test":
                test_nodes.append(node)

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=service_nodes,
            node_color=node_colors["service"],
            node_size=1000,
            alpha=0.8,
            label="Services",
        )
        nx.draw_networkx_nodes(
            graph, pos, nodelist=test_nodes, node_color=node_colors["test"], node_size=1000, alpha=0.8, label="Tests"
        )

        # draw edges by attribute "type"
        for edge_type in self.allowed_edge_types:
            edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get("type") == edge_type]
            if edges:
                nx.draw_networkx_edges(
                    graph,
                    pos,
                    edgelist=edges,
                    edge_color=edge_colors[edge_type],
                    width=2,
                    alpha=0.7,
                    arrowsize=20,
                    label=f"{edge_type} edges",
                )

        # set label
        nx.draw_networkx_labels(graph, pos, font_size=10, font_weight="bold")

        plt.legend(loc="upper left", bbox_to_anchor=(1, 1))

        # set title&layout
        plt.title("Test Execution Plan", pad=20)
        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, bbox_inches="tight", dpi=300)
        else:
            plt.show(block=False)
            plt.pause(10)

        plt.close()

    def visualize_with_rich(self):
        """Visualize test execution DAG with rich tree structure.

        The tree structure shows the dependencies between services and tests.
        Each node is displayed as <node_type>:<node_name>.
        """
        from rich.console import Console
        from rich.tree import Tree

        graph = self._gen_subgraph()
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Graph is not a DAG")

        # get root nodes
        root_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]

        console = Console()
        console.print(">>> Test Executio Plan <<<")

        def build_tree(node: str, tree: Tree, visited: set[str]):
            """build rich tree with node recursive travel

            Args:
                node: current node
                tree: current tree
                visited: visited node collection
            """
            if node in visited:
                return

            visited.add(node)
            node_type = graph.nodes[node].get("type", "unknown")
            node_tree = tree.add(f"{node_type}: {node}")

            # get nodes after current nodes
            successors = list(graph.successors(node))
            for _, succ in enumerate(successors):
                # check circlous dependencies
                if succ in visited:
                    node_tree.add(f"[red]{graph.nodes[succ].get('type', 'unknown')}: {succ} (cycle)[/red]")
                    continue

                # build tree recursively
                build_tree(succ, node_tree, visited.copy())

        # build tree for every root node
        for root in root_nodes:
            tree = Tree(f"{graph.nodes[root].get('type', 'unknown')}: {root}")
            build_tree(root, tree, set())
            console.print(tree)

        # print DAG
        console.print("\n[bold]Graph Statistics:[/bold]")
        console.print(f"Total nodes: {len(graph.nodes)}")
        console.print(f"Total edges: {len(graph.edges)}")
        console.print(f"Service nodes: {len([n for n, d in graph.nodes(data=True) if d.get('type') == 'service'])}")
        console.print(f"Test nodes: {len([n for n, d in graph.nodes(data=True) if d.get('type') == 'test'])}")

        # print statistic
        edge_types = {}
        for _, _, data in graph.edges(data=True):
            edge_type = data.get("type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        console.print("\n[bold]Edge Types:[/bold]")
        for edge_type, count in edge_types.items():
            console.print(f"{edge_type}: {count}")


if __name__ == "__main__":
    """Test cases for DAGManager.

    These tests verify the core functionality of the DAGManager class:
    1. Building correct dependency graph
    2. Detecting cycles
    3. Generating proper execution plans
    """
    import tempfile
    from pathlib import Path

    from octopus.dsl.dsl_config import DslConfig
    from octopus.dsl.dsl_service import DslService
    from octopus.dsl.dsl_test import DslTest

    def create_test_config():
        """Create a test configuration with complex dependencies."""
        config_path = Path(__file__).parent / "test_data" / "config_sample_v0.1.0.yaml"
        config = DslConfig.from_yaml_file(config_path)
        return config

    def test_dag_operations():
        """Test basic DAG operations."""
        config = create_test_config()
        dag_manager = DAGManager(config)

        # Test graph construction
        assert "service_simple" in dag_manager._full_graph.nodes
        assert "test_shell" in dag_manager._full_graph.nodes
        # assert dag_manager.graph.has_edge("service_2", "$service_name")
        assert dag_manager._full_graph.has_edge("service2", "test_http")
        assert dag_manager._full_graph.has_edge("service2", "test_grpc")
        assert dag_manager._full_graph.has_edge("service_simple", "container4test")
        assert not dag_manager._full_graph.has_edge("service_simple", "service_2")  # No reverse edge

        # Test DAG validation
        assert dag_manager.is_valid_dag()

        # Test topological sorting
        order = dag_manager.get_topological_order()
        service_2_index = order.index("service2")
        service_simple_index = order.index("service_simple")
        test_http_index = order.index("test_http")
        assert service_2_index > service_simple_index, "service2 should come before service_simple"
        assert service_simple_index < test_http_index, "service_simple should come before test_shell"

        # Test execution plan
        plan = dag_manager.generate_execution_plan()
        # assert plan["deploy"] == ["service_2", "service_simple", "service_3"], "Deployment order incorrect"
        # assert plan["execute"] == ["test1", "test2"], "Execution order incorrect"
        print(plan)
        print("All basic DAG tests passed!")
        dag_manager.visualize_with_plt()
        dag_manager.visualize_with_rich()
        print("visualize done")

    def test_cycle_detection():
        """Test cycle detection in graph."""
        # Create config with circular dependency
        services = [
            DslService(name="service_1", depends_on=["service_2"], trigger=[]),
            DslService(name="service_2", depends_on=["service_1"], trigger=[]),
        ]

        config = DslConfig(
            version="0.1.0",
            name="cycle_config",
            desc="Configuration with circular dependency",
            services=services,
            tests=[],
        )

        dag_manager = DAGManager(config)
        assert not dag_manager.is_valid_dag(), "Should detect cycle"

        try:
            dag_manager.get_topological_order()
        except ValueError:
            logger.error("Should throw error when getting topological order for cyclic graph")

        print("Cycle detection test passed!")

    def test_missing_dependencies():
        """Test handling of missing dependencies."""
        # Create config with reference to non-existent service
        services = [DslService(name="service_1", depends_on=["non_existent_service"], trigger=["test1"])]

        tests = [DslTest(name="test1", needs=["service_1"])]

        config = DslConfig(
            version="0.1.0",
            name="invalid_config",
            desc="Configuration with invalid references",
            services=services,
            tests=tests,
        )

        dag_manager = DAGManager(config)

        # Should still build graph but log warnings
        assert "service_1" in dag_manager._full_graph.nodes, "Service should be in graph despite missing dependency"
        assert not dag_manager._full_graph.has_edge(
            "non_existent_service", "service_1"
        ), "Should not create edge for missing dependency"

        # Execution plan should fail due to missing dependency
        try:
            dag_manager.generate_execution_plan()
        except ValueError as e:
            assert "missing dependencies" in str(e), "Error message should mention missing dependencies"

        print("Missing dependencies test passed!")

    def test_yaml_based_config():
        """Test DAGManager with config loaded from YAML."""
        # Create test YAML file
        yaml_content = """
        version: "0.1.0"
        name: yaml_config
        desc: Configuration loaded from YAML
        services:
          - name: service_1
            depends_on: [service_2]
            trigger: [test1]
          - name: service_2
            trigger: [test2]
        tests:
          - name: test1
            needs: [service_1]
          - name: test2
            needs: [service_2]
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_yaml_path = f.name

        # Load config from YAML
        config = DslConfig.from_yaml_file(Path(temp_yaml_path))

        # Clean up temporary file
        import os

        os.unlink(temp_yaml_path)

        # Create DAG manager
        dag_manager = DAGManager(config)

        # Verify graph structure
        assert "service_1" in dag_manager._full_graph.nodes
        assert "service_2" in dag_manager._full_graph.nodes
        assert "test1" in dag_manager._full_graph.nodes
        assert "test2" in dag_manager._full_graph.nodes
        assert dag_manager._full_graph.has_edge("service_2", "service_1")
        assert dag_manager._full_graph.has_edge("service_1", "test1")
        assert dag_manager._full_graph.has_edge("service_2", "test2")

        # Test execution plan
        plan = dag_manager.generate_execution_plan()
        assert plan["deploy"] == ["service_2", "service_1"], "Deployment order incorrect"
        assert plan["execute"] == ["test2", "test1"], "Execution order incorrect"

        print("YAML-based config test passed!")

    # Run tests
    test_dag_operations()
    # test_cycle_detection()
    # test_missing_dependencies()
    # test_yaml_based_config()
