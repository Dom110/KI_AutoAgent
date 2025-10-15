"""
Workflow Planner v6 - Dynamic AI-based Workflow Generation

This module replaces the Intent Detector with a dynamic workflow planner
that uses LLM to create flexible, context-aware execution plans.

Author: KI AutoAgent Team
Date: 2025-10-12
Version: v6.1-alpha (Prototype)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Literal
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import ChatOpenAI and messages first
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

# Fix Pydantic v2 / LangChain compatibility issue
# CRITICAL: Import dependencies and rebuild model AFTER ChatOpenAI import
try:
    from langchain_core.caches import BaseCache
    from langchain_core.callbacks.manager import Callbacks
    # Rebuild the model now that all dependencies are available
    ChatOpenAI.model_rebuild()
    logger.info("✅ Successfully rebuilt ChatOpenAI Pydantic model")
except Exception as e:
    # Log error but continue - might still work
    logger.warning(f"⚠️  ChatOpenAI model_rebuild failed: {e}. Will attempt to continue...")

# Load environment variables from global config
global_config = Path.home() / ".ki_autoagent" / "config" / ".env"
if global_config.exists():
    load_dotenv(global_config)
    logger.debug(f"Loaded environment from {global_config}")
elif Path("../.env").exists():
    load_dotenv("../.env")
    logger.debug("Loaded environment from ../.env")
elif Path(".env").exists():
    load_dotenv(".env")
    logger.debug("Loaded environment from .env")


# Available Agents (from our system)
class AgentType(str, Enum):
    """Available agents in the KI AutoAgent system."""
    RESEARCH = "research"
    ARCHITECT = "architect"
    CODESMITH = "codesmith"
    REVIEWFIX = "reviewfix"
    EXPLAIN = "explain"
    DEBUGGER = "debugger"


# Conditional Rule Types
class ConditionType(str, Enum):
    """Types of conditions that can trigger agent execution."""
    ALWAYS = "always"                    # Always execute
    IF_SUCCESS = "if_success"            # Execute if previous succeeded
    IF_FAILURE = "if_failure"            # Execute if previous failed
    IF_QUALITY_LOW = "if_quality_low"    # Execute if quality < threshold
    IF_FILES_EXIST = "if_files_exist"    # Execute if certain files exist
    IF_LLM_DECIDES = "if_llm_decides"    # Ask LLM at runtime
    PARALLEL = "parallel"                 # Execute in parallel with previous


@dataclass(slots=True)
class AgentStep:
    """Represents a single agent execution step in the workflow."""
    agent: AgentType
    description: str
    mode: str = "default"  # Agent execution mode (e.g., research: research/explain/analyze)
    inputs: list[str] = field(default_factory=list)      # What this agent needs
    outputs: list[str] = field(default_factory=list)      # What this agent produces
    condition: ConditionType = ConditionType.ALWAYS
    condition_params: dict[str, Any] = field(default_factory=dict)
    max_iterations: int = 1                               # For agents that can loop
    parallel_with: str | None = None                   # Run parallel with this agent

    def __post_init__(self):
        """Validate mode parameter for each agent type."""
        # Define valid modes per agent (v6.3+ updated)
        valid_modes = {
            AgentType.RESEARCH: ["default", "research", "explain", "analyze", "index"],
            AgentType.ARCHITECT: ["default", "scan", "design", "post_build_scan", "re_scan"],
            AgentType.CODESMITH: ["default"],
            AgentType.REVIEWFIX: ["default"],
            AgentType.EXPLAIN: ["default"],
            AgentType.DEBUGGER: ["default"]
        }

        allowed = valid_modes.get(self.agent, ["default"])
        if self.mode not in allowed:
            logger.warning(
                f"Invalid mode '{self.mode}' for agent {self.agent.value}. "
                f"Allowed: {allowed}. Using 'default'."
            )
            self.mode = "default"


@dataclass(slots=True)
class WorkflowPlan:
    """Complete workflow execution plan."""
    task_description: str
    workflow_type: str                                    # CREATE, UPDATE, FIX, EXPLAIN, REFACTOR, CUSTOM
    agents: list[AgentStep]
    success_criteria: list[str]
    estimated_duration: str
    complexity: Literal["simple", "moderate", "complex"]
    requires_human_approval: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowPlannerV6:
    """
    AI-based Workflow Planner that dynamically creates execution plans.
    Replaces the Intent Detector with flexible, context-aware planning.
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        """Initialize the workflow planner."""
        # Fix Pydantic v2 compatibility issue - explicitly set cache to None
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=2000,
            cache=None  # Explicitly disable caching to avoid Pydantic validation error
        )

        # Agent capabilities (for prompt)
        self.agent_capabilities = {
            AgentType.RESEARCH: {
                "description": "Gathers information, analyzes requirements, searches existing code",
                "inputs": ["user_task", "workspace_path"],
                "outputs": ["requirements", "context", "existing_code_analysis"]
            },
            AgentType.ARCHITECT: {
                "description": "Designs system architecture, creates file structure, plans implementation",
                "inputs": ["requirements", "context"],
                "outputs": ["architecture", "file_structure", "design_decisions"]
            },
            AgentType.CODESMITH: {
                "description": "Generates code based on architecture and requirements",
                "inputs": ["architecture", "file_structure", "requirements"],
                "outputs": ["generated_files", "implementation_details"]
            },
            AgentType.REVIEWFIX: {
                "description": "Reviews code quality, runs validation, fixes issues",
                "inputs": ["generated_files"],
                "outputs": ["review_feedback", "fixed_files", "quality_score"]
            },
            AgentType.EXPLAIN: {
                "description": "Documents and explains existing code",
                "inputs": ["workspace_path", "target_files"],
                "outputs": ["documentation", "explanations"]
            },
            AgentType.DEBUGGER: {
                "description": "Analyzes errors, finds bugs, suggests fixes",
                "inputs": ["error_logs", "code_files"],
                "outputs": ["bug_analysis", "fix_suggestions"]
            }
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the workflow planner."""
        return f"""You are an AI Workflow Planner for the KI AutoAgent system.
Your task is to analyze user requests and create optimal execution plans.

# Available Agents and Their Modes:

## research
- **Description:** Gathers information, analyzes requirements, searches web, analyzes existing code
- **MODES (IMPORTANT!):**
  - **"research"** (default): Search web with Perplexity for new information
    → Use when: CREATE new features, need external information
  - **"explain"**: Analyze and explain existing codebase structure
    → Use when: User wants to UNDERSTAND/EXPLAIN/DESCRIBE existing code
    → Keywords: "explain", "untersuche", "describe", "show me", "how does"
  - **"analyze"**: Deep analysis of existing architecture and code patterns
    → Use when: User wants DEEP INSIGHTS, quality assessment, security audit
    → Keywords: "analyze", "audit", "review", "assess"

## architect
- **Description:** Designs system architecture, creates file structure, plans implementation
- **MODES (v6.3+):**
  - **"scan"**: Load existing architecture (UPDATE workflows)
    → Use when: Modifying existing project, need current state
  - **"design"** (default): Create new architecture or propose updates
    → Use when: New projects OR updating existing ones
  - **"post_build_scan"**: Document system after code generation (CREATE workflows)
    → Use when: After Codesmith completed, create system snapshot
  - **"re_scan"**: Update architecture after modifications (UPDATE workflows)
    → Use when: After modifications, update system snapshot

## codesmith
- **Description:** Generates code based on architecture and requirements
- **MODES:** "default" only

## reviewfix
- **Description:** Reviews code quality, runs validation, fixes issues
- **MODES:** "default" only

## explain (DEPRECATED - Use research with mode="explain" instead!)
- **Description:** Legacy agent for explaining code
- **MODES:** "default" only

## debugger
- **Description:** Analyzes errors, finds bugs, suggests fixes
- **MODES:** "default" only

# CRITICAL RULES FOR RESEARCH AGENT MODES:

1. **CREATE workflows** → research mode="research"
   Example: "Create a task manager" → {{"agent": "research", "mode": "research"}}

2. **EXPLAIN workflows** → research mode="explain"
   Example: "Explain the API" → {{"agent": "research", "mode": "explain"}}
   Example (German): "Untersuche die App" → {{"agent": "research", "mode": "explain"}}

3. **ANALYZE workflows** → research mode="analyze"
   Example: "Analyze code quality" → {{"agent": "research", "mode": "analyze"}}

4. **DO NOT use "explain" agent!** → Use research with mode="explain" instead

# Output Format:

Return a JSON object with this structure:

{{
    "task_summary": "Brief description of the task",
    "workflow_type": "CREATE|UPDATE|FIX|EXPLAIN|REFACTOR|CUSTOM",
    "complexity": "simple|moderate|complex",
    "estimated_duration": "e.g., 2-5 minutes",
    "agents": [
        {{
            "agent": "research|architect|codesmith|reviewfix|debugger",
            "mode": "default|research|explain|analyze",  ← REQUIRED for research agent!
            "description": "What this agent will do",
            "condition": "always|if_success|if_failure|if_quality_low|parallel",
            "condition_params": {{}},
            "inputs_from": ["previous_agent"],
            "outputs_to": ["next_agent"],
            "max_iterations": 1
        }}
    ],
    "success_criteria": [
        "List of conditions that indicate success"
    ],
    "requires_human_approval": false
}}

# Workflow Design Principles:

1. **Efficiency**: Use minimum agents needed, avoid redundancy
2. **Mode Selection**: Choose correct research mode based on task intent
3. **Parallelism**: Run independent agents in parallel when possible
4. **Conditional Execution**: Add conditions to handle edge cases
5. **Quality Gates**: Include review/validation for code generation

# Common Patterns (v6.3+ with Architect modes):

1. **CREATE Pattern**:
   Research (mode="research") → Architect (mode="design") → Codesmith → ReviewFix → Architect (mode="post_build_scan")

2. **UPDATE Pattern**:
   Architect (mode="scan") → Research (mode="research", optional) → Architect (mode="design") → Codesmith → ReviewFix → Architect (mode="re_scan")

3. **EXPLAIN Pattern**:
   Research (mode="explain") → DONE

4. **ANALYZE Pattern**:
   Research (mode="analyze") → DONE

5. **FIX Pattern**:
   Research (mode="analyze") → Debugger → ReviewFix

6. **REFACTOR Pattern**:
   Research (mode="research") → Architect (mode="design") → Codesmith → ReviewFix

# Agent Autonomy (v6.3+):

Agents can invoke other agents AUTOMATICALLY when context is missing:
- Architect can invoke Research if no research data in Memory
- Codesmith can invoke Research if no research data in Memory
- Codesmith can invoke Architect if no design in Memory

This means workflows can be SHORTER - missing agents will be invoked automatically!
Example: User says "Generate code" → Workflow: [Codesmith only] → Codesmith auto-invokes Architect AND Research

# Model Selection (v6.3+):

Codesmith automatically selects the best model based on complexity:
- Simple tasks → Claude Sonnet 4 (fast)
- Moderate tasks → Claude Sonnet 4.5
- Complex tasks → Claude Sonnet 4.5 + Think mode
- Very complex (20+ files, microservices, etc.) → Claude Opus 3.5 + Think mode

User is notified via WebSocket which model was selected and why.

# Correct Examples:

**Example 1: CREATE (v6.3)**
Task: "Create a task manager app"
{{
  "workflow_type": "CREATE",
  "agents": [
    {{"agent": "research", "mode": "research", "description": "Search for task manager patterns"}},
    {{"agent": "architect", "mode": "design", "description": "Design architecture"}},
    {{"agent": "codesmith", "mode": "default", "description": "Generate code (model auto-selected based on complexity)"}},
    {{"agent": "reviewfix", "mode": "default", "description": "Review and fix"}},
    {{"agent": "architect", "mode": "post_build_scan", "description": "Create system snapshot and documentation"}}
  ]
}}

**Example 2: UPDATE (v6.3)**
Task: "Add authentication to existing app"
{{
  "workflow_type": "UPDATE",
  "agents": [
    {{"agent": "architect", "mode": "scan", "description": "Load existing architecture"}},
    {{"agent": "research", "mode": "research", "description": "Research authentication best practices", "condition": "if_llm_decides"}},
    {{"agent": "architect", "mode": "design", "description": "Design authentication integration"}},
    {{"agent": "codesmith", "mode": "default", "description": "Implement authentication"}},
    {{"agent": "reviewfix", "mode": "default", "description": "Review and fix"}},
    {{"agent": "architect", "mode": "re_scan", "description": "Update system snapshot"}}
  ]
}}

**Example 3: EXPLAIN**
Task: "Explain how the API works"
{{
  "workflow_type": "EXPLAIN",
  "agents": [
    {{"agent": "research", "mode": "explain", "description": "Analyze API codebase and explain"}}
  ]
}}

**Example 4: EXPLAIN (German)**
Task: "Untersuche die App und erkläre mir die Architektur"
{{
  "workflow_type": "EXPLAIN",
  "agents": [
    {{"agent": "research", "mode": "explain", "description": "Analyze app architecture and explain"}}
  ]
}}

**Example 5: ANALYZE**
Task: "Analyze the security of this codebase"
{{
  "workflow_type": "EXPLAIN",
  "agents": [
    {{"agent": "research", "mode": "analyze", "description": "Deep security analysis of codebase"}}
  ]
}}

**Example 6: FIX**
Task: "Fix the authentication bug"
{{
  "workflow_type": "FIX",
  "agents": [
    {{"agent": "research", "mode": "analyze", "description": "Analyze authentication code"}},
    {{"agent": "debugger", "description": "Find and fix bug"}},
    {{"agent": "reviewfix", "description": "Validate fix"}}
  ]
}}

Remember: ALWAYS specify mode for research agent! Default is "research"."""

    async def plan_workflow(
        self,
        user_task: str,
        workspace_path: str,
        context: dict[str, Any] | None = None
    ) -> WorkflowPlan:
        """
        Create a dynamic workflow plan based on the user's task.

        Args:
            user_task: The user's request/task description
            workspace_path: Path to the workspace
            context: Additional context (existing files, previous attempts, etc.)

        Returns:
            WorkflowPlan with execution steps
        """
        logger.info(f"🎯 Planning workflow for: {user_task[:100]}...")

        # Build the prompt
        system_prompt = self._build_system_prompt()

        # Add context if available
        context_str = ""
        if context:
            if context.get("existing_files"):
                context_str += f"\nExisting files in workspace: {context['existing_files']}"
            if context.get("previous_error"):
                context_str += f"\nPrevious error: {context['previous_error']}"
            if context.get("language_preference"):
                context_str += f"\nUser prefers: {context['language_preference']}"

        user_prompt = f"""Task: {user_task}
Workspace: {workspace_path}
{context_str}

Create an optimal workflow plan for this task."""

        try:
            # Get LLM response
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # 🔍 Robust response handling
            response_content = response.content.strip()

            if not response_content:
                error_msg = "LLM returned empty response"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Task: {user_task[:200]}")
                logger.error(f"   This indicates an API issue or prompt problem")
                raise RuntimeError(f"{error_msg}. Task: {user_task[:100]}...")

            # Log raw response for debugging
            logger.debug(f"📄 Raw LLM response ({len(response_content)} chars): {response_content[:500]}...")

            # Try to extract JSON if response contains markdown code blocks
            if "```json" in response_content:
                # Extract JSON from markdown code block
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                if json_end != -1:
                    response_content = response_content[json_start:json_end].strip()
                    logger.debug("📝 Extracted JSON from markdown code block")
            elif "```" in response_content:
                # Try generic code block
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                if json_end != -1:
                    response_content = response_content[json_start:json_end].strip()
                    logger.debug("📝 Extracted content from code block")

            # Parse JSON response
            try:
                plan_data = json.loads(response_content)
            except json.JSONDecodeError as json_err:
                error_msg = f"Invalid JSON from LLM: {json_err}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Response preview: {response_content[:500]}")
                raise RuntimeError(f"{error_msg}. Response: {response_content[:200]}...")

            # Validate required fields
            required_fields = ["workflow_type", "agents", "success_criteria", "estimated_duration", "complexity"]
            missing_fields = [f for f in required_fields if f not in plan_data]
            if missing_fields:
                error_msg = f"LLM response missing required fields: {missing_fields}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Got fields: {list(plan_data.keys())}")
                raise RuntimeError(error_msg)

            # Convert to WorkflowPlan
            agents = []
            for step in plan_data["agents"]:
                agent_type = AgentType(step["agent"])

                # Extract mode with validation and smart inference
                mode = step.get("mode", "default")

                # Special handling for research agent - infer mode from description if not specified
                if agent_type == AgentType.RESEARCH and mode == "default":
                    description_lower = step["description"].lower()

                    # Infer "explain" mode
                    explain_keywords = ["explain", "describe", "untersuche", "erkläre", "show me", "how does"]
                    if any(keyword in description_lower for keyword in explain_keywords):
                        mode = "explain"
                        logger.info(f"📝 Inferred research mode 'explain' from description: {step['description'][:50]}")

                    # Infer "analyze" mode (higher priority than explain)
                    analyze_keywords = ["analyze", "audit", "review", "assess", "evaluate", "examine"]
                    if any(keyword in description_lower for keyword in analyze_keywords):
                        mode = "analyze"
                        logger.info(f"📝 Inferred research mode 'analyze' from description: {step['description'][:50]}")

                    # If still default, use "research" as explicit default for research agent
                    if mode == "default":
                        mode = "research"
                        logger.debug(f"📝 Using default research mode 'research' for: {step['description'][:50]}")

                agents.append(AgentStep(
                    agent=agent_type,
                    description=step["description"],
                    mode=mode,  # ← ADD mode parameter
                    inputs=step.get("inputs_from", []),
                    outputs=step.get("outputs_to", []),
                    condition=ConditionType(step.get("condition", "always")),
                    condition_params=step.get("condition_params", {}),
                    max_iterations=step.get("max_iterations", 1)
                ))

            plan = WorkflowPlan(
                task_description=plan_data.get("task_summary", user_task),
                workflow_type=plan_data["workflow_type"],
                agents=agents,
                success_criteria=plan_data["success_criteria"],
                estimated_duration=plan_data["estimated_duration"],
                complexity=plan_data["complexity"],
                requires_human_approval=plan_data.get("requires_human_approval", False),
                metadata=plan_data
            )

            logger.info(f"✅ Workflow plan created: {len(agents)} agents, {plan.complexity} complexity")
            self._log_plan(plan)

            return plan

        except RuntimeError:
            # Re-raise RuntimeError (already logged above)
            raise

        except Exception as e:
            error_msg = f"Workflow planning failed: {type(e).__name__}: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Task: {user_task[:200]}")
            raise RuntimeError(error_msg)

    def _log_plan(self, plan: WorkflowPlan):
        """Log the workflow plan for debugging."""
        logger.info(f"📋 Workflow Plan: {plan.workflow_type}")
        logger.info(f"   Complexity: {plan.complexity}")
        logger.info(f"   Duration: {plan.estimated_duration}")
        logger.info("   Agents:")
        for i, step in enumerate(plan.agents, 1):
            condition_str = f" ({step.condition.value})" if step.condition != ConditionType.ALWAYS else ""
            mode_str = f" [mode={step.mode}]" if step.mode != "default" else ""
            logger.info(f"   {i}. {step.agent.value}{mode_str}: {step.description}{condition_str}")
        logger.info(f"   Success Criteria: {', '.join(plan.success_criteria)}")

    async def validate_plan(self, plan: WorkflowPlan) -> tuple[bool, list[str]]:
        """
        Validate a workflow plan for correctness.

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check for invalid agents
        valid_agents = set(AgentType)
        for step in plan.agents:
            if step.agent not in valid_agents:
                issues.append(f"Invalid agent: {step.agent}")

        # Check for circular dependencies
        seen = set()
        for step in plan.agents:
            if step.agent in seen and step.condition != ConditionType.PARALLEL:
                issues.append(f"Potential circular dependency: {step.agent}")
            seen.add(step.agent)

        # Check for missing required agents
        if plan.workflow_type == "CREATE" and AgentType.CODESMITH not in [s.agent for s in plan.agents]:
            issues.append("CREATE workflow missing CODESMITH agent")

        if plan.workflow_type == "UPDATE":
            agent_list = [s.agent for s in plan.agents]
            # UPDATE must have architect scan FIRST
            if not agent_list or agent_list[0] != AgentType.ARCHITECT:
                issues.append("UPDATE workflow must start with ARCHITECT scan")
            # UPDATE must have architect re-scan at END
            if not agent_list or agent_list[-1] != AgentType.ARCHITECT:
                issues.append("UPDATE workflow must end with ARCHITECT re-scan")

        # Check iteration limits
        for step in plan.agents:
            if step.max_iterations > 10:
                issues.append(f"Excessive iterations for {step.agent}: {step.max_iterations}")

        return len(issues) == 0, issues


# Example usage and testing
async def test_planner():
    """Test the workflow planner with various tasks."""
    planner = WorkflowPlannerV6()

    # Test cases
    test_cases = [
        "Create a task manager app with React frontend and FastAPI backend",
        "Fix the authentication bug in the login system",
        "Explain how the payment processing works",
        "Refactor the database connection code to use connection pooling",
        "Debug why the API is returning 500 errors",
        "Untersuche die App und erkläre die Architektur"  # German
    ]

    for task in test_cases:
        print(f"\n{'='*60}")
        print(f"Task: {task}")
        print(f"{'='*60}")

        plan = await planner.plan_workflow(
            user_task=task,
            workspace_path="/Users/test/project"
        )

        print(f"Workflow Type: {plan.workflow_type}")
        print(f"Complexity: {plan.complexity}")
        print(f"Agents: {', '.join([s.agent.value for s in plan.agents])}")

        # Validate
        is_valid, issues = await planner.validate_plan(plan)
        if is_valid:
            print("✅ Plan is valid")
        else:
            print(f"❌ Plan has issues: {issues}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_planner())