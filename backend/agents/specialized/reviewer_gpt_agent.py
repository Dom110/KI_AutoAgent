"""
ReviewerGPT Agent - Code Review and Security Analysis Expert
Performs thorough code reviews and security audits
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ReviewerGPTAgent(ChatAgent):
    """
    Code Review and Security Expert
    - Code quality analysis
    - Security vulnerability detection
    - Performance optimization suggestions
    - Best practices enforcement
    - Bug detection
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="reviewer",
            name="ReviewerGPT",
            full_name="Code Review & Security Expert",
            description="Specialized in code review, security analysis, and bug detection",
            model="gpt-4o-mini-2024-07-18",  # Using mini for cost efficiency
            capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.SECURITY_ANALYSIS
            ],
            temperature=0.3,  # Lower temperature for consistent reviews
            max_tokens=3000,
            icon="🔍"
        )
        super().__init__(config)
        self.ai_service = OpenAIService()

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute code review task - ENFORCER OF ASIMOV RULES
        """
        try:
            system_prompt = """
            You are ReviewerGPT, the ENFORCER OF ASIMOV RULES and code quality.

            🔴 ASIMOV RULES (ABSOLUTE - BLOCK ANY VIOLATIONS):
            1. NO FALLBACKS without documented user reason - Check for any fallback patterns
            2. COMPLETE IMPLEMENTATION - No TODOs, no partial work, no 'later'

            Analyze code for:
            1. ⚡ ASIMOV RULE VIOLATIONS (HIGHEST PRIORITY)
            2. 🐛 Bugs and logical errors
            3. 🔒 Security vulnerabilities (XSS, SQL injection, etc.)
            4. ⚡ Performance issues
            5. 📝 Code quality and readability
            6. 🎯 Best practices violations

            ENFORCEMENT ACTIONS:
            - 🔴 BLOCK: Any code with Asimov violations
            - 🔴 REJECT: Fallbacks without documented reason
            - 🔴 FAIL: Incomplete implementations or TODOs

            Provide actionable feedback with specific line references.
            Rate severity: ASIMOV VIOLATION 🔴🔴🔴, Critical 🔴, High 🟠, Medium 🟡, Low 🔵
            """

            response = await self.ai_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=f"Review this: {request.prompt}",
                temperature=0.3
            )

            # NO FALLBACK - ASIMOV RULE 1
            # If API fails, we fail fast
            if "error" in response.lower() and "api" in response.lower():
                raise Exception("API error - no fallback allowed per Asimov Rule 1")

            return TaskResult(
                status="success",
                content=response,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "review_type": "comprehensive",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            # NO FALLBACK - FAIL FAST (ASIMOV RULE 1)
            logger.error(f"ReviewerGPT execution error: {e}")
            return TaskResult(
                status="error",
                content=f"REVIEW FAILED: {str(e)}\n\nNo fallback review allowed per Asimov Rule 1.\nFix the error and retry.",
                agent=self.config.agent_id,
                metadata={"asimov_enforcement": "No fallbacks allowed"}
            )

    def check_asimov_violations(self, code: str) -> List[Dict[str, Any]]:
        """
        Check for Asimov Rule violations in code
        This is the PRIMARY enforcement mechanism
        """
        violations = []

        # Check for fallback patterns (Asimov Rule 1)
        fallback_patterns = [
            (r'if.*not.*available.*:', 'Potential fallback without documented reason'),
            (r'except.*pass', 'Silent error handling - violates fail-fast principle'),
            (r'fallback|default.*=|or\s+\w+\(\)', 'Fallback pattern detected'),
            (r'try:.*except:.*return.*None', 'Silent fallback to None'),
        ]

        # Check for incomplete implementation (Asimov Rule 2)
        incomplete_patterns = [
            (r'#\s*TODO', 'TODO found - incomplete implementation'),
            (r'#\s*FIXME', 'FIXME found - incomplete implementation'),
            (r'#\s*HACK', 'HACK found - improper implementation'),
            (r'pass\s*$', 'Empty implementation with pass'),
            (r'raise\s+NotImplementedError', 'Not implemented'),
            (r'return\s+None\s*#.*later', 'Deferred implementation'),
        ]

        import re
        code_lower = code.lower()

        for pattern, description in fallback_patterns:
            if re.search(pattern, code_lower):
                violations.append({
                    'rule': 'ASIMOV RULE 1',
                    'severity': 'ASIMOV_VIOLATION',
                    'description': description,
                    'action': 'BLOCK',
                    'fix': 'Remove fallback or add documented reason with user confirmation'
                })

        for pattern, description in incomplete_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append({
                    'rule': 'ASIMOV RULE 2',
                    'severity': 'ASIMOV_VIOLATION',
                    'description': description,
                    'action': 'BLOCK',
                    'fix': 'Complete the implementation before submission'
                })

        return violations

    async def find_bugs(self, code: str) -> List[Dict[str, Any]]:
        """
        Actively hunt for bugs in code
        """
        # This would use AI to find bugs
        bugs = []
        
        # First check for Asimov violations
        asimov_violations = self.check_asimov_violations(code)
        if asimov_violations:
            for violation in asimov_violations:
                bugs.append({
                    "type": "ASIMOV_VIOLATION",
                    "severity": "BLOCKER",
                    "rule": violation['rule'],
                    "description": violation['description'],
                    "action": violation['action'],
                    "fix": violation['fix']
                })

        # Then check for regular bugs
        if "onclick=" in code.lower():
            bugs.append({
                "type": "event_handler",
                "severity": "medium",
                "description": "onclick handlers might not work in VS Code webviews",
                "suggestion": "Use addEventListener instead"
            })
            
        return bugs

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
