"""
Diagram Service
Generates architecture and code diagrams in multiple formats
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DiagramFormat(Enum):
    """Supported diagram formats"""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    ASCII = "ascii"
    GRAPHVIZ = "graphviz"


class DiagramType(Enum):
    """Types of diagrams"""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    ER = "er"  # Entity-Relationship
    COMPONENT = "component"
    ARCHITECTURE = "architecture"


class DiagramService:
    """
    Service for generating various types of diagrams
    Supports text-based diagram formats (Mermaid, PlantUML, ASCII)
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize diagram service

        Args:
            output_dir: Directory to save diagram files (optional)
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📊 DiagramService initialized")

    def generate_flowchart(self, nodes: List[Dict[str, str]],
                          format: DiagramFormat = DiagramFormat.MERMAID) -> str:
        """
        Generate flowchart diagram

        Args:
            nodes: List of nodes with 'id', 'label', 'type' keys
            format: Output format

        Returns:
            Diagram as text
        """
        if format == DiagramFormat.MERMAID:
            return self._generate_mermaid_flowchart(nodes)
        elif format == DiagramFormat.ASCII:
            return self._generate_ascii_flowchart(nodes)
        else:
            logger.warning(f"Format {format} not supported for flowcharts, using Mermaid")
            return self._generate_mermaid_flowchart(nodes)

    def generate_dependency_graph(self, import_graph: Dict[str, Any]) -> str:
        """Generate dependency graph from import graph"""
        # Simple implementation for now
        logger.info("Generating dependency graph")
        return "```mermaid\ngraph TB\n    A[Module] --> B[Dependencies]\n```"

    def generate_state_diagram(self, states: Dict[str, Any]) -> str:
        """Generate state diagram"""
        # Simple implementation for now
        logger.info("Generating state diagram")
        return "```mermaid\nstateDiagram-v2\n    [*] --> Idle\n    Idle --> Processing\n    Processing --> Complete\n    Complete --> [*]\n```"

    def generate_sequence_diagram(self, interactions: List[Dict[str, str]],
                                 format: DiagramFormat = DiagramFormat.MERMAID) -> str:
        """
        Generate sequence diagram

        Args:
            interactions: List of interactions with 'from', 'to', 'message' keys
            format: Output format

        Returns:
            Diagram as text
        """
        if format == DiagramFormat.MERMAID:
            return self._generate_mermaid_sequence(interactions)
        else:
            logger.warning(f"Format {format} not supported for sequence diagrams, using Mermaid")
            return self._generate_mermaid_sequence(interactions)

    def generate_class_diagram(self, classes: List[Dict[str, Any]],
                              format: DiagramFormat = DiagramFormat.MERMAID) -> str:
        """
        Generate class diagram

        Args:
            classes: List of classes with 'name', 'attributes', 'methods' keys
            format: Output format

        Returns:
            Diagram as text
        """
        if format == DiagramFormat.MERMAID:
            return self._generate_mermaid_class(classes)
        else:
            logger.warning(f"Format {format} not supported for class diagrams, using Mermaid")
            return self._generate_mermaid_class(classes)

    def generate_architecture_diagram(self, components: List[Dict[str, Any]],
                                     format: DiagramFormat = DiagramFormat.MERMAID) -> str:
        """
        Generate architecture/component diagram

        Args:
            components: List of components with 'name', 'type', 'connections' keys
            format: Output format

        Returns:
            Diagram as text
        """
        if format == DiagramFormat.MERMAID:
            return self._generate_mermaid_architecture(components)
        else:
            logger.warning(f"Format {format} not supported for architecture diagrams, using Mermaid")
            return self._generate_mermaid_architecture(components)

    def _generate_mermaid_flowchart(self, nodes: List[Dict[str, str]]) -> str:
        """Generate Mermaid flowchart"""
        lines = ["```mermaid", "flowchart TD"]

        for node in nodes:
            node_id = node.get('id', '')
            label = node.get('label', '')
            node_type = node.get('type', 'process')

            # Different shapes for different node types
            if node_type == 'start':
                lines.append(f"    {node_id}([{label}])")
            elif node_type == 'end':
                lines.append(f"    {node_id}([{label}])")
            elif node_type == 'decision':
                lines.append(f"    {node_id}{{{label}}}")
            else:
                lines.append(f"    {node_id}[{label}]")

            # Add connections if specified
            if 'next' in node:
                lines.append(f"    {node_id} --> {node['next']}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_mermaid_sequence(self, interactions: List[Dict[str, str]]) -> str:
        """Generate Mermaid sequence diagram"""
        lines = ["```mermaid", "sequenceDiagram"]

        for interaction in interactions:
            from_actor = interaction.get('from', '')
            to_actor = interaction.get('to', '')
            message = interaction.get('message', '')

            lines.append(f"    {from_actor}->>+{to_actor}: {message}")

            if 'response' in interaction:
                lines.append(f"    {to_actor}-->>-{from_actor}: {interaction['response']}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_mermaid_class(self, classes: List[Dict[str, Any]]) -> str:
        """Generate Mermaid class diagram"""
        lines = ["```mermaid", "classDiagram"]

        for cls in classes:
            class_name = cls.get('name', '')
            lines.append(f"    class {class_name} {{")

            # Add attributes
            for attr in cls.get('attributes', []):
                lines.append(f"        {attr}")

            # Add methods
            for method in cls.get('methods', []):
                lines.append(f"        {method}()")

            lines.append("    }")

            # Add relationships
            for rel in cls.get('relationships', []):
                rel_type = rel.get('type', 'association')
                target = rel.get('target', '')

                if rel_type == 'inheritance':
                    lines.append(f"    {target} <|-- {class_name}")
                elif rel_type == 'composition':
                    lines.append(f"    {class_name} *-- {target}")
                else:
                    lines.append(f"    {class_name} --> {target}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_mermaid_architecture(self, components: List[Dict[str, Any]]) -> str:
        """Generate Mermaid architecture diagram"""
        lines = ["```mermaid", "graph TB"]

        # Handle case where components might be a string or empty
        if isinstance(components, str):
            logger.warning(f"Components is a string, not a list: {components[:100]}")
            return "```mermaid\ngraph TB\n    A[System] --> B[Not Available]\n```"
        if not components:
            logger.warning("No components provided for architecture diagram")
            return "```mermaid\ngraph TB\n    A[System] --> B[Components]\n```"

        # Define components
        for comp in components:
            # Handle case where comp might be a string
            if isinstance(comp, str):
                logger.warning(f"Component is a string: {comp}")
                continue
            comp_id = comp.get('id', comp.get('name', '').replace(' ', '_'))
            comp_name = comp.get('name', '')
            comp_type = comp.get('type', 'service')

            if comp_type == 'database':
                lines.append(f"    {comp_id}[({comp_name})]")
            elif comp_type == 'external':
                lines.append(f"    {comp_id}>{comp_name}]")
            else:
                lines.append(f"    {comp_id}[{comp_name}]")

        # Add connections
        for comp in components:
            if isinstance(comp, str):
                continue  # Skip string components
            comp_id = comp.get('id', comp.get('name', '').replace(' ', '_'))

            for conn in comp.get('connections', []):
                target = conn if isinstance(conn, str) else conn.get('target', '')
                label = conn.get('label', '') if isinstance(conn, dict) else ''

                if label:
                    lines.append(f"    {comp_id} -->|{label}| {target}")
                else:
                    lines.append(f"    {comp_id} --> {target}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_ascii_flowchart(self, nodes: List[Dict[str, str]]) -> str:
        """Generate simple ASCII flowchart"""
        lines = []

        for i, node in enumerate(nodes):
            label = node.get('label', '')
            node_type = node.get('type', 'process')

            # Simple box representation
            box_width = len(label) + 4
            if node_type == 'decision':
                lines.append(f"    /{'-' * (box_width - 2)}\\")
                lines.append(f"   | {label} |")
                lines.append(f"    \\{'-' * (box_width - 2)}/")
            else:
                lines.append(f"   +{'-' * (box_width - 2)}+")
                lines.append(f"   | {label} |")
                lines.append(f"   +{'-' * (box_width - 2)}+")

            # Add connector if not last node
            if i < len(nodes) - 1:
                lines.append("       |")
                lines.append("       v")

        return "\n".join(lines)

    def save_diagram(self, diagram: str, filename: str) -> Optional[Path]:
        """
        Save diagram to file

        Args:
            diagram: Diagram text
            filename: Output filename

        Returns:
            Path to saved file or None
        """
        if not self.output_dir:
            logger.warning("No output directory configured")
            return None

        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w') as f:
                f.write(diagram)

            logger.info(f"📊 Diagram saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save diagram: {e}")
            return None
