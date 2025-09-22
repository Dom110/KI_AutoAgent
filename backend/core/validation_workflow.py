"""
ValidationWorkflow - Automatic validation and fixing of implementations
Integrates ReviewerGPT and FixerBot for quality assurance
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.workflow_engine import WorkflowEngine, WorkflowNode, NodeType, get_workflow_engine
from core.memory_manager import get_memory_manager, MemoryType
from core.shared_context_manager import get_shared_context

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"  # Must fix
    HIGH = "high"         # Should fix
    MEDIUM = "medium"     # Consider fixing
    LOW = "low"           # Nice to fix
    INFO = "info"         # Informational

@dataclass
class ValidationIssue:
    """Individual validation issue"""
    id: str
    severity: ValidationSeverity
    category: str  # 'bug', 'security', 'performance', 'style', 'documentation'
    description: str
    location: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False

@dataclass
class ValidationResult:
    """Result of validation"""
    task_id: str
    agent: str
    timestamp: float
    passed: bool
    issues: List[ValidationIssue]
    coverage: float = 0.0  # Test coverage if applicable
    performance_score: float = 0.0
    security_score: float = 0.0
    completeness_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationConfig:
    """Configuration for validation workflow"""
    enabled: bool = True
    auto_fix: bool = True
    max_iterations: int = 3
    severity_threshold: ValidationSeverity = ValidationSeverity.HIGH
    validation_agents: List[str] = field(default_factory=lambda: ["reviewer", "fixer"])
    categories_to_check: List[str] = field(default_factory=lambda: [
        "bugs", "security", "performance", "completeness", "best_practices"
    ])

class ValidationWorkflow:
    """
    Manages automatic validation and fixing of implementations
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize validation workflow"""
        self.config = config or ValidationConfig()
        self.workflow_engine = get_workflow_engine()
        self.memory = get_memory_manager()
        self.shared_context = get_shared_context()

        # Statistics
        self.total_validations = 0
        self.passed_validations = 0
        self.auto_fixes_applied = 0

        # Validation history
        self.validation_history: List[ValidationResult] = []

        logger.info(f"ValidationWorkflow initialized (auto_fix={self.config.auto_fix})")

    async def validate_implementation(
        self,
        task: str,
        implementation: str,
        agent: str,
        requirements: Optional[str] = None
    ) -> ValidationResult:
        """Validate an implementation"""
        if not self.config.enabled:
            return self._create_pass_result(task, agent)

        self.total_validations += 1
        task_id = f"val_{int(time.time())}"

        # Create validation workflow
        workflow = self._create_validation_workflow(task_id)

        # Set context
        context = {
            "task": task,
            "implementation": implementation,
            "agent": agent,
            "requirements": requirements or "",
            "iteration": 0,
            "issues": [],
            "fixes_applied": []
        }

        # Execute validation
        try:
            results = await workflow.execute(context)

            # Collect validation results
            validation_result = await self._process_validation_results(
                task_id,
                agent,
                results,
                context
            )

            # Store in memory for learning
            await self._store_validation_memory(validation_result)

            # Apply auto-fix if enabled and needed
            if self.config.auto_fix and not validation_result.passed:
                validation_result = await self._apply_auto_fix(
                    validation_result,
                    implementation,
                    context
                )

            # Update statistics
            if validation_result.passed:
                self.passed_validations += 1

            self.validation_history.append(validation_result)

            return validation_result

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return self._create_error_result(task_id, agent, str(e))

    def _create_validation_workflow(self, task_id: str):
        """Create workflow for validation"""
        workflow = self.workflow_engine.create_workflow(
            name=f"validation_{task_id}"
        )

        # Add validation nodes
        # 1. Code Review
        review_node = WorkflowNode(
            id="review",
            type=NodeType.TASK,
            agent_id="reviewer",
            task="Review code for issues",
            timeout=30.0
        )
        workflow.add_node(review_node)

        # 2. Security Analysis (conditional)
        security_node = WorkflowNode(
            id="security",
            type=NodeType.TASK,
            agent_id="reviewer",
            task="Security analysis",
            condition=lambda ctx: "security" in ctx.get("categories_to_check", []),
            timeout=20.0
        )
        workflow.add_node(security_node)

        # 3. Performance Analysis (conditional)
        performance_node = WorkflowNode(
            id="performance",
            type=NodeType.TASK,
            agent_id="reviewer",
            task="Performance analysis",
            condition=lambda ctx: "performance" in ctx.get("categories_to_check", []),
            timeout=20.0
        )
        workflow.add_node(performance_node)

        # 4. Completeness Check
        completeness_node = WorkflowNode(
            id="completeness",
            type=NodeType.TASK,
            agent_id="reviewer",
            task="Check implementation completeness",
            timeout=15.0
        )
        workflow.add_node(completeness_node)

        # Add edges for sequential execution
        workflow.add_edge("review", "security")
        workflow.add_edge("security", "performance")
        workflow.add_edge("performance", "completeness")

        return workflow

    async def _process_validation_results(
        self,
        task_id: str,
        agent: str,
        results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ValidationResult:
        """Process raw validation results"""
        issues = []
        scores = {
            "coverage": 0.0,
            "performance": 0.0,
            "security": 0.0,
            "completeness": 0.0
        }

        # Parse results from each validation step
        for node_id, result in results.items():
            if result.status == "success" and result.output:
                # Extract issues and scores
                parsed = self._parse_validation_output(result.output)
                issues.extend(parsed["issues"])

                if node_id == "security":
                    scores["security"] = parsed.get("score", 0.0)
                elif node_id == "performance":
                    scores["performance"] = parsed.get("score", 0.0)
                elif node_id == "completeness":
                    scores["completeness"] = parsed.get("score", 0.0)

        # Determine if passed
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == ValidationSeverity.HIGH]

        passed = (
            len(critical_issues) == 0 and
            (self.config.severity_threshold != ValidationSeverity.HIGH or len(high_issues) == 0)
        )

        return ValidationResult(
            task_id=task_id,
            agent=agent,
            timestamp=time.time(),
            passed=passed,
            issues=issues,
            coverage=scores["coverage"],
            performance_score=scores["performance"],
            security_score=scores["security"],
            completeness_score=scores["completeness"],
            metadata={
                "total_issues": len(issues),
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues)
            }
        )

    def _parse_validation_output(self, output: str) -> Dict[str, Any]:
        """Parse validation output from reviewer"""
        # Simple parsing - in production, use structured output
        issues = []
        score = 0.0

        lines = output.split('\n')
        for line in lines:
            line_lower = line.lower()

            # Detect issues
            if any(keyword in line_lower for keyword in ['bug', 'error', 'issue', 'problem']):
                severity = ValidationSeverity.HIGH
                if 'critical' in line_lower:
                    severity = ValidationSeverity.CRITICAL
                elif 'low' in line_lower:
                    severity = ValidationSeverity.LOW

                issues.append(ValidationIssue(
                    id=f"issue_{len(issues)}",
                    severity=severity,
                    category=self._detect_category(line),
                    description=line.strip(),
                    auto_fixable='fix' in line_lower
                ))

            # Extract score if present
            if 'score' in line_lower:
                try:
                    parts = line.split(':')
                    if len(parts) > 1:
                        score_str = parts[1].strip().replace('%', '')
                        score = float(score_str) / 100.0
                except:
                    pass

        return {
            "issues": issues,
            "score": score
        }

    def _detect_category(self, text: str) -> str:
        """Detect issue category from text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['security', 'vulnerability', 'injection']):
            return "security"
        elif any(word in text_lower for word in ['performance', 'slow', 'optimize']):
            return "performance"
        elif any(word in text_lower for word in ['bug', 'error', 'crash']):
            return "bug"
        elif any(word in text_lower for word in ['style', 'format', 'convention']):
            return "style"
        elif any(word in text_lower for word in ['doc', 'comment', 'description']):
            return "documentation"
        else:
            return "other"

    async def _apply_auto_fix(
        self,
        validation_result: ValidationResult,
        original_implementation: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """Apply automatic fixes for issues"""
        if context["iteration"] >= self.config.max_iterations:
            logger.warning(f"Max iterations ({self.config.max_iterations}) reached for auto-fix")
            return validation_result

        # Filter auto-fixable issues
        fixable_issues = [
            issue for issue in validation_result.issues
            if issue.auto_fixable and issue.severity in [
                ValidationSeverity.CRITICAL,
                ValidationSeverity.HIGH
            ]
        ]

        if not fixable_issues:
            return validation_result

        logger.info(f"Attempting to auto-fix {len(fixable_issues)} issues")

        # Create fix workflow
        fix_workflow = self.workflow_engine.create_workflow(
            name=f"fix_{validation_result.task_id}"
        )

        # Add fixer node
        fix_node = WorkflowNode(
            id="fix",
            type=NodeType.TASK,
            agent_id="fixer",
            task="Fix identified issues",
            timeout=60.0
        )
        fix_workflow.add_node(fix_node)

        # Execute fix
        fix_context = {
            "implementation": original_implementation,
            "issues": [self._issue_to_dict(issue) for issue in fixable_issues],
            "iteration": context["iteration"] + 1
        }

        try:
            fix_results = await fix_workflow.execute(fix_context)

            if "fix" in fix_results and fix_results["fix"].status == "success":
                fixed_implementation = fix_results["fix"].output

                # Re-validate the fixed implementation
                self.auto_fixes_applied += 1
                context["iteration"] += 1

                return await self.validate_implementation(
                    task=context["task"],
                    implementation=fixed_implementation,
                    agent=validation_result.agent,
                    requirements=context.get("requirements")
                )

        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")

        return validation_result

    def _issue_to_dict(self, issue: ValidationIssue) -> Dict[str, Any]:
        """Convert issue to dictionary"""
        return {
            "id": issue.id,
            "severity": issue.severity.value,
            "category": issue.category,
            "description": issue.description,
            "location": issue.location,
            "suggested_fix": issue.suggested_fix
        }

    async def _store_validation_memory(self, result: ValidationResult):
        """Store validation result in memory for learning"""
        if self.memory:
            # Store validation pattern
            await self.memory.store(
                agent_id="validation_workflow",
                content={
                    "task_id": result.task_id,
                    "agent": result.agent,
                    "passed": result.passed,
                    "issue_count": len(result.issues),
                    "scores": {
                        "security": result.security_score,
                        "performance": result.performance_score,
                        "completeness": result.completeness_score
                    }
                },
                memory_type=MemoryType.PROCEDURAL,
                metadata={
                    "importance": 0.8 if not result.passed else 0.5,
                    "tags": ["validation", "quality", result.agent]
                }
            )

            # Store common issues for pattern recognition
            if result.issues:
                for issue in result.issues[:5]:  # Store top 5 issues
                    await self.memory.store(
                        agent_id="validation_workflow",
                        content={
                            "category": issue.category,
                            "severity": issue.severity.value,
                            "description": issue.description
                        },
                        memory_type=MemoryType.SEMANTIC,
                        metadata={
                            "importance": 0.7,
                            "tags": ["issue_pattern", issue.category]
                        }
                    )

    def _create_pass_result(self, task: str, agent: str) -> ValidationResult:
        """Create a passing validation result"""
        return ValidationResult(
            task_id=f"val_{int(time.time())}",
            agent=agent,
            timestamp=time.time(),
            passed=True,
            issues=[],
            completeness_score=1.0,
            metadata={"skipped": not self.config.enabled}
        )

    def _create_error_result(
        self,
        task_id: str,
        agent: str,
        error: str
    ) -> ValidationResult:
        """Create an error validation result"""
        return ValidationResult(
            task_id=task_id,
            agent=agent,
            timestamp=time.time(),
            passed=False,
            issues=[
                ValidationIssue(
                    id="error",
                    severity=ValidationSeverity.CRITICAL,
                    category="error",
                    description=f"Validation error: {error}",
                    auto_fixable=False
                )
            ],
            metadata={"error": error}
        )

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        recent_validations = self.validation_history[-20:]

        return {
            "total_validations": self.total_validations,
            "passed_validations": self.passed_validations,
            "pass_rate": self.passed_validations / max(1, self.total_validations),
            "auto_fixes_applied": self.auto_fixes_applied,
            "recent_results": [
                {
                    "task_id": v.task_id,
                    "agent": v.agent,
                    "passed": v.passed,
                    "issue_count": len(v.issues),
                    "timestamp": v.timestamp
                }
                for v in recent_validations
            ],
            "common_issues": self._get_common_issues()
        }

    def _get_common_issues(self) -> List[Dict[str, Any]]:
        """Get most common validation issues"""
        issue_counts = {}

        for result in self.validation_history:
            for issue in result.issues:
                key = f"{issue.category}_{issue.severity.value}"
                issue_counts[key] = issue_counts.get(key, 0) + 1

        # Sort by frequency
        common_issues = sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return [
            {"type": issue[0], "count": issue[1]}
            for issue in common_issues
        ]

# Global instance
_validation_instance = None

def get_validation_workflow(config: Optional[ValidationConfig] = None) -> ValidationWorkflow:
    """Get singleton ValidationWorkflow instance"""
    global _validation_instance
    if _validation_instance is None:
        _validation_instance = ValidationWorkflow(config)
    return _validation_instance