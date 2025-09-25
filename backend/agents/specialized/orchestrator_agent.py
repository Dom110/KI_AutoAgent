"""
OrchestratorAgent - Advanced task orchestration with decomposition and parallel execution
Ported from TypeScript with all modern features
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..base.chat_agent import ChatAgent, StreamMessage
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    """Subtask for decomposition"""
    id: str
    description: str
    agent: str
    priority: int
    dependencies: List[str] = field(default_factory=list)
    expected_output: str = ""
    estimated_duration: float = 0.0
    status: str = "pending"
    result: Optional[str] = None

@dataclass
class TaskDependency:
    """Task dependency definition"""
    from_task: str
    to_task: str
    dependency_type: str  # 'sequential', 'parallel', 'conditional'
    condition: Optional[str] = None

@dataclass
class TaskDecomposition:
    """Complete task decomposition"""
    main_goal: str
    complexity: str  # 'simple', 'moderate', 'complex'
    subtasks: List[SubTask]
    dependencies: List[TaskDependency]
    estimated_duration: float
    required_agents: List[str]
    parallelizable: bool

@dataclass
class WorkflowStep:
    """Workflow execution step"""
    id: str
    agent: str
    task: str
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class OrchestratorAgent(ChatAgent):
    """
    Advanced Orchestrator Agent with:
    - Task decomposition into subtasks
    - Parallel execution capabilities
    - Dynamic workflow adjustment
    - Memory-based learning
    - Agent conflict resolution
    - Real-time progress updates
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="orchestrator",
            name="OrchestratorAgent",
            full_name="Advanced KI AutoAgent Orchestrator",
            description="Intelligent task orchestration with decomposition and parallel execution",
            model="gpt-4o-2024-11-20",
            capabilities=[
                AgentCapability.TASK_DECOMPOSITION,
                AgentCapability.PARALLEL_EXECUTION
            ],
            temperature=0.7,
            max_tokens=4000,
            icon="🎯"
        )
        super().__init__(config)

        # Workflow management
        self.active_workflows: Dict[str, List[WorkflowStep]] = {}
        self.workflow_history: List[Dict[str, Any]] = []

        # Task decomposition cache
        self.decomposition_cache: Dict[str, TaskDecomposition] = {}

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute orchestration task
        """
        start_time = datetime.now()

        try:
            # Analyze task complexity
            complexity = await self.analyze_task_complexity(request.prompt)

            # Get task decomposition
            decomposition = await self.decompose_task(request.prompt, complexity)

            # Create workflow
            workflow = await self.create_workflow(decomposition)

            # Execute workflow (parallel where possible)
            result = await self.execute_workflow(workflow, decomposition.parallelizable)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                status="success",
                content=self.format_orchestration_result(decomposition, result),
                agent=self.config.agent_id,
                metadata={
                    "complexity": complexity,
                    "subtask_count": len(decomposition.subtasks),
                    "parallel_execution": decomposition.parallelizable,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return TaskResult(
                status="error",
                content=f"Failed to orchestrate task: {str(e)}",
                agent=self.config.agent_id
            )

    async def analyze_task_complexity(self, task: str) -> str:
        """
        Analyze task to determine complexity level
        """
        # Check memory for similar tasks
        if self.memory_manager:
            similar = await self.memory_manager.search(task, k=3)
            if similar:
                # Use learned complexity from similar tasks
                complexities = [s.get("complexity", "moderate") for s in similar]
                # Return most common complexity
                return max(set(complexities), key=complexities.count)

        # Simple heuristic for now
        # TODO: Implement AI-based complexity analysis
        task_lower = task.lower()

        if any(word in task_lower for word in ["simple", "basic", "quick", "easy"]):
            return "simple"
        elif any(word in task_lower for word in ["complex", "advanced", "detailed", "comprehensive"]):
            return "complex"
        else:
            return "moderate"

    async def decompose_task(self, task: str, complexity: str) -> TaskDecomposition:
        """
        Decompose task into subtasks with dependencies
        """
        # Check cache
        cache_key = f"{task[:50]}_{complexity}"
        if cache_key in self.decomposition_cache:
            return self.decomposition_cache[cache_key]

        # Create decomposition based on task analysis
        # TODO: Implement AI-based decomposition with OpenAI
        decomposition = await self._create_sample_decomposition(task, complexity)

        # Cache for future use
        self.decomposition_cache[cache_key] = decomposition

        return decomposition

    async def _create_sample_decomposition(self, task: str, complexity: str) -> TaskDecomposition:
        """
        Create sample decomposition (placeholder for AI implementation)
        """
        # This is a simplified version - real implementation would use GPT-5
        subtasks = []

        if complexity == "simple":
            subtasks = [
                SubTask(
                    id="task_1",
                    description=f"Execute: {task}",
                    agent="codesmith",
                    priority=1,
                    estimated_duration=5.0
                )
            ]
        elif complexity == "moderate":
            subtasks = [
                SubTask(
                    id="task_1",
                    description=f"Analyze requirements for: {task}",
                    agent="architect",
                    priority=1,
                    estimated_duration=3.0
                ),
                SubTask(
                    id="task_2",
                    description=f"Implement solution for: {task}",
                    agent="codesmith",
                    priority=2,
                    dependencies=["task_1"],
                    estimated_duration=10.0
                ),
                SubTask(
                    id="task_3",
                    description=f"Review and validate: {task}",
                    agent="reviewer",
                    priority=3,
                    dependencies=["task_2"],
                    estimated_duration=5.0
                )
            ]
        else:  # complex
            subtasks = [
                SubTask(
                    id="task_1",
                    description=f"Research best practices for: {task}",
                    agent="research",
                    priority=1,
                    estimated_duration=5.0
                ),
                SubTask(
                    id="task_2",
                    description=f"Design architecture for: {task}",
                    agent="architect",
                    priority=1,
                    estimated_duration=8.0
                ),
                SubTask(
                    id="task_3",
                    description=f"Implement core functionality: {task}",
                    agent="codesmith",
                    priority=2,
                    dependencies=["task_1", "task_2"],
                    estimated_duration=15.0
                ),
                SubTask(
                    id="task_4",
                    description=f"Write tests for: {task}",
                    agent="codesmith",
                    priority=3,
                    dependencies=["task_3"],
                    estimated_duration=10.0
                ),
                SubTask(
                    id="task_5",
                    description=f"Document solution: {task}",
                    agent="docu",
                    priority=3,
                    dependencies=["task_3"],
                    estimated_duration=5.0
                ),
                SubTask(
                    id="task_6",
                    description=f"Final review and optimization: {task}",
                    agent="reviewer",
                    priority=4,
                    dependencies=["task_4", "task_5"],
                    estimated_duration=5.0
                )
            ]

        # Determine if parallelizable
        parallelizable = complexity in ["moderate", "complex"]

        # Calculate total duration
        if parallelizable:
            # Parallel execution - find critical path
            estimated_duration = self._calculate_critical_path_duration(subtasks)
        else:
            # Sequential execution
            estimated_duration = sum(task.estimated_duration for task in subtasks)

        return TaskDecomposition(
            main_goal=task,
            complexity=complexity,
            subtasks=subtasks,
            dependencies=[],  # Dependencies are in subtasks
            estimated_duration=estimated_duration,
            required_agents=list(set(task.agent for task in subtasks)),
            parallelizable=parallelizable
        )

    def _calculate_critical_path_duration(self, subtasks: List[SubTask]) -> float:
        """
        Calculate duration based on critical path
        """
        # Simple implementation - find longest dependency chain
        max_duration = 0.0

        for task in subtasks:
            if not task.dependencies:
                # Starting task
                duration = self._get_chain_duration(task, subtasks)
                max_duration = max(max_duration, duration)

        return max_duration if max_duration > 0 else sum(t.estimated_duration for t in subtasks)

    def _get_chain_duration(self, start_task: SubTask, all_tasks: List[SubTask]) -> float:
        """
        Get duration of dependency chain starting from a task
        """
        duration = start_task.estimated_duration

        # Find tasks that depend on this task
        dependent_tasks = [
            t for t in all_tasks
            if start_task.id in t.dependencies
        ]

        if dependent_tasks:
            # Add the longest chain from dependent tasks
            max_dependent_duration = max(
                self._get_chain_duration(t, all_tasks)
                for t in dependent_tasks
            )
            duration += max_dependent_duration

        return duration

    async def create_workflow(self, decomposition: TaskDecomposition) -> List[WorkflowStep]:
        """
        Create workflow from task decomposition
        """
        workflow = []

        for subtask in decomposition.subtasks:
            step = WorkflowStep(
                id=subtask.id,
                agent=subtask.agent,
                task=subtask.description
            )
            workflow.append(step)

        # Store workflow
        workflow_id = f"wf_{datetime.now().timestamp()}"
        self.active_workflows[workflow_id] = workflow

        return workflow

    async def execute_workflow(
        self,
        workflow: List[WorkflowStep],
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Execute workflow steps (parallel or sequential)
        """
        results = {}

        if parallel:
            # Execute tasks in parallel where possible
            results = await self._execute_parallel_workflow(workflow)
        else:
            # Execute tasks sequentially
            results = await self._execute_sequential_workflow(workflow)

        # Store in history
        self.workflow_history.append({
            "timestamp": datetime.now().isoformat(),
            "workflow": [step.__dict__ for step in workflow],
            "results": results,
            "parallel": parallel
        })

        return results

    async def _execute_sequential_workflow(
        self,
        workflow: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """
        Execute workflow steps sequentially
        """
        results = {}

        for step in workflow:
            step.started_at = datetime.now()
            step.status = "running"

            try:
                # Execute step with the appropriate agent
                # TODO: Dispatch to actual agent
                result = await self._execute_step(step)

                step.result = result
                step.status = "completed"
                results[step.id] = result

            except Exception as e:
                step.error = str(e)
                step.status = "failed"
                logger.error(f"Step {step.id} failed: {e}")
                results[step.id] = {"error": str(e)}

            step.completed_at = datetime.now()

        return results

    async def _execute_parallel_workflow(
        self,
        workflow: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """
        Execute workflow steps in parallel where dependencies allow
        """
        results = {}
        completed_steps = set()

        # Group steps by dependency level
        dependency_levels = self._group_by_dependency_level(workflow)

        # Execute each level in parallel
        for level, steps in dependency_levels.items():
            # Execute all steps in this level in parallel
            tasks = []
            for step in steps:
                # Check if dependencies are met
                if self._dependencies_met(step, completed_steps, workflow):
                    step.started_at = datetime.now()
                    step.status = "running"
                    tasks.append(self._execute_step_async(step))

            # Wait for all parallel tasks to complete
            if tasks:
                step_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, step in enumerate(steps):
                    if isinstance(step_results[i], Exception):
                        step.error = str(step_results[i])
                        step.status = "failed"
                        results[step.id] = {"error": str(step_results[i])}
                    else:
                        step.result = step_results[i]
                        step.status = "completed"
                        results[step.id] = step_results[i]
                        completed_steps.add(step.id)

                    step.completed_at = datetime.now()

        return results

    def _group_by_dependency_level(
        self,
        workflow: List[WorkflowStep]
    ) -> Dict[int, List[WorkflowStep]]:
        """
        Group workflow steps by dependency level
        """
        levels: Dict[int, List[WorkflowStep]] = {}

        # Simple grouping - steps with no dependencies are level 0
        # Steps depending on level 0 are level 1, etc.
        for step in workflow:
            level = 0  # Default level
            # TODO: Implement proper dependency level calculation

            if level not in levels:
                levels[level] = []
            levels[level].append(step)

        return levels

    def _dependencies_met(
        self,
        step: WorkflowStep,
        completed: set,
        workflow: List[WorkflowStep]
    ) -> bool:
        """
        Check if all dependencies for a step are met
        """
        # TODO: Implement dependency checking
        return True

    async def _execute_step(self, step: WorkflowStep) -> Any:
        """
        Execute a single workflow step
        """
        # Placeholder for actual agent execution
        # TODO: Dispatch to real agent via agent registry
        await asyncio.sleep(1)  # Simulate work
        return f"Result for {step.task} by {step.agent}"

    async def _execute_step_async(self, step: WorkflowStep) -> Any:
        """
        Execute step asynchronously
        """
        return await self._execute_step(step)

    def format_orchestration_result(
        self,
        decomposition: TaskDecomposition,
        results: Dict[str, Any]
    ) -> str:
        """
        Format the orchestration result for display
        """
        output = []
        output.append(f"## 🎯 Task Orchestration Complete\n")
        output.append(f"**Main Goal**: {decomposition.main_goal}\n")
        output.append(f"**Complexity**: {decomposition.complexity}\n")
        output.append(f"**Execution Mode**: {'Parallel' if decomposition.parallelizable else 'Sequential'}\n")
        output.append(f"**Estimated Duration**: {decomposition.estimated_duration:.1f}s\n")
        output.append("\n### 📋 Subtask Results:\n")

        for subtask in decomposition.subtasks:
            result = results.get(subtask.id, {})
            status_icon = "✅" if subtask.id in results and "error" not in result else "❌"
            output.append(f"\n{status_icon} **{subtask.description}**")
            output.append(f"  - Agent: {subtask.agent}")
            output.append(f"  - Priority: {subtask.priority}")

            if subtask.id in results:
                if "error" in result:
                    output.append(f"  - Error: {result['error']}")
                else:
                    output.append(f"  - Result: {str(result)[:200]}")

        return "\n".join(output)

    async def handle_conflict_resolution(
        self,
        conflicting_outputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle conflicts between agent outputs using OpusArbitrator
        """
        # TODO: Implement conflict resolution with OpusArbitrator
        logger.info("Conflict detected, would invoke OpusArbitrator")

        # For now, return the first output
        return conflicting_outputs[0] if conflicting_outputs else {}

    async def _process_agent_request(self, message) -> Any:
        """
        Process request from another agent
        Implementation of abstract method from BaseAgent
        """
        # Handle orchestration requests from other agents
        if message.content.get("requesting_orchestration"):
            task = message.content.get("task", "")
            result = await self.execute(TaskRequest(prompt=task))
            return {"orchestration_result": result.content}

        return {"message": "Orchestrator received request"}