import sys
from typing import Protocol, runtime_checkable

import networkx as nx
from loguru import logger

# from octopus.dsl.dsl_config import DslConfig
from octopus.dsl.dsl_service import DslService
from octopus.dsl.dsl_test import DslTest

logger.remove()
logger.add(sys.stdout, level="DEBUG")

ALLOWED_EDGE_TYPES = ["next", "trigger", "depends_on", "needs"]


@runtime_checkable
class ConfigProtocol(Protocol):
    """Duck typing of DslConfig required by DAGManager."""

    @property
    def services(self) -> list[DslService]:
        """Get list of services."""
        ...

    @property
    def tests(self) -> list[DslTest]:
        """Get list of tests."""
        ...

    def is_valid_service(self, service_name: str) -> bool:
        """Check if a service name is valid."""
        ...

    def is_valid_test(self, test_name: str) -> bool:
        """Check if a test name is valid."""
        ...


class DAGManager:
    """A manager class to handle DAG operations for DslConfig.

    Features:
    - Build graph from DslConfig services and tests
    - Check if the graph is a valid DAG (no cycles)
    - Generate topological order of nodes
    - Create execution plan based on dependencies
    - Visualize the dependency graph (optional)
    """

    dsl_config: ConfigProtocol
    _full_graph: nx.Graph
    __edge_types_in_dag: list[str] = ["next", "trigger"]

    def __init__(self, dsl_config: ConfigProtocol):
        """Initialize the DAGManager with a DslConfig instance.

        Args:
            dsl_config: A configuration instance implementing ConfigProtocol
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

    def generate_execution_plan(self) -> list[str]:
        """Generate execution plan based on dependencies.

        The execution plan follows these rules:
        1. Start from root service nodes (service nodes with in_degree == 0)
        2. For each service node:
           - Execute the service
           - Execute all its triggered tests
           - Move to the next service node through 'next' edge
        3. Continue until all nodes are processed

        Returns:
            List of node names in execution order

        Raises:
            ValueError: If the graph is not a valid DAG
        """
        if not self.is_valid_dag():
            raise ValueError("Cannot generate execution plan for a graph with cycles")

        graph = self._gen_subgraph()
        execution_plan = []
        visited = set()

        # Find root service nodes (service nodes with in_degree == 0)
        root_services = [
            node for node in graph.nodes() if graph.nodes[node].get("type") == "service" and graph.in_degree(node) == 0
        ]

        # Process each root service and its chain
        for root in root_services:
            self._process_service_node(graph, root, execution_plan, visited)

        return execution_plan

    def _process_service_node(self, graph, service_node, execution_plan, visited):
        """Process a service node and its triggered tests.

        Args:
            graph: The graph structure
            service_node: The service node to process
            execution_plan: The execution plan being built
            visited: Set of visited nodes
        """
        if service_node in visited:
            return

        # Add service to execution plan
        visited.add(service_node)
        execution_plan.append(service_node)

        # Process triggered tests
        triggered_tests = self._get_triggered_tests(graph, service_node, visited)
        for test in triggered_tests:
            visited.add(test)
            execution_plan.append(test)

        # Process next service
        next_service = self._get_next_service(graph, service_node, visited)
        if next_service:
            self._process_service_node(graph, next_service, execution_plan, visited)

    def _get_triggered_tests(self, graph, service_node, visited):
        """Get all test nodes triggered by a service node.

        Args:
            graph: The graph structure
            service_node: The service node to check
            visited: Set of visited nodes

        Returns:
            List of test nodes triggered by the service
        """
        triggered_tests = []
        for _, test_node in graph.out_edges(service_node):
            if graph.edges[service_node, test_node].get("type") == "trigger" and test_node not in visited:
                triggered_tests.append(test_node)
        return triggered_tests

    def _get_next_service(self, graph, service_node, visited):
        """Get the next service node through 'next' edge.

        Args:
            graph: The graph structure
            service_node: The current service node
            visited: Set of visited nodes

        Returns:
            The next service node, or None if not found
        """
        for _, next_node in graph.out_edges(service_node):
            if graph.edges[service_node, next_node].get("type") == "next" and next_node not in visited:
                return next_node
        return None

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
