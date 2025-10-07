"""
Custom Exception Classes for KI AutoAgent

Python 3.13+ Best Practice: Use domain-specific exceptions
instead of generic Exception for better error handling.

Created: 2025-10-01
Updated: 2025-10-07 (v5.9.0 - Comprehensive modernization)
"""

from typing import Any


# ============================================================================
# Base Exceptions
# ============================================================================

class AgentError(Exception):
    """Base exception for all agent-related errors."""

    def __init__(
        self,
        message: str,
        agent: str | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        self.message = message
        self.agent = agent
        self.context = context or {}
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with context."""
        parts = [self.message]
        if self.agent:
            parts.append(f"(Agent: {self.agent})")
        if self.context:
            parts.append(f"Context: {self.context}")
        return " ".join(parts)


class WorkflowError(Exception):
    """Base exception for workflow-related errors."""

    def __init__(
        self,
        message: str,
        workflow_id: str | None = None,
        step: str | None = None
    ) -> None:
        self.message = message
        self.workflow_id = workflow_id
        self.step = step
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with workflow context."""
        parts = [self.message]
        if self.workflow_id:
            parts.append(f"(Workflow: {self.workflow_id})")
        if self.step:
            parts.append(f"Step: {self.step}")
        return " ".join(parts)


# ============================================================================
# Agent-Specific Exceptions
# ============================================================================

class ArchitectError(AgentError):
    """Raised when Architect agent encounters errors."""
    pass


class ArchitectValidationError(ArchitectError):
    """Raised when architecture validation fails."""
    pass


class ArchitectResearchError(ArchitectError):
    """Raised when research step fails."""
    pass


class OrchestratorError(AgentError):
    """Raised when Orchestrator agent encounters errors."""
    pass


class TaskDecompositionError(OrchestratorError):
    """Raised when task decomposition fails."""
    pass


class CodesmithError(AgentError):
    """Raised when Codesmith agent encounters errors."""
    pass


class CodeGenerationError(CodesmithError):
    """Raised when code generation fails."""
    pass


class ReviewerError(AgentError):
    """Raised when Reviewer agent encounters errors."""
    pass


class CodeReviewError(ReviewerError):
    """Raised when code review fails."""
    pass


class FixerError(AgentError):
    """Raised when Fixer agent encounters errors."""
    pass


class ResearchError(AgentError):
    """Raised when Research agent encounters errors."""
    pass


# ============================================================================
# Workflow-Specific Exceptions
# ============================================================================

class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""
    pass


class WorkflowValidationError(WorkflowError):
    """Raised when workflow validation fails."""
    pass


class WorkflowTimeoutError(WorkflowError):
    """Raised when workflow times out."""
    pass


class StepExecutionError(WorkflowError):
    """Raised when a workflow step fails."""
    pass


# ============================================================================
# System Exceptions (ASIMOV RULE 1: NO FALLBACKS)
# ============================================================================

class SystemNotReadyError(Exception):
    """
    Raised when system is not ready for operation.

    Used to enforce ASIMOV RULE 1: NO FALLBACKS
    """

    def __init__(
        self,
        component: str,
        reason: str,
        solution: str,
        file: str | None = None,
        line: int | None = None
    ) -> None:
        self.component = component
        self.reason = reason
        self.solution = solution
        self.file = file
        self.line = line

        # Format detailed error message
        message_parts = [
            "❌ System Not Ready\n",
            f"Component: {component}",
            f"Reason: {reason}"
        ]

        if file and line:
            message_parts.append(f"File: {file}:{line}")

        message_parts.extend([
            f"\nSolution: {solution}",
            "\nNO FALLBACK (ASIMOV RULE 1)"
        ])

        super().__init__("\n".join(message_parts))


class DependencyError(Exception):
    """
    Raised when a required dependency is not available.

    Used to enforce ASIMOV RULE 1: NO FALLBACKS
    """

    def __init__(self, dependencies: list[dict[str, str]]) -> None:
        self.dependencies = dependencies

        # Build error message
        messages = []
        for dep in dependencies:
            component = dep.get('component', 'Unknown')
            error = dep.get('error', 'Unknown error')
            solution = dep.get('solution', 'No solution provided')

            messages.append(f"""
❌ {component}
Error: {error}
Solution: {solution}
""")

        error_message = "\n".join(messages)
        super().__init__(error_message)


class CacheNotAvailableError(Exception):
    """
    Raised when cache system (Redis) is not available.

    Used to enforce ASIMOV RULE 1: NO FALLBACKS
    """

    def __init__(self, component: str, file: str, line: int) -> None:
        message = f"""
❌ Cache Not Available

Component: {component}
File: {file}:{line}

The cache system (Redis) is required but not available.

Solution:
1. Start Redis: docker run -d -p 6379:6379 redis:7-alpine
2. Or use cache fill command: "Fülle die Caches"

NO FALLBACK TO IN-MEMORY CACHE (ASIMOV RULE 1)
"""
        super().__init__(message)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        key: str,
        value: Any,
        expected: str,
        file: str | None = None
    ) -> None:
        self.key = key
        self.value = value
        self.expected = expected
        self.file = file

        parts = [
            f"Invalid configuration: {key}={value}",
            f"(expected: {expected})"
        ]
        if file:
            parts.append(f"in {file}")

        super().__init__(" ".join(parts))


class APIKeyError(ConfigurationError):
    """Raised when API key is missing or invalid."""

    def __init__(self, service: str, key_name: str) -> None:
        super().__init__(
            key=key_name,
            value="<missing or invalid>",
            expected=f"Valid {service} API key",
            file=".env"
        )


# ============================================================================
# Data Exceptions
# ============================================================================

class DataValidationError(Exception):
    """Raised when data validation fails."""

    def __init__(
        self,
        field: str,
        value: Any,
        reason: str
    ) -> None:
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for {field}={value}: {reason}")


class ParsingError(Exception):
    """Raised when parsing fails."""

    def __init__(
        self,
        content: str,
        format: str,
        reason: str | None = None
    ) -> None:
        self.content = content[:100]  # Truncate for error message
        self.format = format
        self.reason = reason

        parts = [f"Failed to parse as {format}"]
        if reason:
            parts.append(f": {reason}")
        parts.append(f" Content: {self.content}...")

        super().__init__("".join(parts))


# ============================================================================
# Memory & Storage Exceptions
# ============================================================================

class MemoryError(Exception):
    """Raised when memory operations fail."""

    def __init__(
        self,
        operation: str,
        agent: str | None = None,
        reason: str | None = None
    ) -> None:
        self.operation = operation
        self.agent = agent
        self.reason = reason

        parts = [f"Memory operation failed: {operation}"]
        if agent:
            parts.append(f"(Agent: {agent})")
        if reason:
            parts.append(f"Reason: {reason}")

        super().__init__(" ".join(parts))


class StorageError(Exception):
    """Raised when storage operations fail."""

    def __init__(
        self,
        path: str,
        operation: str,
        reason: str | None = None
    ) -> None:
        self.path = path
        self.operation = operation
        self.reason = reason

        parts = [f"Storage {operation} failed for {path}"]
        if reason:
            parts.append(f": {reason}")

        super().__init__("".join(parts))


# ============================================================================
# Communication Exceptions
# ============================================================================

class WebSocketError(Exception):
    """Raised when WebSocket communication fails."""

    def __init__(
        self,
        client_id: str | None = None,
        reason: str | None = None
    ) -> None:
        self.client_id = client_id
        self.reason = reason

        parts = ["WebSocket error"]
        if client_id:
            parts.append(f"(Client: {client_id})")
        if reason:
            parts.append(f": {reason}")

        super().__init__("".join(parts))


class MessageError(Exception):
    """Raised when message processing fails."""

    def __init__(
        self,
        message_type: str,
        reason: str
    ) -> None:
        self.message_type = message_type
        self.reason = reason
        super().__init__(f"Failed to process {message_type} message: {reason}")


# ============================================================================
# Utility Functions
# ============================================================================

def get_exception_hierarchy() -> dict[str, list[str]]:
    """
    Get the full exception hierarchy for documentation.

    Returns:
        Dictionary mapping base exceptions to their subclasses
    """
    return {
        "AgentError": [
            "ArchitectError",
            "ArchitectValidationError",
            "ArchitectResearchError",
            "OrchestratorError",
            "TaskDecompositionError",
            "CodesmithError",
            "CodeGenerationError",
            "ReviewerError",
            "CodeReviewError",
            "FixerError",
            "ResearchError"
        ],
        "WorkflowError": [
            "WorkflowExecutionError",
            "WorkflowValidationError",
            "WorkflowTimeoutError",
            "StepExecutionError"
        ],
        "SystemError": [
            "SystemNotReadyError",
            "DependencyError",
            "CacheNotAvailableError",
            "ConfigurationError",
            "APIKeyError"
        ],
        "DataError": [
            "DataValidationError",
            "ParsingError"
        ],
        "StorageError": [
            "MemoryError",
            "StorageError"
        ],
        "CommunicationError": [
            "WebSocketError",
            "MessageError"
        ]
    }


def format_exception_docs() -> str:
    """Generate documentation for all custom exceptions."""
    hierarchy = get_exception_hierarchy()

    docs = ["# Custom Exceptions\n\n"]
    for base, subclasses in hierarchy.items():
        docs.append(f"## {base}\n")
        for subclass in subclasses:
            docs.append(f"- `{subclass}`\n")
        docs.append("\n")

    return "".join(docs)
