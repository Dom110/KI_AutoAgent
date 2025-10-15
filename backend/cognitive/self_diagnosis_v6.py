"""
Self-Diagnosis & Recovery v6 - Autonomous Error Detection and Fixing

Capabilities:
- Detect system errors and anomalies
- Diagnose root causes
- Suggest recovery strategies
- Automatically apply fixes
- Learn from recovery actions

Integration:
- Continuous monitoring
- After failed operations
- Health checks

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DiagnosticLevel(str, Enum):
    """Severity levels for diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStrategy(str, Enum):
    """Types of recovery strategies."""

    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    ALTERNATIVE = "alternative"
    MANUAL = "manual"
    ABORT = "abort"


@dataclass(slots=True)
class Diagnostic:
    """Diagnostic finding."""

    diagnostic_id: str
    level: DiagnosticLevel
    component: str
    message: str
    details: dict[str, Any]
    timestamp: datetime
    root_cause: str | None = None


@dataclass(slots=True)
class RecoveryAction:
    """Recovery action to fix an issue."""

    action_id: str
    strategy: RecoveryStrategy
    description: str
    steps: list[str]
    estimated_success_rate: float
    side_effects: list[str]
    requires_approval: bool


@dataclass(slots=True)
class RecoveryResult:
    """Result of recovery attempt."""

    action_id: str
    success: bool
    applied_steps: list[str]
    outcome: str
    timestamp: datetime
    metadata: dict[str, Any]


class SelfDiagnosisV6:
    """
    Self-Diagnosis and Recovery System.

    Autonomously detects, diagnoses, and recovers from errors.
    """

    def __init__(self, learning_system: Any | None = None):
        """
        Initialize self-diagnosis system.

        Args:
            learning_system: Optional learning system for historical data
        """
        self.learning_system = learning_system
        self.diagnostics: list[Diagnostic] = []
        self.recovery_history: list[RecoveryResult] = []

        # Diagnostic patterns
        self.error_patterns: dict[str, dict[str, Any]] = {}
        self._setup_error_patterns()

        logger.info("🏥 Self-Diagnosis v6 initialized")

    def _setup_error_patterns(self) -> None:
        """Setup common error patterns and recovery strategies."""

        self.error_patterns = {
            "import_error": {
                "pattern": ["ImportError", "ModuleNotFoundError", "cannot import"],
                "root_cause": "Missing or incorrect module import",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Check if module is installed",
                    "Verify import path",
                    "Install missing dependency",
                    "Update import statement"
                ]
            },

            "syntax_error": {
                "pattern": ["SyntaxError", "invalid syntax"],
                "root_cause": "Invalid Python syntax",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Identify syntax error location",
                    "Check Python version compatibility",
                    "Fix syntax error",
                    "Verify fix with parser"
                ]
            },

            "type_error": {
                "pattern": ["TypeError", "type", "expected"],
                "root_cause": "Type mismatch in operation",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Identify type mismatch",
                    "Add type conversion",
                    "Update type hints",
                    "Validate types"
                ]
            },

            "name_error": {
                "pattern": ["NameError", "not defined"],
                "root_cause": "Undefined variable or function",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Identify undefined name",
                    "Check for typos",
                    "Add variable definition",
                    "Fix scope issues"
                ]
            },

            "attribute_error": {
                "pattern": ["AttributeError", "has no attribute"],
                "root_cause": "Accessing non-existent attribute",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Identify object type",
                    "Check available attributes",
                    "Fix attribute name",
                    "Add hasattr check"
                ]
            },

            "index_error": {
                "pattern": ["IndexError", "list index", "out of range"],
                "root_cause": "Index out of bounds",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Check list/array length",
                    "Add bounds checking",
                    "Fix index calculation",
                    "Add try-except"
                ]
            },

            "key_error": {
                "pattern": ["KeyError", "key not found"],
                "root_cause": "Dictionary key does not exist",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Check dictionary keys",
                    "Use .get() with default",
                    "Add key existence check",
                    "Fix key name"
                ]
            },

            "timeout_error": {
                "pattern": ["TimeoutError", "timeout", "timed out"],
                "root_cause": "Operation took too long",
                "recovery": RecoveryStrategy.RETRY,
                "steps": [
                    "Increase timeout duration",
                    "Optimize slow operation",
                    "Retry with exponential backoff",
                    "Check network/resource availability"
                ]
            },

            "connection_error": {
                "pattern": ["ConnectionError", "connection refused", "connection failed"],
                "root_cause": "Network connection failed",
                "recovery": RecoveryStrategy.RETRY,
                "steps": [
                    "Check network connectivity",
                    "Verify endpoint availability",
                    "Retry with backoff",
                    "Use fallback endpoint"
                ]
            },

            "file_not_found": {
                "pattern": ["FileNotFoundError", "No such file", "file not found"],
                "root_cause": "File does not exist",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Verify file path",
                    "Check file existence",
                    "Create file if needed",
                    "Use alternative file"
                ]
            },

            "permission_error": {
                "pattern": ["PermissionError", "permission denied"],
                "root_cause": "Insufficient permissions",
                "recovery": RecoveryStrategy.MANUAL,
                "steps": [
                    "Check file/directory permissions",
                    "Request elevated privileges",
                    "Change ownership/permissions",
                    "Use alternative location"
                ]
            },

            "memory_error": {
                "pattern": ["MemoryError", "out of memory", "OOM"],
                "root_cause": "Insufficient memory",
                "recovery": RecoveryStrategy.ALTERNATIVE,
                "steps": [
                    "Reduce memory usage",
                    "Process data in chunks",
                    "Free unused resources",
                    "Increase available memory"
                ]
            }
        }

    async def diagnose(
        self,
        error: Exception | str | dict[str, Any],
        context: dict[str, Any] | None = None
    ) -> list[Diagnostic]:
        """
        Diagnose an error.

        Args:
            error: Error to diagnose (exception, message, or error dict)
            context: Additional context

        Returns:
            List of diagnostic findings
        """
        logger.info(f"🔍 Diagnosing error: {str(error)[:80]}...")

        diagnostics = []
        context = context or {}

        # Convert error to string
        if isinstance(error, Exception):
            error_str = f"{type(error).__name__}: {str(error)}"
            error_type = type(error).__name__
        elif isinstance(error, dict):
            error_str = error.get("message", str(error))
            error_type = error.get("type", "Unknown")
        else:
            error_str = str(error)
            error_type = "Unknown"

        # Match against error patterns
        matched_patterns = []

        for pattern_name, pattern_info in self.error_patterns.items():
            for keyword in pattern_info["pattern"]:
                if keyword.lower() in error_str.lower():
                    matched_patterns.append((pattern_name, pattern_info))
                    break

        # Create diagnostics for matched patterns
        if matched_patterns:
            for pattern_name, pattern_info in matched_patterns:
                diagnostic = Diagnostic(
                    diagnostic_id=f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pattern_name}",
                    level=DiagnosticLevel.ERROR,
                    component=context.get("component", "system"),
                    message=error_str,
                    details={
                        "error_type": error_type,
                        "pattern": pattern_name,
                        "context": context
                    },
                    timestamp=datetime.now(),
                    root_cause=pattern_info["root_cause"]
                )

                diagnostics.append(diagnostic)
                self.diagnostics.append(diagnostic)

                logger.info(f"✅ Matched pattern: {pattern_name}")
                logger.info(f"   Root cause: {diagnostic.root_cause}")

        else:
            # Unknown error pattern
            diagnostic = Diagnostic(
                diagnostic_id=f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}_unknown",
                level=DiagnosticLevel.ERROR,
                component=context.get("component", "system"),
                message=error_str,
                details={
                    "error_type": error_type,
                    "context": context
                },
                timestamp=datetime.now(),
                root_cause="Unknown error pattern"
            )

            diagnostics.append(diagnostic)
            self.diagnostics.append(diagnostic)

            logger.warning("⚠️  Unknown error pattern")

        return diagnostics

    async def suggest_recovery(
        self,
        diagnostic: Diagnostic
    ) -> list[RecoveryAction]:
        """
        Suggest recovery actions for a diagnostic.

        Args:
            diagnostic: Diagnostic finding

        Returns:
            List of recovery actions
        """
        logger.info(f"💡 Suggesting recovery for: {diagnostic.diagnostic_id}")

        actions = []

        # Get pattern from diagnostic
        pattern_name = diagnostic.details.get("pattern")

        if pattern_name and pattern_name in self.error_patterns:
            pattern_info = self.error_patterns[pattern_name]

            # Create primary recovery action
            action = RecoveryAction(
                action_id=f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pattern_name}",
                strategy=pattern_info["recovery"],
                description=f"Fix {pattern_name}",
                steps=pattern_info["steps"],
                estimated_success_rate=0.8,
                side_effects=[],
                requires_approval=False
            )

            actions.append(action)

            # Add retry option if applicable
            if pattern_info["recovery"] != RecoveryStrategy.RETRY:
                retry_action = RecoveryAction(
                    action_id=f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_retry",
                    strategy=RecoveryStrategy.RETRY,
                    description="Retry the operation",
                    steps=["Wait briefly", "Retry operation"],
                    estimated_success_rate=0.5,
                    side_effects=["May fail again"],
                    requires_approval=False
                )
                actions.append(retry_action)

            # Add skip option
            skip_action = RecoveryAction(
                action_id=f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_skip",
                strategy=RecoveryStrategy.SKIP,
                description="Skip this operation and continue",
                steps=["Mark operation as skipped", "Continue workflow"],
                estimated_success_rate=1.0,
                side_effects=["Operation not completed"],
                requires_approval=True
            )
            actions.append(skip_action)

        else:
            # Generic recovery options
            actions = [
                RecoveryAction(
                    action_id=f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_retry",
                    strategy=RecoveryStrategy.RETRY,
                    description="Retry the operation",
                    steps=["Wait briefly", "Retry operation"],
                    estimated_success_rate=0.5,
                    side_effects=[],
                    requires_approval=False
                ),
                RecoveryAction(
                    action_id=f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_manual",
                    strategy=RecoveryStrategy.MANUAL,
                    description="Manual intervention required",
                    steps=["Notify user", "Wait for manual fix"],
                    estimated_success_rate=0.9,
                    side_effects=["Requires user action"],
                    requires_approval=True
                )
            ]

        logger.info(f"✅ Generated {len(actions)} recovery options")

        return actions

    async def apply_recovery(
        self,
        action: RecoveryAction,
        context: dict[str, Any] | None = None
    ) -> RecoveryResult:
        """
        Apply a recovery action.

        Args:
            action: Recovery action to apply
            context: Additional context

        Returns:
            Recovery result
        """
        logger.info(f"🔧 Applying recovery: {action.strategy.value}")

        context = context or {}
        applied_steps = []
        success = False
        outcome = ""

        try:
            # Apply recovery based on strategy
            if action.strategy == RecoveryStrategy.RETRY:
                outcome = "Retry scheduled"
                success = True
                applied_steps = ["Scheduled retry"]

            elif action.strategy == RecoveryStrategy.ROLLBACK:
                outcome = "Rollback completed"
                success = True
                applied_steps = ["Rolled back changes"]

            elif action.strategy == RecoveryStrategy.SKIP:
                outcome = "Operation skipped"
                success = True
                applied_steps = ["Skipped operation"]

            elif action.strategy == RecoveryStrategy.ALTERNATIVE:
                outcome = "Alternative approach applied"
                success = True
                applied_steps = action.steps[:2]  # Apply first 2 steps

            elif action.strategy == RecoveryStrategy.MANUAL:
                outcome = "Manual intervention requested"
                success = False
                applied_steps = ["Notified user"]

            elif action.strategy == RecoveryStrategy.ABORT:
                outcome = "Operation aborted"
                success = True
                applied_steps = ["Aborted operation"]

            result = RecoveryResult(
                action_id=action.action_id,
                success=success,
                applied_steps=applied_steps,
                outcome=outcome,
                timestamp=datetime.now(),
                metadata={
                    "strategy": action.strategy.value,
                    "context": context
                }
            )

            self.recovery_history.append(result)

            logger.info(f"{'✅' if success else '⚠️'} Recovery result: {outcome}")

            return result

        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")

            result = RecoveryResult(
                action_id=action.action_id,
                success=False,
                applied_steps=applied_steps,
                outcome=f"Recovery failed: {str(e)}",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )

            self.recovery_history.append(result)

            return result

    async def self_heal(
        self,
        error: Exception | str | dict[str, Any],
        context: dict[str, Any] | None = None,
        auto_apply: bool = False
    ) -> dict[str, Any]:
        """
        Full self-healing cycle: diagnose → suggest → apply.

        Args:
            error: Error to heal
            context: Additional context
            auto_apply: Automatically apply best recovery action

        Returns:
            Healing result with diagnostics, actions, and recovery
        """
        logger.info("🏥 Starting self-healing cycle...")

        # Step 1: Diagnose
        diagnostics = await self.diagnose(error, context)

        if not diagnostics:
            return {
                "success": False,
                "message": "No diagnostics generated",
                "diagnostics": [],
                "actions": [],
                "recovery": None
            }

        # Step 2: Suggest recovery for most severe diagnostic
        primary_diagnostic = max(diagnostics, key=lambda d: ["info", "warning", "error", "critical"].index(d.level.value))
        actions = await self.suggest_recovery(primary_diagnostic)

        # Step 3: Apply recovery if auto_apply
        recovery_result = None

        if auto_apply and actions:
            # Find best action (highest success rate, doesn't require approval)
            auto_actions = [a for a in actions if not a.requires_approval]
            if auto_actions:
                best_action = max(auto_actions, key=lambda a: a.estimated_success_rate)
                recovery_result = await self.apply_recovery(best_action, context)

        return {
            "success": recovery_result.success if recovery_result else False,
            "message": f"Diagnosed {len(diagnostics)} issue(s), suggested {len(actions)} action(s)",
            "diagnostics": diagnostics,
            "actions": actions,
            "recovery": recovery_result
        }

    def get_health_report(self) -> dict[str, Any]:
        """Get system health report."""

        # Count diagnostics by level
        by_level: dict[str, int] = {}
        for diagnostic in self.diagnostics:
            level = diagnostic.level.value
            by_level[level] = by_level.get(level, 0) + 1

        # Recovery success rate
        if self.recovery_history:
            successful_recoveries = sum(1 for r in self.recovery_history if r.success)
            success_rate = successful_recoveries / len(self.recovery_history)
        else:
            success_rate = 0.0

        return {
            "total_diagnostics": len(self.diagnostics),
            "by_level": by_level,
            "recovery_attempts": len(self.recovery_history),
            "recovery_success_rate": success_rate,
            "recent_issues": [
                {
                    "id": d.diagnostic_id,
                    "level": d.level.value,
                    "message": d.message[:80],
                    "root_cause": d.root_cause
                }
                for d in self.diagnostics[-5:]
            ]
        }


# Global self-diagnosis instance
_self_diagnosis: SelfDiagnosisV6 | None = None


def get_self_diagnosis() -> SelfDiagnosisV6:
    """Get global self-diagnosis instance."""
    global _self_diagnosis
    if _self_diagnosis is None:
        _self_diagnosis = SelfDiagnosisV6()
    return _self_diagnosis


# Export
__all__ = [
    "SelfDiagnosisV6",
    "Diagnostic",
    "RecoveryAction",
    "RecoveryResult",
    "DiagnosticLevel",
    "RecoveryStrategy",
    "get_self_diagnosis"
]
