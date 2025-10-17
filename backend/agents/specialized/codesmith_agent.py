from __future__ import annotations

"""
CodeSmithAgent - Code generation and implementation specialist
Uses Claude 4.1 Sonnet for superior code generation
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from utils.claude_code_service import ClaudeCodeConfig, ClaudeCodeService

from ..base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                               TaskResult)
from ..base.chat_agent import ChatAgent

logger = logging.getLogger(__name__)

import os
# Import new analysis tools
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import indexing tools - OPTIONAL (NEW FEATURE)
# DOCUMENTED REASON: New indexing features for enhanced code analysis
# CodeSmith works without indexing using AI-only code generation
INDEXING_AVAILABLE = False
try:
    from core.indexing.code_indexer import CodeIndexer
    from core.indexing.tree_sitter_indexer import TreeSitterIndexer

    INDEXING_AVAILABLE = True
    logger.info("✅ Code indexing tools available")
except ImportError as e:
    logger.warning(f"⚠️  Code indexing not available (new feature): {e}")
    TreeSitterIndexer = None
    CodeIndexer = None

# Import analysis tools - OPTIONAL (NEW FEATURE)
# DOCUMENTED REASON: New analysis tools for code quality checks
# CodeSmith works without these using AI-only mode
ANALYSIS_AVAILABLE = False
try:
    from core.analysis.radon_metrics import RadonMetrics
    from core.analysis.vulture_analyzer import VultureAnalyzer

    ANALYSIS_AVAILABLE = True
    logger.info("✅ Code analysis tools available")
except ImportError as e:
    logger.warning(f"⚠️  Code analysis tools not available (new feature): {e}")
    VultureAnalyzer = None
    RadonMetrics = None

# Import diagram service - OPTIONAL (NEW FEATURE)
# DOCUMENTED REASON: Diagram generation is a new feature
# CodeSmith works without diagrams, generating text-based documentation instead
DIAGRAM_AVAILABLE = False
try:
    from services.diagram_service import DiagramService

    DIAGRAM_AVAILABLE = True
    logger.info("✅ Diagram service available")
except ImportError as e:
    logger.warning(f"⚠️  Diagram service not available (new feature): {e}")
    DiagramService = None


@dataclass()
class CodeImplementation:
    """Code implementation details"""

    language: str
    filename: str
    code: str
    tests: str | None = None
    documentation: str | None = None
    dependencies: list[str] = None
    complexity: str = "medium"  # simple, medium, complex


class CodeSmithAgent(ChatAgent):
    """
    Code Generation and Implementation Specialist
    - Code generation in multiple languages
    - Test creation
    - Code refactoring
    - Bug fixing
    - Documentation generation
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="codesmith",
            name="CodeSmithAgent",
            full_name="Code Implementation Specialist",
            description="Expert in code generation, implementation, and optimization using Claude",
            model="claude-4.1-sonnet-20250920",
            capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.BUG_FIXING],
            temperature=0.6,  # Lower for more consistent code
            max_tokens=4000,
            icon="💻",
            instructions_path=".ki_autoagent/instructions/codesmith-v2-instructions.md",
        )

        # Apply capabilities from config file before calling parent init
        try:
            from config.capabilities_loader import apply_capabilities_to_agent

            config = apply_capabilities_to_agent(config)
        except ImportError:
            pass  # Capabilities loader not available

        super().__init__(config)

        # Initialize Claude Code CLI service (NO FALLBACKS)
        self.claude_cli = ClaudeCodeService(
            ClaudeCodeConfig(model="sonnet")  # Use Sonnet model via CLI
        )

        # Set ai_service to claude_cli for the new AI-based methods
        self.ai_service = self.claude_cli

        # Check if CLI is available
        if not self.claude_cli.is_available():
            error_msg = (
                "CodeSmithAgent requires Claude Code CLI!\n"
                "Install with: npm install -g @anthropic-ai/claude-code\n"
                "Or configure a different agent/model for code tasks."
            )
            logger.error(error_msg)
            # Don't raise here, but log the error

        # Initialize code analysis tools if available
        if INDEXING_AVAILABLE:
            self.tree_sitter = TreeSitterIndexer()
            self.code_indexer = CodeIndexer()
        else:
            self.tree_sitter = None
            self.code_indexer = None
            logger.warning(
                "Code indexing tools not available - some features will be limited"
            )

        if ANALYSIS_AVAILABLE:
            self.vulture = VultureAnalyzer()
            self.metrics = RadonMetrics()
        else:
            self.vulture = None
            self.metrics = None
            logger.warning(
                "Analysis tools not available - some features will be limited"
            )

        if DIAGRAM_AVAILABLE:
            self.diagram_service = DiagramService()
        else:
            self.diagram_service = None
            logger.warning(
                "Diagram service not available - visualization features disabled"
            )

        # Code intelligence cache
        self.code_knowledge = None

        # Code patterns and templates
        self.code_patterns = self._load_code_patterns()

        # Language-specific configurations
        self.language_configs = self._load_language_configs()

    @override
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        🆕 v5.8.2: Generic Code Generator - Creates ANY type of application

        NO hardcoded assumptions about KI_AutoAgent or any specific project.
        Uses AI to understand user intent and generates complete, working applications.

        v5.9.0: Retrieves architecture knowledge from memory before code generation
        """
        start_time = datetime.now()

        # v5.8.1: Store current request for workspace context (BaseAgent needs this!)
        self._current_request = request

        try:
            prompt = request.prompt
            workspace_path = request.context.get("workspace_path", os.getcwd())

            logger.info(f"🚀 CodeSmith executing: {prompt[:100]}...")
            logger.info(f"📂 Workspace: {workspace_path}")

            # 🧠 v5.9.0: RETRIEVE ARCHITECTURE KNOWLEDGE from previous architect analyses
            architecture_context = ""
            if self.memory_manager:
                try:
                    # Search for recent architect analyses in this workspace
                    arch_memories = self.memory_manager.search(
                        query=prompt, memory_type="procedural", limit=5
                    )

                    # Filter for architect-generated memories
                    relevant_arch = [
                        m
                        for m in arch_memories
                        if '"agent": "architect"' in m.get("content", "")
                    ]

                    if relevant_arch:
                        logger.info(
                            f"🏗️ Found {len(relevant_arch)} architecture memories"
                        )
                        architecture_context = (
                            "\n\n# ARCHITECTURE KNOWLEDGE (from Architect):\n"
                        )
                        for mem in relevant_arch[:3]:  # Top 3 most relevant
                            try:
                                mem_data = json.loads(mem["content"])
                                architecture_context += (
                                    f"\n## {mem_data.get('task', 'Analysis')}:\n"
                                )
                                architecture_context += (
                                    f"{mem_data.get('result', '')[:1000]}\n"
                                )
                            except (json.JSONDecodeError, KeyError):
                                continue

                        logger.info(
                            f"📚 Loaded {len(architecture_context)} chars of architecture context"
                        )
                    else:
                        logger.info(
                            "ℹ️ No architecture memories found - will rely on AI analysis"
                        )

                except Exception as mem_error:
                    logger.warning(
                        f"⚠️ Memory retrieval failed (non-critical): {mem_error}"
                    )
                    architecture_context = ""

            # STEP 1: AI analyzes what user wants to create
            # Raises ValueError if unclear - NO fallback to 'generic'
            project_spec = await self._analyze_user_request(prompt)

            # STEP 2: AI plans which files to create
            files_plan = await self._plan_project_files(
                project_spec=project_spec,
                workspace_path=workspace_path,
                user_prompt=prompt,
            )

            # STEP 3: Generate and write each file
            files_created = []
            files_failed = []

            for file_spec in files_plan:
                file_path = file_spec["path"]

                try:
                    # Generate file content with AI (v5.9.0: includes architecture context)
                    content = await self._generate_file_content(
                        file_spec=file_spec,
                        project_spec=project_spec,
                        user_prompt=prompt,
                        architecture_context=architecture_context,
                    )

                    # Write file to workspace
                    full_path = os.path.join(workspace_path, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                    # Use write_implementation for proper validation and permissions
                    result = await self.write_implementation(
                        file_path=file_path, content=content, create_dirs=True
                    )

                    if result.get("status") == "success":
                        files_created.append(file_path)
                        logger.info(f"✅ Created: {file_path}")
                    else:
                        files_failed.append(
                            {
                                "path": file_path,
                                "error": result.get("error", "Unknown error"),
                            }
                        )
                        logger.error(
                            f"❌ Failed to create {file_path}: {result.get('error')}"
                        )

                except Exception as e:
                    files_failed.append({"path": file_path, "error": str(e)})
                    logger.error(f"❌ Exception creating {file_path}: {e}")

            # STEP 4: Return results
            execution_time = (datetime.now() - start_time).total_seconds()

            if not files_created and files_failed:
                # All files failed
                error_details = "\n".join(
                    f"- {f['path']}: {f['error']}" for f in files_failed[:5]
                )
                return TaskResult(
                    status="error",
                    content=f"❌ Failed to create project files:\n{error_details}",
                    agent=self.config.agent_id,
                    execution_time=execution_time,
                    metadata={
                        "project_type": project_spec["project_type"],
                        "files_failed": files_failed,
                    },
                )

            # Build success message
            message = f"✅ Created {project_spec['project_type']} project using {project_spec['framework'] or project_spec['language']}\n\n"
            message += f"**Files created ({len(files_created)}):**\n"

            # Group files by type for better presentation
            file_types = {}
            for file_path in files_created:
                file_type = next(
                    (f["type"] for f in files_plan if f["path"] == file_path), "other"
                )
                if file_type not in file_types:
                    file_types[file_type] = []
                file_types[file_type].append(file_path)

            for file_type, paths in sorted(file_types.items()):
                message += f"\n**{file_type.capitalize()}:**\n"
                for path in paths:
                    message += f"  - `{path}`\n"

            if files_failed:
                message += f"\n⚠️ **Partial failures ({len(files_failed)}):**\n"
                for failure in files_failed[:3]:
                    message += f"  - {failure['path']}: {failure['error']}\n"
                if len(files_failed) > 3:
                    message += f"  ... and {len(files_failed) - 3} more\n"

            return TaskResult(
                status="success",
                content=message,
                agent=self.config.agent_id,
                execution_time=execution_time,
                metadata={
                    "project_type": project_spec["project_type"],
                    "framework": project_spec["framework"],
                    "language": project_spec["language"],
                    "files_created": files_created,
                    "files_failed": files_failed,
                    "total_files": len(files_plan),
                },
            )

        except ValueError as e:
            # User request was unclear - ask for clarification
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                status="error",
                content=str(e),
                agent=self.config.agent_id,
                execution_time=execution_time,
                metadata={"error_type": "unclear_request"},
            )

        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            import traceback

            traceback.print_exc()

            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                status="error",
                content=f"Failed to generate code: {str(e)}",
                agent=self.config.agent_id,
                execution_time=execution_time,
            )

    async def analyze_code_request(self, prompt: str) -> dict[str, Any]:
        """
        Analyze code generation request
        """
        # Detect programming language
        language = self._detect_language(prompt)

        # Extract specifications
        system_prompt = """
        You are a senior software engineer.
        Analyze the code request and identify:
        1. Main functionality required
        2. Input/output specifications
        3. Performance requirements
        4. Error handling needs
        5. Testing requirements
        6. Documentation needs

        Be thorough and specific.
        """

        analysis_prompt = f"""
        Request: {prompt}

        Analyze and provide specifications:
        - Main functionality
        - Language: {language}
        - Complexity level
        - Special requirements
        - Include tests: yes/no
        - Include documentation: yes/no
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for code analysis")

        response = await self.claude_cli.complete(analysis_prompt, system_prompt)

        return {
            "prompt": prompt,
            "language": language,
            "functionality": self._extract_functionality(response),
            "include_tests": "test" in prompt.lower() or "testing" in prompt.lower(),
            "include_docs": "document" in prompt.lower() or "doc" in prompt.lower(),
            "complexity": self._assess_complexity(prompt),
        }

    async def generate_implementation(self, spec: dict[str, Any]) -> CodeImplementation:
        """
        Generate code implementation
        """
        language = spec["language"]
        self.language_configs.get(language, {})

        system_prompt = f"""
        You are Claude, an expert {language} programmer.
        Generate production-ready, clean, efficient code.
        Follow {language} best practices and conventions.
        Include comprehensive error handling.
        Make the code maintainable and well-structured.
        """

        implementation_prompt = f"""
        Language: {language}

        Requirements:
        {spec['prompt']}

        Generate complete, production-ready implementation with:
        1. Clear function/class structure
        2. Type hints (if applicable)
        3. Error handling
        4. Input validation
        5. Inline comments for complex logic

        Code should be ready to use without modifications.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for code generation")

        code = await self.claude_cli.generate_code(
            specification=spec["prompt"],
            language=language,
            context=str(spec.get("functionality", "")),
        )

        # Extract filename
        filename = self._generate_filename(spec["prompt"], language)

        # Extract dependencies
        dependencies = self._extract_dependencies(code, language)

        return CodeImplementation(
            language=language,
            filename=filename,
            code=code,
            dependencies=dependencies,
            complexity=spec.get("complexity", "medium"),
        )

    async def generate_tests(self, implementation: CodeImplementation) -> str:
        """
        Generate tests for the implementation
        """
        language = implementation.language
        test_framework = self._get_test_framework(language)

        system_prompt = f"""
        You are a test engineer expert in {language}.
        Generate comprehensive tests using {test_framework}.
        Cover edge cases, error conditions, and normal operation.
        Make tests clear, maintainable, and thorough.
        """

        test_prompt = f"""
        Generate comprehensive tests for this {language} code:

        ```{language}
        {implementation.code}
        ```

        Use {test_framework} framework.
        Include:
        1. Unit tests for all functions/methods
        2. Edge case testing
        3. Error condition testing
        4. Integration tests if applicable

        Make tests production-ready.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for test generation")

        tests = await self.claude_cli.complete(test_prompt, system_prompt)

        return tests

    async def generate_documentation(self, implementation: CodeImplementation) -> str:
        """
        Generate documentation for the implementation
        """
        system_prompt = """
        You are a technical writer.
        Generate clear, comprehensive documentation.
        Include usage examples and API reference.
        """

        doc_prompt = f"""
        Generate documentation for this {implementation.language} code:

        ```{implementation.language}
        {implementation.code}
        ```

        Include:
        1. Overview and purpose
        2. Installation/setup (if needed)
        3. API reference
        4. Usage examples
        5. Parameters and return values
        6. Error handling notes

        Use markdown format.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for documentation generation")

        documentation = await self.claude_cli.complete(doc_prompt, system_prompt)

        return documentation

    async def refactor_code(
        self, code: str, language: str, improvements: list[str] = None
    ) -> str:
        """
        Refactor existing code for improvements
        """
        system_prompt = f"""
        You are a senior {language} developer specializing in code refactoring.
        Improve code quality, performance, and maintainability.
        Follow {language} best practices and modern patterns.
        """

        refactor_prompt = f"""
        Refactor this {language} code:

        ```{language}
        {code}
        ```

        Improvements to make:
        {chr(10).join('- ' + imp for imp in improvements) if improvements else '- General improvements'}

        Focus on:
        1. Code clarity and readability
        2. Performance optimization
        3. Better error handling
        4. Reduced complexity
        5. Modern {language} patterns

        Provide the refactored code with comments explaining major changes.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for code refactoring")

        refactored = await self.claude_cli.complete(refactor_prompt, system_prompt)

        return refactored

    async def fix_bugs(self, code: str, error_description: str, language: str) -> str:
        """
        Fix bugs in code
        """
        system_prompt = f"""
        You are a debugging expert in {language}.
        Identify and fix bugs efficiently.
        Ensure the fix is robust and doesn't introduce new issues.
        """

        fix_prompt = f"""
        Fix the bug in this {language} code:

        Code:
        ```{language}
        {code}
        ```

        Error/Bug Description:
        {error_description}

        Provide:
        1. Fixed code
        2. Explanation of the bug
        3. How the fix works
        4. Any additional improvements

        Make sure the fix is complete and tested.
        """

        if not self.claude_cli.is_available():
            raise Exception("Claude CLI not available for bug fixing")

        fixed_code = await self.claude_cli.complete(fix_prompt, system_prompt)

        return fixed_code

    async def _analyze_user_request(self, prompt: str) -> dict[str, Any]:
        """
        🧠 Use AI to understand what project user wants to create
        NO templates, NO hardcoded logic - pure AI analysis

        v5.8.2: COMPLETELY GENERIC - analyzes ANY project type
        If unclear: Raises exception to ask user (no fallback to 'generic')
        """
        logger.info("🧠 Analyzing user request with AI...")

        analysis_prompt = f"""Analyze this software project request and determine what the user wants to create.

USER REQUEST: {prompt}

Return a JSON object with this structure:
{{
    "project_type": "web_app|api|cli_tool|library|fullstack|mobile_app|desktop_app|game|...",
    "framework": "React|Vue|FastAPI|Express|Django|Flask|...|null",
    "language": "TypeScript|JavaScript|Python|Go|Rust|Java|...",
    "tech_stack": ["list", "of", "technologies", "and", "libraries"],
    "features": ["list", "of", "features", "to", "implement"],
    "infrastructure": ["docker", "nginx", "..."],
    "databases": ["postgresql", "redis", "mongodb", "..."],
    "description": "brief description of what user wants to build",
    "clarity_score": 0-100
}}

CRITICAL RULES:
1. infrastructure and databases are FOR THE PROJECT THE USER WANTS TO CREATE
   - Example: "Dashboard with Docker" → Docker is for the Dashboard app, NOT for KI_AutoAgent
   - Example: "API with Redis caching" → Redis is for the API, NOT for KI_AutoAgent backend
2. If clarity_score < 50, set ALL fields to null and explain what's unclear
3. Be specific about framework/language if mentioned or clearly implied
4. Return ONLY valid JSON, no markdown, no explanation"""

        try:
            # Use AI service to analyze the request
            response = await self.ai_service.complete(analysis_prompt)

            # Parse JSON response
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                # Extract JSON from markdown code block
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                response = response.replace("```json", "").replace("```", "").strip()

            project_spec = json.loads(response)

            # Check clarity score
            clarity = project_spec.get("clarity_score", 0)
            if clarity < 50:
                error_msg = f"❌ Request unclear (clarity: {clarity}/100). Please be more specific about:\n"
                error_msg += (
                    "- What type of application? (web app, API, CLI tool, etc.)\n"
                )
                error_msg += (
                    "- What technology/framework? (React, Python, Node.js, etc.)\n"
                )
                error_msg += "- What should it do?\n\n"
                if project_spec.get("description"):
                    error_msg += f"What I understood: {project_spec['description']}"
                raise ValueError(error_msg)

            logger.info(
                f"✅ Project analysis: {project_spec['project_type']} using {project_spec['framework'] or project_spec['language']}"
            )
            return project_spec

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            raise ValueError(
                "AI analysis failed. Please rephrase your request more clearly."
            )
        except Exception as e:
            logger.error(f"❌ Project analysis failed: {e}")
            raise

    async def _plan_project_files(
        self, project_spec: dict[str, Any], workspace_path: str, user_prompt: str
    ) -> list[dict[str, Any]]:
        """
        📋 Plan which files to create based on project type
        Uses AI to generate file structure based on project_spec

        v5.8.2: COMPLETELY GENERIC - generates file plan for ANY project type
        """
        logger.info(f"📋 Planning file structure for {project_spec['project_type']}...")

        planning_prompt = f"""Generate a complete file structure for this project.

PROJECT ANALYSIS:
- Type: {project_spec['project_type']}
- Framework: {project_spec['framework']}
- Language: {project_spec['language']}
- Tech Stack: {', '.join(project_spec['tech_stack'])}
- Features: {', '.join(project_spec['features'])}
- Infrastructure: {', '.join(project_spec.get('infrastructure', []))}
- Databases: {', '.join(project_spec.get('databases', []))}

USER REQUEST: {user_prompt}

Return a JSON array of files to create. Each file should have:
{{
    "path": "relative/path/to/file.ext",
    "type": "component|config|infrastructure|test|documentation|...",
    "description": "what this file does",
    "priority": 1-10 (higher = create first)
}}

IMPORTANT:
1. Create a COMPLETE, working project (not just a demo)
2. Include ALL necessary files: code, config, infrastructure, tests, README
3. Use modern best practices for the chosen framework
4. Infrastructure files are FOR THIS PROJECT (e.g., Dockerfile for THIS app)
5. Organize files logically (src/, components/, config/, etc.)
6. Return ONLY valid JSON array, no markdown"""

        try:
            response = await self.ai_service.complete(planning_prompt)

            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                response = response.replace("```json", "").replace("```", "").strip()

            files_plan = json.loads(response)

            # Sort by priority (highest first)
            files_plan.sort(key=lambda x: x.get("priority", 5), reverse=True)

            logger.info(f"✅ Planned {len(files_plan)} files to create")
            for file_spec in files_plan[:5]:  # Log first 5
                logger.info(f"  - {file_spec['path']} ({file_spec['type']})")
            if len(files_plan) > 5:
                logger.info(f"  ... and {len(files_plan) - 5} more files")

            return files_plan

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse file plan JSON: {e}")
            raise ValueError(
                "Failed to plan file structure. AI response was not valid JSON."
            )
        except Exception as e:
            logger.error(f"❌ File planning failed: {e}")
            raise

    async def _generate_file_content(
        self,
        file_spec: dict[str, Any],
        project_spec: dict[str, Any],
        user_prompt: str,
        architecture_context: str = "",
    ) -> str:
        """
        ✍️ Use AI to generate production-ready code for each file
        NO templates - pure AI generation based on project context

        v5.8.2: COMPLETELY GENERIC - generates ANY file type
        v5.9.0: Uses architecture knowledge from Architect agent
        """
        file_path = file_spec["path"]
        logger.info(f"✍️ Generating content for {file_path}...")

        # v5.9.0: Add architecture context if available
        arch_section = ""
        if architecture_context:
            arch_section = f"\n{architecture_context}\n\nIMPORTANT: Use the architecture knowledge above when generating code. Match existing function names, patterns, and structures.\n"

        generation_prompt = f"""Generate COMPLETE, PRODUCTION-READY content for this file.

USER'S ORIGINAL REQUEST: {user_prompt}

PROJECT CONTEXT:
- Type: {project_spec['project_type']}
- Framework: {project_spec['framework']}
- Language: {project_spec['language']}
- Tech Stack: {', '.join(project_spec['tech_stack'])}
- Features: {', '.join(project_spec['features'])}
{arch_section}
FILE TO GENERATE:
- Path: {file_path}
- Type: {file_spec['type']}
- Purpose: {file_spec['description']}

REQUIREMENTS:
1. Generate COMPLETE, working code (not a skeleton or TODO)
2. Use modern best practices and idioms for {project_spec['language']}/{project_spec['framework']}
3. Include proper error handling, types/interfaces (if applicable)
4. Add helpful comments for complex logic
5. This file is part of THE PROJECT USER REQUESTED, NOT KI_AutoAgent or any other system
6. Make it production-ready and following industry standards
7. If this is a config file (package.json, etc.), include ALL necessary dependencies
8. If architecture knowledge is provided above, FOLLOW IT EXACTLY (correct function names, structures, etc.)

RETURN ONLY THE FILE CONTENT. NO markdown code blocks, NO explanations, just the raw file content."""

        try:
            content = await self.ai_service.complete(generation_prompt)

            # Remove markdown code blocks if AI added them despite instructions
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first line (```language) and last line (```)
                if lines[0].startswith("```") and lines[-1].strip() == "```":
                    content = "\n".join(lines[1:-1])

            logger.info(f"✅ Generated {len(content)} characters for {file_path}")
            return content

        except Exception as e:
            logger.error(f"❌ Failed to generate content for {file_path}: {e}")
            raise

    def format_implementation(self, implementation: CodeImplementation) -> str:
        """
        Format implementation for output
        """
        output = []
        output.append("# 💻 Code Implementation\n")
        output.append(f"**Language**: {implementation.language}")
        output.append(f"**Filename**: `{implementation.filename}`")
        output.append(f"**Complexity**: {implementation.complexity}\n")

        if implementation.dependencies:
            output.append("## 📦 Dependencies")
            for dep in implementation.dependencies:
                output.append(f"- {dep}")
            output.append("")

        output.append("## 📄 Code")
        output.append(f"```{implementation.language}")
        output.append(implementation.code)
        output.append("```\n")

        if implementation.tests:
            output.append("## 🧪 Tests")
            output.append(f"```{implementation.language}")
            output.append(implementation.tests)
            output.append("```\n")

        if implementation.documentation:
            output.append("## 📚 Documentation")
            output.append(implementation.documentation)

        output.append("\n---")
        output.append("*Generated by CodeSmithAgent (Claude 4.1 Sonnet)*")

        return "\n".join(output)

    def _detect_language(self, prompt: str) -> str:
        """
        Detect programming language from prompt using match/case
        """
        prompt_lower = prompt.lower()

        language_keywords = {
            "python": ["python", "py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue"],
            "typescript": ["typescript", "ts", "angular"],
            "java": ["java", "spring", "junit"],
            "go": ["go", "golang"],
            "rust": ["rust", "cargo"],
            "cpp": ["c++", "cpp"],
            "csharp": ["c#", "csharp", "dotnet"],
            "ruby": ["ruby", "rails"],
            "php": ["php", "laravel"],
        }

        # Check each language's keywords using match/case pattern
        for lang, keywords in language_keywords.items():
            match prompt_lower:
                case s if any(keyword in s for keyword in keywords):
                    return lang

        # Default to Python if no language detected
        return "python"

    def _extract_functionality(self, response: str) -> str:
        """
        Extract main functionality from analysis
        """
        # Simple extraction - could be enhanced
        lines = response.split("\n")
        for line in lines:
            if "functionality" in line.lower():
                return line.strip()

        return "General implementation"

    def _assess_complexity(self, prompt: str) -> str:
        """
        Assess code complexity from prompt using match/case
        """
        prompt_lower = prompt.lower()

        match prompt_lower:
            case s if any(word in s for word in ["simple", "basic", "hello world"]):
                return "simple"
            case s if any(word in s for word in ["complex", "advanced", "sophisticated"]):
                return "complex"
            case _:
                return "medium"

    def _generate_filename(self, prompt: str, language: str) -> str:
        """
        Generate appropriate filename
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "rust": ".rs",
            "cpp": ".cpp",
            "csharp": ".cs",
            "ruby": ".rb",
            "php": ".php",
        }

        # Extract main concept from prompt
        words = prompt.lower().split()[:5]
        name = "_".join(w for w in words if len(w) > 2)[:30]

        if not name:
            name = "implementation"

        return name + extensions.get(language, ".txt")

    def _extract_dependencies(self, code: str, language: str) -> list[str]:
        """
        Extract dependencies from code
        """
        dependencies = []

        if language == "python":
            # Extract import statements
            import_pattern = r"^(?:import|from)\s+(\S+)"
            matches = re.findall(import_pattern, code, re.MULTILINE)
            dependencies = [m.split(".")[0] for m in matches]

        elif language in ["javascript", "typescript"]:
            # Extract require/import statements
            import_pattern = r'(?:import|require)\s*\(?[\'"]([^\'")]+)[\'"]\)?'
            matches = re.findall(import_pattern, code)
            dependencies = matches

        # Filter out standard library modules
        dependencies = list({d for d in dependencies if not d.startswith("_")})

        return dependencies[:10]  # Limit to 10 dependencies

    def _get_test_framework(self, language: str) -> str:
        """
        Get appropriate test framework for language
        """
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "JUnit",
            "go": "testing",
            "rust": "cargo test",
            "cpp": "gtest",
            "csharp": "xUnit",
            "ruby": "RSpec",
            "php": "PHPUnit",
        }

        return frameworks.get(language, "unit test")

    def _load_code_patterns(self) -> list[dict[str, Any]]:
        """
        Load code patterns library
        """
        return [
            {
                "pattern": "singleton",
                "languages": ["python", "java", "csharp"],
                "use_case": "Ensure single instance of a class",
            },
            {
                "pattern": "factory",
                "languages": ["python", "java", "typescript"],
                "use_case": "Create objects without specifying exact class",
            },
            {
                "pattern": "observer",
                "languages": ["javascript", "typescript", "python"],
                "use_case": "Event-driven programming",
            },
        ]

    def _load_language_configs(self) -> dict[str, dict[str, Any]]:
        """
        Load language-specific configurations
        """
        return {
            "python": {
                "style_guide": "PEP 8",
                "type_hints": True,
                "docstring_format": "Google",
            },
            "javascript": {
                "style_guide": "Airbnb",
                "es_version": "ES6+",
                "module_system": "ESM",
            },
            "typescript": {
                "style_guide": "Airbnb",
                "strict_mode": True,
                "target": "ES2022",
            },
        }

    async def analyze_codebase(self, root_path: str = ".") -> dict[str, Any]:
        """
        Perform deep code analysis for intelligent code generation

        Uses Tree-sitter AST and metrics to understand:
        - Existing code patterns
        - Coding style
        - Common abstractions
        - Performance hotspots
        """
        if not INDEXING_AVAILABLE:
            logger.warning("Code indexing not available - returning empty analysis")
            return {
                "error": "Code analysis tools not installed",
                "message": "Please install requirements: pip install -r requirements.txt",
            }

        logger.info("Analyzing codebase for pattern extraction...")

        # Build complete code index
        self.code_knowledge = await self.code_indexer.build_full_index(root_path)

        # Extract code patterns for reuse
        self.code_knowledge.get("patterns", {})

        # Find dead code that can be removed
        dead_code = await self.vulture.find_dead_code(root_path)

        # Calculate code metrics
        metrics = await self.metrics.calculate_all_metrics(root_path)

        self.code_knowledge["dead_code"] = dead_code
        self.code_knowledge["metrics"] = metrics

        return self.code_knowledge

    async def implement_with_patterns(self, spec: str) -> str:
        """
        Implement feature using existing code patterns from the codebase

        This ensures new code matches existing style and patterns
        """
        # Skip analyze_codebase if it might fail
        if not self.code_knowledge:
            logger.info("📝 Using simplified implementation (no codebase analysis)")
            # Use simplified implementation without patterns
            # ✅ OPTIMIZED PROMPT based on Anthropic Best Practices
            simple_prompt = f"""ULTRATHINK THROUGH THIS STEP BY STEP:

You are a senior software engineer. Your task is to WRITE ACTUAL, COMPLETE, WORKING CODE.

CRITICAL INSTRUCTIONS:
- Output ONLY the complete code file - NO explanations, NO descriptions, NO summaries
- Write code that is ready to run immediately
- Include ALL necessary HTML, CSS, and JavaScript in a single file
- Make it fully functional - not a template or example
- DO NOT describe what the code should do - WRITE THE ACTUAL CODE

SPECIFICATION:
{spec}

OUTPUT FORMAT: A single, complete, working code file.
BEGIN YOUR RESPONSE WITH THE CODE DIRECTLY (no preamble, no markdown blocks, just the code):"""

            try:
                response = await self.claude_cli.complete(simple_prompt)
                return response
            except Exception as e:
                logger.error(f"❌ Claude CLI failed: {e}")
                # Return empty to trigger fallback
                return ""

        # Extract relevant patterns
        patterns = self.code_knowledge.get("patterns", {})
        architecture = self.code_knowledge.get("architecture", {})

        # Build context-aware prompt
        design_patterns_list = patterns.get("design_patterns", [])
        # Convert to strings if they are dicts
        if design_patterns_list and isinstance(design_patterns_list[0], dict):
            pattern_names = [
                p.get("name", str(p)) if isinstance(p, dict) else str(p)
                for p in design_patterns_list
            ]
        else:
            pattern_names = [str(p) for p in design_patterns_list]

        context_prompt = f"""
        Implement the following feature using these existing patterns:

        Architecture Style: {architecture.get('style', 'Unknown')}
        Design Patterns Found: {', '.join(pattern_names)}

        Feature Specification:
        {spec}

        Follow the existing code style and patterns exactly.
        """

        # Generate implementation using claude_cli.complete
        response = await self.claude_cli.complete(context_prompt)
        return response

    async def refactor_complex_code(
        self, file_path: str = None
    ) -> list[dict[str, Any]]:
        """
        Identify and refactor complex code sections

        Uses Radon metrics to find complex functions and suggest refactoring
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        metrics = self.code_knowledge.get("metrics", {})

        # Find refactoring candidates
        candidates = await self.metrics.identify_refactoring_candidates(metrics)

        refactorings = []
        for candidate in candidates[:3]:  # Limit to top 3
            if candidate["type"] == "function":
                # Generate refactoring suggestion
                prompt = f"""
                Refactor this complex function:
                File: {candidate['file']}
                Function: {candidate['name']}
                Complexity: {candidate['complexity']}

                Suggestion: {candidate['suggestion']}

                Provide refactored code that reduces complexity.
                """

                refactored_code = await self.claude_cli.process_message(prompt)

                refactorings.append(
                    {
                        "original": candidate,
                        "refactored_code": refactored_code,
                        "improvement": "Reduced complexity",
                    }
                )

        return refactorings

    async def _refresh_cache_if_needed(
        self, files_created: list[str], request: TaskRequest
    ):
        """
        Refresh cache after implementing new functions or modifying code

        Args:
            files_created: List of files that were created or modified
            request: Original task request for context
        """
        try:
            # Get the architect agent from registry
            from agents.agent_registry import get_agent_registry

            registry = get_agent_registry()
            architect = registry.get_agent("architect")

            if not architect:
                logger.warning("Architect agent not available for cache refresh")
                return

            # Determine which components to refresh based on files created
            components_to_refresh = []

            for file_path in files_created:
                if any(
                    ext in file_path for ext in [".py", ".js", ".ts", ".java", ".go"]
                ):
                    components_to_refresh.append("code_index")
                    components_to_refresh.append("functions")
                    break

            # If we created configuration files, refresh metrics
            if any("config" in f or "settings" in f for f in files_created):
                components_to_refresh.append("metrics")

            # If we have components to refresh, do it
            if components_to_refresh:
                # Get client_id and manager from context if available
                client_id = (
                    request.context.get("client_id")
                    if isinstance(request.context, dict)
                    else None
                )
                manager = (
                    request.context.get("manager")
                    if isinstance(request.context, dict)
                    else None
                )

                logger.info(
                    f"🔄 Refreshing cache for components: {list(set(components_to_refresh))}"
                )
                await architect.refresh_cache_after_implementation(
                    client_id=client_id,
                    manager=manager,
                    components=list(set(components_to_refresh)),
                )
                logger.info("✅ Cache refreshed after code implementation")
        except Exception as e:
            logger.warning(f"Could not refresh cache after implementation: {e}")
            # Don't fail the whole operation if cache refresh fails

    async def optimize_performance_hotspots(self) -> list[dict[str, str]]:
        """
        Find and optimize performance bottlenecks in the code

        Uses pattern analysis to identify inefficient code
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        patterns = self.code_knowledge.get("patterns", {})
        perf_issues = patterns.get("performance_issues", [])

        optimizations = []

        for issue in perf_issues[:5]:  # Top 5 issues
            optimization_prompt = f"""
            Optimize this performance issue:
            Type: {issue.get('type')}
            File: {issue.get('file')}
            Line: {issue.get('line')}

            Current code causing issue:
            {issue.get('code', 'N/A')}

            Provide optimized version.
            """

            optimized = await self.claude_cli.process_message(optimization_prompt)

            optimizations.append(
                {
                    "issue": issue,
                    "optimized_code": optimized,
                    "expected_improvement": "Significant performance gain",
                }
            )

        return optimizations

    async def generate_missing_tests(self) -> str:
        """
        Identify untested code and generate comprehensive tests

        Uses code index to find functions without tests
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        # Find functions without tests
        all_functions = self.code_knowledge.get("ast", {}).get("functions", {})

        # Simple heuristic: functions without 'test_' prefix likely need tests
        untested = []
        for func_key, func_info in all_functions.items():
            func_name = func_info.get("name", "")
            if not func_name.startswith("test_") and not func_name.startswith("_"):
                untested.append(func_info)

        if not untested:
            return "All functions appear to have tests!"

        # Generate tests for top untested functions
        test_prompt = f"""
        Generate comprehensive unit tests for these functions:

        {json.dumps(untested[:5], indent=2)}

        Use pytest framework with proper fixtures and assertions.
        """

        tests = await self.claude_cli.process_message(test_prompt)
        return tests

    async def cleanup_dead_code(self) -> str:
        """
        Generate script to remove dead code safely

        Uses Vulture analysis to identify unused code
        """
        if not self.code_knowledge:
            await self.analyze_codebase()

        dead_code = self.code_knowledge.get("dead_code", {})

        if not dead_code.get("summary", {}).get("total_dead_code"):
            return "No dead code found!"

        # Generate cleanup script
        cleanup_script = await self.vulture.generate_cleanup_script(dead_code)

        return f"""
## Dead Code Cleanup Report

### Summary
- **{dead_code['summary']['total_dead_code']}** items of dead code found
- **{dead_code['summary']['estimated_lines_to_remove']}** lines can be removed
- **Priority**: {dead_code['summary']['cleanup_priority']}

### Cleanup Script
```python
{cleanup_script}
```

Run this script to safely comment out dead code for review.
"""

    async def _process_agent_request(self, message) -> Any:
        """
        Process request from another agent
        Implementation of abstract method from BaseAgent
        """
        # Handle code generation requests from other agents
        if message.content.get("requesting_code"):
            task = message.content.get("task", "")
            result = await self.execute(TaskRequest(prompt=task))
            return {"code_result": result.content}

        return {"message": "CodeSmith received request"}

    def _check_for_hallucination(self, content: str) -> bool:
        """
        🧠 Check if agent is hallucinating about wrong systems
        Prevents talking about JD Edwards, Oracle, etc.
        """
        hallucination_indicators = [
            "JD Edwards",
            "jd edwards",
            "JDEdwards",
            "Oracle",
            "oracle",
            "EnterpriseOne",
            "enterprise one",
            "P4310",
            "Form Extension",
            "form extension",
            "ERP",
            "SAP",
            "PeopleSoft",
        ]

        content_lower = content.lower()
        for indicator in hallucination_indicators:
            if indicator.lower() in content_lower:
                logger.error(
                    f"🚨 HALLUCINATION DETECTED: Found '{indicator}' in response!"
                )
                logger.error("🚨 This is KI_AutoAgent, not an enterprise system!")
                return True

        return False

    def _enforce_asimov_rule_1(self, file_path: str):
        """
        🚫 ASIMOV RULE 1 ENFORCEMENT
        Ensure NO FALLBACKS are used - fail fast and clear
        """
        if not file_path:
            raise ValueError(
                "ASIMOV RULE 1 VIOLATION: No file path determined.\n"
                "System must create actual files, not fallback to text.\n"
                "File: backend/agents/specialized/codesmith_agent.py\n"
                "Line: execute() method"
            )

        # Check for fallback patterns in the path
        fallback_patterns = ["fallback", "temp", "tmp", "test", "dummy"]
        if any(pattern in file_path.lower() for pattern in fallback_patterns):
            logger.warning(f"⚠️ Suspicious file path detected: {file_path}")

        logger.info(f"✅ ASIMOV RULE 1 CHECK PASSED: {file_path}")

    async def _ai_detect_implementation_request(self, prompt: str) -> bool:
        """
        🧠 Use AI to intelligently detect if this is an implementation request
        With KI_AutoAgent project context awareness
        """
        try:
            ai_prompt = f"""You are an expert code implementation assistant.

Request: {prompt}

Answer with ONLY 'YES' or 'NO':
- YES if: The request asks to implement, create, build, develop, write code/files, add features, modify code, etc.
  Examples of YES:
  * "Implement the application"
  * "Create a Tetris game"
  * "Build a web app"
  * "Add a button"
  * "Write a function"
  * "Develop a feature"

- NO if: The request is only asking for explanation, analysis, review, or questions without code creation
  Examples of NO:
  * "Explain how X works"
  * "What is the purpose of Y?"
  * "Review this code"
  * "Analyze the architecture"

Remember: Focus on the ACTION requested, not the subject matter.

Answer (YES/NO):"""

            # Use complete method with combined prompt
            full_prompt = f"System: You are an expert code implementation assistant.\n\n{ai_prompt}"
            response = await self.claude_cli.complete(full_prompt)

            result = response.strip().upper().startswith("YES")
            if result:
                logger.info("🧠 AI detected: Implementation request → Will create files")
            else:
                logger.info(
                    "🧠 AI detected: Non-implementation request → No files needed"
                )
            return result

        except Exception as e:
            logger.error(f"AI detection failed: {e}")
            # ASIMOV RULE 1: No fallback - raise the error
            raise Exception(f"Failed to determine implementation intent: {e}")

    async def _ai_determine_file_path(self, prompt: str, workspace_path: str) -> str:
        """
        🧠 Use AI to intelligently determine the appropriate file path
        With explicit KI_AutoAgent project knowledge
        """
        try:
            # Check for button-related keywords first
            prompt_lower = prompt.lower()
            if "button" in prompt_lower and "orchestrator" in prompt_lower:
                # We KNOW where buttons go in KI_AutoAgent
                file_path = "vscode-extension/src/ui/MultiAgentChatPanel.ts"
                logger.info(
                    f"🎯 Direct path determination: Button near Orchestrator → {file_path}"
                )
                return os.path.join(workspace_path, file_path)

            # Get project structure context
            project_files = []
            try:
                for root, dirs, files in os.walk(workspace_path):
                    # Skip node_modules and other large directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if d not in [".git", "node_modules", "venv", "__pycache__"]
                    ]
                    for file in files[:50]:  # Limit to first 50 files for context
                        rel_path = os.path.relpath(
                            os.path.join(root, file), workspace_path
                        )
                        if not rel_path.startswith("."):
                            project_files.append(rel_path)
                    if len(project_files) > 100:
                        break
            except (OSError, PermissionError) as e:
                logger.debug(f"Error reading project files: {e}")
                project_files = []

            project_structure = (
                "\n".join(project_files[:30]) if project_files else "Empty project"
            )

            # Check if this is a standalone web app request
            is_web_app = any(
                keyword in prompt_lower
                for keyword in [
                    "webapplikation",
                    "web app",
                    "html",
                    "tetris",
                    "game",
                    "website",
                ]
            )

            if is_web_app:
                # For standalone web apps, use simple HTML file in workspace root
                feature_name = self._extract_feature_name(prompt)
                file_path = f"{feature_name}.html"
                full_path = os.path.join(workspace_path, file_path)
                logger.info(f"🌐 Standalone web app detected → {full_path}")
                return full_path  # ✅ FIX: Return full path in workspace!

            ai_prompt = f"""Determine the correct file path for this code implementation.

Request: {prompt}

Workspace: {workspace_path}

Based on the request and standard conventions:
- For Python code: use .py extension
- For JavaScript/TypeScript: use .js/.ts extension
- For HTML/CSS: use .html/.css extension
- For configuration: use .json/.yaml extension

Return ONLY the filename (e.g., "myfeature.py" or "app.js"), nothing else.

Filename:"""

            # Use complete method with combined prompt
            full_prompt = f"System: You are an expert at determining file paths based on project structure and conventions.\n\n{ai_prompt}"
            response = await self.claude_cli.complete(full_prompt)

            file_path = response.strip()

            # Validate and clean the path
            if not file_path or file_path == "":
                # Extract feature name and generate path
                feature_name = self._extract_feature_name(prompt)
                file_path = f"{feature_name}.py"

            # Clean up any absolute path - we want relative only
            if file_path.startswith("/"):
                file_path = os.path.basename(file_path)

            # Build full path in workspace
            full_path = os.path.join(workspace_path, file_path)
            logger.info(f"🧠 AI determined file path: {full_path}")
            return full_path  # ✅ FIX: Return full path in workspace!

        except Exception as e:
            logger.error(f"AI file path determination failed: {e}")
            # ASIMOV RULE 1: No fallback - raise the error
            raise Exception(f"Failed to determine file path: {e}")

    def _extract_file_path(self, prompt: str) -> str:
        """Extract file path from prompt if mentioned"""
        import re

        # Look for file paths in the prompt
        patterns = [
            r"(?:file|create|write|update|in)\s+([a-zA-Z0-9_/.-]+\.(?:py|js|ts|tsx|jsx|yml|yaml|json|md|txt))",
            r"([a-zA-Z0-9_/.-]+\.(?:py|js|ts|tsx|jsx|yml|yaml|json|md|txt))",
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _generate_file_path(self, prompt: str) -> str:
        """Generate appropriate file path based on prompt"""
        prompt_lower = prompt.lower()

        # Determine directory
        if "test" in prompt_lower:
            directory = "backend/tests/"
        elif "button" in prompt_lower or "ui" in prompt_lower:
            directory = "vscode-extension/src/ui/"
        elif "agent" in prompt_lower:
            directory = "backend/agents/"
        elif "api" in prompt_lower or "endpoint" in prompt_lower:
            directory = "backend/api/"
        elif "service" in prompt_lower:
            directory = "backend/services/"
        else:
            directory = "backend/"

        # Extract feature name
        feature_name = self._extract_feature_name(prompt)

        # Determine extension
        if "typescript" in prompt_lower or "button" in prompt_lower:
            extension = ".ts"
        elif "react" in prompt_lower:
            extension = ".tsx"
        elif "config" in prompt_lower:
            extension = ".yml"
        else:
            extension = ".py"

        return f"{directory}{feature_name}{extension}"

    def _extract_feature_name(self, prompt: str) -> str:
        """Extract feature name from prompt"""
        import re

        # Remove common words
        stop_words = [
            "implement",
            "create",
            "add",
            "build",
            "write",
            "erstelle",
            "the",
            "a",
            "an",
            "for",
            "with",
            "to",
            "in",
            "feature",
            "function",
            "button",
            "einen",
            "der",
            "die",
            "das",
        ]

        words = re.findall(r"\w+", prompt.lower())
        feature_words = [w for w in words if w not in stop_words and len(w) > 2]

        if feature_words:
            # Take first meaningful word
            feature = feature_words[0].replace("-", "_")
            # For buttons, add _button suffix
            if "button" in prompt.lower():
                feature = f"{feature}_button"
            return feature

        return "new_feature"

    async def implement_code_to_file(self, spec: str, file_path: str) -> dict[str, Any]:
        """
        Generate code and write it to a file

        Args:
            spec: Code specification/requirements
            file_path: Path where to write the code

        Returns:
            Dict with status and details
        """
        logger.info("🔧 implement_code_to_file called")
        logger.info(f"  📁 Target file: {file_path}")
        logger.info(f"  📝 Spec length: {len(spec)} characters")

        try:
            # Generate the code - NO FALLBACKS (ASIMOV RULE 1)
            logger.info("⚡ Generating code with AI...")
            code = await self.implement_with_patterns(spec)

            if not code:
                logger.error("❌ Code generation returned empty result")
                return {
                    "status": "error",
                    "error": "Failed to generate code - empty result",
                    "agent": self.name,
                }

            logger.info(f"✅ Code generated: {len(code)} characters")

            # Write the code to file
            logger.info(f"📝 Writing code to file: {file_path}")
            result = await self.write_implementation(file_path, code)

            if result.get("status") == "success":
                logger.info(
                    f"✅ CodeSmithAgent successfully implemented code to {file_path}"
                )

                # Add to response
                result["code"] = code[:500] + "..." if len(code) > 500 else code
                result["lines"] = len(code.split("\n"))

                # Track in shared context if available
                # v5.5.3: Wrap in try/except to not corrupt successful result
                # v5.7.0: Fixed - use update() method instead of non-existent update_context()
                if self.shared_context:
                    try:
                        self.shared_context.update(
                            {
                                f"{self.config.agent_id}_last_implementation": {
                                    "file": file_path,
                                    "spec": spec[:200],
                                    "timestamp": datetime.now().isoformat(),
                                }
                            }
                        )
                    except Exception as ctx_error:
                        logger.warning(
                            f"⚠️ Shared context update failed (non-critical): {ctx_error}"
                        )

            return result

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            logger.error(f"❌ CodeSmithAgent failed to implement code: {e}")
            logger.error(f"📋 Stack trace:\n{error_details}")
            logger.error(f"📁 Target file was: {file_path}")
            logger.error(f"📝 Spec was: {spec[:200]}...")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "path": file_path,
                "traceback": error_details,
            }
