# Self-Diagnosis and Self-Healing Patterns for KI AutoAgent
## v5.4.3 - Enhanced Autonomous Problem Resolution

---

## 🔍 Current Self-Diagnosis Capabilities Analysis

### What the System CAN Currently Detect:

#### 1. **Infinite Loops (v5.4.2 Fix)**
```python
# The system NOW detects when orchestrator is routing to itself
if agent == "orchestrator":
    step_status = "completed"  # Prevent re-execution
```
**✅ FIXED** - But only after we manually identified and patched it

#### 2. **Stuck Steps (v5.2.2)**
```python
stuck_steps = [s for s in state["execution_plan"] if s.status == "in_progress"]
if stuck_steps:
    logger.error("❌ CRITICAL: Found in_progress steps but no more routing possible!")
```
**✅ DETECTABLE** - System can identify stuck steps but forcibly marks as failed

#### 3. **Escalation Patterns (v5.1.0)**
```python
if collaboration_count > 12:
    escalation_level = 5  # Ask user for help
```
**✅ IMPLEMENTED** - System escalates when stuck in collaboration loops

### What the System CANNOT Currently Detect:

#### 1. **Status Transition Violations**
- No validation that status transitions are legal
- Can't detect if a step goes from "completed" back to "pending"
- No state machine enforcement

#### 2. **Dependency Cycles**
- No detection of circular dependencies
- Can't identify if Step A depends on B, B depends on C, C depends on A

#### 3. **Resource Exhaustion**
- No memory usage tracking
- No detection of growing message lists
- No circuit breakers for API rate limits

#### 4. **Logic Errors in Planning**
- Can't detect if orchestrator creates duplicate steps
- No validation of plan coherence
- Can't identify contradictory instructions

---

## 🤖 Self-Diagnosis Implementation Strategy

### Phase 1: Detection Layer (Immediate)

```python
class WorkflowDiagnostics:
    """v5.4.3: Self-diagnosis system for workflow health"""

    def __init__(self):
        self.health_metrics = {
            "loop_detections": 0,
            "timeout_events": 0,
            "retry_exhaustions": 0,
            "escalation_triggers": 0,
            "dependency_violations": 0
        }
        self.patterns_detected = []

    def diagnose_workflow_health(self, state: ExtendedAgentState) -> Dict[str, Any]:
        """Run comprehensive health check on workflow state"""
        issues = []

        # Check 1: Infinite Loop Detection
        if self._detect_routing_loop(state):
            issues.append({
                "type": "ROUTING_LOOP",
                "severity": "CRITICAL",
                "description": "Same agent being routed repeatedly",
                "suggested_fix": "Mark orchestrator steps as completed"
            })

        # Check 2: Status Inconsistencies
        status_issues = self._check_status_consistency(state)
        if status_issues:
            issues.extend(status_issues)

        # Check 3: Dependency Health
        dep_issues = self._check_dependency_health(state)
        if dep_issues:
            issues.extend(dep_issues)

        # Check 4: Performance Degradation
        if self._detect_performance_issues(state):
            issues.append({
                "type": "PERFORMANCE_DEGRADATION",
                "severity": "WARNING",
                "description": "Workflow taking longer than expected"
            })

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "metrics": self.health_metrics
        }

    def _detect_routing_loop(self, state: ExtendedAgentState) -> bool:
        """Detect if same routing pattern repeats"""
        history = state.get("collaboration_history", [])
        if len(history) >= 3:
            # Check last 3 routing decisions
            last_3 = history[-3:]
            if all(h["to"] == last_3[0]["to"] for h in last_3):
                return True
        return False

    def _check_status_consistency(self, state: ExtendedAgentState) -> List[Dict]:
        """Validate status transitions are legal"""
        issues = []
        valid_transitions = {
            "pending": ["in_progress", "blocked", "cancelled"],
            "in_progress": ["completed", "failed", "timeout"],
            "completed": [],  # Terminal state
            "failed": ["pending"],  # Allow retry
            "blocked": ["pending", "cancelled"],
            "timeout": ["pending", "failed"]
        }

        # Track status history (would need to be added to ExecutionStep)
        for step in state["execution_plan"]:
            # This would need status_history tracking
            pass

        return issues

    def _check_dependency_health(self, state: ExtendedAgentState) -> List[Dict]:
        """Check for dependency cycles and violations"""
        issues = []
        steps = state["execution_plan"]

        # Build dependency graph
        for step in steps:
            visited = set()
            if self._has_cycle(step.id, steps, visited):
                issues.append({
                    "type": "DEPENDENCY_CYCLE",
                    "severity": "CRITICAL",
                    "step_id": step.id,
                    "description": f"Step {step.id} has circular dependency"
                })

        return issues

    def _has_cycle(self, step_id: str, all_steps: List, visited: set) -> bool:
        """DFS to detect cycles in dependency graph"""
        if step_id in visited:
            return True
        visited.add(step_id)

        step = next((s for s in all_steps if s.id == step_id), None)
        if step:
            for dep_id in step.dependencies:
                if self._has_cycle(dep_id, all_steps, visited):
                    return True

        visited.remove(step_id)
        return False
```

### Phase 2: Self-Healing Actions

```python
class WorkflowSelfHealing:
    """v5.4.3: Self-healing mechanisms for common issues"""

    def __init__(self, diagnostics: WorkflowDiagnostics):
        self.diagnostics = diagnostics
        self.healing_actions_taken = []

    async def auto_heal(self, state: ExtendedAgentState) -> ExtendedAgentState:
        """Attempt to automatically fix detected issues"""
        health_report = self.diagnostics.diagnose_workflow_health(state)

        if not health_report["healthy"]:
            for issue in health_report["issues"]:
                if issue["severity"] == "CRITICAL":
                    state = await self._heal_critical_issue(state, issue)
                elif issue["severity"] == "WARNING":
                    state = await self._heal_warning_issue(state, issue)

        return state

    async def _heal_critical_issue(self, state: ExtendedAgentState, issue: Dict) -> ExtendedAgentState:
        """Handle critical issues that block workflow"""

        if issue["type"] == "ROUTING_LOOP":
            # Fix: Complete orchestrator steps immediately
            for step in state["execution_plan"]:
                if step.agent == "orchestrator" and step.status == "pending":
                    step.status = "completed"
                    step.result = "Orchestrator planning complete"
                    logger.warning(f"🔧 SELF-HEAL: Marked orchestrator step {step.id} as completed to prevent loop")

            state["execution_plan"] = list(state["execution_plan"])
            self.healing_actions_taken.append({
                "issue": "ROUTING_LOOP",
                "action": "completed_orchestrator_steps",
                "timestamp": datetime.now()
            })

        elif issue["type"] == "DEPENDENCY_CYCLE":
            # Fix: Break cycle by removing one dependency
            step_id = issue["step_id"]
            for step in state["execution_plan"]:
                if step.id == step_id and step.dependencies:
                    removed_dep = step.dependencies.pop()
                    logger.warning(f"🔧 SELF-HEAL: Removed dependency {removed_dep} from step {step_id} to break cycle")
                    break

            state["execution_plan"] = list(state["execution_plan"])

        return state

    async def _heal_warning_issue(self, state: ExtendedAgentState, issue: Dict) -> ExtendedAgentState:
        """Handle non-critical issues"""

        if issue["type"] == "PERFORMANCE_DEGRADATION":
            # Increase timeouts for remaining steps
            for step in state["execution_plan"]:
                if step.status == "pending":
                    step.timeout_seconds = int(step.timeout_seconds * 1.5)

            logger.info("🔧 SELF-HEAL: Increased timeouts due to performance degradation")

        return state
```

### Phase 3: Proactive Problem Prevention

```python
class WorkflowPrevention:
    """v5.4.3: Prevent problems before they occur"""

    @staticmethod
    def validate_execution_plan(plan: List[ExecutionStep]) -> List[str]:
        """Validate plan before execution"""
        warnings = []

        # Check 1: No orchestrator as destination
        for step in plan:
            if step.agent == "orchestrator" and step.status == "pending":
                warnings.append("Orchestrator set as destination agent - will cause loop!")

        # Check 2: Reasonable step count
        if len(plan) > 20:
            warnings.append(f"Plan has {len(plan)} steps - consider breaking into sub-tasks")

        # Check 3: Dependency depth
        max_depth = WorkflowPrevention._calculate_max_dependency_depth(plan)
        if max_depth > 5:
            warnings.append(f"Dependency chain depth is {max_depth} - may cause delays")

        return warnings

    @staticmethod
    def _calculate_max_dependency_depth(plan: List[ExecutionStep]) -> int:
        """Calculate maximum dependency chain length"""
        def get_depth(step_id: str, steps_dict: Dict) -> int:
            step = steps_dict.get(step_id)
            if not step or not step.dependencies:
                return 0
            return 1 + max(get_depth(dep, steps_dict) for dep in step.dependencies)

        steps_dict = {s.id: s for s in plan}
        return max(get_depth(s.id, steps_dict) for s in plan) if plan else 0
```

---

## 🎯 Making Agents Self-Aware

### Current Gap: Agents Can't Detect Their Own Issues

**Problem**: Our infinite loop bug existed because:
1. Orchestrator didn't know it was creating plans for itself
2. No agent checked if the plan made logical sense
3. Status management was implicit, not explicit

### Solution: Agent Self-Awareness Protocol

```python
class AgentSelfAwareness:
    """Make agents aware of their role and limitations"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.capabilities = self._define_capabilities()
        self.limitations = self._define_limitations()
        self.valid_outputs = self._define_valid_outputs()

    def _define_capabilities(self) -> List[str]:
        """What this agent CAN do"""
        capabilities_map = {
            "orchestrator": ["plan_tasks", "decompose_complex_tasks", "route_to_agents"],
            "architect": ["design_systems", "create_architectures", "propose_solutions"],
            "codesmith": ["write_code", "implement_features", "create_functions"],
            "reviewer": ["review_code", "find_bugs", "suggest_improvements"],
            "fixer": ["fix_bugs", "resolve_issues", "repair_code"]
        }
        return capabilities_map.get(self.agent_name, [])

    def _define_limitations(self) -> List[str]:
        """What this agent CANNOT do"""
        limitations_map = {
            "orchestrator": ["execute_code", "be_destination_agent", "modify_files"],
            "architect": ["implement_code", "fix_bugs", "execute_plans"],
            "codesmith": ["review_own_code", "deploy_code", "approve_changes"],
            "reviewer": ["fix_issues_found", "write_new_code", "execute_tests"],
            "fixer": ["create_new_features", "design_architecture", "review_fixes"]
        }
        return limitations_map.get(self.agent_name, [])

    def validate_task(self, task: str) -> Tuple[bool, str]:
        """Check if this agent should handle this task"""
        task_lower = task.lower()

        # Check if task violates limitations
        for limitation in self.limitations:
            if limitation.replace("_", " ") in task_lower:
                return False, f"Agent {self.agent_name} cannot {limitation}"

        # Check if task matches capabilities
        capability_match = False
        for capability in self.capabilities:
            if any(word in task_lower for word in capability.split("_")):
                capability_match = True
                break

        if not capability_match:
            return False, f"Task doesn't match {self.agent_name} capabilities"

        return True, "Task is valid for this agent"

    def validate_output(self, output: Any) -> Tuple[bool, str]:
        """Validate agent's output is reasonable"""
        if self.agent_name == "orchestrator":
            # Orchestrator should never create steps for itself
            if isinstance(output, list):
                for step in output:
                    if hasattr(step, 'agent') and step.agent == "orchestrator":
                        return False, "Orchestrator cannot assign tasks to itself"

        return True, "Output is valid"
```

---

## 📋 Implementation Checklist

### Immediate (v5.4.3):
- [x] Task Ledger for better tracking
- [x] Progress Ledger for visibility
- [x] Timeout management with retry
- [x] Parallel execution identification
- [ ] Basic self-diagnosis in workflow.py
- [ ] Validation before plan execution

### Next Release (v5.5.0):
- [ ] WorkflowDiagnostics class
- [ ] WorkflowSelfHealing class
- [ ] AgentSelfAwareness protocol
- [ ] Status transition validation
- [ ] Dependency cycle detection
- [ ] Performance monitoring

### Future (v6.0.0):
- [ ] Machine learning for pattern detection
- [ ] Predictive problem prevention
- [ ] Automatic optimization suggestions
- [ ] Self-modifying workflows
- [ ] Distributed health monitoring

---

## 🚨 Critical Insight: Why the Bug Happened

The infinite loop bug (v5.4.2) occurred because:

1. **Implicit Assumptions**: Code assumed orchestrator would never be a destination
2. **Missing Validation**: No checks that plans were logically valid
3. **Status Ambiguity**: "pending" meant different things in different contexts
4. **No Self-Checking**: Agents didn't validate their own inputs/outputs

**Key Learning**: The system needs explicit rules, not implicit assumptions.

---

## 💡 Recommendations for True Self-Healing

### 1. **Explicit State Machine**
Replace implicit status handling with explicit state machine that enforces valid transitions.

### 2. **Contract-Based Design**
Each agent should have explicit contracts:
- **Preconditions**: What must be true before execution
- **Postconditions**: What must be true after execution
- **Invariants**: What must always be true

### 3. **Observability First**
Before self-healing can work, the system needs complete observability:
- Structured logging with correlation IDs
- Metrics for every decision point
- Traces for entire workflow execution

### 4. **Fail-Fast Philosophy**
Instead of trying to continue with invalid state, fail immediately with clear error messages.

### 5. **Test Harness for Edge Cases**
Create automated tests that specifically test:
- Routing loops
- Status transitions
- Dependency cycles
- Timeout scenarios
- Retry exhaustion

---

## 🎯 Conclusion

**Current State**: The system has basic error detection but lacks true self-diagnosis.

**Gap**: Agents operate without awareness of system-wide constraints.

**Solution**: Implement three-layer approach:
1. **Detection** - Comprehensive health checks
2. **Healing** - Automated fixes for known issues
3. **Prevention** - Validation before problems occur

**Most Important**: The infinite loop bug showed that implicit assumptions are dangerous. Every rule must be explicit, validated, and enforced.

With the v5.4.3 enhancements and this self-diagnosis framework, the system will be much more resilient and self-aware.