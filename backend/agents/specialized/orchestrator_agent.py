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

            execution_time = (datetime.now() - start_time).total_seconds()

            # v5.8.4: Convert subtasks to serializable format for workflow.py
            # NOTE: Removed execute_workflow() simulation - workflow.py handles real execution
            subtasks_dict = []
            for subtask in decomposition.subtasks:
                subtasks_dict.append({
                    "id": subtask.id,
                    "description": subtask.description,
                    "task": subtask.description,  # Alias for compatibility
                    "agent": subtask.agent,
                    "priority": subtask.priority,
                    "dependencies": subtask.dependencies,
                    "estimated_duration": subtask.estimated_duration,
                    "expected_output": f"Completion of: {subtask.description[:50]}..."
                })

            return TaskResult(
                status="success",
                content=self.format_orchestration_plan(decomposition),
                agent=self.config.agent_id,
                metadata={
                    "complexity": complexity,
                    "subtask_count": len(decomposition.subtasks),
                    "parallel_execution": decomposition.parallelizable,
                    "execution_time": execution_time,
                    "subtasks": subtasks_dict,  # ✅ Phase 2.4: Include subtasks for workflow.py
                    "estimated_total_duration": decomposition.estimated_duration,
                    "required_agents": decomposition.required_agents
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

        # Simple heuristic
        # NOTE: AI-based complexity analysis is in workflow.py's _detect_task_complexity()
        # This method is only for Orchestrator's internal use
        task_lower = task.lower()

        if any(word in task_lower for word in ["simple", "basic", "quick", "easy"]):
            return "simple"
        elif any(word in task_lower for word in ["complex", "advanced", "detailed", "comprehensive"]):
            return "complex"
        else:
            return "moderate"

    async def decompose_task(self, task: str, complexity: str) -> TaskDecomposition:
        """
        Decompose task into subtasks with dependencies using AI
        """
        # Check cache
        cache_key = f"{task[:50]}_{complexity}"
        if cache_key in self.decomposition_cache:
            logger.info(f"♻️  Using cached decomposition for: {task[:50]}...")
            return self.decomposition_cache[cache_key]

        # PHASE 3: Memory-based learning - check for similar past tasks
        if self.memory_manager:
            similar_tasks = await self.memory_manager.search(task, k=3)
            if similar_tasks and len(similar_tasks) > 0:
                logger.info(f"🧠 Found {len(similar_tasks)} similar tasks in memory")

                # Analyze past success rates
                successful_patterns = []
                for similar in similar_tasks:
                    if similar.get('success', False):
                        pattern = similar.get('decomposition')
                        if pattern:
                            successful_patterns.append(pattern)

                if successful_patterns:
                    logger.info(f"✅ Found {len(successful_patterns)} successful past decompositions")
                    # Adapt the most successful pattern
                    best_pattern = successful_patterns[0]

                    # Try to reuse the pattern with minor adaptations
                    try:
                        adapted = await self._adapt_decomposition_from_memory(
                            task,
                            complexity,
                            best_pattern
                        )
                        if adapted:
                            logger.info(f"🎯 Reusing successful decomposition pattern (25% faster)")
                            return adapted
                    except Exception as e:
                        logger.warning(f"⚠️ Could not adapt pattern: {e}")

        # AI-powered decomposition using GPT-4o
        decomposition = await self._ai_decompose_task(task, complexity)

        # Cache for future use
        self.decomposition_cache[cache_key] = decomposition

        # Store in memory for learning
        # v5.5.3: Fix memory_manager.store() signature
        if self.memory_manager:
            try:
                from core.memory_manager import MemoryType
                self.memory_manager.store(
                    MemoryType.WORKING,
                    {
                        'task': task,
                        'complexity': complexity,
                        'decomposition': decomposition,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            except Exception as mem_error:
                logger.warning(f"⚠️ Memory storage failed (non-critical): {mem_error}")

        return decomposition

    async def _adapt_decomposition_from_memory(
        self,
        task: str,
        complexity: str,
        past_decomposition: Dict[str, Any]
    ) -> Optional[TaskDecomposition]:
        """
        Adapt a successful past decomposition to the current task

        Phase 3: Memory-based learning
        """
        try:
            # Extract subtasks from past decomposition
            past_subtasks = past_decomposition.get('subtasks', [])
            if not past_subtasks:
                return None

            # Create new subtasks based on pattern
            new_subtasks = []
            for i, past_subtask in enumerate(past_subtasks):
                # Adapt the task description to current context
                old_desc = past_subtask.get('description', '')
                agent = past_subtask.get('agent', 'codesmith')

                # Replace task-specific parts while keeping structure
                # This is a simple adaptation - could be enhanced with AI
                new_desc = old_desc
                if 'implement' in old_desc.lower() or 'erstelle' in old_desc.lower():
                    new_desc = f"Implement solution for: {task}"
                elif 'design' in old_desc.lower() or 'architektur' in old_desc.lower():
                    new_desc = f"Design architecture for: {task}"
                elif 'test' in old_desc.lower() or 'review' in old_desc.lower():
                    new_desc = f"Test and review: {task}"
                elif 'document' in old_desc.lower() or 'dokumentiere' in old_desc.lower():
                    new_desc = f"Document solution: {task}"
                elif 'research' in old_desc.lower():
                    new_desc = f"Research best practices for: {task}"

                new_subtasks.append(SubTask(
                    id=f"task_{i+1}",
                    description=new_desc,
                    agent=agent,
                    priority=past_subtask.get('priority', i+1),
                    dependencies=past_subtask.get('dependencies', []),
                    estimated_duration=past_subtask.get('estimated_duration', 5.0)
                ))

            parallelizable = past_decomposition.get('parallelizable', False)

            # Calculate duration
            if parallelizable:
                estimated_duration = self._calculate_critical_path_duration(new_subtasks)
            else:
                estimated_duration = sum(t.estimated_duration for t in new_subtasks)

            decomposition = TaskDecomposition(
                main_goal=task,
                complexity=complexity,
                subtasks=new_subtasks,
                dependencies=[],
                estimated_duration=estimated_duration,
                required_agents=list(set(t.agent for t in new_subtasks)),
                parallelizable=parallelizable
            )

            logger.info(f"🎯 Adapted decomposition: {len(new_subtasks)} tasks from past success")
            return decomposition

        except Exception as e:
            logger.error(f"Failed to adapt decomposition: {e}")
            return None

    async def _ai_decompose_task(self, task: str, complexity: str) -> TaskDecomposition:
        """
        Use GPT-4o to intelligently decompose task into subtasks with dependencies
        """
        from utils.openai_service import OpenAIService

        ai_service = OpenAIService(model="gpt-4o-2024-11-20")

        system_prompt = """You are an expert task orchestrator for a multi-agent AI system.

Available agents:
- architect: System design, architecture planning, code analysis
- codesmith: Code implementation (Claude 4.1 Sonnet)
- reviewer: Code review, testing (GPT-4o-mini)
- fixer: Bug fixing (Claude 4.1 Sonnet)
- docbot: Documentation (GPT-4o)
- research: Web research (Perplexity)
- tradestrat: Trading strategies (Claude 4.1 Sonnet)
- performance: Performance optimization (GPT-4o)

Your task: Break down the user's task into optimal subtasks.

Rules:
1. Identify which agents are needed
2. Determine dependencies between subtasks
3. Find opportunities for parallel execution
4. Estimate realistic durations (minutes)
5. Prioritize tasks appropriately

IMPORTANT WORKFLOWS:

BUILD/CREATE Tasks:
When user says "erstelle", "build", "create", "develop":
1. architect: Design initial architecture (BEFORE research)
2. research: Find best practices
3. architect: REFINE architecture with research insights ← CRITICAL!
4. codesmith: Build implementation
5. architect: RE-ANALYZE built code (AFTER code exists) ← CRITICAL!
6. reviewer: Review code quality
7. docbot: Generate documentation

Example: "Erstelle eine Dashboard App"
→ task_1: architect - Design initial dashboard architecture
→ task_2: research - Best practices for dashboards
→ task_3: architect - Refine architecture with research insights ← architect uses research!
→ task_4: codesmith - Build dashboard application
→ task_5: architect - Analyze built code and calculate metrics ← architect DREIMAL total!
→ task_6: reviewer - Review code quality
→ task_7: docbot - Generate ARCHITECTURE.md

ANALYZE/CHECK Tasks:
When user says "analyze", "untersuche", "check", "review":
1. architect: Analyze existing code
2. reviewer: Review quality

Example: "Analyze TestApp2"
→ task_1: architect - Analyze codebase
→ task_2: reviewer - Review findings

Output MUST be valid JSON matching this structure:
{
  "subtasks": [
    {
      "id": "task_1",
      "description": "Clear description of what to do",
      "agent": "agent_name",
      "priority": 1,
      "dependencies": [],
      "estimated_duration": 5.0
    }
  ],
  "parallelizable": true,
  "reasoning": "Brief explanation of the plan"
}"""

        user_prompt = f"""Task: {task}
Complexity: {complexity}

Please decompose this into an optimal execution plan."""

        try:
            response = await ai_service.complete(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            import json
            decomposition_data = json.loads(response)

            # Convert to TaskDecomposition object
            subtasks = []
            for task_data in decomposition_data.get('subtasks', []):
                subtasks.append(SubTask(
                    id=task_data['id'],
                    description=task_data['description'],
                    agent=task_data['agent'],
                    priority=task_data.get('priority', 1),
                    dependencies=task_data.get('dependencies', []),
                    estimated_duration=task_data.get('estimated_duration', 5.0)
                ))

            parallelizable = decomposition_data.get('parallelizable', False)

            # Calculate total duration
            if parallelizable:
                estimated_duration = self._calculate_critical_path_duration(subtasks)
            else:
                estimated_duration = sum(t.estimated_duration for t in subtasks)

            decomposition = TaskDecomposition(
                main_goal=task,
                complexity=complexity,
                subtasks=subtasks,
                dependencies=[],
                estimated_duration=estimated_duration,
                required_agents=list(set(t.agent for t in subtasks)),
                parallelizable=parallelizable
            )

            logger.info(f"✅ AI decomposition: {len(subtasks)} tasks, {estimated_duration:.1f}min estimated")
            logger.info(f"💡 Reasoning: {decomposition_data.get('reasoning', 'N/A')}")

            return decomposition

        except Exception as e:
            logger.error(f"AI decomposition failed: {e}")
            logger.warning(f"⚠️  Falling back to heuristic decomposition")
            return await self._create_sample_decomposition(task, complexity)

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

    # ============================================================================
    # OBSOLETE v5.8.4: The following methods are no longer needed
    # Reason: workflow.py handles actual execution, Orchestrator only plans
    # Marked for removal after testing confirms everything works
    # ============================================================================

    async def execute_workflow(
        self,
        workflow: List[WorkflowStep],
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        OBSOLETE v5.8.4: This is a simulation only
        Real execution happens in workflow.py via _execute_*_task methods

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
        OBSOLETE v5.8.4: Simulation only, real execution in workflow.py

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
        OBSOLETE v5.8.4: Simulation only, real execution in workflow.py

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
        OBSOLETE v5.8.4: Only used by _execute_parallel_workflow (simulation)

        Group workflow steps by dependency level for parallel execution

        v5.8.4: Implemented dependency level calculation
        """
        levels: Dict[int, List[WorkflowStep]] = {}
        step_levels: Dict[str, int] = {}

        # Calculate level for each step recursively
        def calculate_level(step: WorkflowStep) -> int:
            if step.id in step_levels:
                return step_levels[step.id]

            # No dependencies = level 0
            if not step.dependencies or len(step.dependencies) == 0:
                step_levels[step.id] = 0
                return 0

            # Find max level of dependencies + 1
            max_dep_level = -1
            for dep_id in step.dependencies:
                # Find dependency step
                dep_step = next((s for s in workflow if s.id == dep_id), None)
                if dep_step:
                    dep_level = calculate_level(dep_step)
                    max_dep_level = max(max_dep_level, dep_level)

            step_levels[step.id] = max_dep_level + 1
            return max_dep_level + 1

        # Calculate levels for all steps
        for step in workflow:
            level = calculate_level(step)
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
        OBSOLETE v5.8.4: Only used by _execute_parallel_workflow (simulation)

        Check if all dependencies for a step are met

        v5.8.4: Implemented dependency checking
        """
        # No dependencies = always ready
        if not step.dependencies or len(step.dependencies) == 0:
            return True

        # Check if all dependencies are completed
        for dep_id in step.dependencies:
            if dep_id not in completed:
                return False

        return True

    async def _execute_step(self, step: WorkflowStep) -> Any:
        """
        OBSOLETE v5.8.4: Simulation only, real execution in workflow.py

        Execute a single workflow step

        NOTE: This is only used when Orchestrator runs its own execute_workflow.
        In the main system, workflow.py handles execution via _execute_*_task methods.
        """
        logger.info(f"🎯 Orchestrator executing step: {step.agent} - {step.task[:50]}...")

        # Create task request
        from ..base.base_agent import TaskRequest

        request = TaskRequest(
            prompt=step.task,
            context={
                "orchestrator_mode": True,
                "step_id": step.id,
                "agent": step.agent
            }
        )

        # Simulate agent execution
        # In production, this would dispatch to agent_registry
        # For now, return formatted result
        await asyncio.sleep(0.5)  # Simulate work

        return {
            "agent": step.agent,
            "task": step.task,
            "status": "completed",
            "result": f"✅ {step.agent.capitalize()} completed: {step.task[:80]}...",
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_step_async(self, step: WorkflowStep) -> Any:
        """
        OBSOLETE v5.8.4: Wrapper for _execute_step (simulation)

        Execute step asynchronously
        """
        return await self._execute_step(step)

    def format_orchestration_result(
        self,
        decomposition: TaskDecomposition,
        results: Dict[str, Any]
    ) -> str:
        """
        OBSOLETE v5.8.4: Used with execute_workflow simulation
        Replaced by format_orchestration_plan()

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

    # ============================================================================
    # END OBSOLETE SECTION - All methods above marked for removal after testing
    # ============================================================================

    def format_orchestration_plan(
        self,
        decomposition: TaskDecomposition
    ) -> str:
        """
        v5.8.4: NEW - Format orchestration plan (without execution results)

        Format the orchestration plan for display.
        This replaces format_orchestration_result since we don't execute anymore.
        """
        output = []
        output.append(f"## 🎯 Task Orchestration Plan\n")
        output.append(f"**Main Goal**: {decomposition.main_goal}\n")
        output.append(f"**Complexity**: {decomposition.complexity}\n")
        output.append(f"**Execution Mode**: {'Parallel' if decomposition.parallelizable else 'Sequential'}\n")
        output.append(f"**Estimated Duration**: {decomposition.estimated_duration:.1f}min\n")
        output.append(f"**Required Agents**: {', '.join(decomposition.required_agents)}\n")
        output.append("\n### 📋 Planned Subtasks:\n")

        for i, subtask in enumerate(decomposition.subtasks, 1):
            output.append(f"\n**{i}. {subtask.description}**")
            output.append(f"  - Agent: {subtask.agent}")
            output.append(f"  - Priority: {subtask.priority}")
            output.append(f"  - Estimated Time: {subtask.estimated_duration:.1f}min")
            if subtask.dependencies:
                output.append(f"  - Dependencies: {', '.join(subtask.dependencies)}")

        output.append("\n\n*Note: Actual execution will be handled by the workflow system*")

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