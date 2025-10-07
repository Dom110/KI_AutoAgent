from __future__ import annotations

"""
OpusArbitrator Agent - Supreme Conflict Resolution Authority
Uses Claude Opus for final binding decisions when agents disagree
"""

import logging
from datetime import datetime
from typing import Any, override

from utils.claude_code_service import ClaudeCodeConfig, ClaudeCodeService

from ..base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                               TaskResult)
from ..base.chat_agent import ChatAgent

logger = logging.getLogger(__name__)


class OpusArbitratorAgent(ChatAgent):
    """
    Supreme Agent Arbitrator - Conflict Resolution
    - Resolves agent disagreements
    - Makes final binding decisions
    - Evaluates competing solutions
    - Ensures consensus
    - Superior reasoning capabilities
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="opus-arbitrator",
            name="OpusArbitrator",
            full_name="Supreme Agent Arbitrator",
            description="Final authority for resolving agent conflicts with superior reasoning",
            model="claude-opus-4-1-20250805",  # Claude Opus 4.1
            capabilities=[AgentCapability.CONFLICT_RESOLUTION],
            temperature=0.3,  # Lower for consistent decisions
            max_tokens=4000,
            icon="⚖️",
            instructions_path=".ki_autoagent/instructions/opus-arbitrator-instructions.md",
        )
        super().__init__(config)
        # Use Claude CLI with Opus model - NO FALLBACKS
        self.ai_service = ClaudeCodeService(
            ClaudeCodeConfig(model="opus")  # Opus for supreme arbitration
        )
        if not self.ai_service.is_available():
            logger.error(
                "OpusArbitrator requires Claude CLI! Install with: npm install -g @anthropic-ai/claude-code"
            )

    @override
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute arbitration task
        """
        try:
            # Check if this is a conflict resolution request
            if (
                "conflict" in request.prompt.lower()
                or "disagree" in request.prompt.lower()
            ):
                response = await self.resolve_conflict(request)
            else:
                response = await self.provide_judgment(request)

            return TaskResult(
                status="success",
                content=response,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "decision_type": "binding",
                    "authority": "supreme",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"OpusArbitrator execution error: {e}")
            # ASIMOV RULE 1: NO FALLBACK - FAIL FAST
            error_msg = (
                f"OpusArbitrator execution failed: {str(e)}. File: {__file__}, Line: 73"
            )
            logger.error(error_msg)
            return TaskResult(
                status="error", content=error_msg, agent=self.config.agent_id
            )

    async def resolve_conflict(self, request: TaskRequest) -> str:
        """
        Resolve conflicts between agents
        """
        system_prompt = """
        You are the OpusArbitrator, the supreme authority for resolving conflicts between AI agents.
        Your decisions are FINAL and BINDING.
        
        When agents disagree, you must:
        1. Analyze all positions objectively
        2. Consider technical merit and practicality
        3. Evaluate risks and benefits
        4. Make a clear, reasoned decision
        5. Provide implementation guidance
        
        Your decision format:
        ## ⚖️ ARBITRATION DECISION
        **Winner**: [Agent name or "Hybrid Approach"]
        **Confidence**: [percentage]
        **Reasoning**: [detailed explanation]
        **Implementation**: [specific steps]
        **This decision is final and binding.**
        """

        if not self.ai_service.is_available():
            raise Exception("Claude CLI not available for OpusArbitrator")

        response = await self.ai_service.complete(
            prompt=request.prompt, system_prompt=system_prompt, temperature=0.3
        )

        return response

    async def provide_judgment(self, request: TaskRequest) -> str:
        """
        Provide authoritative judgment on complex matters
        """
        system_prompt = """
        You are the OpusArbitrator with superior reasoning capabilities.
        Provide authoritative judgment on complex technical decisions.
        Consider all aspects: technical, practical, ethical, and long-term implications.
        Your analysis should be thorough and your conclusions definitive.
        """

        response = await self.ai_service.get_completion(
            system_prompt=system_prompt, user_prompt=request.prompt, temperature=0.3
        )

        if "error" in response.lower() and "api" in response.lower():
            # ASIMOV RULE 1: NO FALLBACK - FAIL FAST
            error_msg = f"Claude API error in OpusArbitrator judgment. File: {__file__}, Line: 133"
            raise Exception(error_msg)

        return response

    # ASIMOV RULE 1: NO FALLBACK - FALLBACK METHOD REMOVED
    # All fallback functionality has been eliminated to enforce fail-fast architecture
    # If OpusArbitrator cannot provide a decision, the system must fail explicitly

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        request = TaskRequest(
            prompt=message.get("prompt", ""), context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content
