"""
Research Agent - Support Agent for Information Gathering in v7.0

This is a SUPPORT agent that gathers context for other agents.
Research NEVER communicates directly with users!

Key Responsibilities:
- Workspace analysis and file discovery
- Web search for best practices
- Error analysis and debugging help
- Technology verification
- Security vulnerability research

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Support agent for information gathering.

    This agent provides research capabilities to other agents
    but NEVER formats responses for users. All user-facing
    responses go through ResponderAgent.
    """

    def __init__(self, workspace_path: str | None = None):
        """
        Initialize the Research agent.

        Args:
            workspace_path: Path to workspace for memory/learning access
        """
        logger.info("🔬 ResearchAgent initialized")

        self.workspace_path = workspace_path
        self.memory_system = None
        self.learning_system = None
        self.global_memory = None

        # Initialize Perplexity service if available
        self.perplexity_service = None
        try:
            from backend.utils.perplexity_service import PerplexityService
            self.perplexity_service = PerplexityService(model="sonar")
            logger.info("   ✅ Perplexity API connected")
        except Exception as e:
            logger.warning(f"   ⚠️ Perplexity API not available: {e}")

        # Initialize Memory System if workspace provided
        if workspace_path:
            self._initialize_memory_system(workspace_path)

        # Initialize Global Memory (optional)
        try:
            from backend.memory.global_memory_system import GlobalMemorySystem
            self.global_memory = GlobalMemorySystem()
            logger.info("   🌍 Global memory available")
        except Exception as e:
            logger.debug(f"   Global memory not available: {e}")

    def _initialize_memory_system(self, workspace_path: str) -> None:
        """Initialize connection to Memory and Learning systems."""
        try:
            from backend.memory.memory_system_v6 import MemorySystem
            from backend.cognitive.learning_system_v6 import LearningSystemV6

            # Note: We'll initialize these lazily when needed to avoid async in __init__
            self.workspace_path = workspace_path
            logger.info(f"   📚 Memory/Learning systems will initialize on first use")
        except Exception as e:
            logger.warning(f"   ⚠️ Memory/Learning systems not available: {e}")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute research based on supervisor instructions.

        Args:
            state: Contains:
                - instructions: What to research
                - workspace_path: Path to analyze
                - error_info: Errors to investigate

        Returns:
            Dictionary with research_context field
        """
        instructions = state.get("instructions", "")
        workspace_path = state.get("workspace_path", "")
        error_info = state.get("error_info", [])

        # Update workspace path if different
        if workspace_path and workspace_path != self.workspace_path:
            self.workspace_path = workspace_path
            self._initialize_memory_system(workspace_path)

        logger.info(f"🔍 Researching: {instructions[:100]}...")

        # Determine research type from instructions
        research_context = {}

        # Workspace analysis
        if "workspace" in instructions.lower() or "analyze" in instructions.lower():
            research_context["workspace_analysis"] = await self._analyze_workspace(
                workspace_path
            )

        # Web search for best practices
        if "best practice" in instructions.lower() or "research" in instructions.lower():
            research_context["web_results"] = await self._search_web(instructions)

        # Error analysis
        if error_info or "error" in instructions.lower() or "fix" in instructions.lower():
            research_context["error_analysis"] = await self._analyze_errors(
                error_info or self._extract_errors_from_instructions(instructions)
            )

        # Technology verification
        if "technology" in instructions.lower() or "library" in instructions.lower():
            research_context["tech_verification"] = await self._verify_technology(
                instructions
            )

        # Security analysis
        if "security" in instructions.lower() or "vulnerability" in instructions.lower():
            research_context["security_analysis"] = await self._analyze_security(
                workspace_path
            )

        logger.info(f"   ✅ Research complete: {len(research_context)} areas covered")

        return {
            "research_context": research_context,
            "research_complete": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _analyze_workspace(self, workspace_path: str) -> dict[str, Any]:
        """
        Analyze workspace structure and content.

        This is critical for understanding the project before
        architecture design or code generation.
        """
        logger.info(f"   📁 Analyzing workspace: {workspace_path}")

        if not workspace_path or not os.path.exists(workspace_path):
            return {
                "error": "Invalid workspace path",
                "file_count": 0,
                "project_type": "unknown"
            }

        analysis = {
            "workspace_path": workspace_path,
            "file_count": 0,
            "file_types": {},
            "directories": [],
            "project_type": "unknown",
            "languages": [],
            "frameworks": [],
            "has_tests": False,
            "has_docs": False,
            "configuration_files": []
        }

        try:
            # Count files by type
            for root, dirs, files in os.walk(workspace_path):
                # Skip hidden and cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

                for file in files:
                    if file.startswith('.'):
                        continue

                    analysis["file_count"] += 1
                    ext = Path(file).suffix.lower()

                    if ext:
                        analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

                    # Detect configuration files
                    if file in ["package.json", "requirements.txt", "pyproject.toml",
                               "Cargo.toml", "go.mod", "pom.xml", "build.gradle"]:
                        analysis["configuration_files"].append(file)

                    # Check for tests
                    if "test" in file.lower() or "spec" in file.lower():
                        analysis["has_tests"] = True

                    # Check for docs
                    if file.lower() in ["readme.md", "readme.rst", "readme.txt"]:
                        analysis["has_docs"] = True

            # Determine project type and languages
            if ".py" in analysis["file_types"]:
                analysis["languages"].append("Python")
                if "requirements.txt" in analysis["configuration_files"]:
                    analysis["project_type"] = "Python"
                if "pyproject.toml" in analysis["configuration_files"]:
                    analysis["project_type"] = "Python (Modern)"

            if ".js" in analysis["file_types"] or ".ts" in analysis["file_types"]:
                analysis["languages"].append("JavaScript/TypeScript")
                if "package.json" in analysis["configuration_files"]:
                    analysis["project_type"] = "Node.js"

            if ".rs" in analysis["file_types"]:
                analysis["languages"].append("Rust")
                analysis["project_type"] = "Rust"

            if ".go" in analysis["file_types"]:
                analysis["languages"].append("Go")
                analysis["project_type"] = "Go"

            # Detect frameworks
            if os.path.exists(os.path.join(workspace_path, "manage.py")):
                analysis["frameworks"].append("Django")
            if os.path.exists(os.path.join(workspace_path, "app.py")):
                analysis["frameworks"].append("Flask/FastAPI")
            if os.path.exists(os.path.join(workspace_path, "next.config.js")):
                analysis["frameworks"].append("Next.js")

        except Exception as e:
            logger.error(f"   ❌ Workspace analysis error: {e}")
            analysis["error"] = str(e)

        return analysis

    async def _search_web(self, query: str) -> list[dict[str, Any]]:
        """
        Search web for information using Perplexity API.
        Also caches results in memory for future use.
        """
        logger.info(f"   🌐 Searching web: {query[:50]}...")

        if self.perplexity_service:
            try:
                # Add timeout to prevent hanging
                import asyncio
                result = await asyncio.wait_for(
                    self.perplexity_service.search_web(query),
                    timeout=30.0  # 30 second timeout
                )

                web_results = [{
                    "title": "Web Search Results",
                    "summary": result.get("answer", ""),
                    "citations": result.get("citations", []),
                    "timestamp": datetime.now().isoformat()
                }]

                # Cache the results in memory for future use
                await self._cache_research_results(query, web_results)

                return web_results

            except asyncio.TimeoutError:
                logger.warning(f"   ⏱️ Web search timed out after 5 seconds")
            except Exception as e:
                logger.error(f"   ❌ Web search error: {e}")

        # Try to use project knowledge when Perplexity not available
        project_knowledge = await self._get_project_knowledge(query)

        if project_knowledge:
            logger.info("   ✅ Found relevant project knowledge")
            return [{
                "title": "Project Knowledge (from previous work)",
                "summary": project_knowledge,
                "source": "Internal project memory/learning system",
                "timestamp": datetime.now().isoformat()
            }]

        # No knowledge available - be honest about it
        logger.warning("   ❌ No web search or project knowledge available")
        return [{
            "title": "Research Unavailable",
            "summary": "Unable to perform web research (API timeout) and no relevant project knowledge found.",
            "error": True,
            "timestamp": datetime.now().isoformat()
        }]

    async def _analyze_errors(self, errors: list) -> dict[str, Any]:
        """
        Analyze errors and suggest fixes.

        This is crucial for the Research-Fix Loop where ReviewFix
        requests help with validation errors.
        """
        logger.info(f"   🔧 Analyzing {len(errors)} errors")

        analysis = {
            "error_count": len(errors),
            "errors": [],
            "root_cause": "Unknown",
            "suggested_fix": "Further investigation needed",
            "common_patterns": []
        }

        for error in errors[:5]:  # Analyze max 5 errors
            error_str = str(error)
            error_analysis = {
                "error": error_str,
                "type": "unknown",
                "suggestion": ""
            }

            # Pattern matching for common errors
            if "ImportError" in error_str or "ModuleNotFoundError" in error_str:
                error_analysis["type"] = "import"
                error_analysis["suggestion"] = "Check if module is installed and import path is correct"

            elif "SyntaxError" in error_str:
                error_analysis["type"] = "syntax"
                error_analysis["suggestion"] = "Check for missing parentheses, colons, or indentation"

            elif "TypeError" in error_str:
                error_analysis["type"] = "type"
                error_analysis["suggestion"] = "Check argument types and function signatures"

            elif "AttributeError" in error_str:
                error_analysis["type"] = "attribute"
                error_analysis["suggestion"] = "Verify object has the attribute/method being accessed"

            elif "KeyError" in error_str:
                error_analysis["type"] = "key"
                error_analysis["suggestion"] = "Check if dictionary key exists before accessing"

            elif "test" in error_str.lower() and "fail" in error_str.lower():
                error_analysis["type"] = "test_failure"
                error_analysis["suggestion"] = "Review test assertions and expected vs actual values"

            analysis["errors"].append(error_analysis)

        # Determine root cause based on patterns
        error_types = [e["type"] for e in analysis["errors"]]
        if error_types:
            most_common = max(set(error_types), key=error_types.count)
            analysis["root_cause"] = f"Primarily {most_common} errors"

            if most_common == "import":
                analysis["suggested_fix"] = "Review dependencies and import statements"
            elif most_common == "test_failure":
                analysis["suggested_fix"] = "Fix implementation to match test expectations"

        return analysis

    async def _verify_technology(self, query: str) -> dict[str, Any]:
        """
        Verify if a technology/library exists and get details.
        """
        logger.info(f"   🔎 Verifying technology: {query[:50]}...")

        # Extract technology names (simple heuristic)
        tech_terms = [
            word for word in query.split()
            if len(word) > 2 and not word.lower() in ["the", "and", "for", "with"]
        ]

        verification = {
            "query": query,
            "technologies": [],
            "verified_at": datetime.now().isoformat()
        }

        # Known technologies (would use web search in production)
        known_tech = {
            "fastapi": {"type": "framework", "language": "Python", "category": "web"},
            "django": {"type": "framework", "language": "Python", "category": "web"},
            "react": {"type": "library", "language": "JavaScript", "category": "frontend"},
            "vue": {"type": "framework", "language": "JavaScript", "category": "frontend"},
            "tensorflow": {"type": "library", "language": "Python", "category": "ml"},
            "pytorch": {"type": "library", "language": "Python", "category": "ml"},
            "redis": {"type": "database", "language": "agnostic", "category": "cache"},
            "postgresql": {"type": "database", "language": "agnostic", "category": "sql"},
        }

        for term in tech_terms:
            term_lower = term.lower()
            if term_lower in known_tech:
                tech_info = known_tech[term_lower].copy()
                tech_info["name"] = term
                tech_info["verified"] = True
                verification["technologies"].append(tech_info)
            elif self.perplexity_service:
                # Would search for unknown technologies
                verification["technologies"].append({
                    "name": term,
                    "verified": "pending",
                    "note": "Requires web search for verification"
                })

        return verification

    async def _analyze_security(self, workspace_path: str) -> dict[str, Any]:
        """
        Analyze potential security issues in the workspace.
        """
        logger.info(f"   🔒 Analyzing security: {workspace_path}")

        security = {
            "vulnerabilities": [],
            "warnings": [],
            "recommendations": [],
            "scan_timestamp": datetime.now().isoformat()
        }

        if not workspace_path or not os.path.exists(workspace_path):
            security["error"] = "Invalid workspace path"
            return security

        # Check for common security issues
        try:
            for root, dirs, files in os.walk(workspace_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    file_path = os.path.join(root, file)
                    file_lower = file.lower()

                    # Check for sensitive files
                    if file_lower in [".env", "credentials.json", "secrets.yaml"]:
                        security["warnings"].append(f"Sensitive file found: {file}")
                        security["recommendations"].append(f"Ensure {file} is in .gitignore")

                    # Check for hardcoded secrets pattern (simple)
                    if file.endswith((".py", ".js", ".ts", ".java")):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(1000)  # Read first 1000 chars
                                if "api_key=" in content.lower() or "password=" in content.lower():
                                    security["vulnerabilities"].append({
                                        "file": file,
                                        "issue": "Possible hardcoded credentials",
                                        "severity": "high"
                                    })
                        except:
                            pass

            # Add general recommendations
            security["recommendations"].extend([
                "Use environment variables for sensitive data",
                "Implement input validation and sanitization",
                "Keep dependencies updated",
                "Use HTTPS for all external communications"
            ])

        except Exception as e:
            logger.error(f"   ❌ Security analysis error: {e}")
            security["error"] = str(e)

        return security

    def _extract_errors_from_instructions(self, instructions: str) -> list:
        """
        Extract error information from instructions text.
        """
        errors = []

        # Look for common error patterns in instructions
        if "ImportError" in instructions:
            errors.append("ImportError mentioned in instructions")
        if "TypeError" in instructions:
            errors.append("TypeError mentioned in instructions")
        if "test" in instructions.lower() and "fail" in instructions.lower():
            errors.append("Test failure mentioned in instructions")

        return errors

    async def _get_project_knowledge(self, query: str) -> str | None:
        """
        Search for knowledge from previous project work.

        This searches:
        1. Global patterns (cross-project learning)
        2. Previous Research results (cached)
        3. Architecture decisions from Architect
        4. Code documentation from Codesmith
        5. Learning system memories

        Returns None if no relevant knowledge found.
        """
        logger.info(f"   🔍 Searching project knowledge for: {query[:50]}...")

        knowledge_parts = []

        # 1. CHECK GLOBAL KNOWLEDGE FIRST (cross-project patterns)
        if self.global_memory:
            try:
                # Initialize global memory if needed
                if not hasattr(self.global_memory, 'initialized'):
                    await self.global_memory.initialize()
                    self.global_memory.initialized = True

                # Search for relevant patterns
                patterns = await self.global_memory.search_patterns(
                    query=query,
                    project_type=self._detect_project_type(query),
                    limit=3
                )

                if patterns:
                    logger.info(f"   🌍 Found {len(patterns)} global patterns")
                    for pattern in patterns:
                        knowledge_parts.append(
                            f"Global Pattern ({pattern['success_rate']:.0%} success, "
                            f"used {pattern['usage_count']}x):\n"
                            f"{pattern['content']}"
                        )

                # Check for known error solutions if we have errors
                error_info = getattr(self, 'state', {}).get('error_info', [])
                if error_info:
                    for error in error_info[:2]:
                        solutions = await self.global_memory.get_error_solutions(str(error))
                        if solutions:
                            logger.info(f"   🔧 Found {len(solutions)} known solutions")
                            knowledge_parts.append(
                                f"Known solutions for similar error:\n" +
                                "\n".join(f"- {s}" for s in solutions)
                            )

            except Exception as e:
                logger.debug(f"   Global memory search failed: {e}")

        # 2. CHECK LOCAL PROJECT KNOWLEDGE
        if not self.workspace_path:
            logger.debug("   No workspace path - cannot search local project knowledge")
            # Return global knowledge if we have any
            if knowledge_parts:
                combined_knowledge = "\n\n---\n\n".join(knowledge_parts)
                logger.info(f"   ✅ Compiled {len(knowledge_parts)} global knowledge sources")
                return combined_knowledge
            return None

        try:
            # Lazy initialize Memory System
            if not self.memory_system:
                from backend.memory.memory_system_v6 import MemorySystem
                self.memory_system = MemorySystem(self.workspace_path)
                await self.memory_system.initialize()
                logger.debug("   ✅ Memory System initialized")

            # 1. Search for previous research results
            research_results = await self.memory_system.search(
                query=query,
                filters={"agent": "research"},
                k=3
            )

            if research_results:
                logger.info(f"   📚 Found {len(research_results)} previous research results")
                for result in research_results:
                    knowledge_parts.append(
                        f"Previous Research (similarity: {result['similarity']:.2f}):\n"
                        f"{result['content']}"
                    )

            # 2. Search for architecture decisions
            arch_results = await self.memory_system.search(
                query=query,
                filters={"agent": "architect"},
                k=2
            )

            if arch_results:
                logger.info(f"   🏗️ Found {len(arch_results)} architecture decisions")
                for result in arch_results:
                    knowledge_parts.append(
                        f"Architecture Decision:\n{result['content']}"
                    )

            # 3. Search for code documentation
            code_docs = await self.memory_system.search(
                query=query,
                filters={"agent": "codesmith"},
                k=2
            )

            if code_docs:
                logger.info(f"   📝 Found {len(code_docs)} code documentations")
                for result in code_docs:
                    knowledge_parts.append(
                        f"Code Documentation:\n{result['content']}"
                    )

            # 4. Get insights from Learning System
            if not self.learning_system:
                from backend.cognitive.learning_system_v6 import LearningSystemV6
                self.learning_system = LearningSystemV6(memory=self.memory_system)
                logger.debug("   ✅ Learning System initialized")

            # Try to detect project type from query
            project_type = self._detect_project_type(query)
            suggestions = await self.learning_system.suggest_optimizations(
                task_description=query,
                project_type=project_type
            )

            if suggestions and suggestions["based_on"] > 0:
                logger.info(f"   🧠 Found learning insights from {suggestions['based_on']} similar tasks")
                knowledge_parts.append(
                    f"Learning System Insights (based on {suggestions['based_on']} similar tasks):\n"
                    + "\n".join(f"- {s}" for s in suggestions["suggestions"])
                )

        except Exception as e:
            logger.warning(f"   ⚠️ Error searching project knowledge: {e}")

        # Combine all knowledge parts
        if knowledge_parts:
            combined_knowledge = "\n\n---\n\n".join(knowledge_parts)
            logger.info(f"   ✅ Compiled {len(knowledge_parts)} knowledge sources")
            return combined_knowledge

        logger.debug("   No relevant project knowledge found")
        return None

    def _detect_project_type(self, query: str) -> str | None:
        """
        Detect project type from query text.

        Returns:
            Project type string or None
        """
        query_lower = query.lower()

        # Common project type patterns
        project_types = {
            "calculator": ["calculator", "calculation", "math"],
            "web_app": ["web app", "web application", "frontend", "website"],
            "api": ["api", "rest", "endpoint", "backend service"],
            "cli": ["cli", "command line", "terminal"],
            "game": ["game", "gaming", "player"],
            "ml": ["machine learning", "ml", "neural", "model training"],
            "database": ["database", "sql", "postgres", "mongodb"]
        }

        for project_type, keywords in project_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return project_type

        return None

    async def _cache_research_results(
        self,
        query: str,
        results: list[dict[str, Any]]
    ) -> None:
        """
        Cache research results in memory for future retrieval.

        Args:
            query: The original search query
            results: The research results to cache
        """
        if not self.workspace_path or not results:
            return

        try:
            # Ensure memory system is initialized
            if not self.memory_system:
                from backend.memory.memory_system_v6 import MemorySystem
                self.memory_system = MemorySystem(self.workspace_path)
                await self.memory_system.initialize()

            # Store each result in memory with appropriate metadata
            for result in results:
                content = f"Query: {query}\n\n{result.get('title', '')}\n\n{result.get('summary', '')}"

                # Add citations if available
                if result.get('citations'):
                    content += f"\n\nCitations: {', '.join(result['citations'])}"

                metadata = {
                    "agent": "research",
                    "type": "research_result",
                    "query": query,
                    "timestamp": result.get('timestamp', datetime.now().isoformat()),
                    "has_citations": bool(result.get('citations')),
                    "source": "perplexity_api"
                }

                await self.memory_system.store(content=content, metadata=metadata)
                logger.debug(f"   💾 Cached research result in memory")

        except Exception as e:
            logger.warning(f"   ⚠️ Failed to cache research results: {e}")


# ============================================================================
# Export
# ============================================================================

__all__ = ["ResearchAgent"]