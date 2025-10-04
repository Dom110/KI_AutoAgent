"""
Dynamic Workflow Manager for runtime graph modification
Allows adding/removing nodes and edges at runtime
"""

import logging
from typing import Dict, List, Callable, Any, Optional, Literal
from dataclasses import dataclass
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


@dataclass
class DynamicNode:
    """Represents a dynamic node that can be added at runtime"""
    name: str
    func: Callable
    node_type: Literal["standard", "conditional", "tool"]
    description: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class DynamicEdge:
    """Represents a dynamic edge between nodes"""
    source: str
    target: str
    condition: Optional[Callable] = None
    metadata: Dict[str, Any] = None


@dataclass
class ConditionalRoute:
    """Represents conditional routing logic"""
    source: str
    condition: Callable
    routes: Dict[str, str]
    metadata: Dict[str, Any] = None


class DynamicWorkflowManager:
    """
    Manages dynamic modifications to LangGraph workflows
    Allows runtime changes to graph structure
    """

    def __init__(self, base_graph: Optional[StateGraph] = None):
        """
        Initialize with optional base graph

        Args:
            base_graph: Initial StateGraph to build upon
        """
        self.base_graph = base_graph
        self.base_nodes: Dict[str, Callable] = {}
        self.base_edges: List[DynamicEdge] = []

        # Dynamic additions
        self.dynamic_nodes: Dict[str, DynamicNode] = {}
        self.dynamic_edges: List[DynamicEdge] = []
        self.conditional_routes: List[ConditionalRoute] = []

        # Graph versions for rollback
        self.graph_versions: List[Any] = []  # List of compiled graphs
        self.current_version = 0

        # Workflow templates
        self.templates: Dict[str, Dict[str, Any]] = {}

        # Extract base graph structure if provided
        if base_graph:
            self._extract_base_structure()

    def _extract_base_structure(self):
        """Extract nodes and edges from base graph"""
        # Note: This is simplified - actual extraction would depend on LangGraph internals
        logger.info("Extracting base graph structure")
        # Base nodes and edges would be extracted here

    def add_node(
        self,
        name: str,
        func: Callable,
        node_type: Literal["standard", "conditional", "tool"] = "standard",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a new node to the workflow

        Args:
            name: Unique node identifier
            func: Callable function for the node
            node_type: Type of node
            description: Node description
            metadata: Additional metadata

        Returns:
            True if node was added successfully
        """
        if name in self.dynamic_nodes or name in self.base_nodes:
            logger.warning(f"Node '{name}' already exists")
            return False

        node = DynamicNode(
            name=name,
            func=func,
            node_type=node_type,
            description=description,
            metadata=metadata or {}
        )

        self.dynamic_nodes[name] = node
        logger.info(f"Added dynamic node: {name}")
        return True

    def remove_node(self, name: str) -> bool:
        """
        Remove a node from the workflow

        Args:
            name: Node identifier to remove

        Returns:
            True if node was removed successfully
        """
        if name in self.dynamic_nodes:
            del self.dynamic_nodes[name]

            # Remove related edges
            self.dynamic_edges = [
                edge for edge in self.dynamic_edges
                if edge.source != name and edge.target != name
            ]

            # Remove related conditional routes
            self.conditional_routes = [
                route for route in self.conditional_routes
                if route.source != name
            ]

            logger.info(f"Removed dynamic node: {name}")
            return True

        logger.warning(f"Node '{name}' not found in dynamic nodes")
        return False

    def add_edge(
        self,
        source: str,
        target: str,
        condition: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an edge between nodes

        Args:
            source: Source node name
            target: Target node name
            condition: Optional condition function
            metadata: Additional metadata

        Returns:
            True if edge was added successfully
        """
        # Validate nodes exist
        all_nodes = {**self.base_nodes, **self.dynamic_nodes}
        if source not in all_nodes and source != END:
            logger.error(f"Source node '{source}' does not exist")
            return False
        if target not in all_nodes and target != END:
            logger.error(f"Target node '{target}' does not exist")
            return False

        edge = DynamicEdge(
            source=source,
            target=target,
            condition=condition,
            metadata=metadata or {}
        )

        self.dynamic_edges.append(edge)
        logger.info(f"Added edge: {source} -> {target}")
        return True

    def add_conditional_routing(
        self,
        source: str,
        condition: Callable,
        routes: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add conditional routing from a node

        Args:
            source: Source node name
            condition: Function that returns route key
            routes: Mapping of condition results to target nodes
            metadata: Additional metadata

        Returns:
            True if routing was added successfully
        """
        route = ConditionalRoute(
            source=source,
            condition=condition,
            routes=routes,
            metadata=metadata or {}
        )

        self.conditional_routes.append(route)
        logger.info(f"Added conditional routing from: {source}")
        return True

    def compile_graph(self, state_class: type) -> Any:
        """
        Compile the current graph configuration

        Args:
            state_class: State class for the graph

        Returns:
            Compiled graph ready for execution
        """
        graph = StateGraph(state_class)

        # Add base nodes
        for name, func in self.base_nodes.items():
            graph.add_node(name, func)

        # Add dynamic nodes
        for name, node in self.dynamic_nodes.items():
            graph.add_node(name, node.func)

        # Add base edges
        for edge in self.base_edges:
            if edge.condition:
                # This is simplified - actual conditional edge handling needed
                graph.add_edge(edge.source, edge.target)
            else:
                graph.add_edge(edge.source, edge.target)

        # Add dynamic edges
        for edge in self.dynamic_edges:
            if edge.condition:
                # Conditional edge
                graph.add_edge(edge.source, edge.target)
            else:
                graph.add_edge(edge.source, edge.target)

        # Add conditional routes
        for route in self.conditional_routes:
            graph.add_conditional_edges(
                route.source,
                route.condition,
                route.routes
            )

        # Compile the graph
        compiled = graph.compile()

        # Save version for rollback
        self.graph_versions.append(compiled)
        self.current_version = len(self.graph_versions) - 1

        logger.info(f"Compiled graph version {self.current_version}")
        return compiled

    def create_template(
        self,
        name: str,
        nodes: List[DynamicNode],
        edges: List[DynamicEdge],
        routes: Optional[List[ConditionalRoute]] = None,
        description: str = ""
    ) -> bool:
        """
        Create a reusable workflow template

        Args:
            name: Template name
            nodes: List of nodes in template
            edges: List of edges in template
            routes: Optional conditional routes
            description: Template description

        Returns:
            True if template was created successfully
        """
        self.templates[name] = {
            "nodes": nodes,
            "edges": edges,
            "routes": routes or [],
            "description": description
        }

        logger.info(f"Created template: {name}")
        return True

    def apply_template(
        self,
        template_name: str,
        node_prefix: str = "",
        parameter_mapping: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Apply a workflow template

        Args:
            template_name: Name of template to apply
            node_prefix: Prefix for node names to avoid conflicts
            parameter_mapping: Parameter substitutions

        Returns:
            True if template was applied successfully
        """
        if template_name not in self.templates:
            logger.error(f"Template '{template_name}' not found")
            return False

        template = self.templates[template_name]

        # Apply nodes with prefix
        for node in template["nodes"]:
            self.add_node(
                name=f"{node_prefix}{node.name}",
                func=node.func,
                node_type=node.node_type,
                description=node.description,
                metadata=node.metadata
            )

        # Apply edges with prefix
        for edge in template["edges"]:
            self.add_edge(
                source=f"{node_prefix}{edge.source}",
                target=f"{node_prefix}{edge.target}",
                condition=edge.condition,
                metadata=edge.metadata
            )

        # Apply routes with prefix
        for route in template["routes"]:
            prefixed_routes = {
                k: f"{node_prefix}{v}" if v != END else END
                for k, v in route.routes.items()
            }
            self.add_conditional_routing(
                source=f"{node_prefix}{route.source}",
                condition=route.condition,
                routes=prefixed_routes,
                metadata=route.metadata
            )

        logger.info(f"Applied template: {template_name}")
        return True

    def rollback(self, version: Optional[int] = None) -> Optional[Any]:
        """
        Rollback to a previous graph version

        Args:
            version: Version number to rollback to (None for previous)

        Returns:
            Compiled graph at specified version
        """
        if not self.graph_versions:
            logger.warning("No graph versions available for rollback")
            return None

        if version is None:
            # Rollback to previous version
            version = max(0, self.current_version - 1)

        if 0 <= version < len(self.graph_versions):
            self.current_version = version
            logger.info(f"Rolled back to graph version {version}")
            return self.graph_versions[version]

        logger.error(f"Invalid version number: {version}")
        return None

    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about current graph structure"""
        all_nodes = {**self.base_nodes, **self.dynamic_nodes}

        return {
            "total_nodes": len(all_nodes),
            "base_nodes": list(self.base_nodes.keys()),
            "dynamic_nodes": list(self.dynamic_nodes.keys()),
            "total_edges": len(self.base_edges) + len(self.dynamic_edges),
            "conditional_routes": len(self.conditional_routes),
            "templates": list(self.templates.keys()),
            "current_version": self.current_version,
            "total_versions": len(self.graph_versions)
        }

    def visualize_graph(self, format: str = "mermaid") -> str:
        """
        Generate graph visualization

        Args:
            format: Output format (mermaid, dot, etc.)

        Returns:
            Graph visualization string
        """
        if format == "mermaid":
            lines = ["graph TD"]

            # Add nodes
            all_nodes = {**self.base_nodes, **self.dynamic_nodes}
            for name in all_nodes:
                node_type = ""
                if name in self.dynamic_nodes:
                    node = self.dynamic_nodes[name]
                    if node.node_type == "conditional":
                        node_type = "{" + name + "}"
                    elif node.node_type == "tool":
                        node_type = "[" + name + "]"
                    else:
                        node_type = "(" + name + ")"
                else:
                    node_type = "(" + name + ")"
                lines.append(f"    {name}{node_type}")

            # Add edges
            for edge in self.base_edges + self.dynamic_edges:
                if edge.condition:
                    lines.append(f"    {edge.source} -->|condition| {edge.target}")
                else:
                    lines.append(f"    {edge.source} --> {edge.target}")

            # Add conditional routes
            for route in self.conditional_routes:
                for condition_result, target in route.routes.items():
                    lines.append(f"    {route.source} -->|{condition_result}| {target}")

            return "\n".join(lines)

        elif format == "dot":
            lines = ["digraph G {"]

            # Add nodes
            all_nodes = {**self.base_nodes, **self.dynamic_nodes}
            for name in all_nodes:
                shape = "ellipse"
                if name in self.dynamic_nodes:
                    node = self.dynamic_nodes[name]
                    if node.node_type == "conditional":
                        shape = "diamond"
                    elif node.node_type == "tool":
                        shape = "box"
                lines.append(f'    "{name}" [shape={shape}];')

            # Add edges
            for edge in self.base_edges + self.dynamic_edges:
                label = ""
                if edge.condition:
                    label = ' [label="condition"]'
                lines.append(f'    "{edge.source}" -> "{edge.target}"{label};')

            # Add conditional routes
            for route in self.conditional_routes:
                for condition_result, target in route.routes.items():
                    lines.append(f'    "{route.source}" -> "{target}" [label="{condition_result}"];')

            lines.append("}")
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")