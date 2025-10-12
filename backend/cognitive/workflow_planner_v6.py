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
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

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


@dataclass
class AgentStep:
    """Represents a single agent execution step in the workflow."""
    agent: AgentType
    description: str
    inputs: List[str] = field(default_factory=list)      # What this agent needs
    outputs: List[str] = field(default_factory=list)      # What this agent produces
    condition: ConditionType = ConditionType.ALWAYS
    condition_params: Dict[str, Any] = field(default_factory=dict)
    max_iterations: int = 1                               # For agents that can loop
    parallel_with: Optional[str] = None                   # Run parallel with this agent


@dataclass
class WorkflowPlan:
    """Complete workflow execution plan."""
    task_description: str
    workflow_type: str                                    # CREATE, FIX, EXPLAIN, CUSTOM
    agents: List[AgentStep]
    success_criteria: List[str]
    estimated_duration: str
    complexity: Literal["simple", "moderate", "complex"]
    requires_human_approval: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowPlannerV6:
    """
    AI-based Workflow Planner that dynamically creates execution plans.
    Replaces the Intent Detector with flexible, context-aware planning.
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        """Initialize the workflow planner."""
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=2000
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
        agents_desc = "\n".join([
            f"- {agent.value}: {caps['description']}"
            for agent, caps in self.agent_capabilities.items()
        ])

        return f"""You are an AI Workflow Planner for the KI AutoAgent system.
Your task is to analyze user requests and create optimal execution plans.

# Available Agents:
{agents_desc}

# Workflow Design Principles:

1. **Efficiency**: Use minimum agents needed, avoid redundancy
2. **Parallelism**: Run independent agents in parallel when possible
3. **Conditional Execution**: Add conditions to handle edge cases
4. **Quality Gates**: Include review/validation for code generation
5. **Iterative Refinement**: Allow loops for quality improvement

# Output Format:

Return a JSON object with this structure:

{{
    "task_summary": "Brief description of the task",
    "workflow_type": "CREATE|FIX|EXPLAIN|REFACTOR|CUSTOM",
    "complexity": "simple|moderate|complex",
    "estimated_duration": "e.g., 2-5 minutes",
    "agents": [
        {{
            "agent": "research|architect|codesmith|reviewfix|explain|debugger",
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

# Conditional Execution Rules:

- "always": Execute unconditionally
- "if_success": Only if previous agent succeeded
- "if_failure": Only if previous agent failed (error recovery)
- "if_quality_low": Only if quality score < threshold
- "parallel": Run simultaneously with previous agent

# Common Patterns:

1. **CREATE Pattern**: Research → Architect → Codesmith → ReviewFix
2. **FIX Pattern**: Research → ReviewFix (with loop)
3. **EXPLAIN Pattern**: Research → Explain
4. **REFACTOR Pattern**: Research → Architect → Codesmith → ReviewFix
5. **DEBUG Pattern**: Debugger → Codesmith → ReviewFix

# Examples:

Task: "Create a task manager app"
Workflow: Research → Architect → Codesmith → ReviewFix (loop if quality < 0.90)

Task: "Fix the authentication bug"
Workflow: Research → Debugger → Codesmith → ReviewFix

Task: "Explain how the payment system works"
Workflow: Research → Explain

Remember: Be intelligent about agent selection. Not every task needs all agents."""

    async def plan_workflow(
        self,
        user_task: str,
        workspace_path: str,
        context: Optional[Dict[str, Any]] = None
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

            # Parse JSON response
            plan_data = json.loads(response.content)

            # Convert to WorkflowPlan
            agents = []
            for step in plan_data["agents"]:
                agents.append(AgentStep(
                    agent=AgentType(step["agent"]),
                    description=step["description"],
                    inputs=step.get("inputs_from", []),
                    outputs=step.get("outputs_to", []),
                    condition=ConditionType(step.get("condition", "always")),
                    condition_params=step.get("condition_params", {}),
                    max_iterations=step.get("max_iterations", 1)
                ))

            plan = WorkflowPlan(
                task_description=plan_data["task_summary"],
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

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback to default CREATE workflow
            return self._get_fallback_plan(user_task)

        except Exception as e:
            logger.error(f"Workflow planning failed: {e}")
            return self._get_fallback_plan(user_task)

    def _log_plan(self, plan: WorkflowPlan):
        """Log the workflow plan for debugging."""
        logger.info(f"📋 Workflow Plan: {plan.workflow_type}")
        logger.info(f"   Complexity: {plan.complexity}")
        logger.info(f"   Duration: {plan.estimated_duration}")
        logger.info("   Agents:")
        for i, step in enumerate(plan.agents, 1):
            condition_str = f" ({step.condition.value})" if step.condition != ConditionType.ALWAYS else ""
            logger.info(f"   {i}. {step.agent.value}: {step.description}{condition_str}")
        logger.info(f"   Success Criteria: {', '.join(plan.success_criteria)}")

    def _get_fallback_plan(self, user_task: str) -> WorkflowPlan:
        """Get a fallback plan if planning fails."""
        # Default CREATE workflow
        return WorkflowPlan(
            task_description=user_task,
            workflow_type="CREATE",
            agents=[
                AgentStep(
                    agent=AgentType.RESEARCH,
                    description="Analyze requirements and gather information",
                    outputs=["requirements", "context"]
                ),
                AgentStep(
                    agent=AgentType.ARCHITECT,
                    description="Design system architecture",
                    inputs=["requirements"],
                    outputs=["architecture"]
                ),
                AgentStep(
                    agent=AgentType.CODESMITH,
                    description="Generate code",
                    inputs=["architecture"],
                    outputs=["generated_files"]
                ),
                AgentStep(
                    agent=AgentType.REVIEWFIX,
                    description="Review and fix code",
                    inputs=["generated_files"],
                    condition=ConditionType.IF_SUCCESS,
                    max_iterations=3
                )
            ],
            success_criteria=["All files generated", "No syntax errors", "Quality score > 0.80"],
            estimated_duration="3-5 minutes",
            complexity="moderate"
        )

    async def validate_plan(self, plan: WorkflowPlan) -> tuple[bool, List[str]]:
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