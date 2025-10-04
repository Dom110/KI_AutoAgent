"""
Custom exceptions for KI AutoAgent core systems
"""


class DependencyError(Exception):
    """
    Raised when a required dependency is not available

    Used to enforce ASIMOV RULE 1: NO FALLBACKS
    """

    def __init__(self, dependencies: list):
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
    Raised when cache system (Redis) is not available

    Used to enforce ASIMOV RULE 1: NO FALLBACKS
    """

    def __init__(self, component: str, file: str, line: int):
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


class SystemNotReadyError(Exception):
    """
    Raised when a system component is not ready

    Used to enforce ASIMOV RULE 1: NO FALLBACKS
    """

    def __init__(self, component: str, reason: str, solution: str, file: str, line: int):
        message = f"""
❌ System Not Ready

Component: {component}
Reason: {reason}
File: {file}:{line}

Solution: {solution}

NO FALLBACK (ASIMOV RULE 1)
"""
        super().__init__(message)
