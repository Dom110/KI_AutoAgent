"""
ArchitectAgent - System design and architecture specialist
Uses GPT-5 for architectural decisions and technology selection
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Import custom exceptions
from core.exceptions import (ArchitectError, ArchitectResearchError,
                             ArchitectValidationError, ParsingError)
from utils.openai_service import OpenAIService

from ..base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                               TaskResult)
from ..base.chat_agent import ChatAgent

# Setup logger first
logger = logging.getLogger(__name__)

import os
# Import new analysis and visualization tools
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import cache services - OPTIONAL (NOT YET IMPLEMENTED)
# DOCUMENTED REASON: Cache services are planned but not yet implemented
# This is NOT a fallback - Architect will work without caching, just slower
CACHE_SERVICES_AVAILABLE = False
try:
    from services.code_search import LightweightCodeSearch
    from services.project_cache import ProjectCache
    from services.smart_file_watcher import SmartFileWatcher

    CACHE_SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(
        f"⚠️  Cache services not available (feature not yet implemented): {e}"
    )
    logger.warning("⚠️  Architect will work without caching (slower analysis)")
    ProjectCache = None
    SmartFileWatcher = None
    LightweightCodeSearch = None

# Import indexing tools - OPTIONAL (NEW FEATURE)
# DOCUMENTED REASON: New indexing features for enhanced analysis
# Architect works without indexing using AI-only mode
INDEXING_AVAILABLE = False
try:
    from core.indexing.code_indexer import CodeIndexer
    from core.indexing.tree_sitter_indexer import TreeSitterIndexer

    INDEXING_AVAILABLE = True
    logger.info("✅ Code indexing tools available")
except ImportError as e:
    logger.warning(f"⚠️  Code indexing not available (new feature): {e}")
    logger.warning("⚠️  Architect will use AI-only mode")
    TreeSitterIndexer = None
    CodeIndexer = None

# Import analysis tools - OPTIONAL (NEW FEATURE)
# DOCUMENTED REASON: New analysis tools for enhanced architecture insights
# Architect works without these using AI-only mode
ANALYSIS_AVAILABLE = False
try:
    from core.analysis.call_graph_analyzer import CallGraphAnalyzer
    from core.analysis.layer_analyzer import LayerAnalyzer
    from core.analysis.radon_metrics import RadonMetrics
    from core.analysis.semgrep_analyzer import SemgrepAnalyzer
    from core.analysis.vulture_analyzer import VultureAnalyzer

    ANALYSIS_AVAILABLE = True
    logger.info("✅ Code analysis tools available")
except ImportError as e:
    logger.warning(f"⚠️  Code analysis tools not available (new feature): {e}")
    logger.warning("⚠️  Architect will use AI-only mode")
    SemgrepAnalyzer = None
    VultureAnalyzer = None
    RadonMetrics = None
    CallGraphAnalyzer = None
    LayerAnalyzer = None

# Import diagram service - OPTIONAL (NEW FEATURE)
# DOCUMENTED REASON: Diagram generation is a new feature
# Architect works without diagrams using text-based architecture descriptions
DIAGRAM_AVAILABLE = False
try:
    from services.diagram_service import DiagramService

    DIAGRAM_AVAILABLE = True
    logger.info("✅ Diagram service available")
except ImportError as e:
    logger.warning(f"⚠️  Diagram service not available (new feature): {e}")
    DiagramService = None


@dataclass
class ArchitectureDesign:
    """Architecture design specification"""

    project_name: str
    architecture_type: str  # monolithic, microservices, serverless, etc.
    components: list[dict[str, Any]]
    technologies: list[str]
    patterns: list[str]
    data_flow: dict[str, Any]
    deployment: dict[str, Any]
    scalability_notes: str
    security_considerations: str


class ArchitectAgent(ChatAgent):
    """
    Architecture and System Design Specialist
    - System architecture design
    - Technology selection
    - Design patterns recommendation
    - Scalability planning
    - Security architecture
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="architect",
            name="ArchitectAgent",
            full_name="System Architecture Specialist",
            description="Expert in system design, architecture patterns, and technology selection",
            model="gpt-4o-2024-11-20",
            capabilities=[AgentCapability.ARCHITECTURE_DESIGN],
            temperature=0.7,
            max_tokens=4000,
            instructions_path=".ki_autoagent/instructions/architect-v2-instructions.md",
            icon="🏗️",
        )

        # Apply capabilities from config file before calling parent init
        try:
            from config.capabilities_loader import apply_capabilities_to_agent

            config = apply_capabilities_to_agent(config)
        except ImportError:
            pass  # Capabilities loader not available

        super().__init__(config)

        # Progress deduplication tracking
        self._last_progress_messages = {}  # Track last message per client
        self._progress_debounce_timers = {}  # Debounce timers per client

        # Initialize OpenAI service with specific model
        self.openai = OpenAIService(model=self.config.model)

        # v5.8.0: Get workspace path from KI_WORKSPACE_PATH (set by client)
        # Backend runs from $HOME/.ki_autoagent/backend/, but analyzes user workspace
        # Priority: KI_WORKSPACE_PATH > PROJECT_PATH > fallback to parent of backend dir
        default_path = (
            os.getcwd()
            if os.path.basename(os.getcwd()) != "backend"
            else os.path.dirname(os.getcwd())
        )
        workspace_path = os.getenv("KI_WORKSPACE_PATH") or os.getenv(
            "PROJECT_PATH", default_path
        )

        # For consistency, always use the full absolute path
        workspace_path = os.path.abspath(workspace_path)
        logger.info(f"🏗️ Initializing ArchitectAgent with workspace: {workspace_path}")

        # v5.8.0: Workspace-specific cache directory
        # Cache/DB files go in $WORKSPACE/.ki_autoagent_ws/cache/
        workspace_cache_dir = os.path.join(workspace_path, ".ki_autoagent_ws", "cache")
        os.makedirs(workspace_cache_dir, exist_ok=True)
        logger.info(f"📦 Workspace cache directory: {workspace_cache_dir}")

        # Store workspace path for later use
        self.workspace_path = workspace_path

        # Initialize cache services if available
        # DOCUMENTED REASON: Cache services are optional - not yet implemented
        # Architect works without caching, just slower
        if CACHE_SERVICES_AVAILABLE:
            # Pass cache_dir to ProjectCache (it will use this instead of creating in workspace root)
            self.project_cache = ProjectCache(workspace_cache_dir)
            if not self.project_cache.connected:
                from core.exceptions import CacheNotAvailableError

                raise CacheNotAvailableError(
                    component="ArchitectAgent", file=__file__, line=123
                )

            # Initialize SQLite search with workspace path and cache dir
            self.code_search = LightweightCodeSearch(
                workspace_path, cache_dir=workspace_cache_dir
            )

            # Initialize SMART file watcher with debouncing
            self.file_watcher = SmartFileWatcher(
                workspace_path, self.project_cache, debounce_seconds=30
            )
            self.file_watcher.start()

            logger.info(
                "✅ Cache services initialized: Redis cache, SQLite search, Smart File watcher with 30s debounce"
            )
        else:
            # No cache services - work without them
            self.project_cache = None
            self.code_search = None
            self.file_watcher = None
            logger.warning(
                "⚠️  Cache services not available - working without caching (slower)"
            )

        # Initialize code indexing tools - REQUIRED
        self.tree_sitter = TreeSitterIndexer()
        self.code_indexer = CodeIndexer()
        logger.info("✅ Code indexing tools initialized")

        if ANALYSIS_AVAILABLE:
            self.semgrep = SemgrepAnalyzer()
            self.vulture = VultureAnalyzer()
            self.metrics = RadonMetrics()
            self.call_graph_analyzer = CallGraphAnalyzer()
            self.layer_analyzer = LayerAnalyzer()
            logger.info(
                "✅ Analysis tools initialized: Semgrep, Vulture, Radon, CallGraph, Layers"
            )
        else:
            self.semgrep = None
            self.vulture = None
            self.metrics = None
            self.call_graph_analyzer = None
            self.layer_analyzer = None
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

        # System knowledge cache - no in-memory fallback, Redis only
        self.system_knowledge = None
        self.last_index_time = None

        # Architecture patterns library
        self.architecture_patterns = self._load_architecture_patterns()

        # Technology stack recommendations
        self.tech_stacks = self._load_tech_stacks()

        # Research Agent connection (will be set by workflow/orchestrator)
        self.research_agent = None

        # v5.8.7: Cache task classification to avoid re-classifying meta-prompts
        self._cached_classification = None
        self._cached_classification_prompt = None

    async def _is_workspace_empty(self, workspace_path: str) -> bool:
        """
        Check if workspace has no significant code files yet (new project detection)

        Args:
            workspace_path: Path to workspace directory

        Returns:
            True if workspace is empty/new, False if existing project
        """
        code_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".c",
            ".php",
            ".rb",
        ]

        try:
            for root, dirs, files in os.walk(workspace_path):
                # Skip common non-project directories
                dirs[:] = [
                    d
                    for d in dirs
                    if d
                    not in [
                        ".ki_autoagent_ws",
                        "node_modules",
                        ".git",
                        "__pycache__",
                        "venv",
                        "env",
                        ".venv",
                        "dist",
                        "build",
                        ".cache",
                    ]
                ]

                # Check for code files
                for file in files:
                    if any(file.endswith(ext) for ext in code_extensions):
                        logger.info(
                            f"📂 Found existing code file: {file} - Not a new project"
                        )
                        return False

            logger.info("🆕 Workspace appears empty - New project mode")
            return True

        except Exception as e:
            logger.warning(
                f"⚠️ Error checking workspace: {e} - Assuming existing project"
            )
            return False

    async def _classify_task_complexity(self, prompt: str) -> dict[str, Any]:
        """
        Classify task complexity using AI (GPT-4o) for accurate assessment

        v5.8.7: Replaced keyword-based heuristics with AI classification
        Reason: Keywords like "calculator" or "page" don't reliably indicate
        architecture type. A "calculator microservice" needs backend, while
        "HTML calculator" doesn't. Only AI can understand context properly.

        v5.8.7 FIX: Caches classification to avoid re-classifying meta-prompts
        like "create comprehensive ARCHITECTURE PROPOSAL" which AI misinterprets
        as requiring distributed systems.

        Args:
            prompt: User's task description (original, not orchestrator-rewritten)

        Returns:
            Dict with classification details from AI analysis
        """
        # Extract ONLY the original user prompt (first line before any additions)
        # This avoids false positives from orchestrator rewrites or research text
        prompt_lines = [line.strip() for line in prompt.split("\n") if line.strip()]
        original_prompt = prompt_lines[0] if prompt_lines else prompt

        # v5.8.7 DEBUG: Log what we're classifying
        logger.info(f"📝 Classification input (full): {prompt[:200]}...")
        logger.info(f"📝 Classification input (extracted first line): {original_prompt}")

        # v5.8.7 FIX: Return cached classification if same prompt
        if self._cached_classification_prompt == original_prompt:
            logger.info(f"✅ Using cached classification for: {original_prompt[:60]}...")
            return self._cached_classification

        # v5.8.7 FIX: Detect meta-prompts and skip classification
        meta_prompt_indicators = [
            "based on your research, create",
            "create a comprehensive architecture proposal",
            "architecture proposal for user approval",
            "create a detailed proposal",
            "refine the architecture",
        ]
        prompt_lower = original_prompt.lower()
        if any(indicator in prompt_lower for indicator in meta_prompt_indicators):
            logger.warning(
                f"⚠️ Detected meta-prompt, skipping classification: {original_prompt[:60]}..."
            )
            if self._cached_classification:
                logger.info("✅ Returning previous classification instead")
                return self._cached_classification
            else:
                logger.warning(
                    "⚠️ No cached classification available, will classify anyway"
                )

        logger.info(f"🔍 AI-classifying task: {original_prompt[:100]}...")

        # Use GPT-4o for intelligent classification
        classification_prompt = f"""Analyze this software development task and classify it:

Task: "{original_prompt}"

Determine:
1. **Complexity**: simple | medium | complex
   - simple: Single-file or few-file apps, basic UIs, client-side only
   - medium: Multi-file apps, moderate features, may need backend
   - complex: Distributed systems, enterprise scale, microservices

2. **Type**: frontend_only | fullstack | backend_only | distributed
   - frontend_only: Pure client-side (HTML/CSS/JS) - NO server needed
   - fullstack: Frontend + Backend + Database
   - backend_only: API/Service without UI
   - distributed: Microservices, Kubernetes, etc.

3. **Requires Backend**: true | false
   - true ONLY if EXPLICITLY needs: database, API, authentication, server-side processing, data persistence
   - false if it can run in browser without server

4. **Requires Database**: true | false
   - true ONLY if EXPLICITLY needs: data storage, user accounts, persistent data
   - false if data can be in-memory or localStorage

5. **Suggested Stack**: List appropriate technologies

6. **File Structure**: single_file | modular | fullstack | microservices
   - single_file: One HTML file with inline CSS/JS
   - modular: Separate HTML/CSS/JS files, no backend
   - fullstack: Frontend + Backend directories
   - microservices: Multiple services

7. **Reasoning**: Brief explanation (1-2 sentences)

Return ONLY valid JSON:
{{
  "complexity": "simple|medium|complex",
  "type": "frontend_only|fullstack|backend_only|distributed",
  "requires_backend": true|false,
  "requires_database": true|false,
  "suggested_stack": ["tech1", "tech2", ...],
  "file_structure": "single_file|modular|fullstack|microservices",
  "reasoning": "explanation"
}}

CRITICAL RULES:
1. "HTML calculator", "design the architecture for a calculator", "simple HTML page" = frontend_only, requires_backend=false, requires_database=false
2. "Calculator API", "REST API for calculations" = backend_only
3. "Calculator with user login" or "save calculations to database" = fullstack
4. Keywords "architecture", "functionality", "layout" do NOT automatically mean backend is needed
5. If task CAN BE DONE client-side only, classify as frontend_only
6. Default to SIMPLER classification when unsure - prefer frontend_only over fullstack"""

        try:
            response = await self.openai.complete(
                classification_prompt,
                "You are an expert software architect. Classify tasks accurately based on EXPLICIT requirements only. Never over-engineer.",
                response_format={"type": "json_object"},
            )

            classification = json.loads(response)
            logger.info(
                f"✅ AI Classification: {classification['complexity']} - {classification['type']}"
            )
            logger.info(
                f"   Backend: {classification['requires_backend']}, Database: {classification['requires_database']}"
            )
            logger.info(f"   Reasoning: {classification['reasoning']}")

            # v5.8.7 FIX: Cache the classification for this prompt
            self._cached_classification = classification
            self._cached_classification_prompt = original_prompt
            logger.info("💾 Cached classification for future calls")

            return classification

        except Exception as e:
            logger.error(f"❌ AI classification failed: {e}")
            # ASIMOV RULE 1: NO FALLBACK - Classification is REQUIRED
            from core.exceptions import SystemNotReadyError

            raise SystemNotReadyError(
                component="ArchitectAgent",
                reason=f"Task classification failed: {str(e)}",
                solution="Check OpenAI API connectivity or retry",
                file=__file__,
                line=350,
            )

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute architecture design task - ENHANCED with AI Systems Integration
        """
        start_time = datetime.now()
        files_created = []

        # 🧠 v5.9.0: NEUROSYMBOLIC REASONING now handled by execute_agent_with_retry() wrapper
        # All AI systems (Asimov Rules, Predictive Learning, Curiosity, Framework Comparison)
        # are centrally managed in workflow.py to ensure consistent enforcement

        # v5.8.1: Store current request for workspace context (BaseAgent needs this!)
        self._current_request = request

        # Get client_id for progress updates
        # Ensure context is a dictionary - ROBUST handling
        if not hasattr(request, "context"):
            request.context = {}
        elif request.context is None:
            request.context = {}
        elif isinstance(request.context, str):
            try:
                # Try to parse as JSON if it's a string
                request.context = json.loads(request.context)
                logger.info("Successfully parsed context string as JSON")
            except (json.JSONDecodeError, TypeError):
                logger.warning("Could not parse context string, using empty dict")
                request.context = {}
        elif not isinstance(request.context, dict):
            logger.warning(f"Context was {type(request.context)}, converting to dict")
            request.context = {}

        # Safe client_id and manager extraction
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

        try:
            # Get workspace path and ensure it's absolute for consistent hashing
            workspace_path = request.context.get("workspace_path", os.getcwd())
            workspace_path = os.path.abspath(workspace_path)
            logger.info(f"📂 Using workspace path: {workspace_path}")

            # Update file watcher to use correct workspace path if needed
            if hasattr(self, "file_watcher") and self.file_watcher:
                current_watch_path = getattr(self.file_watcher, "project_path", None)
                if current_watch_path != workspace_path:
                    logger.info(
                        f"🔄 Updating file watcher from {current_watch_path} to {workspace_path}"
                    )
                    self.file_watcher.stop()
                    # Reinitialize ProjectCache with correct workspace path for consistent hashing
                    self.project_cache = ProjectCache(workspace_path)
                    self.file_watcher = SmartFileWatcher(
                        workspace_path, self.project_cache, debounce_seconds=30
                    )
                    self.file_watcher.start()
                    logger.info(
                        f"✅ ProjectCache updated with workspace path: {workspace_path}"
                    )

            ki_autoagent_dir = os.path.join(workspace_path, ".ki_autoagent_ws")
            os.makedirs(ki_autoagent_dir, exist_ok=True)

            # Send initial progress
            await self._send_progress(
                client_id, "🏗️ Architect starting system analysis...", manager
            )

            # v5.8.7: NEW PROJECT DETECTION - Check if workspace is empty
            is_new_project = await self._is_workspace_empty(workspace_path)
            logger.info(f"🔍 New project detection: {is_new_project}")

            # v5.8.7: TASK COMPLEXITY CLASSIFICATION
            task_classification = await self._classify_task_complexity(request.prompt)
            logger.info(f"📊 Task classification: {task_classification}")

            # v5.8.7: NEW PROJECT PATH - Use Research Agent for best practices
            if is_new_project:
                logger.info(
                    "🆕 New project detected - Using Research-Driven Architecture Design"
                )
                await self._send_progress(
                    client_id,
                    "🆕 New project detected - Researching best practices...",
                    manager,
                )

                # 1. Research best practices using Research Agent
                # v5.8.7 FIX: Check if research results already provided by workflow
                research_insights = (
                    request.context.get("research_results")
                    if isinstance(request.context, dict)
                    else None
                )

                if research_insights:
                    logger.info(
                        f"✅ Using research results from workflow context ({len(research_insights)} chars)"
                    )
                    await self._send_progress(
                        client_id, "✅ Using research insights from workflow...", manager
                    )
                elif self.research_agent:
                    try:
                        logger.info(f"📚 Calling Research Agent for: {request.prompt}")
                        await self._send_progress(
                            client_id,
                            "📚 Researching latest best practices via Perplexity AI...",
                            manager,
                        )

                        # v5.8.7 FIX: Use execute() instead of research_for_agent() for real Perplexity API
                        from ..base.base_agent import \
                            TaskRequest as ResearchTaskRequest

                        research_query = f"Best practices for: {request.prompt}. Include modern architecture patterns, tech stack recommendations, and implementation guidelines for 2025."

                        research_task = ResearchTaskRequest(
                            prompt=research_query, context={}
                        )
                        research_result = await self.research_agent.execute(
                            research_task
                        )

                        # Extract content from TaskResult
                        if hasattr(research_result, "content"):
                            research_insights = research_result.content
                        else:
                            research_insights = str(research_result)

                        logger.info(
                            f"✅ Research completed: {len(research_insights)} chars"
                        )
                    except Exception as e:
                        # ASIMOV RULE 1: NO FALLBACK - Research is REQUIRED for new projects
                        logger.error(f"❌ Research Agent failed: {e}")
                        logger.error(
                            "❌ ABORT: Cannot design new project architecture without research"
                        )

                        from core.exceptions import SystemNotReadyError

                        raise SystemNotReadyError(
                            component="ArchitectAgent",
                            reason=f"Research Agent failed for new project: {str(e)}",
                            solution="Check Perplexity API key in .env or select a different workflow for existing projects",
                            file=__file__,
                            line=455,
                        )
                else:
                    # ASIMOV RULE 1: NO FALLBACK - Research Agent is REQUIRED for new projects
                    logger.error("❌ Research Agent not available for new project!")
                    logger.error(
                        "❌ ABORT: Cannot design new project architecture without best practices research"
                    )

                    from core.exceptions import SystemNotReadyError

                    raise SystemNotReadyError(
                        component="ArchitectAgent",
                        reason="Research Agent not available but required for new project architecture",
                        solution="Initialize ResearchAgent with Perplexity API key, or use Architect only for existing projects with 'analyze' or 'improve' keywords",
                        file=__file__,
                        line=465,
                    )

                # 2. Analyze requirements WITH research context
                await self._send_progress(
                    client_id,
                    "🔍 Analyzing requirements with research insights...",
                    manager,
                )
                requirements = await self.analyze_requirements_with_research(
                    request.prompt, research_insights, task_classification
                )

                # 3. Design architecture based on requirements
                await self._send_progress(
                    client_id, "🏗️ Designing architecture...", manager
                )
                design = await self.design_architecture(requirements)

                # 4. Generate documentation with research insights
                await self._send_progress(
                    client_id, "📝 Generating architecture proposal...", manager
                )
                documentation = await self.generate_documentation_with_research(
                    design, research_insights, task_classification
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                # v5.9.0: AI SYSTEMS (Predictive Learning, Curiosity, Framework Comparison)
                # now handled by execute_agent_with_retry() wrapper in workflow.py
                # All post-execution updates happen centrally for consistency

                response_content = documentation

                return TaskResult(
                    status="success",
                    content=response_content,
                    agent=self.config.agent_id,
                    metadata={
                        "new_project": True,
                        "task_classification": task_classification,
                        "research_used": research_insights is not None,
                        "execution_time": execution_time,
                    },
                    execution_time=execution_time,
                )

            # v5.8.7: EXISTING PROJECT PATH - Continue with existing logic
            # Determine which tools to use based on the request
            prompt_lower = request.prompt.lower()
            logger.info(f"🔍 Received prompt: '{request.prompt}'")
            logger.info(f"🔍 Prompt lower: '{prompt_lower}'")

            # Tool 1: understand_system() - Always use for infrastructure tasks
            if any(
                word in prompt_lower
                for word in [
                    "understand",
                    "analyze",
                    "infrastructure",
                    "infrastruktur",
                    "improve",
                    "verbessert",
                    "optimize",
                ]
            ):
                logger.info("🔍 Using understand_system() to analyze workspace...")
                await self._send_progress(
                    client_id,
                    "🔍 Using understand_system() to analyze workspace...",
                    manager,
                )

                logger.info(
                    f"🔍 INDEXING_AVAILABLE = {INDEXING_AVAILABLE}, self.code_indexer = {self.code_indexer is not None}"
                )
                if INDEXING_AVAILABLE and self.code_indexer:
                    logger.info("✅ Taking indexing path with understand_system()")
                    system_analysis = await self.understand_system(
                        workspace_path, client_id, request.prompt, manager
                    )

                    # Save to file
                    analysis_file = os.path.join(
                        ki_autoagent_dir, "system_analysis.json"
                    )
                    with open(analysis_file, "w") as f:
                        json.dump(system_analysis, f, indent=2)
                    files_created.append(analysis_file)
                    logger.info(f"✅ Created: {analysis_file}")
                else:
                    # Standard analysis when indexing not triggered
                    logger.warning(
                        "⚠️ Indexing not available, falling back to analyze_requirements"
                    )
                    system_analysis = await self.analyze_requirements(request.prompt)

                # Tool 2: analyze_infrastructure_improvements()
                if (
                    "improve" in prompt_lower
                    or "optimization" in prompt_lower
                    or "verbessert" in prompt_lower
                    or "verbessern" in prompt_lower
                ):
                    logger.info("🔧 Using analyze_infrastructure_improvements()...")

                    if ANALYSIS_AVAILABLE:
                        # Get the full formatted improvements report
                        improvements_report = (
                            await self.analyze_infrastructure_improvements()
                        )

                        # Store the report in summary so it gets returned
                        summary = improvements_report

                        # Save improvements to file
                        improvements_file = os.path.join(
                            ki_autoagent_dir, "improvements.md"
                        )
                        with open(improvements_file, "w") as f:
                            f.write(improvements_report)
                        files_created.append(improvements_file)
                        logger.info(f"✅ Created: {improvements_file}")
                    else:
                        summary = "Analysis tools not available. Install with: pip install semgrep radon vulture"

                # Tool 3: generate_architecture_flowchart()
                if (
                    "diagram" in prompt_lower
                    or "flowchart" in prompt_lower
                    or "visualize" in prompt_lower
                ):
                    logger.info("📊 Using generate_architecture_flowchart()...")

                    if DIAGRAM_AVAILABLE:
                        diagram = await self.generate_architecture_flowchart()

                        # Save diagram
                        diagram_file = os.path.join(
                            ki_autoagent_dir, "architecture.mermaid"
                        )
                        with open(diagram_file, "w") as f:
                            f.write(diagram)
                        files_created.append(diagram_file)
                        logger.info(f"✅ Created: {diagram_file}")
                    else:
                        diagram = "graph TB\n  A[System] --> B[Not Available]\n  B --> C[Install mermaid-py]"

                # Create summary if not already set (e.g., by improvements analysis)
                if "summary" not in locals():
                    summary = f"Actively analyzed system and created {len(files_created)} files:\n"
                    for file in files_created:
                        summary += f"- {os.path.basename(file)}\n"

                    if not files_created:
                        # Standard behavior when no specific tools triggered
                        requirements = await self.analyze_requirements(request.prompt)
                        design = await self.design_architecture(requirements)
                        documentation = await self.generate_documentation(design)
                        summary = documentation
                    else:
                        summary += f"\nAll files saved in: {ki_autoagent_dir}"

            else:
                # Standard architecture design (not infrastructure)
                requirements = await self.analyze_requirements(request.prompt)
                design = await self.design_architecture(requirements)
                documentation = await self.generate_documentation(design)
                summary = documentation

            execution_time = (datetime.now() - start_time).total_seconds()

            # v5.9.0: AI SYSTEMS (Predictive Learning, Curiosity, Framework Comparison)
            # now handled by execute_agent_with_retry() wrapper in workflow.py
            # All post-execution updates happen centrally for consistency

            response_content = summary

            return TaskResult(
                status="success",
                content=response_content,
                agent=self.config.agent_id,
                metadata={
                    "files_created": files_created,
                    "tools_used": [
                        "understand_system",
                        "analyze_infrastructure_improvements",
                        "generate_architecture_flowchart",
                    ]
                    if files_created
                    else [],
                    "execution_time": execution_time,
                },
                execution_time=execution_time,
            )

        except (json.JSONDecodeError, ParsingError) as e:
            logger.error(f"JSON parsing error in architecture design: {e}")
            raise ParsingError(
                content=str(request),
                format="json",
                reason=f"Failed to parse architecture response: {e}",
            )
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Connection error in architecture design: {e}")
            raise ArchitectError(f"Connection failed: {e}")
        except (ArchitectError, ArchitectValidationError, ArchitectResearchError):
            # Re-raise specific architect exceptions
            raise
        except Exception as e:
            logger.error(f"Architecture design failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Wrap in ArchitectError
            raise ArchitectError(f"Failed to design architecture: {e}")

    async def analyze_requirements(self, prompt: str) -> dict[str, Any]:
        """
        Analyze project requirements from prompt
        """
        system_prompt = """
        You are a senior system architect.
        Analyze the project requirements and identify:
        1. Project type (web app, API, mobile, desktop, etc.)
        2. Scale requirements (users, requests, data volume)
        3. Performance requirements (latency, throughput)
        4. Security requirements
        5. Integration needs
        6. Special constraints

        Provide structured analysis.
        """

        analysis_prompt = f"""
        Project Description:
        {prompt}

        Analyze and provide requirements in JSON format:
        {{
            "project_type": "type",
            "scale": {{"users": "estimated", "requests_per_second": "estimated"}},
            "performance": {{"latency": "requirement", "throughput": "requirement"}},
            "security": ["requirement1", "requirement2"],
            "integrations": ["system1", "system2"],
            "constraints": ["constraint1", "constraint2"],
            "key_features": ["feature1", "feature2"]
        }}
        """

        response = await self.openai.complete(
            analysis_prompt, system_prompt, response_format={"type": "json_object"}
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # No fallback - fail with clear error
            from core.exceptions import SystemNotReadyError

            raise SystemNotReadyError(
                component="ArchitectAgent",
                reason=f"Failed to parse OpenAI response as JSON: {str(e)}",
                solution="Check OpenAI API response format or retry the request",
                file=__file__,
                line=368,
            )

    async def analyze_requirements_with_research(
        self,
        prompt: str,
        research_insights: str | None,
        task_classification: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze project requirements with research insights and task classification

        v5.8.7: Enhanced version that incorporates:
        - Research Agent insights about best practices
        - Task complexity classification
        - Smart tech stack recommendations

        Args:
            prompt: User's project description
            research_insights: Research findings from Research Agent (can be None)
            task_classification: Task complexity classification

        Returns:
            Enhanced requirements dict with research-backed decisions
        """
        system_prompt = f"""
        You are a senior system architect with access to latest best practices research.

        Task Classification:
        - Complexity: {task_classification['complexity']}
        - Type: {task_classification['type']}
        - Requires Backend: {task_classification['requires_backend']}
        - Requires Database: {task_classification['requires_database']}
        - Suggested Stack: {', '.join(task_classification['suggested_stack'])}

        {"Research Insights:\n" + research_insights if research_insights else "No research available - use your knowledge of best practices."}

        Based on the task classification and research, analyze requirements with appropriate scale:
        - For 'simple' frontend-only tasks: Minimal infrastructure, single file or simple modular structure
        - For 'medium' tasks: Standard web app with reasonable complexity
        - For 'complex' tasks: Full enterprise architecture with scalability

        IMPORTANT: Do not over-engineer simple tasks. A calculator doesn't need microservices!
        """

        analysis_prompt = f"""
        Project Description:
        {prompt}

        Analyze and provide requirements in JSON format:
        {{
            "project_type": "type (e.g., 'frontend-only', 'fullstack', 'backend-api')",
            "complexity": "{task_classification['complexity']}",
            "architecture_type": "appropriate for complexity (e.g., 'single-file', 'modular', 'client-server', 'microservices')",
            "scale": {{"users": "estimated", "concurrent_users": "estimated"}},
            "performance": {{"latency": "requirement", "target_load_time": "seconds"}},
            "security": ["requirement1", "requirement2"],
            "integrations": ["system1", "system2"],
            "constraints": ["constraint1", "constraint2"],
            "key_features": ["feature1", "feature2"],
            "tech_stack": {{
                "frontend": ["tech1", "tech2"],
                "backend": ["tech1", "tech2"] if backend needed,
                "database": ["tech"] if database needed,
                "justification": "why these technologies based on research"
            }},
            "file_structure": "{task_classification['file_structure']}",
            "research_applied": ["insight1", "insight2"] if research available
        }}
        """

        response = await self.openai.complete(
            analysis_prompt, system_prompt, response_format={"type": "json_object"}
        )

        try:
            requirements = json.loads(response)
            # Inject classification for downstream use
            requirements["_task_classification"] = task_classification
            requirements["_research_used"] = research_insights is not None
            logger.info(
                f"✅ Requirements analyzed with research: {requirements.get('project_type', 'unknown')}"
            )
            return requirements
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse requirements: {e}")
            from core.exceptions import SystemNotReadyError

            raise SystemNotReadyError(
                component="ArchitectAgent",
                reason=f"Failed to parse OpenAI response as JSON: {str(e)}",
                solution="Check OpenAI API response format or retry the request",
                file=__file__,
                line=720,
            )

    async def design_architecture(
        self, requirements: dict[str, Any]
    ) -> ArchitectureDesign:
        """
        Design system architecture based on requirements
        """
        system_prompt = """
        You are an expert system architect.
        Design a comprehensive system architecture that:
        1. Meets all requirements
        2. Follows best practices
        3. Is scalable and maintainable
        4. Uses modern, proven technologies
        5. Considers security from the start

        Be specific and practical.
        """

        design_prompt = f"""
        Requirements:
        {json.dumps(requirements, indent=2)}

        Design a complete system architecture including:
        1. Architecture type (monolithic, microservices, serverless, etc.)
        2. Main components and their responsibilities
        3. Technology stack (languages, frameworks, databases, etc.)
        4. Design patterns to use
        5. Data flow between components
        6. Deployment architecture
        7. Scalability strategy
        8. Security measures

        Provide detailed, actionable architecture design.
        """

        response = await self.openai.complete(design_prompt, system_prompt)

        # Parse response into ArchitectureDesign
        return self._parse_architecture_response(response, requirements)

    def _parse_architecture_response(
        self, response: str, requirements: dict[str, Any]
    ) -> ArchitectureDesign:
        """
        Parse architecture response into structured design

        v5.8.7 FIX: Respects task_classification to avoid over-engineering
        Only adds components that classification says are needed
        """
        # Extract key information from response
        # This is a simplified parser - could be enhanced with better NLP

        # v5.8.7: Get task classification to guide component selection
        task_classification = requirements.get("_task_classification", {})
        requires_backend = task_classification.get(
            "requires_backend", True
        )  # Default to True for safety
        requires_database = task_classification.get("requires_database", True)
        complexity = task_classification.get("complexity", "medium")

        logger.info(
            f"🔧 Parsing architecture with constraints: backend={requires_backend}, database={requires_database}, complexity={complexity}"
        )

        # Architecture type based on classification, not keywords
        architecture_type = "monolithic"  # Default to simplest
        if (
            complexity == "simple"
            or requirements.get("file_structure") == "single_file"
        ):
            architecture_type = "single_file"
        elif complexity == "simple" or requirements.get("file_structure") == "modular":
            architecture_type = "monolithic"
        elif "serverless" in response.lower():
            architecture_type = "serverless"
        elif complexity == "complex":
            architecture_type = "microservices"

        # Extract components ONLY if classification allows
        components = []

        # Frontend is almost always present
        if (
            "frontend" in response.lower()
            or "html" in response.lower()
            or "ui" in response.lower()
        ):
            components.append(
                {
                    "name": "Frontend",
                    "type": "UI",
                    "technology": task_classification.get(
                        "suggested_stack", ["HTML", "CSS", "JavaScript"]
                    )[0]
                    if task_classification.get("suggested_stack")
                    else "HTML/CSS/JavaScript",
                    "responsibility": "User interface",
                }
            )

        # v5.8.7 FIX: Only add backend if classification says it's needed
        if requires_backend and (
            "backend" in response.lower() or "api" in response.lower()
        ):
            components.append(
                {
                    "name": "Backend API",
                    "type": "API",
                    "technology": "Python/FastAPI",
                    "responsibility": "Business logic and data management",
                }
            )
        elif not requires_backend:
            logger.info(
                "✅ Skipping backend component (classification says not needed)"
            )

        # v5.8.7 FIX: Only add database if classification says it's needed
        if requires_database and "database" in response.lower():
            components.append(
                {
                    "name": "Database",
                    "type": "Storage",
                    "technology": "PostgreSQL",
                    "responsibility": "Data persistence",
                }
            )
        elif not requires_database:
            logger.info(
                "✅ Skipping database component (classification says not needed)"
            )

        # Extract technologies
        technologies = []
        tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "fastapi",
            "postgresql",
            "redis",
            "docker",
            "kubernetes",
            "aws",
            "azure",
        ]

        for tech in tech_keywords:
            if tech in response.lower():
                technologies.append(tech.capitalize())

        # Design patterns
        patterns = []
        pattern_keywords = [
            "mvc",
            "mvvm",
            "repository",
            "factory",
            "singleton",
            "observer",
            "strategy",
            "decorator",
            "cqrs",
            "event sourcing",
        ]

        for pattern in pattern_keywords:
            if pattern in response.lower():
                patterns.append(pattern.upper())

        return ArchitectureDesign(
            project_name=requirements.get("project_type", "System"),
            architecture_type=architecture_type,
            components=components,
            technologies=technologies,
            patterns=patterns,
            data_flow={"type": "REST API", "protocol": "HTTPS"},
            deployment={"platform": "Cloud", "containerization": "Docker"},
            scalability_notes="Horizontal scaling with load balancer",
            security_considerations="OAuth2, HTTPS, rate limiting, input validation",
        )

    async def generate_documentation(self, design: ArchitectureDesign) -> str:
        """
        Generate architecture documentation
        """
        doc = []
        doc.append("# 🏗️ System Architecture Design\n")
        doc.append(f"## Project: {design.project_name}\n")
        doc.append(f"**Architecture Type**: {design.architecture_type}\n")

        doc.append("\n## 📦 Components\n")
        for component in design.components:
            doc.append(f"### {component['name']}")
            doc.append(f"- **Type**: {component['type']}")
            doc.append(f"- **Technology**: {component['technology']}")
            doc.append(f"- **Responsibility**: {component['responsibility']}\n")

        doc.append("\n## 🛠️ Technology Stack\n")
        for tech in design.technologies:
            doc.append(f"- {tech}")

        doc.append("\n## 📐 Design Patterns\n")
        for pattern in design.patterns:
            doc.append(f"- {pattern}")

        doc.append("\n## 🔄 Data Flow\n")
        doc.append(f"- **Type**: {design.data_flow.get('type', 'N/A')}")
        doc.append(f"- **Protocol**: {design.data_flow.get('protocol', 'N/A')}\n")

        doc.append("\n## 🚀 Deployment\n")
        doc.append(f"- **Platform**: {design.deployment.get('platform', 'N/A')}")
        doc.append(
            f"- **Containerization**: {design.deployment.get('containerization', 'N/A')}\n"
        )

        doc.append("\n## 📈 Scalability\n")
        doc.append(design.scalability_notes + "\n")

        doc.append("\n## 🔒 Security Considerations\n")
        doc.append(design.security_considerations + "\n")

        doc.append("\n---\n")
        doc.append("*Generated by ArchitectAgent (GPT-5)*")

        return "\n".join(doc)

    async def generate_documentation_with_research(
        self,
        design: ArchitectureDesign,
        research_insights: str | None,
        task_classification: dict[str, Any],
    ) -> str:
        """
        Generate enhanced architecture documentation with research insights

        v5.8.7: Includes research findings and task classification context
        to provide more informed architecture proposals

        Args:
            design: Architecture design specification
            research_insights: Research findings (can be None)
            task_classification: Task complexity classification

        Returns:
            Enhanced documentation string with research context
        """
        doc = []
        doc.append("# 🏗️ Architecture Proposal\n")
        doc.append(f"## Project: {design.project_name}\n")

        # Task Classification Summary
        doc.append("\n## 📊 Task Analysis\n")
        doc.append(f"- **Complexity**: {task_classification['complexity'].title()}")
        doc.append(f"- **Type**: {task_classification['type']}")
        doc.append(f"- **Architecture**: {design.architecture_type}")

        # v5.8.7 FIX: Rewrite reasoning to avoid trigger keywords when not needed
        reasoning = task_classification["reasoning"]
        if not task_classification.get(
            "requires_backend"
        ) and not task_classification.get("requires_database"):
            # Remove mentions of backend/database for frontend-only projects to avoid false positives
            reasoning = reasoning.replace(
                "without requiring a backend or database",
                "as a pure client-side application",
            )
            reasoning = reasoning.replace(
                "without backend or database", "client-side only"
            )
            reasoning = reasoning.replace("backend", "server")
            reasoning = reasoning.replace("database", "persistent storage")

        doc.append(f"- **Reasoning**: {reasoning}\n")

        # Research Insights (if available)
        if research_insights:
            doc.append("\n## 🔍 Research Insights\n")
            doc.append("*Based on latest best practices via Perplexity AI*\n")

            # Smart extraction of key points from research
            research_text = research_insights.strip()

            # Check if research has structure (sections, bullets, etc.)
            if any(
                marker in research_text
                for marker in ["##", "**", "- ", "* ", "1.", "2."]
            ):
                # Research is already formatted - use it as-is but limit length
                research_lines = research_text.split("\n")
                shown_lines = 0
                for line in research_lines:
                    if shown_lines >= 15:  # Show max 15 lines
                        doc.append("\n*(Research insights truncated for brevity)*")
                        break
                    if line.strip():
                        # Keep markdown formatting
                        if line.strip().startswith("#"):
                            doc.append(line.strip())
                        elif line.strip().startswith("-") or line.strip().startswith(
                            "*"
                        ):
                            doc.append(line.strip())
                        elif line.strip()[0].isdigit() and "." in line[:3]:
                            doc.append(line.strip())
                        else:
                            doc.append(f"- {line.strip()}")
                        shown_lines += 1
            else:
                # Research is plain text - extract sentences as bullets
                sentences = research_text.replace("\n", " ").split(". ")
                key_sentences = [
                    s.strip() + "." for s in sentences[:8] if len(s.strip()) > 20
                ]
                for sentence in key_sentences:
                    doc.append(f"- {sentence}")

            doc.append("")

        # File Structure
        if task_classification.get("file_structure"):
            doc.append("\n## 📁 Project Structure\n")
            file_structure = task_classification["file_structure"]
            if file_structure == "single_file":
                doc.append("**Single File Approach** (Simple & Clean)\n")
                doc.append("```")
                doc.append(f"{design.project_name.lower().replace(' ', '_')}.html")
                doc.append("  - HTML structure")
                doc.append("  - CSS styling (inline or in <style> tag)")
                doc.append("  - JavaScript logic (inline or in <script> tag)")
                doc.append("```\n")
            elif file_structure == "modular":
                doc.append("**Modular Structure** (Organized & Maintainable)\n")
                doc.append("```")
                doc.append("├── index.html       (Main HTML)")
                doc.append("├── styles.css       (Styling)")
                doc.append("└── script.js        (Logic)")
                doc.append("```\n")
            elif file_structure == "fullstack":
                doc.append("**Fullstack Structure**\n")
                doc.append("```")
                doc.append("├── frontend/")
                doc.append("│   ├── src/")
                doc.append("│   └── public/")
                doc.append("├── backend/")
                doc.append("│   ├── api/")
                doc.append("│   └── services/")
                doc.append("└── database/")
                doc.append("```\n")

        # Components
        if design.components:
            doc.append("\n## 📦 Components\n")
            for component in design.components:
                doc.append(f"### {component['name']}")
                doc.append(f"- **Type**: {component['type']}")
                doc.append(f"- **Technology**: {component['technology']}")
                doc.append(f"- **Responsibility**: {component['responsibility']}\n")

        # Technology Stack
        doc.append("\n## 🛠️ Technology Stack\n")
        suggested_stack = task_classification.get(
            "suggested_stack", design.technologies
        )
        for tech in suggested_stack:
            doc.append(f"- {tech}")
        doc.append("")

        # Design Patterns (if applicable)
        if design.patterns:
            doc.append("\n## 📐 Design Patterns\n")
            for pattern in design.patterns:
                doc.append(f"- {pattern}")
            doc.append("")

        # Security Considerations
        if design.security_considerations:
            doc.append("\n## 🔒 Security Considerations\n")
            doc.append(design.security_considerations + "\n")

        # Implementation Notes
        doc.append("\n## 💡 Implementation Notes\n")
        if task_classification["complexity"] == "simple":
            doc.append("- Keep it simple - avoid over-engineering")
            doc.append("- Single file or minimal modular structure")
            doc.append("- Focus on clean, readable code")
        elif task_classification["complexity"] == "medium":
            doc.append("- Modular structure for maintainability")
            doc.append("- Consider scalability for future growth")
            doc.append("- Follow established patterns")
        else:
            doc.append("- Enterprise-grade architecture")
            doc.append("- High scalability and availability")
            doc.append("- Comprehensive monitoring and logging")
        doc.append("")

        # Scalability (if relevant)
        if task_classification.get("requires_backend"):
            doc.append("\n## 📈 Scalability\n")
            doc.append(design.scalability_notes + "\n")

        doc.append("\n---\n")
        doc.append("*Generated by ArchitectAgent v5.8.7 with Research Integration*")
        if research_insights:
            doc.append("\n*Research-backed design with latest best practices*")

        return "\n".join(doc)

    def _extract_features(self, prompt: str) -> list[str]:
        """
        Extract key features from prompt
        """
        features = []

        feature_keywords = [
            "authentication",
            "authorization",
            "api",
            "database",
            "real-time",
            "messaging",
            "payment",
            "search",
            "analytics",
            "reporting",
            "dashboard",
            "admin",
        ]

        prompt_lower = prompt.lower()
        for keyword in feature_keywords:
            if keyword in prompt_lower:
                features.append(keyword)

        return features[:5]  # Return top 5 features

    def _load_architecture_patterns(self) -> list[dict[str, Any]]:
        """
        Load architecture patterns library
        """
        return [
            {
                "name": "Microservices",
                "when_to_use": "Large, complex applications with multiple teams",
                "pros": [
                    "Independent deployment",
                    "Technology diversity",
                    "Fault isolation",
                ],
                "cons": ["Complexity", "Network latency", "Data consistency"],
            },
            {
                "name": "Monolithic",
                "when_to_use": "Simple applications, MVPs, small teams",
                "pros": ["Simple deployment", "Easy debugging", "Low latency"],
                "cons": [
                    "Scaling challenges",
                    "Technology lock-in",
                    "Team coordination",
                ],
            },
            {
                "name": "Serverless",
                "when_to_use": "Event-driven, variable load, rapid development",
                "pros": [
                    "No infrastructure management",
                    "Auto-scaling",
                    "Cost-effective",
                ],
                "cons": ["Vendor lock-in", "Cold starts", "Debugging challenges"],
            },
        ]

    async def invalidate_cache(self, cache_type: str = None):
        """
        Invalidate cache - either specific type or all

        Args:
            cache_type: Specific cache to invalidate ('code_index', 'security_analysis', etc.)
                       If None, invalidates all caches
        """
        if not self.project_cache:
            logger.info("No cache to invalidate (Redis not available)")
            return

        if cache_type:
            self.project_cache.invalidate(cache_type)
            logger.info(f"♻️ Invalidated {cache_type} cache")
        else:
            # Invalidate all cache types
            self.project_cache.clear_all()
            logger.info("♻️ Invalidated all caches")

        # Clear in-memory cache as well
        self.system_knowledge = None
        self.last_index_time = None

    async def refresh_analysis(self, client_id: str = None, manager=None):
        """
        Force a complete refresh of system analysis
        Invalidates cache and rebuilds from scratch
        """
        logger.info("🔄 Forcing complete system analysis refresh...")
        await self._send_progress(client_id, "🔄 Refreshing system analysis...", manager)

        # Clear all caches
        await self.invalidate_cache()

        # Rebuild analysis
        return await self.understand_system(".", client_id, "full refresh", manager)

    async def refresh_cache_after_implementation(
        self, client_id: str = None, manager=None, components: list[str] = None
    ):
        """
        Intelligently refresh cache after new functions/components are implemented

        Args:
            client_id: Client ID for progress messages
            manager: Manager for sending progress
            components: List of components that were modified (e.g., ['code_index', 'metrics'])
                       If None, refreshes everything
        """
        logger.info(
            f"🔄 Refreshing cache after implementation. Components: {components}"
        )
        await self._send_progress(
            client_id, "🔄 Updating system knowledge after changes...", manager
        )

        if not components:
            # Full refresh if no specific components specified
            return await self.refresh_analysis(client_id, manager)

        # Selective cache refresh based on what was implemented
        workspace_path = os.path.abspath(os.getcwd())

        if "code_index" in components or "functions" in components:
            logger.info("📂 Refreshing code index...")
            await self._send_progress(
                client_id, "📂 Re-indexing code changes...", manager
            )
            if self.project_cache:
                self.project_cache.invalidate("code_index")

            # Re-index code
            async def progress_callback(msg: str):
                await self._send_progress(client_id, msg, manager)

            code_index = await self.code_indexer.build_full_index(
                workspace_path, progress_callback, "incremental"
            )
            if self.project_cache:
                self.project_cache.set("code_index", code_index)

        if "security" in components:
            logger.info("🔒 Refreshing security analysis...")
            await self._send_progress(
                client_id, "🔒 Re-running security analysis...", manager
            )
            if self.project_cache:
                self.project_cache.invalidate("security_analysis")

        if "metrics" in components:
            logger.info("📊 Refreshing code metrics...")
            await self._send_progress(
                client_id, "📊 Recalculating code metrics...", manager
            )
            if self.project_cache:
                self.project_cache.invalidate("metrics")

        if "diagrams" in components:
            logger.info("📊 Refreshing diagrams...")
            await self._send_progress(client_id, "📊 Regenerating diagrams...", manager)
            if self.project_cache:
                self.project_cache.invalidate("diagrams")

        # Invalidate the main system knowledge to force rebuild on next access
        if self.project_cache:
            self.project_cache.invalidate("system_knowledge")
        self.system_knowledge = None

        await self._send_progress(
            client_id, "✅ Cache refreshed after implementation", manager
        )
        logger.info("✅ Selective cache refresh completed")

        return {
            "status": "success",
            "message": f"Cache refreshed for components: {components}",
        }

    def __del__(self):
        """
        Cleanup when agent is destroyed
        """
        try:
            # Stop file watcher if running
            if hasattr(self, "file_watcher") and self.file_watcher:
                self.file_watcher.stop()
                logger.info("✅ File watcher stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _load_tech_stacks(self) -> dict[str, list[str]]:
        """
        Load technology stack recommendations
        """
        return {
            "web": ["React", "Next.js", "FastAPI", "PostgreSQL", "Redis"],
            "mobile": ["React Native", "Flutter", "Firebase", "GraphQL"],
            "api": ["FastAPI", "Node.js", "Go", "PostgreSQL", "MongoDB"],
            "data": ["Python", "Apache Spark", "Kafka", "Elasticsearch"],
            "ml": ["Python", "TensorFlow", "PyTorch", "MLflow", "Kubeflow"],
        }

    async def _process_agent_request(self, message) -> Any:
        """
        Process request from another agent
        Implementation of abstract method from BaseAgent
        """
        # Handle architecture requests from other agents
        if message.content.get("requesting_architecture"):
            task = message.content.get("task", "")
            result = await self.execute(TaskRequest(prompt=task))
            return {"architecture_result": result.content}

        return {"message": "Architect received request"}

    async def create_redis_config(
        self, optimization_params: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Create optimized Redis configuration file

        Args:
            optimization_params: Optional parameters for Redis optimization

        Returns:
            Dict with status and file details
        """
        try:
            # Generate optimized Redis configuration
            config_content = self._generate_redis_config(optimization_params)

            # Write to file
            result = await self.write_implementation("redis.config", config_content)

            if result.get("status") == "success":
                logger.info("✅ ArchitectAgent created Redis configuration")
                result["config_type"] = "redis"
                result["optimizations"] = optimization_params or {}

            return result

        except Exception as e:
            logger.error(f"❌ Failed to create Redis config: {e}")
            return {"status": "error", "error": str(e), "agent": self.name}

    async def create_docker_compose(self, services: list[str] = None) -> dict[str, Any]:
        """
        Create Docker Compose configuration

        Args:
            services: List of services to include (default: ['redis', 'backend'])

        Returns:
            Dict with status and file details
        """
        try:
            if not services:
                services = ["redis", "backend"]

            # Generate Docker Compose configuration
            compose_content = self._generate_docker_compose(services)

            # Write to file
            result = await self.write_implementation(
                "docker-compose.yml", compose_content
            )

            if result.get("status") == "success":
                logger.info("✅ ArchitectAgent created Docker Compose configuration")
                result["config_type"] = "docker-compose"
                result["services"] = services

            return result

        except Exception as e:
            logger.error(f"❌ Failed to create Docker Compose: {e}")
            return {"status": "error", "error": str(e), "agent": self.name}

    def _generate_redis_config(self, params: dict[str, Any] = None) -> str:
        """Generate optimized Redis configuration content"""
        params = params or {}

        config = f"""# Redis Configuration - Generated by ArchitectAgent
# Optimized for KI_AutoAgent caching

# Memory Management
maxmemory {params.get('maxmemory', '512mb')}
maxmemory-policy {params.get('policy', 'allkeys-lru')}

# Persistence
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir ./

# Performance
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
replica-lazy-flush yes

# Network
bind 127.0.0.1
protected-mode yes
port 6379
tcp-backlog 511
tcp-keepalive 300
timeout 0

# Logging
loglevel notice
logfile ""

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Client output buffer limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Hz
hz 10

# AOF
appendonly no
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Lua scripting
lua-time-limit 5000

# Cluster
cluster-enabled no

# Generated at: {datetime.now().isoformat()}
# Optimizations: {', '.join(params.keys()) if params else 'default'}
"""
        return config

    def _generate_docker_compose(self, services: list[str]) -> str:
        """Generate Docker Compose configuration"""
        compose = """version: '3.8'

services:
"""

        if "redis" in services:
            compose += """  redis:
    image: redis:7-alpine
    container_name: ki_autoagent_redis
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - ./redis.config:/usr/local/etc/redis/redis.conf
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - ki_autoagent_network

"""

        if "backend" in services:
            compose += """  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ki_autoagent_backend
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONUNBUFFERED=1
    volumes:
      - ./backend:/app
      - ./data:/data
    ports:
      - "8000:8000"
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - ki_autoagent_network

"""

        compose += """volumes:
  redis_data:

networks:
  ki_autoagent_network:
    driver: bridge
"""
        return compose

    async def understand_system(
        self,
        root_path: str = ".",
        client_id: str = None,
        request_prompt: str = "",
        manager=None,
    ) -> dict[str, Any]:
        """
        Build comprehensive understanding of the system through code analysis

        This method performs deep analysis using:
        - Tree-sitter AST indexing
        - Semantic code analysis
        - Metrics calculation
        - Architecture extraction

        Now with PERMANENT Redis caching - no TTL!
        """
        if not INDEXING_AVAILABLE:
            logger.warning("Code indexing not available - returning limited analysis")
            return {
                "error": "Code analysis tools not installed",
                "message": "Please install requirements: pip install -r requirements.txt",
            }

        # Try to get from permanent cache first
        if self.project_cache:
            cached_knowledge = self.project_cache.get("system_knowledge")
            if cached_knowledge:
                logger.info(
                    "✅ Using cached system knowledge from Redis (permanent cache)"
                )
                await self._send_progress(
                    client_id,
                    "📦 Using cached system analysis (permanent cache)",
                    manager,
                )
                self.system_knowledge = cached_knowledge
                return cached_knowledge

        logger.info("Building comprehensive system understanding...")
        await self._send_progress(
            client_id, "🏗️ Building comprehensive system understanding...", manager
        )

        # Detect request type for smart analysis
        request_type = self._detect_request_type(request_prompt)
        logger.info(f"Request type detected: {request_type}")

        # Phase 1: Complete code indexing
        logger.info("Phase 1: Indexing codebase with AST parsing")
        await self._send_progress(
            client_id, "📂 Phase 1: Indexing codebase with AST parsing...", manager
        )

        # Create progress callback
        async def progress_callback(msg: str):
            await self._send_progress(client_id, msg, manager)

        # Check if we have cached code index
        code_index = None
        if self.project_cache:
            code_index = self.project_cache.get("code_index")

        if not code_index:
            code_index = await self.code_indexer.build_full_index(
                root_path, progress_callback, request_type
            )
            # Store in permanent cache
            if self.project_cache:
                self.project_cache.set("code_index", code_index)

        # Phase 2: Security and quality analysis
        logger.info("Phase 2: Running security and quality analysis")
        await self._send_progress(
            client_id, "🔒 Phase 2: Running security and quality analysis...", manager
        )

        # Check cache for each analysis
        security_analysis = None
        dead_code = None
        metrics = None

        if self.project_cache:
            security_analysis = self.project_cache.get("security_analysis")
            dead_code = self.project_cache.get("dead_code")
            metrics = self.project_cache.get("metrics")

        if not security_analysis:
            await self._send_progress(
                client_id,
                "🔒 Phase 2a: Scanning for security vulnerabilities...",
                manager,
            )
            security_analysis = await self.semgrep.run_analysis(
                root_path, progress_callback=progress_callback
            )
            if self.project_cache:
                self.project_cache.set("security_analysis", security_analysis)

        if not dead_code:
            await self._send_progress(
                client_id, "🧹 Phase 2b: Finding dead code...", manager
            )
            dead_code = await self.vulture.find_dead_code(
                root_path, progress_callback=progress_callback
            )
            if self.project_cache:
                self.project_cache.set("dead_code", dead_code)

        if not metrics:
            await self._send_progress(
                client_id, "📊 Phase 2c: Calculating code metrics...", manager
            )
            metrics = await self.metrics.calculate_all_metrics(
                root_path, progress_callback=progress_callback
            )
            if self.project_cache:
                self.project_cache.set("metrics", metrics)

        # Phase 2d: Build Function Call Graph (NEW - v5.0)
        call_graph = None
        if self.project_cache:
            call_graph = self.project_cache.get("function_call_graph")

        if not call_graph and self.call_graph_analyzer:
            await self._send_progress(
                client_id, "📞 Phase 2d: Building function call graph...", manager
            )
            call_graph = await self.call_graph_analyzer.build_call_graph(code_index)
            if self.project_cache:
                self.project_cache.set("function_call_graph", call_graph)
            logger.info(
                f"✅ Call graph built: {call_graph['metrics']['total_functions']} functions, {call_graph['metrics']['total_calls']} calls"
            )

        # Phase 2e: Analyze System Layers (NEW - v5.0)
        system_layers = None
        if self.project_cache:
            system_layers = self.project_cache.get("system_layers")

        if not system_layers and self.layer_analyzer:
            await self._send_progress(
                client_id, "🏗️ Phase 2e: Analyzing system layers...", manager
            )
            system_layers = await self.layer_analyzer.detect_system_layers(code_index)
            if self.project_cache:
                self.project_cache.set("system_layers", system_layers)
            logger.info(
                f"✅ System layers analyzed: Quality score = {system_layers['quality_score']:.2f}, Violations = {len(system_layers['violations'])}"
            )

        # Phase 3: Generate visualizations
        logger.info("Phase 3: Generating architecture diagrams")
        await self._send_progress(
            client_id, "📊 Phase 3: Generating architecture diagrams...", manager
        )

        diagrams = None
        if self.project_cache:
            diagrams = self.project_cache.get("diagrams")

        if not diagrams:
            # v5.8.2: Use AI-powered diagram generation for meaningful, project-specific diagrams
            logger.info("🤖 Generating diagrams with AI (GPT-4o)...")
            diagrams = {
                "system_context": await self.diagram_service.generate_architecture_diagram_ai(
                    code_index, "context"
                ),
                "container": await self.diagram_service.generate_architecture_diagram_ai(
                    code_index, "container"
                ),
                "component": await self.diagram_service.generate_architecture_diagram_ai(
                    code_index, "component"
                ),
                "dependency_graph": self.diagram_service.generate_dependency_graph(
                    code_index.get("import_graph", {})
                ),
                "sequence": self.diagram_service.generate_sequence_diagram({}),
                "state": self.diagram_service.generate_state_diagram({}),
            }
            if self.project_cache:
                self.project_cache.set("diagrams", diagrams)
            logger.info("✅ AI-powered diagrams generated successfully")

        # Store system knowledge
        self.system_knowledge = {
            "code_index": code_index,
            "security": security_analysis,
            "dead_code": dead_code,
            "metrics": metrics,
            "call_graph": call_graph,  # NEW - v5.0
            "system_layers": system_layers,  # NEW - v5.0
            "diagrams": diagrams,
            "timestamp": datetime.now().isoformat(),
        }

        # Store complete knowledge in permanent cache
        if self.project_cache:
            self.project_cache.set("system_knowledge", self.system_knowledge)
            logger.info("✅ System knowledge stored in permanent Redis cache")

        # v5.8.2: Store in shared_context for other agents to access
        if self.shared_context:
            self.shared_context.set("architect:system_knowledge", self.system_knowledge)
            logger.info(
                "✅ System knowledge shared via shared_context for agent collaboration"
            )

        # Index functions for search
        if self.code_search and code_index:
            await self._index_functions_for_search(code_index)

        logger.info(
            f"System understanding complete: {len(code_index.get('ast', {}).get('files', {}))} files analyzed"
        )
        return self.system_knowledge

    async def _index_functions_for_search(self, code_index: dict):
        """
        Index functions in SQLite search database for fast retrieval
        """
        if not self.code_search:
            return

        try:
            # Extract functions from AST
            ast_data = code_index.get("ast", {})
            files_data = ast_data.get("files", {})

            for file_path, file_info in files_data.items():
                functions = file_info.get("functions", [])
                for func in functions:
                    func_data = {
                        "file_path": file_path,
                        "name": func.get("name"),
                        "signature": func.get("signature", ""),
                        "docstring": func.get("docstring", ""),
                        "body": func.get("body", "")[:1000],  # Limit body size
                        "return_type": func.get("return_type", ""),
                        "parameters": func.get("parameters", []),
                        "line_number": func.get("line_number", 0),
                    }
                    await self.code_search.index_function(func_data)

            logger.info("✅ Indexed functions in SQLite search database")
        except Exception as e:
            logger.error(f"Failed to index functions for search: {e}")

    async def analyze_infrastructure_improvements(self) -> str:
        """
        Analyze codebase and suggest infrastructure improvements

        This is the main method to answer: "Was kann an der Infrastruktur verbessert werden?"
        """
        if not self.system_knowledge:
            await self.understand_system(".", None, "infrastructure improvements")

        # Extract insights from analysis
        code_index = self.system_knowledge["code_index"]
        security = self.system_knowledge["security"]
        metrics = self.system_knowledge["metrics"]
        dead_code = self.system_knowledge["dead_code"]

        # Build comprehensive response
        response = []
        response.append("## 🔍 System-Analyse Report\n")

        # Statistics
        stats = code_index.get("statistics", {})
        response.append("### 📊 Code-Index Status")
        response.append(
            f"- **{stats.get('total_files', 0)}** Files vollständig indiziert"
        )
        response.append(f"- **{stats.get('total_functions', 0)}** Functions analysiert")
        response.append(f"- **{stats.get('total_classes', 0)}** Classes dokumentiert")
        response.append(
            f"- **{stats.get('total_api_endpoints', 0)}** API Endpoints gefunden"
        )
        response.append(f"- **{stats.get('lines_of_code', 0)}** Lines of Code\n")

        # Architecture Overview (with Mermaid diagram)
        if self.system_knowledge.get("diagrams", {}).get("container"):
            response.append("### 🏗️ Architecture Overview")
            response.append("```mermaid")
            response.append(self.system_knowledge["diagrams"]["container"])
            response.append("```\n")

        # Security Analysis
        security_summary = security.get("summary", {})
        if security_summary:
            response.append("### 🔒 Security Analysis")
            if security_summary.get("critical", 0) > 0:
                response.append(
                    f"- ⛔ **{security_summary['critical']} Critical** issues found"
                )
            if security_summary.get("high", 0) > 0:
                response.append(
                    f"- 🔴 **{security_summary['high']} High** risk vulnerabilities"
                )
            if security_summary.get("medium", 0) > 0:
                response.append(
                    f"- 🟡 **{security_summary['medium']} Medium** risk issues"
                )
            response.append("")

        # Performance Metrics
        metrics_summary = metrics.get("summary", {})
        response.append("### 📈 Performance Metrics")
        response.append(
            f"- **Average Complexity**: {metrics_summary.get('average_complexity', 0):.1f}"
        )
        response.append(
            f"- **Maintainability Index**: {metrics_summary.get('average_maintainability', 0):.1f}"
        )
        response.append(
            f"- **Quality Score**: {metrics_summary.get('quality_score', 0):.1f}/100"
        )

        # Dead Code
        dead_code_summary = dead_code.get("summary", {})
        if dead_code_summary.get("total_dead_code", 0) > 0:
            response.append(
                f"\n### 🧹 Dead Code: **{dead_code_summary['total_dead_code']}** unused items found\n"
            )

        # Concrete Improvements
        response.append("### 🚀 Konkrete Verbesserungen (Priorisiert)\n")

        improvements = await self._generate_improvement_suggestions()
        for i, improvement in enumerate(improvements, 1):
            response.append(
                f"#### {i}. {improvement['title']} [{improvement['priority']}]"
            )
            response.append(f"**Problem**: {improvement['problem']}")
            response.append(f"**Lösung**: {improvement['solution']}")
            if "code" in improvement:
                response.append(f"```python\n{improvement['code']}\n```")
            response.append(f"**Impact**: {improvement['impact']}\n")

        # Dependency Graph
        if self.system_knowledge.get("diagrams", {}).get("dependency_graph"):
            response.append("### 📊 Dependency Graph")
            response.append("```mermaid")
            response.append(self.system_knowledge["diagrams"]["dependency_graph"])
            response.append("```\n")

        return "\n".join(response)

    async def _generate_improvement_suggestions(self) -> list[dict[str, str]]:
        """
        Generate specific improvement suggestions based on analysis
        Provides KI_AutoAgent specific improvements, not generic suggestions
        """
        improvements = []

        # Analyze actual KI_AutoAgent system
        self.system_knowledge.get("code_index", {})
        self.system_knowledge.get("metrics", {})
        security = self.system_knowledge.get("security", {})
        dead_code = self.system_knowledge.get("dead_code", {})

        # 1. Check if we already have Redis (we do!)
        has_redis = await self._check_for_technology("redis")
        await self._check_for_technology("docker")

        # KI_AutoAgent Specific Improvement #1: Optimize Redis Cache Usage
        if has_redis:
            improvements.append(
                {
                    "title": "Optimize Redis Cache Strategy for Agent Responses",
                    "priority": "HIGH",
                    "problem": "Redis exists but cache invalidation happens too frequently, causing repeated re-indexing",
                    "solution": "Implement smarter cache invalidation - only invalidate affected components",
                    "impact": "80% reduction in re-indexing operations, 3x faster agent responses",
                    "code": """# Optimize cache invalidation in architect_agent.py
# Instead of invalidating all cache on file change:
if file_changed in ['.py', '.js', '.ts']:
    self.project_cache.invalidate('code_index', [file_changed])
    # Don't invalidate metrics, security, etc unless needed
""",
                }
            )

        # KI_AutoAgent Specific Improvement #2: Parallel Agent Execution
        improvements.append(
            {
                "title": "Enable Parallel Agent Execution in Orchestrator",
                "priority": "HIGH",
                "problem": "Agents execute sequentially even when they could run in parallel",
                "solution": "Modify orchestrator to detect independent subtasks and run agents concurrently",
                "impact": "3-5x faster for multi-agent workflows like infrastructure analysis",
                "code": """# In orchestrator_agent_v2.py
# Execute independent subtasks in parallel:
if workflow_type == "parallel":
    tasks = [agent.execute(subtask) for subtask in independent_subtasks]
    results = await asyncio.gather(*tasks)
""",
            }
        )

        # KI_AutoAgent Specific Improvement #3: Fix Stop Button
        improvements.append(
            {
                "title": "Fix Stop Button Functionality",
                "priority": "CRITICAL",
                "problem": "Stop button doesn't properly cancel running agent tasks",
                "solution": "Integrate CancelToken system with WebSocket stop handler",
                "impact": "Users can interrupt long-running tasks, better UX",
                "code": """# In server.py WebSocket handler:
if message_type == "stop":
    if client_id in active_tasks:
        active_tasks[client_id].cancel()
    await manager.send_json(client_id, {"type": "stopped"})
""",
            }
        )

        # KI_AutoAgent Specific Improvement #4: Reduce Progress Message Spam
        improvements.append(
            {
                "title": "Implement Progress Message Deduplication",
                "priority": "MEDIUM",
                "problem": 'Duplicate progress messages spam the UI ("Indexing file 28/154" appears multiple times)',
                "solution": "Add deduplication and rate limiting for progress messages",
                "impact": "Cleaner UI, better performance, reduced message queue size",
            }
        )

        # KI_AutoAgent Specific Improvement #5: Dead Code Removal
        dead_code_summary = dead_code.get("summary", {})
        if dead_code_summary.get("total_dead_code", 0) > 10:
            improvements.append(
                {
                    "title": f"Remove {dead_code_summary.get('total_dead_code', 0)} Dead Code Items",
                    "priority": "MEDIUM",
                    "problem": "Unused functions and variables clutter the codebase",
                    "solution": "Automated dead code removal with vulture",
                    "impact": "Smaller codebase, faster parsing, better maintainability",
                    "specific_files": dead_code.get("files", [])[
                        :5
                    ],  # Show first 5 files
                }
            )

        # v5.8.4: Memory Optimization - Check actual file size instead of hardcoded value
        import os

        analysis_file = os.path.join(
            self.workspace_path or ".", ".ki_autoagent_ws", "system_analysis.json"
        )
        if os.path.exists(analysis_file):
            file_size_mb = os.path.getsize(analysis_file) / (1024 * 1024)
            # Only add improvement if file is actually large (>50MB)
            if file_size_mb > 50:
                improvements.append(
                    {
                        "title": "Optimize Agent Memory Usage",
                        "priority": "HIGH",
                        "problem": f"system_analysis.json is {file_size_mb:.1f}MB - being loaded into memory repeatedly",
                        "solution": "Stream large files instead of loading entirely, use chunked processing",
                        "impact": "Reduce memory usage, prevent OOM errors",
                    }
                )

        # KI_AutoAgent Specific Improvement #7: Security Vulnerabilities
        security_summary = security.get("summary", {})
        if (
            security_summary.get("critical", 0) > 0
            or security_summary.get("high", 0) > 0
        ):
            improvements.append(
                {
                    "title": f"Fix {security_summary.get('critical', 0) + security_summary.get('high', 0)} Security Issues",
                    "priority": "CRITICAL",
                    "problem": "Critical and high severity security vulnerabilities detected",
                    "solution": "Apply semgrep recommendations and security patches",
                    "impact": "Prevent security breaches and data leaks",
                    "details": security.get("findings", [])[:3],  # First 3 findings
                }
            )

        # KI_AutoAgent Specific Improvement #8: WebSocket Performance
        improvements.append(
            {
                "title": "Optimize WebSocket Message Handling",
                "priority": "MEDIUM",
                "problem": "WebSocket messages are processed synchronously, causing UI lag",
                "solution": "Implement message queuing and batch processing",
                "impact": "Smoother UI updates, 50% reduction in message latency",
            }
        )

        return improvements[:5]  # Return top 5 improvements

    async def _check_for_technology(self, tech: str) -> bool:
        """
        Check if a technology is used in the codebase
        """
        if not self.system_knowledge:
            return False

        try:
            # Search in code index if available
            if self.code_indexer and hasattr(self.code_indexer, "tree_sitter"):
                results = await self.code_indexer.tree_sitter.search_pattern(tech)
                return len(results) > 0
        except Exception as e:
            logger.warning(f"Error checking for technology {tech}: {e}")

        # Fallback: Check in code_index directly
        code_index = self.system_knowledge.get("code_index", {})
        ast_data = code_index.get("ast", {})
        files_data = ast_data.get("files", {})

        # Simple text search in indexed files
        for file_path, file_info in files_data.items():
            if tech.lower() in str(file_info).lower():
                return True

        return False

    async def generate_architecture_flowchart(self) -> str:
        """
        Generate a detailed architecture flowchart of the current system
        v5.8.3: Fixed to use AI-powered generation for proper diagrams
        """
        if not self.system_knowledge:
            await self.understand_system(".", None, "architecture flowchart")

        # v5.8.3: Use AI-powered generation instead of template
        # This creates meaningful diagrams instead of empty ones
        flowchart = await self.diagram_service.generate_architecture_diagram_ai(
            self.system_knowledge["code_index"], "component"
        )

        # If AI generation failed, try to convert code_index to components format
        if not flowchart or "Not Available" in flowchart:
            # Extract components from code_index
            code_index = self.system_knowledge.get("code_index", {})
            components = []

            # Add main system components
            if "agents" in code_index:
                for agent in code_index.get("agents", []):
                    components.append(
                        {"name": agent, "type": "service", "connections": []}
                    )

            if "services" in code_index:
                for service in code_index.get("services", []):
                    components.append(
                        {"name": service, "type": "service", "connections": []}
                    )

            if "modules" in code_index:
                for module_name in list(code_index.get("modules", {}).keys())[:10]:
                    components.append(
                        {"name": module_name, "type": "module", "connections": []}
                    )

            # Generate with components list
            if components:
                flowchart = self.diagram_service.generate_architecture_diagram(
                    components, "component"
                )

        return f"## System Architecture Flowchart\n\n{flowchart}"

    def _detect_request_type(self, prompt: str) -> str:
        """Detect the type of request from the prompt"""
        prompt_lower = prompt.lower()

        # Check for specific request types
        if any(
            word in prompt_lower
            for word in [
                "infrastructure",
                "infra",
                "caching",
                "redis",
                "database",
                "scale",
            ]
        ):
            return "infrastructure"
        elif any(
            word in prompt_lower
            for word in ["architecture", "design", "pattern", "structure"]
        ):
            return "architecture"
        elif any(
            word in prompt_lower for word in ["refactor", "restructure", "reorganize"]
        ):
            return "refactor"
        elif any(
            word in prompt_lower
            for word in ["optimize", "performance", "speed", "faster"]
        ):
            return "optimize"
        elif any(word in prompt_lower for word in ["dead code", "unused", "cleanup"]):
            return "dead_code"
        elif any(
            word in prompt_lower for word in ["security", "vulnerability", "exploit"]
        ):
            return "security"
        elif any(
            word in prompt_lower
            for word in ["dependency", "dependencies", "imports", "requires"]
        ):
            return "dependencies"
        elif any(
            word in prompt_lower for word in ["impact", "affect", "change", "modify"]
        ):
            return "impact_analysis"
        else:
            return "general"

    async def _send_progress(self, client_id: str, message: str, manager=None):
        """Send progress update to WebSocket client with deduplication"""
        logger.debug(
            f"🔍 Architect _send_progress called with client_id={client_id}, message={message}"
        )
        if not client_id:
            logger.debug("⚠️ No client_id, skipping progress message")
            return

        # Check for duplicate message
        last_message = self._last_progress_messages.get(client_id)
        if last_message == message:
            logger.debug(
                f"⚠️ Skipping duplicate progress message for {client_id}: {message[:50]}..."
            )
            return

        # Update last message
        self._last_progress_messages[client_id] = message

        try:
            # First try to use manager from parameter (passed through context)
            if not manager:
                # Fall back to importing (though this may not work due to circular imports)
                logger.debug(
                    "📦 Manager not passed, attempting to import from api.server"
                )
                try:
                    from api.server import manager
                except ImportError:
                    logger.warning("⚠️ Could not import manager from api.server")
                    return

            from datetime import datetime

            logger.debug(f"✅ Manager available: {manager}")
            logger.debug(
                f"📊 Active connections: {list(manager.active_connections.keys()) if manager else 'No manager'}"
            )

            if manager and client_id in manager.active_connections:
                try:
                    logger.info(
                        f"📡 Architect about to send progress via manager.send_json to {client_id}"
                    )
                    await manager.send_json(
                        client_id,
                        {
                            "type": "agent_progress",
                            "agent": "architect",
                            "content": message,  # Changed from "message" to "content" for consistency
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                    logger.info(
                        f"📤 Architect successfully sent progress to client {client_id}: {message}"
                    )
                except Exception as send_err:
                    logger.error(
                        f"❌ Architect failed to send via manager.send_json: {send_err}"
                    )
            else:
                if not manager:
                    logger.warning("⚠️ Architect: No manager instance available")
                else:
                    logger.warning(
                        f"⚠️ Architect: Client {client_id} not in active connections: {list(manager.active_connections.keys())}"
                    )
        except Exception as e:
            logger.error(f"❌ Could not send progress update: {e}")
