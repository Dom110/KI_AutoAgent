"""
DocuBot Agent - Technical Documentation Specialist
Generates documentation, API specs, and user guides
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class DocuBotAgent(ChatAgent):
    """
    Technical Documentation Specialist
    - API documentation generation
    - Code documentation
    - User guides and tutorials
    - README files
    - Architecture documentation
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="docubot",
            name="DocuBot",
            full_name="Technical Documentation Expert",
            description="Specialized in creating comprehensive documentation",
            model="gpt-4o-2024-11-20",
            capabilities=[
                AgentCapability.DOCUMENTATION
            ],
            temperature=0.7,
            max_tokens=4000,
            icon="📝"
        )
        super().__init__(config)
        self.ai_service = OpenAIService()

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute documentation task
        """
        try:
            # Generate documentation based on request
            system_prompt = """
            You are DocuBot, a technical documentation expert. Generate clear,
            comprehensive documentation based on the user's request. Include:
            - Clear structure with headers
            - Code examples where relevant
            - API specifications if applicable
            - Usage instructions
            - Best practices
            """

            response = await self.ai_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=request.prompt,
                temperature=0.7
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
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"DocuBot execution error: {e}")
            # ASIMOV RULE 1: NO FALLBACK - FAIL FAST
            return TaskResult(
                status="error",
                content=f"DOCUMENTATION FAILED: {str(e)}\n\nNo fallback allowed per Asimov Rule 1.\nFix the error and retry.",
                agent=self.config.agent_id
            )

    # REMOVED: _generate_fallback_documentation method
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
