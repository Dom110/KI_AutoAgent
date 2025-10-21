"""
Architect Agent - System Design Specialist for v7.0

This agent designs system architecture based on research context.
It can request additional research when needed.

Key Responsibilities:
- Design system architecture
- Create file structures
- Select appropriate technologies
- Document design decisions
- Request research when context is insufficient

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)


class ArchitectAgent:
    """
    System architect that designs based on research context.

    This agent creates comprehensive system designs but can
    request additional research through the supervisor when
    the context is insufficient.
    """

    def __init__(self):
        """Initialize the Architect agent."""
        logger.info("📐 ArchitectAgent initialized")

        # Initialize OpenAI service for architecture generation
        self.openai_service = None
        try:
            from backend.utils.openai_service import OpenAIService
            self.openai_service = OpenAIService(model="gpt-4o-2024-11-20")
            logger.info("   ✅ OpenAI service connected")
        except Exception as e:
            logger.warning(f"   ⚠️ OpenAI service not available: {e}")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute architecture design based on supervisor instructions.

        Args:
            state: Contains:
                - instructions: What to design
                - research_context: Context from Research agent
                - workspace_path: Target workspace

        Returns:
            Dictionary with architecture or research request
        """
        instructions = state.get("instructions", "")
        research_context = state.get("research_context", {})
        workspace_path = state.get("workspace_path", "")

        logger.info(f"🏗️ Designing architecture: {instructions[:100]}...")

        # Check if we have sufficient context
        if self._needs_more_research(instructions, research_context):
            logger.info("   📚 Requesting additional research")
            return {
                "needs_research": True,
                "research_request": self._formulate_research_request(instructions, research_context),
                "architecture_complete": False
            }

        # Design the architecture
        architecture = await self._design_architecture(
            instructions,
            research_context,
            workspace_path
        )

        logger.info(f"   ✅ Architecture designed: {len(architecture.get('components', []))} components")

        return {
            "architecture": architecture,
            "architecture_complete": True,
            "needs_research": False,
            "timestamp": datetime.now().isoformat()
        }

    def _needs_more_research(
        self,
        instructions: str,
        research_context: dict
    ) -> bool:
        """
        Determine if more research is needed before design.

        This implements the research request mechanism where
        agents can ask for additional context.
        """
        # Check if we have any research context
        if not research_context:
            return True

        # Check for specific missing information
        workspace_analysis = research_context.get("workspace_analysis", {})

        # Need workspace analysis for existing project modifications
        if "modify" in instructions.lower() or "refactor" in instructions.lower():
            if not workspace_analysis or workspace_analysis.get("file_count", 0) == 0:
                return True

        # Need technology verification for specific tech mentions
        if "fastapi" in instructions.lower() or "django" in instructions.lower():
            tech_verification = research_context.get("tech_verification", {})
            if not tech_verification:
                return True

        # Need security analysis for security-related tasks
        if "security" in instructions.lower() or "authentication" in instructions.lower():
            security_analysis = research_context.get("security_analysis", {})
            if not security_analysis:
                return True

        return False

    def _formulate_research_request(
        self,
        instructions: str,
        research_context: dict
    ) -> str:
        """
        Formulate specific research request based on what's missing.
        """
        requests = []

        if not research_context:
            requests.append("Analyze workspace structure and existing code")

        if "modify" in instructions.lower() and "workspace_analysis" not in research_context:
            requests.append("Analyze existing project structure and dependencies")

        if "fastapi" in instructions.lower() and "tech_verification" not in research_context:
            requests.append("Research FastAPI best practices and patterns")

        if "security" in instructions.lower() and "security_analysis" not in research_context:
            requests.append("Research security best practices for the requested features")

        return " AND ".join(requests) if requests else "Gather more context for architecture design"

    async def _design_architecture(
        self,
        instructions: str,
        research_context: dict,
        workspace_path: str
    ) -> dict[str, Any]:
        """
        Design the system architecture based on context.
        """
        logger.info("   🎨 Creating architecture design")

        architecture = {
            "description": "",
            "components": [],
            "file_structure": [],
            "technologies": [],
            "patterns": [],
            "data_flow": [],
            "created_at": datetime.now().isoformat()
        }

        # Extract insights from research context
        workspace_analysis = research_context.get("workspace_analysis", {})
        web_results = research_context.get("web_results", [])
        tech_verification = research_context.get("tech_verification", {})

        # Use OpenAI to generate architecture if available
        if self.openai_service:
            architecture = await self._generate_with_ai(
                instructions,
                research_context,
                workspace_analysis
            )
        else:
            # Fallback to rule-based architecture
            architecture = self._generate_rule_based(
                instructions,
                workspace_analysis
            )

        # Add workspace-specific adjustments
        if workspace_analysis:
            architecture = self._adjust_for_workspace(
                architecture,
                workspace_analysis
            )

        return architecture

    async def _generate_with_ai(
        self,
        instructions: str,
        research_context: dict,
        workspace_analysis: dict
    ) -> dict[str, Any]:
        """
        Generate architecture using OpenAI GPT-4o.
        """
        prompt = f"""Design a system architecture based on the following:

Instructions: {instructions}

Workspace Context:
- Project Type: {workspace_analysis.get('project_type', 'Unknown')}
- Languages: {', '.join(workspace_analysis.get('languages', []))}
- Existing Files: {workspace_analysis.get('file_count', 0)}
- Has Tests: {workspace_analysis.get('has_tests', False)}

Research Context:
{json.dumps(research_context, indent=2)[:1000]}  # Truncate for token limits

Please provide a comprehensive architecture with:
1. Overall system description
2. Core components and their responsibilities
3. File structure
4. Technology stack
5. Design patterns to use
6. Data flow between components

Format as JSON with these keys: description, components, file_structure, technologies, patterns, data_flow"""

        try:
            response = await self.openai_service.complete(prompt)
            # Parse response as JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            else:
                json_str = response

            architecture = json.loads(json_str)
            return architecture

        except Exception as e:
            logger.error(f"   ❌ AI generation error: {e}")
            # Fallback to rule-based
            return self._generate_rule_based(instructions, workspace_analysis)

    def _generate_rule_based(
        self,
        instructions: str,
        workspace_analysis: dict
    ) -> dict[str, Any]:
        """
        Generate architecture using rule-based approach.
        """
        logger.info("   📏 Using rule-based architecture generation")

        architecture = {
            "description": f"Architecture for: {instructions[:100]}",
            "components": [],
            "file_structure": [],
            "technologies": [],
            "patterns": ["MVC", "Repository Pattern", "Dependency Injection"],
            "data_flow": []
        }

        # Determine architecture based on keywords
        instructions_lower = instructions.lower()

        if "api" in instructions_lower or "fastapi" in instructions_lower:
            architecture["components"] = [
                {"name": "API Gateway", "description": "Handles HTTP requests and routing"},
                {"name": "Controllers", "description": "Request handlers and validation"},
                {"name": "Services", "description": "Business logic implementation"},
                {"name": "Repositories", "description": "Data access layer"},
                {"name": "Models", "description": "Data models and schemas"}
            ]
            architecture["file_structure"] = [
                "app/",
                "app/api/",
                "app/api/endpoints/",
                "app/core/",
                "app/core/config.py",
                "app/models/",
                "app/services/",
                "app/repositories/",
                "tests/",
                "requirements.txt"
            ]
            architecture["technologies"] = ["FastAPI", "Pydantic", "SQLAlchemy", "PostgreSQL"]

        elif "frontend" in instructions_lower or "react" in instructions_lower:
            architecture["components"] = [
                {"name": "Components", "description": "Reusable UI components"},
                {"name": "Pages", "description": "Route-level components"},
                {"name": "Services", "description": "API communication layer"},
                {"name": "Store", "description": "State management"},
                {"name": "Utils", "description": "Helper functions"}
            ]
            architecture["file_structure"] = [
                "src/",
                "src/components/",
                "src/pages/",
                "src/services/",
                "src/store/",
                "src/utils/",
                "public/",
                "package.json"
            ]
            architecture["technologies"] = ["React", "TypeScript", "Redux", "Axios"]

        elif "microservice" in instructions_lower:
            architecture["components"] = [
                {"name": "API Gateway", "description": "Entry point for all services"},
                {"name": "Auth Service", "description": "Authentication and authorization"},
                {"name": "User Service", "description": "User management"},
                {"name": "Data Service", "description": "Data operations"},
                {"name": "Message Queue", "description": "Async communication"}
            ]
            architecture["file_structure"] = [
                "services/",
                "services/gateway/",
                "services/auth/",
                "services/users/",
                "services/data/",
                "docker-compose.yml",
                "kubernetes/"
            ]
            architecture["technologies"] = ["Docker", "Kubernetes", "RabbitMQ", "Redis"]

        else:
            # Generic architecture
            architecture["components"] = [
                {"name": "Main Module", "description": "Core application logic"},
                {"name": "Utils", "description": "Helper functions"},
                {"name": "Config", "description": "Configuration management"},
                {"name": "Tests", "description": "Test suite"}
            ]
            architecture["file_structure"] = [
                "src/",
                "src/main.py",
                "src/utils/",
                "src/config/",
                "tests/",
                "README.md"
            ]
            architecture["technologies"] = ["Python", "pytest"]

        # Add data flow
        if architecture["components"]:
            for i in range(len(architecture["components"]) - 1):
                architecture["data_flow"].append({
                    "from": architecture["components"][i]["name"],
                    "to": architecture["components"][i + 1]["name"],
                    "description": "Data flow"
                })

        return architecture

    def _adjust_for_workspace(
        self,
        architecture: dict,
        workspace_analysis: dict
    ) -> dict:
        """
        Adjust architecture based on existing workspace.
        """
        if not workspace_analysis:
            return architecture

        # If workspace already has structure, preserve it
        if workspace_analysis.get("file_count", 0) > 10:
            architecture["description"] += "\n\nNote: Architecture adjusted to fit existing project structure"

        # Add detected frameworks
        existing_frameworks = workspace_analysis.get("frameworks", [])
        if existing_frameworks:
            architecture["technologies"].extend(existing_frameworks)
            architecture["technologies"] = list(set(architecture["technologies"]))

        # Adjust for test presence
        if workspace_analysis.get("has_tests"):
            # Ensure test directory is in file structure
            if not any("test" in str(f).lower() for f in architecture["file_structure"]):
                architecture["file_structure"].append("tests/")

        return architecture


# ============================================================================
# Export
# ============================================================================

__all__ = ["ArchitectAgent"]