from __future__ import annotations

"""
Diagram Service
Generates architecture and code diagrams in multiple formats
"""

import base64
import json
import logging
import re
import urllib.parse
import urllib.request
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Import OpenAI service for AI-powered diagram generation
try:
    from utils.openai_service import OpenAIService

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI service not available - AI diagram generation disabled")


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

    def __init__(self, output_dir: str | None = None):
        """
        Initialize diagram service

        Args:
            output_dir: Directory to save diagram files (optional)
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("📊 DiagramService initialized")

    def generate_flowchart(
        self, nodes: list[dict[str, str]], format: DiagramFormat = DiagramFormat.MERMAID
    ) -> str:
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
            logger.warning(
                f"Format {format} not supported for flowcharts, using Mermaid"
            )
            return self._generate_mermaid_flowchart(nodes)

    def generate_dependency_graph(self, import_graph: dict[str, Any]) -> str:
        """Generate dependency graph from import graph"""
        # Simple implementation for now
        logger.info("Generating dependency graph")
        return "```mermaid\ngraph TB\n    A[Module] --> B[Dependencies]\n```"

    def generate_state_diagram(self, states: dict[str, Any]) -> str:
        """Generate state diagram"""
        # Simple implementation for now
        logger.info("Generating state diagram")
        return "```mermaid\nstateDiagram-v2\n    [*] --> Idle\n    Idle --> Processing\n    Processing --> Complete\n    Complete --> [*]\n```"

    def generate_sequence_diagram(
        self,
        interactions: list[dict[str, str]],
        format: DiagramFormat = DiagramFormat.MERMAID,
    ) -> str:
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
            logger.warning(
                f"Format {format} not supported for sequence diagrams, using Mermaid"
            )
            return self._generate_mermaid_sequence(interactions)

    def generate_class_diagram(
        self,
        classes: list[dict[str, Any]],
        format: DiagramFormat = DiagramFormat.MERMAID,
    ) -> str:
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
            logger.warning(
                f"Format {format} not supported for class diagrams, using Mermaid"
            )
            return self._generate_mermaid_class(classes)

    def generate_architecture_diagram(
        self,
        components: list[dict[str, Any]],
        format: DiagramFormat = DiagramFormat.MERMAID,
    ) -> str:
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
            logger.warning(
                f"Format {format} not supported for architecture diagrams, using Mermaid"
            )
            return self._generate_mermaid_architecture(components)

    def _generate_mermaid_flowchart(self, nodes: list[dict[str, str]]) -> str:
        """Generate Mermaid flowchart"""
        lines = ["```mermaid", "flowchart TD"]

        for node in nodes:
            node_id = node.get("id", "")
            label = node.get("label", "")
            node_type = node.get("type", "process")

            # Different shapes for different node types
            if node_type == "start":
                lines.append(f"    {node_id}([{label}])")
            elif node_type == "end":
                lines.append(f"    {node_id}([{label}])")
            elif node_type == "decision":
                lines.append(f"    {node_id}{{{label}}}")
            else:
                lines.append(f"    {node_id}[{label}]")

            # Add connections if specified
            if "next" in node:
                lines.append(f"    {node_id} --> {node['next']}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_mermaid_sequence(self, interactions: list[dict[str, str]]) -> str:
        """Generate Mermaid sequence diagram"""
        lines = ["```mermaid", "sequenceDiagram"]

        for interaction in interactions:
            from_actor = interaction.get("from", "")
            to_actor = interaction.get("to", "")
            message = interaction.get("message", "")

            lines.append(f"    {from_actor}->>+{to_actor}: {message}")

            if "response" in interaction:
                lines.append(
                    f"    {to_actor}-->>-{from_actor}: {interaction['response']}"
                )

        lines.append("```")
        return "\n".join(lines)

    def _generate_mermaid_class(self, classes: list[dict[str, Any]]) -> str:
        """Generate Mermaid class diagram"""
        lines = ["```mermaid", "classDiagram"]

        for cls in classes:
            class_name = cls.get("name", "")
            lines.append(f"    class {class_name} {{")

            # Add attributes
            for attr in cls.get("attributes", []):
                lines.append(f"        {attr}")

            # Add methods
            for method in cls.get("methods", []):
                lines.append(f"        {method}()")

            lines.append("    }")

            # Add relationships
            for rel in cls.get("relationships", []):
                rel_type = rel.get("type", "association")
                target = rel.get("target", "")

                if rel_type == "inheritance":
                    lines.append(f"    {target} <|-- {class_name}")
                elif rel_type == "composition":
                    lines.append(f"    {class_name} *-- {target}")
                else:
                    lines.append(f"    {class_name} --> {target}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_mermaid_architecture(self, components: list[dict[str, Any]]) -> str:
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
            comp_id = comp.get("id", comp.get("name", "").replace(" ", "_"))
            comp_name = comp.get("name", "")
            comp_type = comp.get("type", "service")

            if comp_type == "database":
                lines.append(f"    {comp_id}[({comp_name})]")
            elif comp_type == "external":
                lines.append(f"    {comp_id}>{comp_name}]")
            else:
                lines.append(f"    {comp_id}[{comp_name}]")

        # Add connections
        for comp in components:
            if isinstance(comp, str):
                continue  # Skip string components
            comp_id = comp.get("id", comp.get("name", "").replace(" ", "_"))

            for conn in comp.get("connections", []):
                target = conn if isinstance(conn, str) else conn.get("target", "")
                label = conn.get("label", "") if isinstance(conn, dict) else ""

                if label:
                    lines.append(f"    {comp_id} -->|{label}| {target}")
                else:
                    lines.append(f"    {comp_id} --> {target}")

        lines.append("```")
        return "\n".join(lines)

    def _generate_ascii_flowchart(self, nodes: list[dict[str, str]]) -> str:
        """Generate simple ASCII flowchart"""
        lines = []

        for i, node in enumerate(nodes):
            label = node.get("label", "")
            node_type = node.get("type", "process")

            # Simple box representation
            box_width = len(label) + 4
            if node_type == "decision":
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

    def save_diagram(self, diagram: str, filename: str) -> Path | None:
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
            with open(output_path, "w") as f:
                f.write(diagram)

            logger.info(f"📊 Diagram saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save diagram: {e}")
            return None

    def _validate_mermaid(self, mermaid_code: str) -> bool:
        """
        Validate Mermaid diagram syntax (basic validation)

        Checks:
        - Has diagram type declaration (graph/flowchart/sequenceDiagram/etc.)
        - No empty content
        - No duplicate backtick wrappers
        - Basic syntax structure

        Returns:
            True if valid, False otherwise
        """
        if not mermaid_code or not mermaid_code.strip():
            logger.error("Mermaid validation failed: Empty code")
            return False

        # Remove backticks if present (for validation)
        code = mermaid_code.strip()
        if code.startswith("```"):
            code = re.sub(r"^```mermaid\s*\n", "", code)
            code = re.sub(r"\n```\s*$", "", code)

        # Check for diagram type
        diagram_types = [
            "graph TB",
            "graph TD",
            "graph LR",
            "graph RL",
            "flowchart TB",
            "flowchart TD",
            "flowchart LR",
            "sequenceDiagram",
            "classDiagram",
            "stateDiagram",
            "erDiagram",
            "gantt",
            "pie",
            "journey",
        ]

        has_type = any(dtype in code for dtype in diagram_types)
        if not has_type:
            logger.error(
                f"Mermaid validation failed: No diagram type found. Code: {code[:100]}"
            )
            return False

        # Check for minimal content (more than just the type declaration)
        lines = [l.strip() for l in code.split("\n") if l.strip()]
        if len(lines) < 2:
            logger.error(
                "Mermaid validation failed: Too few lines (need content after type)"
            )
            return False

        # Check for double backtick wrappers (error in generation)
        if code.count("```") >= 2:
            logger.error("Mermaid validation failed: Double backtick wrappers detected")
            return False

        logger.info("✅ Mermaid syntax validation passed")
        return True

    async def generate_architecture_diagram_ai(
        self, code_index: dict[str, Any], diagram_type: str = "container"
    ) -> str:
        """
        Generate Mermaid architecture diagram using GPT-4o (v5.8.2)

        AI-powered generation creates meaningful, project-specific diagrams
        instead of hardcoded templates.

        Args:
            code_index: Complete code index from ArchitectAgent
            diagram_type: Type of C4 diagram ('context', 'container', 'component')

        Returns:
            Mermaid diagram code (with ```mermaid wrapper)
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - falling back to template")
            return self._fallback_diagram_template(diagram_type)

        try:
            # Prepare code structure summary for AI
            structure_summary = {
                "total_files": len(code_index.get("files", [])),
                "modules": list(code_index.get("modules", {}).keys())[
                    :20
                ],  # Limit to 20
                "api_endpoints": code_index.get("api_endpoints", [])[
                    :15
                ],  # Limit to 15
                "agents": code_index.get("agents", []),
                "services": code_index.get("services", []),
                "tech_stack": code_index.get("tech_stack", {}),
                "main_components": code_index.get("components", []),
            }

            # Build AI prompt based on diagram type
            if diagram_type == "context":
                prompt_template = """Generate a Mermaid C4 Context diagram for this system.

System Info:
{system_info}

Requirements:
1. Show the system as the center
2. Show external users/systems interacting with it
3. Use simple boxes and arrows
4. Include technology labels where relevant
5. Use Mermaid graph TB syntax

Return ONLY the Mermaid code (no ```mermaid wrapper, no explanations):"""

            elif diagram_type == "component":
                prompt_template = """Generate a Mermaid Component diagram for this system.

System Info:
{system_info}

Requirements:
1. Show internal components and their relationships
2. Group related components in subgraphs if applicable
3. Show data flow between components
4. Use descriptive labels
5. Use Mermaid graph TB syntax

Return ONLY the Mermaid code (no ```mermaid wrapper, no explanations):"""

            else:  # container (default)
                prompt_template = """Generate a Mermaid Container diagram for this system.

System Info:
{system_info}

Requirements:
1. Show main containers: VS Code Extension, Backend (FastAPI), Agents, Services, Database
2. Show WebSocket connections (Extension ↔ Backend)
3. Show Agent orchestration flow
4. Show data persistence (Redis/SQLite)
5. Use Mermaid graph TB syntax with descriptive labels

Return ONLY the Mermaid code (no ```mermaid wrapper, no explanations):"""

            # Format system info
            system_info_text = json.dumps(structure_summary, indent=2)
            full_prompt = prompt_template.format(system_info=system_info_text)

            # Call GPT-4o
            openai_service = OpenAIService(model="gpt-4o")
            logger.info(f"🤖 Generating {diagram_type} diagram with GPT-4o...")

            response = await openai_service.get_completion(
                system_prompt="You are an expert at creating Mermaid diagrams. Generate ONLY valid Mermaid syntax, no explanations.",
                user_prompt=full_prompt,
                temperature=0.3,  # Lower temperature for consistent syntax
            )

            # Validate Mermaid syntax
            if not self._validate_mermaid(response):
                logger.error("AI-generated Mermaid failed validation - using fallback")
                return self._fallback_diagram_template(diagram_type)

            # Wrap in mermaid code block
            mermaid_code = f"```mermaid\n{response.strip()}\n```"

            logger.info(f"✅ AI-generated {diagram_type} diagram created")
            return mermaid_code

        except Exception as e:
            logger.error(f"AI diagram generation failed: {e}")
            return self._fallback_diagram_template(diagram_type)

    def mermaid_to_svg(self, mermaid_code: str) -> str | None:
        """
        Convert Mermaid diagram to SVG using mermaid.ink API (v5.8.7)

        Args:
            mermaid_code: Mermaid diagram code (with or without ```mermaid wrapper)

        Returns:
            SVG string or None if conversion fails
        """
        try:
            # Remove ```mermaid wrapper if present
            code = mermaid_code.strip()
            if code.startswith("```mermaid"):
                code = re.sub(r"^```mermaid\s*\n", "", code)
                code = re.sub(r"\n```\s*$", "", code)

            # Encode mermaid code to base64
            encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("utf-8")

            # Use mermaid.ink API
            url = f"https://mermaid.ink/svg/{encoded}"

            logger.info("🎨 Converting Mermaid to SVG via mermaid.ink...")

            # Fetch SVG
            request = urllib.request.Request(url)
            request.add_header("User-Agent", "KI-AutoAgent/5.8.7")

            with urllib.request.urlopen(request, timeout=10) as response:
                svg_content = response.read().decode("utf-8")

            if svg_content and "<svg" in svg_content:
                logger.info("✅ Mermaid converted to SVG successfully")
                return svg_content
            else:
                logger.warning("⚠️ Mermaid.ink returned invalid SVG")
                return None

        except urllib.error.HTTPError as e:
            logger.error(f"❌ Mermaid.ink API error: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"❌ Network error converting Mermaid to SVG: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to convert Mermaid to SVG: {e}")
            return None

    def render_mermaid_for_chat(
        self, mermaid_code: str, fallback_to_code: bool = True
    ) -> str:
        """
        Render Mermaid diagram for chat display (v5.8.7)

        Converts Mermaid to inline SVG data URI for rendering in chat.
        Falls back to code block if conversion fails.

        Args:
            mermaid_code: Mermaid diagram code
            fallback_to_code: If True, return original code block on failure

        Returns:
            Inline SVG data URI or original mermaid code block
        """
        svg = self.mermaid_to_svg(mermaid_code)

        if svg:
            # Create inline SVG data URI for embedding in markdown
            # Use HTML img tag with data URI (works in VS Code webviews)
            svg_b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
            data_uri = f"data:image/svg+xml;base64,{svg_b64}"

            # Return as markdown image with fallback text
            return f"![Architecture Diagram]({data_uri})\n\n<details><summary>View Mermaid Source</summary>\n\n{mermaid_code}\n\n</details>"
        else:
            logger.warning("⚠️ SVG conversion failed - using mermaid code block")
            if fallback_to_code:
                return mermaid_code
            else:
                return "<!-- Diagram rendering failed -->"

    def _fallback_diagram_template(self, diagram_type: str) -> str:
        """
        Fallback to template when AI generation fails

        Returns:
            Basic Mermaid diagram template
        """
        logger.info(f"Using fallback template for {diagram_type} diagram")

        if diagram_type == "context":
            return """```mermaid
graph TB
    User[User/Developer]
    System[KI AutoAgent System]
    VSCode[VS Code]

    User --> VSCode
    VSCode --> System
    System --> User
```"""

        elif diagram_type == "component":
            return """```mermaid
graph TB
    UI[UI Layer]
    API[API Layer]
    Business[Business Logic]
    Data[Data Layer]

    UI --> API
    API --> Business
    Business --> Data
```"""

        else:  # container (default)
            return """```mermaid
graph TB
    VSCode[VS Code Extension<br/>TypeScript]
    Backend[Backend API<br/>FastAPI/Python]
    Agents[Agent System<br/>LangGraph]
    Redis[(Redis Cache)]

    VSCode -->|WebSocket| Backend
    Backend --> Agents
    Agents --> Redis
    Backend --> Redis
```"""
