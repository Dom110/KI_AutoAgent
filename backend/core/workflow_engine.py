"""
WorkflowEngine - Graph-based workflow execution for complex task orchestration
Enables parallel execution, conditional flows, and dynamic plan adjustment
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Types of workflow nodes"""
    TASK = "task"           # Single task execution
    DECISION = "decision"   # Conditional branching
    PARALLEL = "parallel"   # Parallel execution
    SEQUENTIAL = "sequential"  # Sequential execution
    LOOP = "loop"          # Loop execution

class WorkflowState(Enum):
    """Workflow execution states"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class RetryPolicy:
    """Retry policy for failed tasks"""
    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    max_backoff_ms: int = 30000

@dataclass
class WorkflowNode:
    """Node in workflow graph"""
    id: str
    type: NodeType
    agent_id: Optional[str] = None
    task: Optional[Any] = None
    condition: Optional[Callable[[Dict], bool]] = None
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    retry_policy: Optional[RetryPolicy] = None
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowEdge:
    """Edge between workflow nodes"""
    from_node: str
    to_node: str
    condition: Optional[Callable[[Dict], bool]] = None
    weight: float = 1.0

@dataclass
class TaskResult:
    """Result of task execution"""
    node_id: str
    status: str  # 'success', 'failure', 'skipped'
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    retries: int = 0

@dataclass
class Checkpoint:
    """Workflow checkpoint for recovery"""
    id: str
    node_id: str
    timestamp: float
    context: Dict[str, Any]
    results: Dict[str, TaskResult]

@dataclass
class ExecutionStage:
    """Stage in execution plan"""
    stage_id: str
    nodes: List[WorkflowNode]
    parallel: bool
    dependencies: List[str]
    estimated_duration: float

class WorkflowEngine:
    """
    Graph-based workflow execution engine
    """

    def __init__(self):
        """Initialize workflow engine"""
        self.workflows: Dict[str, 'Workflow'] = {}
        self.templates: Dict[str, Dict] = {}
        self.executors: Dict[str, 'WorkflowExecutor'] = {}

        # Statistics
        self.total_workflows = 0
        self.completed_workflows = 0
        self.failed_workflows = 0

        self._initialize_templates()
        logger.info("WorkflowEngine initialized")

    def _initialize_templates(self):
        """Initialize workflow templates"""
        # Code generation workflow
        self.templates["code_generation"] = {
            "nodes": [
                {"id": "analyze", "type": NodeType.TASK, "agent_id": "architect"},
                {"id": "implement", "type": NodeType.TASK, "agent_id": "codesmith"},
                {"id": "review", "type": NodeType.TASK, "agent_id": "reviewer"},
                {"id": "fix", "type": NodeType.TASK, "agent_id": "fixer", "condition": lambda ctx: ctx.get("has_issues")}
            ],
            "edges": [
                {"from": "analyze", "to": "implement"},
                {"from": "implement", "to": "review"},
                {"from": "review", "to": "fix"}
            ]
        }

        # Research workflow
        self.templates["research"] = {
            "nodes": [
                {"id": "research", "type": NodeType.TASK, "agent_id": "research"},
                {"id": "analyze", "type": NodeType.TASK, "agent_id": "architect"},
                {"id": "document", "type": NodeType.TASK, "agent_id": "docubot"}
            ],
            "edges": [
                {"from": "research", "to": "analyze"},
                {"from": "analyze", "to": "document"}
            ]
        }

    def create_workflow(
        self,
        name: str,
        template: Optional[str] = None
    ) -> 'Workflow':
        """Create a new workflow"""
        workflow_id = self._generate_id()

        workflow = Workflow(
            id=workflow_id,
            name=name,
            engine=self
        )

        # Apply template if provided
        if template and template in self.templates:
            self._apply_template(workflow, self.templates[template])

        self.workflows[workflow_id] = workflow
        self.total_workflows += 1

        logger.info(f"Created workflow: {name} ({workflow_id})")
        return workflow

    def _apply_template(self, workflow: 'Workflow', template: Dict):
        """Apply template to workflow"""
        # Add nodes
        for node_data in template.get("nodes", []):
            node = WorkflowNode(**node_data)
            workflow.add_node(node)

        # Add edges
        for edge_data in template.get("edges", []):
            workflow.add_edge(
                edge_data["from"],
                edge_data["to"],
                edge_data.get("condition")
            )

    def get_workflow(self, workflow_id: str) -> Optional['Workflow']:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)

    def _generate_id(self) -> str:
        """Generate unique ID"""
        return f"wf_{uuid.uuid4().hex[:8]}"

class Workflow:
    """
    Workflow instance
    """

    def __init__(self, id: str, name: str, engine: WorkflowEngine):
        """Initialize workflow"""
        self.id = id
        self.name = name
        self.engine = engine

        # Graph structure
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.start_node: Optional[str] = None
        self.end_nodes: List[str] = []

        # Execution state
        self.state = WorkflowState.PENDING
        self.context: Dict[str, Any] = {}
        self.results: Dict[str, TaskResult] = {}
        self.checkpoints: List[Checkpoint] = []

        # Status tracking
        self.current_nodes: Set[str] = set()
        self.completed_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def add_node(self, node: WorkflowNode):
        """Add node to workflow"""
        self.nodes[node.id] = node

        # Set as start node if first
        if not self.start_node:
            self.start_node = node.id

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable] = None
    ):
        """Add edge between nodes"""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist in workflow")

        edge = WorkflowEdge(
            from_node=from_node,
            to_node=to_node,
            condition=condition
        )

        self.edges.append(edge)

        # Update node relationships
        self.nodes[from_node].children.append(to_node)
        self.nodes[to_node].dependencies.append(from_node)

    def create_execution_plan(self) -> List[ExecutionStage]:
        """Create execution plan using topological sort"""
        # Topological sort to find execution order
        sorted_nodes = self._topological_sort()

        # Group into stages based on dependencies
        stages = self._group_into_stages(sorted_nodes)

        return stages

    def _topological_sort(self) -> List[str]:
        """Perform topological sort on workflow graph"""
        in_degree = defaultdict(int)

        # Calculate in-degrees
        for node_id in self.nodes:
            in_degree[node_id] = len(self.nodes[node_id].dependencies)

        # Find nodes with no dependencies
        queue = deque([
            node_id for node_id in self.nodes
            if in_degree[node_id] == 0
        ])

        sorted_nodes = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)

            # Reduce in-degree for children
            for child_id in self.nodes[node_id].children:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Workflow contains cycles")

        return sorted_nodes

    def _group_into_stages(self, sorted_nodes: List[str]) -> List[ExecutionStage]:
        """Group nodes into execution stages"""
        stages = []
        processed = set()
        stage_num = 0

        while len(processed) < len(sorted_nodes):
            # Find nodes that can execute in this stage
            stage_nodes = []

            for node_id in sorted_nodes:
                if node_id in processed:
                    continue

                # Check if all dependencies are processed
                deps = self.nodes[node_id].dependencies
                if all(dep in processed for dep in deps):
                    stage_nodes.append(self.nodes[node_id])

            if not stage_nodes:
                break

            # Create stage
            stage = ExecutionStage(
                stage_id=f"stage_{stage_num}",
                nodes=stage_nodes,
                parallel=len(stage_nodes) > 1,
                dependencies=[f"stage_{i}" for i in range(stage_num)],
                estimated_duration=max(
                    n.timeout for n in stage_nodes
                ) if stage_nodes else 0
            )

            stages.append(stage)

            # Mark nodes as processed
            for node in stage_nodes:
                processed.add(node.id)

            stage_num += 1

        return stages

    async def execute(
        self,
        context: Optional[Dict[str, Any]] = None,
        executor: Optional['WorkflowExecutor'] = None
    ) -> Dict[str, TaskResult]:
        """Execute the workflow"""
        if context:
            self.context.update(context)

        # Use provided executor or create new one
        if not executor:
            executor = WorkflowExecutor(self)

        # Update state
        self.state = WorkflowState.RUNNING
        self.start_time = time.time()

        try:
            # Create execution plan
            plan = self.create_execution_plan()

            # Execute plan
            results = await executor.execute_plan(plan)

            # Update state
            self.state = WorkflowState.COMPLETED
            self.end_time = time.time()

            logger.info(f"Workflow {self.name} completed in {self.end_time - self.start_time:.2f}s")
            return results

        except Exception as e:
            self.state = WorkflowState.FAILED
            self.end_time = time.time()
            logger.error(f"Workflow {self.name} failed: {e}")
            raise

    def create_checkpoint(self) -> Checkpoint:
        """Create a checkpoint for recovery"""
        return Checkpoint(
            id=f"cp_{int(time.time())}",
            node_id=list(self.current_nodes)[0] if self.current_nodes else "",
            timestamp=time.time(),
            context=dict(self.context),
            results=dict(self.results)
        )

    def restore_from_checkpoint(self, checkpoint: Checkpoint):
        """Restore workflow from checkpoint"""
        self.context = dict(checkpoint.context)
        self.results = dict(checkpoint.results)

        # Determine completed nodes
        self.completed_nodes = set(checkpoint.results.keys())

        logger.info(f"Restored workflow from checkpoint {checkpoint.id}")

class WorkflowExecutor:
    """
    Executes workflow plans
    """

    def __init__(self, workflow: Workflow):
        """Initialize executor"""
        self.workflow = workflow
        self.registry = None  # Will be injected

    async def execute_plan(
        self,
        plan: List[ExecutionStage]
    ) -> Dict[str, TaskResult]:
        """Execute workflow plan"""
        all_results = {}

        for stage in plan:
            logger.info(f"Executing stage {stage.stage_id} with {len(stage.nodes)} nodes")

            if stage.parallel:
                # Execute nodes in parallel
                results = await self._execute_parallel(stage.nodes)
            else:
                # Execute nodes sequentially
                results = await self._execute_sequential(stage.nodes)

            all_results.update(results)

            # Check for failures
            if any(r.status == "failure" for r in results.values()):
                if not self._should_continue_on_failure():
                    break

        return all_results

    async def _execute_parallel(
        self,
        nodes: List[WorkflowNode]
    ) -> Dict[str, TaskResult]:
        """Execute nodes in parallel"""
        tasks = [
            self._execute_node(node)
            for node in nodes
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            node.id: result if not isinstance(result, Exception)
            else TaskResult(
                node_id=node.id,
                status="failure",
                error=str(result)
            )
            for node, result in zip(nodes, results)
        }

    async def _execute_sequential(
        self,
        nodes: List[WorkflowNode]
    ) -> Dict[str, TaskResult]:
        """Execute nodes sequentially"""
        results = {}

        for node in nodes:
            result = await self._execute_node(node)
            results[node.id] = result

            if result.status == "failure" and not self._should_continue_on_failure():
                break

        return results

    async def _execute_node(self, node: WorkflowNode) -> TaskResult:
        """Execute a single node"""
        start_time = time.time()

        try:
            # Check condition if present
            if node.condition and not node.condition(self.workflow.context):
                return TaskResult(
                    node_id=node.id,
                    status="skipped",
                    duration=0
                )

            # Update current nodes
            self.workflow.current_nodes.add(node.id)

            # Execute based on node type
            output = await self._execute_task(node)

            # Mark as completed
            self.workflow.current_nodes.remove(node.id)
            self.workflow.completed_nodes.add(node.id)

            return TaskResult(
                node_id=node.id,
                status="success",
                output=output,
                duration=time.time() - start_time
            )

        except Exception as e:
            self.workflow.failed_nodes.add(node.id)

            return TaskResult(
                node_id=node.id,
                status="failure",
                error=str(e),
                duration=time.time() - start_time
            )

    async def _execute_task(self, node: WorkflowNode) -> Any:
        """Execute the actual task for a node"""
        # For now, simulate task execution
        # In real implementation, this would dispatch to agents

        if node.agent_id and self.registry:
            # Dispatch to agent through registry
            from agents.base.base_agent import TaskRequest

            request = TaskRequest(
                prompt=node.task or "",
                context=self.workflow.context
            )

            result = await self.registry.dispatch_task(node.agent_id, request)
            return result.content
        else:
            # Simulate execution
            await asyncio.sleep(0.5)
            return f"Executed {node.id}"

    def _should_continue_on_failure(self) -> bool:
        """Check if workflow should continue on failure"""
        return self.workflow.context.get("continue_on_failure", False)

# Global instance
_engine_instance = None

def get_workflow_engine() -> WorkflowEngine:
    """Get singleton WorkflowEngine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = WorkflowEngine()
    return _engine_instance