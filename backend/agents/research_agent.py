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

    def __init__(self):
        """Initialize the Research agent."""
        logger.info("🔬 ResearchAgent initialized")

        # Initialize Perplexity service if available
        self.perplexity_service = None
        try:
            from backend.utils.perplexity_service import PerplexityService
            self.perplexity_service = PerplexityService(model="sonar")
            logger.info("   ✅ Perplexity API connected")
        except Exception as e:
            logger.warning(f"   ⚠️ Perplexity API not available: {e}")

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
        """
        logger.info(f"   🌐 Searching web: {query[:50]}...")

        if self.perplexity_service:
            try:
                # Add timeout to prevent hanging
                import asyncio
                result = await asyncio.wait_for(
                    self.perplexity_service.search_web(query),
                    timeout=5.0  # 5 second timeout
                )
                return [{
                    "title": "Web Search Results",
                    "summary": result.get("answer", ""),
                    "citations": result.get("citations", []),
                    "timestamp": datetime.now().isoformat()
                }]
            except asyncio.TimeoutError:
                logger.warning(f"   ⏱️ Web search timed out after 5 seconds")
            except Exception as e:
                logger.error(f"   ❌ Web search error: {e}")

        # Fallback when Perplexity not available
        # Use HARDCODED responses for common queries (not real research!)
        logger.warning("   ⚠️ Web search unavailable - using hardcoded fallback")

        fallback_info = self._get_fallback_info(query)

        return [{
            "title": "⚠️ Hardcoded Response (No Web Search)",
            "summary": fallback_info,
            "note": "IMPORTANT: This is NOT from web search. It's a hardcoded response from the agent's code.",
            "warning": "Perplexity API timed out. Using static, potentially outdated information.",
            "is_fallback": True,
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

    def _get_fallback_info(self, query: str) -> str:
        """
        HARDCODED fallback responses for common queries.

        WARNING: This is NOT real research! Just static text in the code.
        Only covers: async/await, FastAPI, React
        Everything else gets a generic "search failed" message.
        """
        query_lower = query.lower()

        # Provide basic information for common queries
        if "async" in query_lower and "await" in query_lower:
            return """Python async/await is a way to write concurrent code that looks sequential.

Key concepts:
- **async def**: Defines an asynchronous function (coroutine)
- **await**: Pauses execution until an async operation completes
- **asyncio.run()**: Runs the main async function

Simple example:
```python
import asyncio

async def fetch_data():
    print("Starting fetch...")
    await asyncio.sleep(2)  # Simulate network delay
    print("Data fetched!")
    return "data"

async def main():
    result = await fetch_data()
    print(f"Got: {result}")

asyncio.run(main())
```

Benefits:
- Non-blocking I/O operations
- Better performance for I/O-bound tasks
- Cleaner code than callbacks or threads

Use cases:
- Web scraping multiple URLs
- API calls
- Database operations
- File I/O operations"""

        elif "fastapi" in query_lower:
            return """FastAPI is a modern Python web framework for building APIs.

Key features:
- Fast performance (on par with Node.js and Go)
- Automatic API documentation
- Type hints and validation with Pydantic
- Async/await support

Basic example:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```"""

        elif "react" in query_lower:
            return """React is a JavaScript library for building user interfaces.

Key concepts:
- Components (building blocks)
- JSX (JavaScript XML syntax)
- State management
- Virtual DOM for performance"""

        else:
            # Generic fallback - BE HONEST
            return f"""❌ NO HARDCODED RESPONSE AVAILABLE

Query: '{query[:100]}'

This agent has hardcoded responses for only 3 topics:
- Python async/await
- FastAPI basics
- React basics

Your query doesn't match any of these. Without Perplexity API access,
I cannot provide real research. The supervisor will need to make decisions
without research context, using only its general knowledge."""


# ============================================================================
# Export
# ============================================================================

__all__ = ["ResearchAgent"]