"""
Workflow Self-Diagnosis System v5.5.0
Implements comprehensive self-diagnosis, validation, and healing capabilities

Based on extensive research of workflow orchestration anti-patterns and failures (2024)
"""

import logging
import asyncio
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import json
from collections import defaultdict, deque

from .state import ExtendedAgentState, ExecutionStep, TaskLedger, ProgressLedger

logger = logging.getLogger(__name__)


# =================== KNOWN ANTI-PATTERNS DATABASE ===================
# Based on Internet Research (2024)

class AntiPatternType(Enum):
    """Categorization of known workflow anti-patterns"""
    SELF_ROUTING = "self_routing"  # Agent routing to itself
    CIRCULAR_DEPENDENCY = "circular_dependency"  # A->B->C->A
    UNBOUNDED_DELEGATION = "unbounded_delegation"  # Infinite agent spawning
    CONTEXT_COLLAPSE = "context_collapse"  # Lost context in deep chains
    INCREMENTAL_LOCKING = "incremental_locking"  # Deadlock risk
    NO_ERROR_HANDLING = "no_error_handling"  # Missing failure recovery
    SYNCHRONOUS_BLOCKING = "synchronous_blocking"  # Blocking operations
    STATE_INCONSISTENCY = "state_inconsistency"  # Invalid status transitions
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory/API limits
    CYCLIC_PROCESS = "cyclic_process"  # Ruleset calling cycles


@dataclass
class KnownAntiPattern:
    """Definition of a known anti-pattern from research"""
    type: AntiPatternType
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    detection_pattern: str  # Regex or logic description
    suggested_fix: str
    source: str  # Research source/reference


class KnownAntiPatternsDatabase:
    """
    Database of known anti-patterns based on internet research
    Sources: Microsoft Azure, Google Cloud, AWS, academic papers (2024)
    """

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.detection_history = deque(maxlen=100)  # Track recent detections

    def _initialize_patterns(self) -> List[KnownAntiPattern]:
        """Initialize database with researched anti-patterns"""
        return [
            KnownAntiPattern(
                type=AntiPatternType.SELF_ROUTING,
                severity="CRITICAL",
                description="Orchestrator routing to itself causes infinite loops",
                detection_pattern="agent=='orchestrator' and destination=='orchestrator'",
                suggested_fix="Mark orchestrator steps as completed immediately",
                source="KI AutoAgent v5.4.2 bug, Microsoft Azure AI patterns"
            ),
            KnownAntiPattern(
                type=AntiPatternType.CIRCULAR_DEPENDENCY,
                severity="CRITICAL",
                description="Circular task dependencies create deadlock",
                detection_pattern="Task A depends on B, B depends on C, C depends on A",
                suggested_fix="Break cycle by removing weakest dependency link",
                source="Flowsana documentation, Stack Overflow #62439522"
            ),
            KnownAntiPattern(
                type=AntiPatternType.UNBOUNDED_DELEGATION,
                severity="HIGH",
                description="Agents spawning sub-agents without limits",
                detection_pattern="delegation_depth > 5 or spawned_agents > 10",
                suggested_fix="Implement max_steps, max_children, max_rounds limits",
                source="Multi-Agent Gen AI Anti-Patterns (Arman Kamran, 2025)"
            ),
            KnownAntiPattern(
                type=AntiPatternType.CONTEXT_COLLAPSE,
                severity="HIGH",
                description="Context lost in deep collaboration chains",
                detection_pattern="collaboration_count > 10 and no escalation",
                suggested_fix="Escalate to higher-order agent or human-in-loop",
                source="LangChain multi-agent systems best practices"
            ),
            KnownAntiPattern(
                type=AntiPatternType.INCREMENTAL_LOCKING,
                severity="HIGH",
                description="Acquiring locks without strict order causes deadlock",
                detection_pattern="multiple agents waiting for same resources",
                suggested_fix="Enforce strict lock acquisition order",
                source="InfoWorld deadlock anti-patterns #3"
            ),
            KnownAntiPattern(
                type=AntiPatternType.NO_ERROR_HANDLING,
                severity="MEDIUM",
                description="Workflow assumes services never fail",
                detection_pattern="no retry policy or error handling defined",
                suggested_fix="Add exponential backoff retry with max attempts",
                source="Google Cloud Workflows best practices"
            ),
            KnownAntiPattern(
                type=AntiPatternType.CYCLIC_PROCESS,
                severity="HIGH",
                description="Ruleset A calls B, B calls A back",
                detection_pattern="repeated pattern in execution history",
                suggested_fix="Add recursion detection with event origin tracking",
                source="Fluent Commerce workflow anti-patterns"
            ),
            KnownAntiPattern(
                type=AntiPatternType.STATE_INCONSISTENCY,
                severity="MEDIUM",
                description="Invalid state transitions (completed->pending)",
                detection_pattern="status transition violates state machine rules",
                suggested_fix="Enforce state machine transition validation",
                source="Symfony Workflow documentation"
            ),
            KnownAntiPattern(
                type=AntiPatternType.RESOURCE_EXHAUSTION,
                severity="HIGH",
                description="Unlimited growth of messages/memory usage",
                detection_pattern="message_count > 1000 or memory > threshold",
                suggested_fix="Implement circuit breakers and resource limits",
                source="DevOps anti-patterns ALPACKED"
            )
        ]

    def detect_patterns(self, state: ExtendedAgentState) -> List[Tuple[KnownAntiPattern, str]]:
        """Detect any known anti-patterns in current state"""
        detected = []

        for pattern in self.patterns:
            if self._check_pattern(pattern, state):
                reason = self._get_detection_reason(pattern, state)
                detected.append((pattern, reason))
                self.detection_history.append({
                    "pattern": pattern.type.value,
                    "timestamp": datetime.now(),
                    "severity": pattern.severity
                })

        return detected

    def _check_pattern(self, pattern: KnownAntiPattern, state: ExtendedAgentState) -> bool:
        """Check if a specific anti-pattern is present"""

        if pattern.type == AntiPatternType.SELF_ROUTING:
            # Check for orchestrator self-routing
            for step in state.get("execution_plan", []):
                if step.agent == "orchestrator" and step.status == "pending":
                    return True

        elif pattern.type == AntiPatternType.CIRCULAR_DEPENDENCY:
            # Check for circular dependencies
            return self._has_circular_dependencies(state.get("execution_plan", []))

        elif pattern.type == AntiPatternType.UNBOUNDED_DELEGATION:
            # Check delegation depth
            collab_count = state.get("collaboration_count", 0)
            return collab_count > 10

        elif pattern.type == AntiPatternType.CONTEXT_COLLAPSE:
            # Check for lost context
            collab_count = state.get("collaboration_count", 0)
            escalation_level = state.get("escalation_level", 0)
            return collab_count > 10 and escalation_level == 0

        elif pattern.type == AntiPatternType.NO_ERROR_HANDLING:
            # Check for missing error handling
            for step in state.get("execution_plan", []):
                if step.max_retries == 0:
                    return True

        elif pattern.type == AntiPatternType.CYCLIC_PROCESS:
            # Check for cyclic patterns in history
            history = state.get("collaboration_history", [])
            if len(history) >= 4:
                # Check for A->B->A->B pattern
                last_4 = history[-4:]
                if (last_4[0]["to"] == last_4[2]["to"] and
                    last_4[1]["to"] == last_4[3]["to"]):
                    return True

        elif pattern.type == AntiPatternType.STATE_INCONSISTENCY:
            # Would need status history tracking
            pass

        elif pattern.type == AntiPatternType.RESOURCE_EXHAUSTION:
            # Check resource usage
            messages = state.get("messages", [])
            return len(messages) > 500

        return False

    def _has_circular_dependencies(self, steps: List[ExecutionStep]) -> bool:
        """Detect circular dependencies using DFS"""

        def has_cycle_from(step_id: str, visited: Set[str], path: Set[str]) -> bool:
            visited.add(step_id)
            path.add(step_id)

            step = next((s for s in steps if s.id == step_id), None)
            if step:
                for dep_id in step.dependencies:
                    if dep_id in path:
                        return True
                    if dep_id not in visited:
                        if has_cycle_from(dep_id, visited, path):
                            return True

            path.remove(step_id)
            return False

        visited = set()
        for step in steps:
            if step.id not in visited:
                if has_cycle_from(step.id, visited, set()):
                    return True
        return False

    def _get_detection_reason(self, pattern: KnownAntiPattern, state: ExtendedAgentState) -> str:
        """Get specific reason for pattern detection"""

        if pattern.type == AntiPatternType.SELF_ROUTING:
            for step in state.get("execution_plan", []):
                if step.agent == "orchestrator" and step.status == "pending":
                    return f"Step {step.id} routes orchestrator to itself"

        elif pattern.type == AntiPatternType.UNBOUNDED_DELEGATION:
            collab_count = state.get("collaboration_count", 0)
            return f"Collaboration count ({collab_count}) exceeds safe limit"

        return "Pattern detected based on defined criteria"


# =================== WORKFLOW INVARIANTS ===================

class WorkflowInvariants:
    """
    Explicit invariants that must ALWAYS be true
    Based on formal verification principles
    """

    def __init__(self):
        self.invariants = self._define_invariants()
        self.violations = []

    def _define_invariants(self) -> List[Dict[str, Any]]:
        """Define all system invariants"""
        return [
            {
                "id": "INV001",
                "name": "No orchestrator self-assignment",
                "description": "Orchestrator can never be a destination agent",
                "check": lambda state: not any(
                    step.agent == "orchestrator" and step.status == "pending"
                    for step in state.get("execution_plan", [])
                ),
                "severity": "CRITICAL"
            },
            {
                "id": "INV002",
                "name": "No self-dependencies",
                "description": "No step can depend on itself",
                "check": lambda state: not any(
                    step.id in step.dependencies
                    for step in state.get("execution_plan", [])
                ),
                "severity": "CRITICAL"
            },
            {
                "id": "INV003",
                "name": "Valid status transitions",
                "description": "Status transitions must follow state machine rules",
                "check": lambda state: self._check_valid_transitions(state),
                "severity": "HIGH"
            },
            {
                "id": "INV004",
                "name": "No duplicate step IDs",
                "description": "All step IDs must be unique",
                "check": lambda state: self._check_unique_ids(state),
                "severity": "CRITICAL"
            },
            {
                "id": "INV005",
                "name": "Dependencies exist",
                "description": "All referenced dependencies must exist",
                "check": lambda state: self._check_dependencies_exist(state),
                "severity": "HIGH"
            },
            {
                "id": "INV006",
                "name": "Resource limits",
                "description": "Resource usage within limits",
                "check": lambda state: (
                    len(state.get("messages", [])) < 1000 and
                    len(state.get("execution_plan", [])) < 50
                ),
                "severity": "MEDIUM"
            },
            {
                "id": "INV007",
                "name": "No infinite escalation",
                "description": "Escalation level must be bounded",
                "check": lambda state: state.get("escalation_level", 0) <= 7,
                "severity": "HIGH"
            },
            {
                "id": "INV008",
                "name": "Agent capabilities match",
                "description": "Agents assigned tasks they can handle",
                "check": lambda state: self._check_agent_capabilities(state),
                "severity": "MEDIUM"
            }
        ]

    def check_all(self, state: ExtendedAgentState) -> Tuple[bool, List[Dict]]:
        """Check all invariants and return violations"""
        self.violations = []

        for invariant in self.invariants:
            try:
                if not invariant["check"](state):
                    self.violations.append({
                        "id": invariant["id"],
                        "name": invariant["name"],
                        "description": invariant["description"],
                        "severity": invariant["severity"],
                        "timestamp": datetime.now()
                    })
            except Exception as e:
                logger.error(f"Error checking invariant {invariant['id']}: {e}")

        return len(self.violations) == 0, self.violations

    def _check_valid_transitions(self, state: ExtendedAgentState) -> bool:
        """Check if all status transitions are valid"""
        valid_transitions = {
            "pending": ["in_progress", "blocked", "cancelled"],
            "in_progress": ["completed", "failed", "timeout"],
            "completed": [],  # Terminal
            "failed": ["pending"],  # Allow retry
            "blocked": ["pending", "cancelled"],
            "timeout": ["pending", "failed"],
            "cancelled": []  # Terminal
        }

        # Would need status history tracking in ExecutionStep
        # For now, basic check
        for step in state.get("execution_plan", []):
            if step.status not in valid_transitions:
                return False
        return True

    def _check_unique_ids(self, state: ExtendedAgentState) -> bool:
        """Check all step IDs are unique"""
        steps = state.get("execution_plan", [])
        ids = [step.id for step in steps]
        return len(ids) == len(set(ids))

    def _check_dependencies_exist(self, state: ExtendedAgentState) -> bool:
        """Check all dependencies reference existing steps"""
        steps = state.get("execution_plan", [])
        all_ids = {step.id for step in steps}

        for step in steps:
            for dep_id in step.dependencies:
                if dep_id not in all_ids:
                    return False
        return True

    def _check_agent_capabilities(self, state: ExtendedAgentState) -> bool:
        """
        Check agents are assigned appropriate tasks.
        v5.7.0: Enhanced with agent suggestions and added new agents
        """
        agent_capabilities = {
            "orchestrator": ["plan", "decompose", "route", "coordinate"],
            "architect": ["design", "architecture", "propose", "structure"],
            "codesmith": ["implement", "code", "create", "build", "generate"],
            "reviewer": ["review", "analyze", "check", "validate", "test"],
            "fixer": ["fix", "repair", "resolve", "debug", "correct"],
            "research": ["search", "research", "find", "investigate", "analyze"],
            "docbot": ["document", "explain", "describe", "write", "readme", "comment"],
            "performance": ["optimize", "speed", "improve", "benchmark", "faster", "efficient"],
            "tradestrat": ["trading", "strategy", "backtest", "market", "portfolio", "risk"],
            "opus_arbitrator": ["conflict", "decide", "arbitrate", "resolve", "choose", "final"]
        }

        for step in state.get("execution_plan", []):
            agent = step.agent
            task_lower = step.task.lower()

            if agent in agent_capabilities:
                capabilities = agent_capabilities[agent]
                # Check if task matches any capability
                if not any(cap in task_lower for cap in capabilities):
                    # Suggest better suited agent
                    suggestion = self._suggest_better_agent(agent, task_lower, agent_capabilities)
                    if suggestion:
                        logger.warning(
                            f"⚠️ Agent '{agent}' may not be optimal for task: {step.task[:50]}...\n"
                            f"   💡 Suggestion: Consider using '{suggestion}' instead"
                        )
                    else:
                        logger.warning(f"⚠️ Agent '{agent}' may not be suited for task: {step.task[:50]}")
                    # Not a hard failure, just warning

        return True

    def _suggest_better_agent(self, current_agent: str, task: str, agent_capabilities: dict) -> Optional[str]:
        """
        Suggest better suited agent based on task keywords.
        v5.7.0: New method for intelligent agent suggestions
        """
        # Don't suggest if already using the agent
        best_match = None
        best_score = 0

        for agent, capabilities in agent_capabilities.items():
            if agent == current_agent:
                continue

            # Count how many capability keywords match the task
            matches = sum(1 for cap in capabilities if cap in task)

            if matches > best_score:
                best_score = matches
                best_match = agent

        # Only suggest if we found at least one match
        return best_match if best_score > 0 else None


# =================== PRE-EXECUTION VALIDATION ===================

class PreExecutionValidator:
    """
    Comprehensive pre-execution validation system
    Performs multiple validation passes with increasing depth
    """

    def __init__(self, known_patterns: KnownAntiPatternsDatabase, invariants: WorkflowInvariants):
        self.known_patterns = known_patterns
        self.invariants = invariants
        self.validation_passes = 0
        self.max_passes = 3  # Allow multiple validation rounds
        self.validation_history = []

    async def validate_comprehensive(
        self,
        state: ExtendedAgentState,
        fix_issues: bool = True
    ) -> Tuple[bool, List[Dict], ExtendedAgentState]:
        """
        Perform comprehensive validation with multiple passes
        Returns: (is_valid, issues_found, potentially_fixed_state)
        """
        logger.info("🔍 Starting Pre-Execution Validation")

        all_issues = []
        current_state = state

        for pass_num in range(self.max_passes):
            logger.info(f"  📋 Validation Pass {pass_num + 1}/{self.max_passes}")

            pass_issues = []

            # 1. Check invariants
            invariant_valid, invariant_violations = self.invariants.check_all(current_state)
            if not invariant_valid:
                logger.error(f"  ❌ Found {len(invariant_violations)} invariant violations")
                pass_issues.extend([{
                    "type": "INVARIANT_VIOLATION",
                    "pass": pass_num + 1,
                    **violation
                } for violation in invariant_violations])

            # 2. Check for known anti-patterns
            detected_patterns = self.known_patterns.detect_patterns(current_state)
            if detected_patterns:
                logger.warning(f"  ⚠️ Detected {len(detected_patterns)} anti-patterns")
                for pattern, reason in detected_patterns:
                    pass_issues.append({
                        "type": "ANTI_PATTERN",
                        "pass": pass_num + 1,
                        "pattern": pattern.type.value,
                        "severity": pattern.severity,
                        "description": pattern.description,
                        "reason": reason,
                        "suggested_fix": pattern.suggested_fix
                    })

            # 3. Structural validation
            structural_issues = await self._validate_structure(current_state)
            if structural_issues:
                logger.warning(f"  ⚠️ Found {len(structural_issues)} structural issues")
                pass_issues.extend(structural_issues)

            # 4. Semantic validation
            semantic_issues = await self._validate_semantics(current_state)
            if semantic_issues:
                logger.warning(f"  ⚠️ Found {len(semantic_issues)} semantic issues")
                pass_issues.extend(semantic_issues)

            # 5. Performance validation
            perf_issues = await self._validate_performance(current_state)
            if perf_issues:
                logger.info(f"  📊 Found {len(perf_issues)} performance concerns")
                pass_issues.extend(perf_issues)

            all_issues.extend(pass_issues)

            # If no issues or can't fix, stop
            if not pass_issues or not fix_issues:
                break

            # Try to fix issues
            logger.info(f"  🔧 Attempting to fix {len(pass_issues)} issues")
            current_state = await self._attempt_fixes(current_state, pass_issues)

            # Check if fixes resolved issues
            if pass_num < self.max_passes - 1:
                await asyncio.sleep(0.1)  # Brief pause between passes

        # Record validation results
        self.validation_history.append({
            "timestamp": datetime.now(),
            "passes": self.validation_passes,
            "issues_found": len(all_issues),
            "is_valid": len(all_issues) == 0
        })

        # Only count CRITICAL and ERROR issues, not INFO or WARNING
        critical_issues = [i for i in all_issues if i.get("severity") in ["CRITICAL", "ERROR", "HIGH"]]
        is_valid = len(critical_issues) == 0

        if is_valid:
            logger.info("✅ Pre-Execution Validation PASSED")
        else:
            logger.error(f"❌ Pre-Execution Validation FAILED with {len(all_issues)} issues")

        return is_valid, all_issues, current_state

    async def _validate_structure(self, state: ExtendedAgentState) -> List[Dict]:
        """Validate structural integrity of execution plan"""
        issues = []
        steps = state.get("execution_plan", [])

        # Check for empty plan
        if not steps:
            issues.append({
                "type": "STRUCTURAL",
                "severity": "HIGH",
                "description": "Empty execution plan"
            })
            return issues

        # Check step count
        if len(steps) > 20:
            issues.append({
                "type": "STRUCTURAL",
                "severity": "MEDIUM",
                "description": f"Plan has {len(steps)} steps (recommended max: 20)",
                "suggested_fix": "Consider breaking into sub-tasks"
            })

        # Check dependency depth
        max_depth = self._calculate_dependency_depth(steps)
        if max_depth > 5:
            issues.append({
                "type": "STRUCTURAL",
                "severity": "MEDIUM",
                "description": f"Dependency chain depth is {max_depth} (recommended max: 5)",
                "suggested_fix": "Flatten dependency structure where possible"
            })

        # Check for orphaned steps (no dependencies and nothing depends on them)
        all_deps = set()
        for step in steps:
            all_deps.update(step.dependencies)

        for step in steps:
            if not step.dependencies and step.id not in all_deps:
                if len(steps) > 1:  # Only issue if multiple steps
                    issues.append({
                        "type": "STRUCTURAL",
                        "severity": "LOW",
                        "description": f"Step {step.id} is orphaned (no dependencies)",
                        "suggested_fix": "Verify step ordering"
                    })

        return issues

    async def _validate_semantics(self, state: ExtendedAgentState) -> List[Dict]:
        """Validate semantic correctness of plan"""
        issues = []
        steps = state.get("execution_plan", [])

        # Check for duplicate tasks
        task_counts = defaultdict(int)
        for step in steps:
            task_key = f"{step.agent}:{step.task[:50]}"
            task_counts[task_key] += 1

        for task_key, count in task_counts.items():
            if count > 1:
                issues.append({
                    "type": "SEMANTIC",
                    "severity": "MEDIUM",
                    "description": f"Duplicate task detected: {task_key} ({count} times)",
                    "suggested_fix": "Consolidate duplicate tasks"
                })

        # Check for conflicting agents (e.g., reviewer reviewing their own code)
        for i, step in enumerate(steps):
            if step.agent == "reviewer":
                # Check if previous step was codesmith by same ID pattern
                if i > 0 and steps[i-1].agent == "codesmith":
                    # This is actually OK - reviewer reviews codesmith's work
                    pass
                elif i > 0 and steps[i-1].agent == "reviewer":
                    issues.append({
                        "type": "SEMANTIC",
                        "severity": "LOW",
                        "description": "Reviewer following reviewer - may be redundant",
                        "suggested_fix": "Consider consolidating review steps"
                    })

        return issues

    async def _validate_performance(self, state: ExtendedAgentState) -> List[Dict]:
        """Validate performance characteristics"""
        issues = []
        steps = state.get("execution_plan", [])

        # Estimate total execution time
        total_timeout = sum(step.timeout_seconds for step in steps)
        if total_timeout > 1800:  # 30 minutes
            issues.append({
                "type": "PERFORMANCE",
                "severity": "MEDIUM",
                "description": f"Estimated execution time: {total_timeout/60:.1f} minutes",
                "suggested_fix": "Consider optimizing timeouts or parallelizing"
            })

        # Check for parallelization opportunities
        parallel_groups = self._find_parallelizable_steps(steps)
        if len(parallel_groups) > 0:
            total_parallel = sum(len(group) for group in parallel_groups)
            issues.append({
                "type": "PERFORMANCE",
                "severity": "INFO",
                "description": f"Found {len(parallel_groups)} parallelizable groups ({total_parallel} steps)",
                "suggested_fix": "Enable parallel execution for better performance"
            })

        return issues

    async def _attempt_fixes(self, state: ExtendedAgentState, issues: List[Dict]) -> ExtendedAgentState:
        """Attempt to automatically fix detected issues"""
        fixed_state = state.copy()
        fixes_applied = []

        for issue in issues:
            if issue.get("severity") in ["CRITICAL", "HIGH"]:

                # Fix orchestrator self-routing
                if "orchestrator self-assignment" in issue.get("description", "").lower():
                    for step in fixed_state["execution_plan"]:
                        if step.agent == "orchestrator" and step.status == "pending":
                            step.status = "completed"
                            step.result = "Orchestrator planning complete (auto-fixed)"
                            fixes_applied.append("Fixed orchestrator self-routing")
                            logger.info("  🔧 Fixed: Orchestrator self-routing")

                # Fix circular dependencies
                elif "circular" in issue.get("description", "").lower():
                    # Simple fix: remove last dependency in cycle
                    steps = fixed_state["execution_plan"]
                    for step in steps:
                        if self._is_in_cycle(step, steps):
                            if step.dependencies:
                                removed = step.dependencies.pop()
                                fixes_applied.append(f"Removed circular dependency: {removed}")
                                logger.info(f"  🔧 Fixed: Removed dependency {removed}")
                                break

                # Fix resource limits
                elif "resource" in issue.get("description", "").lower():
                    # Trim old messages if too many
                    messages = fixed_state.get("messages", [])
                    if len(messages) > 500:
                        fixed_state["messages"] = messages[-500:]  # Keep last 500
                        fixes_applied.append("Trimmed message history")
                        logger.info("  🔧 Fixed: Trimmed message history")

        if fixes_applied:
            fixed_state["execution_plan"] = list(fixed_state["execution_plan"])  # Trigger update
            logger.info(f"  ✅ Applied {len(fixes_applied)} fixes")

        return fixed_state

    def _calculate_dependency_depth(self, steps: List[ExecutionStep]) -> int:
        """Calculate maximum dependency chain depth"""
        def get_depth(step_id: str, steps_dict: Dict) -> int:
            step = steps_dict.get(step_id)
            if not step or not step.dependencies:
                return 0
            return 1 + max(get_depth(dep, steps_dict) for dep in step.dependencies)

        if not steps:
            return 0

        steps_dict = {s.id: s for s in steps}
        return max(get_depth(s.id, steps_dict) for s in steps)

    def _find_parallelizable_steps(self, steps: List[ExecutionStep]) -> List[List[ExecutionStep]]:
        """Find groups of steps that can run in parallel"""
        groups = []
        processed = set()

        for step in steps:
            if step.id in processed:
                continue

            group = [step]
            for other in steps:
                if other.id != step.id and other.id not in processed:
                    # Check if no dependency conflicts
                    if not self._has_dependency_conflict(step, other, steps):
                        group.append(other)
                        processed.add(other.id)

            if len(group) > 1:
                groups.append(group)
            processed.add(step.id)

        return groups

    def _has_dependency_conflict(self, step1: ExecutionStep, step2: ExecutionStep, all_steps: List) -> bool:
        """Check if two steps have dependency conflicts"""
        return (step1.id in step2.dependencies or
                step2.id in step1.dependencies)

    def _is_in_cycle(self, step: ExecutionStep, all_steps: List) -> bool:
        """Check if step is part of a dependency cycle"""
        visited = set()
        path = set()

        def has_cycle(s_id: str) -> bool:
            if s_id in path:
                return True
            if s_id in visited:
                return False

            visited.add(s_id)
            path.add(s_id)

            s = next((x for x in all_steps if x.id == s_id), None)
            if s:
                for dep_id in s.dependencies:
                    if has_cycle(dep_id):
                        return True

            path.remove(s_id)
            return False

        return has_cycle(step.id)


# =================== PATTERN RECOGNITION ===================

class PatternRecognitionEngine:
    """
    Detects patterns and anomalies in workflow execution
    Uses both rule-based and statistical approaches
    """

    def __init__(self):
        self.pattern_history = deque(maxlen=1000)
        self.anomaly_threshold = 2.0  # Standard deviations
        self.known_patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, Any]:
        """Initialize pattern definitions"""
        return {
            "routing_loop": {
                "description": "Same agent routed multiple times",
                "detection": lambda history: self._detect_routing_loop(history),
                "threshold": 3
            },
            "collaboration_spiral": {
                "description": "Reviewer-Fixer infinite loop",
                "detection": lambda history: self._detect_collaboration_spiral(history),
                "threshold": 4
            },
            "stuck_progress": {
                "description": "No progress in execution",
                "detection": lambda metrics: self._detect_stuck_progress(metrics),
                "threshold": 5
            },
            "resource_spike": {
                "description": "Sudden resource usage increase",
                "detection": lambda metrics: self._detect_resource_spike(metrics),
                "threshold": 2.0
            },
            "timeout_cluster": {
                "description": "Multiple timeouts in sequence",
                "detection": lambda events: self._detect_timeout_cluster(events),
                "threshold": 3
            }
        }

    def analyze_patterns(self, state: ExtendedAgentState) -> Dict[str, Any]:
        """Analyze state for patterns and anomalies"""
        analysis = {
            "patterns_detected": [],
            "anomalies": [],
            "risk_score": 0.0,
            "recommendations": []
        }

        # Extract relevant data
        history = state.get("collaboration_history", [])
        steps = state.get("execution_plan", [])
        messages = state.get("messages", [])

        # Check for known patterns
        for pattern_name, pattern_def in self.known_patterns.items():
            if pattern_name in ["routing_loop", "collaboration_spiral"]:
                if pattern_def["detection"](history):
                    analysis["patterns_detected"].append({
                        "name": pattern_name,
                        "description": pattern_def["description"],
                        "severity": "HIGH"
                    })
                    analysis["risk_score"] += 0.3

        # Statistical anomaly detection
        anomalies = self._detect_statistical_anomalies(state)
        analysis["anomalies"].extend(anomalies)
        analysis["risk_score"] += len(anomalies) * 0.1

        # Generate recommendations
        if analysis["risk_score"] > 0.5:
            analysis["recommendations"].append("Consider halting workflow for review")
        if len(history) > 10:
            analysis["recommendations"].append("High collaboration count - consider escalation")

        # Cap risk score at 1.0
        analysis["risk_score"] = min(1.0, analysis["risk_score"])

        return analysis

    def _detect_routing_loop(self, history: List[Dict]) -> bool:
        """Detect if same routing pattern repeats"""
        if len(history) < 3:
            return False

        # Check last 3 entries
        last_3 = history[-3:]
        return all(h.get("to") == last_3[0].get("to") for h in last_3)

    def _detect_collaboration_spiral(self, history: List[Dict]) -> bool:
        """Detect Reviewer-Fixer spiral pattern"""
        if len(history) < 4:
            return False

        # Check for alternating pattern
        last_4 = history[-4:]
        pattern1 = ["reviewer", "fixer", "reviewer", "fixer"]
        pattern2 = ["fixer", "reviewer", "fixer", "reviewer"]

        actual = [h.get("to") for h in last_4]
        return actual == pattern1 or actual == pattern2

    def _detect_stuck_progress(self, metrics: Dict) -> bool:
        """Detect if workflow is not progressing"""
        # Would need progress tracking over time
        return False

    def _detect_resource_spike(self, metrics: Dict) -> bool:
        """Detect sudden resource usage increase"""
        # Would need resource metrics tracking
        return False

    def _detect_timeout_cluster(self, events: List) -> bool:
        """Detect multiple timeouts close together"""
        # Would need event tracking
        return False

    def _detect_statistical_anomalies(self, state: ExtendedAgentState) -> List[Dict]:
        """Use statistical methods to detect anomalies"""
        anomalies = []

        # Check message growth rate
        messages = state.get("messages", [])
        if len(messages) > 100:
            recent_rate = len(messages[-20:]) / 20
            overall_rate = len(messages) / max(1, state.get("collaboration_count", 1))

            if recent_rate > overall_rate * 2:
                anomalies.append({
                    "type": "MESSAGE_GROWTH_SPIKE",
                    "description": "Message growth rate increased significantly",
                    "metric": f"Recent: {recent_rate:.2f} msgs/step vs Overall: {overall_rate:.2f}"
                })

        # Check step completion rate
        steps = state.get("execution_plan", [])
        if steps:
            completed = sum(1 for s in steps if s.status == "completed")
            failed = sum(1 for s in steps if s.status == "failed")
            total = len(steps)

            if total > 5 and failed > total * 0.4:
                anomalies.append({
                    "type": "HIGH_FAILURE_RATE",
                    "description": "Abnormally high failure rate",
                    "metric": f"{failed}/{total} steps failed ({failed/total*100:.1f}%)"
                })

        return anomalies


# =================== SELF-TEST FRAMEWORK ===================

class SelfTestFramework:
    """
    Automated self-test framework for continuous health monitoring
    Runs periodic health checks and reports issues
    """

    def __init__(
        self,
        invariants: WorkflowInvariants,
        validator: PreExecutionValidator,
        pattern_engine: PatternRecognitionEngine
    ):
        self.invariants = invariants
        self.validator = validator
        self.pattern_engine = pattern_engine
        self.test_history = deque(maxlen=100)
        self.last_test_time = None
        self.test_interval = 60  # seconds

    async def run_comprehensive_health_check(self, state: ExtendedAgentState) -> Dict[str, Any]:
        """Run comprehensive health check suite"""
        logger.info("🏥 Running Self-Test Health Check")

        health_report = {
            "timestamp": datetime.now(),
            "overall_health": "HEALTHY",
            "scores": {},
            "issues": [],
            "metrics": {},
            "recommendations": []
        }

        # Test 1: Invariants
        invariant_valid, violations = self.invariants.check_all(state)
        health_report["scores"]["invariants"] = 1.0 if invariant_valid else 0.0
        if not invariant_valid:
            health_report["issues"].extend(violations)
            health_report["overall_health"] = "UNHEALTHY"

        # Test 2: Pattern Analysis
        pattern_analysis = self.pattern_engine.analyze_patterns(state)
        health_report["scores"]["patterns"] = 1.0 - pattern_analysis["risk_score"]
        if pattern_analysis["risk_score"] > 0.5:
            health_report["overall_health"] = "AT_RISK"
        health_report["metrics"]["risk_score"] = pattern_analysis["risk_score"]

        # Test 3: Resource Health
        resource_health = await self._test_resource_health(state)
        health_report["scores"]["resources"] = resource_health["score"]
        health_report["metrics"].update(resource_health["metrics"])

        # Test 4: Performance Health
        perf_health = await self._test_performance_health(state)
        health_report["scores"]["performance"] = perf_health["score"]
        health_report["metrics"].update(perf_health["metrics"])

        # Test 5: Structural Health
        struct_health = await self._test_structural_health(state)
        health_report["scores"]["structure"] = struct_health["score"]

        # Calculate overall score
        scores = health_report["scores"].values()
        overall_score = sum(scores) / len(scores) if scores else 0.0
        health_report["overall_score"] = overall_score

        # Determine overall health status
        if overall_score < 0.5:
            health_report["overall_health"] = "CRITICAL"
        elif overall_score < 0.7:
            health_report["overall_health"] = "UNHEALTHY"
        elif overall_score < 0.9:
            health_report["overall_health"] = "AT_RISK"

        # Generate recommendations
        if health_report["overall_health"] != "HEALTHY":
            if health_report["overall_health"] == "CRITICAL":
                health_report["recommendations"].append("IMMEDIATE ACTION REQUIRED: Halt workflow")

            if health_report["scores"].get("invariants", 1.0) < 1.0:
                health_report["recommendations"].append("Fix invariant violations before continuing")

            if health_report["scores"].get("patterns", 1.0) < 0.7:
                health_report["recommendations"].append("Review detected patterns for potential issues")

        # Store test result
        self.test_history.append(health_report)
        self.last_test_time = datetime.now()

        # Log summary
        logger.info(f"  📊 Health Check Complete: {health_report['overall_health']}")
        logger.info(f"     Overall Score: {overall_score:.2%}")

        return health_report

    async def _test_resource_health(self, state: ExtendedAgentState) -> Dict:
        """Test resource utilization health"""
        messages = state.get("messages", [])
        steps = state.get("execution_plan", [])

        message_score = 1.0 - min(1.0, len(messages) / 1000)
        step_score = 1.0 - min(1.0, len(steps) / 50)

        return {
            "score": (message_score + step_score) / 2,
            "metrics": {
                "message_count": len(messages),
                "step_count": len(steps),
                "message_score": message_score,
                "step_score": step_score
            }
        }

    async def _test_performance_health(self, state: ExtendedAgentState) -> Dict:
        """Test performance characteristics"""
        steps = state.get("execution_plan", [])

        # Calculate timeout distribution
        timeouts = [s.timeout_seconds for s in steps]
        avg_timeout = sum(timeouts) / len(timeouts) if timeouts else 0

        # Check retry counts
        retry_counts = [s.retry_count for s in steps]
        avg_retries = sum(retry_counts) / len(retry_counts) if retry_counts else 0

        # Score based on reasonable thresholds
        timeout_score = 1.0 if avg_timeout < 300 else 0.5  # 5 min threshold
        retry_score = 1.0 - min(1.0, avg_retries / 3)  # Penalize high retries

        return {
            "score": (timeout_score + retry_score) / 2,
            "metrics": {
                "avg_timeout": avg_timeout,
                "avg_retries": avg_retries,
                "max_retries": max(retry_counts) if retry_counts else 0
            }
        }

    async def _test_structural_health(self, state: ExtendedAgentState) -> Dict:
        """Test structural integrity"""
        steps = state.get("execution_plan", [])

        if not steps:
            return {"score": 0.0}

        # Check completion rate
        completed = sum(1 for s in steps if s.status == "completed")
        completion_rate = completed / len(steps)

        # Check failure rate
        failed = sum(1 for s in steps if s.status == "failed")
        failure_rate = failed / len(steps) if steps else 0

        # Score calculation
        score = completion_rate * (1.0 - failure_rate)

        return {
            "score": score,
            "metrics": {
                "completion_rate": completion_rate,
                "failure_rate": failure_rate
            }
        }

    async def continuous_monitoring(self, state_provider, interval: int = None):
        """Run continuous health monitoring"""
        interval = interval or self.test_interval

        logger.info(f"🔄 Starting continuous health monitoring (interval: {interval}s)")

        while True:
            try:
                # Get current state
                state = await state_provider()

                # Run health check
                health_report = await self.run_comprehensive_health_check(state)

                # Take action based on health
                if health_report["overall_health"] == "CRITICAL":
                    logger.error("🚨 CRITICAL health detected - alerting")
                    # Could trigger alerts, auto-healing, etc.
                elif health_report["overall_health"] == "UNHEALTHY":
                    logger.warning("⚠️ UNHEALTHY state detected - monitoring closely")

                # Wait for next interval
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(interval)


# =================== MAIN SELF-DIAGNOSIS SYSTEM ===================

class WorkflowSelfDiagnosisSystem:
    """
    Main entry point for the complete self-diagnosis system
    Integrates all components for comprehensive workflow health management
    """

    def __init__(self):
        # Initialize all components
        self.known_patterns = KnownAntiPatternsDatabase()
        self.invariants = WorkflowInvariants()
        self.validator = PreExecutionValidator(self.known_patterns, self.invariants)
        self.pattern_engine = PatternRecognitionEngine()
        self.self_test = SelfTestFramework(
            self.invariants,
            self.validator,
            self.pattern_engine
        )

        logger.info("🏥 Workflow Self-Diagnosis System v5.5.0 initialized")

    async def pre_execution_check(
        self,
        state: ExtendedAgentState,
        auto_fix: bool = True
    ) -> Tuple[bool, ExtendedAgentState]:
        """
        Main pre-execution validation entry point
        Returns: (is_safe_to_execute, potentially_fixed_state)
        """
        logger.info("=" * 60)
        logger.info("🚀 COMPREHENSIVE PRE-EXECUTION VALIDATION")
        logger.info("=" * 60)

        # Phase 1: Initial validation with fixes
        is_valid, issues, fixed_state = await self.validator.validate_comprehensive(
            state,
            fix_issues=auto_fix
        )

        # Phase 2: Pattern analysis
        pattern_analysis = self.pattern_engine.analyze_patterns(fixed_state)

        # Phase 3: Health check
        health_report = await self.self_test.run_comprehensive_health_check(fixed_state)

        # Decision logic
        safe_to_execute = (
            is_valid and
            pattern_analysis["risk_score"] < 0.7 and
            health_report["overall_health"] not in ["CRITICAL", "UNHEALTHY"]
        )

        # Log summary
        logger.info("=" * 60)
        logger.info("📊 PRE-EXECUTION VALIDATION SUMMARY")
        logger.info(f"  Validation: {'PASS' if is_valid else 'FAIL'}")
        logger.info(f"  Risk Score: {pattern_analysis['risk_score']:.2%}")
        logger.info(f"  Health: {health_report['overall_health']}")
        logger.info(f"  Decision: {'SAFE TO EXECUTE' if safe_to_execute else 'NOT SAFE - REVIEW REQUIRED'}")
        logger.info("=" * 60)

        if not safe_to_execute:
            logger.error("❌ Workflow NOT safe to execute. Issues found:")
            for issue in issues[:5]:  # Show first 5 issues
                logger.error(f"  - {issue.get('description', issue)}")

            if pattern_analysis["patterns_detected"]:
                logger.warning("⚠️ Patterns detected:")
                for pattern in pattern_analysis["patterns_detected"]:
                    logger.warning(f"  - {pattern['description']}")

        return safe_to_execute, fixed_state

    async def real_time_monitoring(self, state: ExtendedAgentState) -> Dict[str, Any]:
        """Real-time health monitoring during execution"""
        return await self.self_test.run_comprehensive_health_check(state)

    def get_diagnosis_report(self) -> Dict[str, Any]:
        """Get comprehensive diagnosis report"""
        return {
            "validation_history": self.validator.validation_history[-10:],
            "test_history": list(self.self_test.test_history)[-10:],
            "detected_patterns": list(self.known_patterns.detection_history)[-20:],
            "current_invariants": len(self.invariants.invariants),
            "known_anti_patterns": len(self.known_patterns.patterns)
        }