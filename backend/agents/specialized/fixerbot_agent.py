"""
FixerBot Agent - Bug Fixing and Code Optimization Specialist
Fixes bugs, optimizes performance, and refactors code
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.claude_code_service import ClaudeCodeService, ClaudeCodeConfig

logger = logging.getLogger(__name__)

class FixerBotAgent(ChatAgent):
    """
    Bug Fixing and Optimization Expert
    - Bug fixes and patches
    - Performance optimization
    - Code refactoring
    - Memory leak fixes
    - Modernization of legacy code
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="fixer",
            name="FixerBot",
            full_name="Bug Fixing & Optimization Expert",
            description="Specialized in fixing bugs, optimizing performance, and refactoring",
            model="claude-4.1-sonnet-20250920",
            capabilities=[
                AgentCapability.BUG_FIXING,
                AgentCapability.CODE_GENERATION
            ],
            temperature=0.5,
            max_tokens=4000,
            icon="🔧",
            instructions_path=".kiautoagent/instructions/fixerbot-instructions.md"
        )
        super().__init__(config)
        # Use Claude CLI - NO FALLBACKS
        self.ai_service = ClaudeCodeService(
            ClaudeCodeConfig(model="sonnet")
        )
        if not self.ai_service.is_available():
            logger.error("FixerBot requires Claude CLI! Install with: npm install -g @anthropic-ai/claude-code")

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute bug fixing task
        """
        try:
            system_prompt = """
            You are FixerBot, an expert at fixing bugs and optimizing code.
            Your specialties:
            1. 🐛 Bug Fixes - Identify and fix all types of bugs
            2. ⚡ Performance - Optimize for speed and efficiency
            3. 🔄 Refactoring - Clean up and modernize code
            4. 💧 Memory - Fix memory leaks and optimize usage
            5. 🆕 Modernization - Update legacy code to modern standards
            
            Always provide:
            - Fixed code with explanations
            - Performance improvements made
            - Potential issues prevented
            - Testing recommendations
            """

            if not self.ai_service.is_available():
                raise Exception("Claude CLI not available for FixerBot")

            response = await self.ai_service.complete(
                prompt=f"Fix this: {request.prompt}",
                system_prompt=system_prompt,
                temperature=0.5
            )

            # ASIMOV RULE 1: NO FALLBACK WITHOUT DOCUMENTED REASON
            if "error" in response.lower() and "api" in response.lower():
                raise Exception(f"API error - no fallback allowed per Asimov Rule 1: {response}")

            return TaskResult(
                status="success",
                content=response,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "fix_type": "comprehensive",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"FixerBot execution error: {e}")
            # ASIMOV RULE 1: NO FALLBACK - FAIL FAST
            return TaskResult(
                status="error",
                content=f"FIX FAILED: {str(e)}\n\nNo fallback allowed per Asimov Rule 1.\nFix the error and retry.",
                agent=self.config.agent_id
            )

    # REMOVED: _generate_fallback_fix method
    # ASIMOV RULE 1: No fallbacks without documented user reason
    # All errors must fail fast with clear error messages

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
