"""
Intent Detector v6 - Simple LLM-based Workflow Routing

Uses GPT-4o-mini to classify user intent and route to appropriate workflow:
- CREATE: Build new application (Research → Architect → Codesmith → ReviewFix)
- FIX: Fix existing code (ReviewFix directly)
- REFACTOR: Restructure existing code (Architect → Codesmith → ReviewFix)
- EXPLAIN: Explain existing code (Research only)

Simple, reliable, and works for all cases - no complex keyword matching needed.

Author: KI AutoAgent Team
Date: 2025-10-12
Version: 6.2.0
Python: 3.13+
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """User intent types for workflow routing."""
    CREATE = "create"
    FIX = "fix"
    REFACTOR = "refactor"
    EXPLAIN = "explain"


class IntentResult:
    """Result of intent detection."""

    def __init__(
        self,
        intent: UserIntent,
        confidence: float,
        workflow_path: list[str],
        reasoning: str
    ):
        self.intent = intent
        self.confidence = confidence
        self.workflow_path = workflow_path
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return (
            f"IntentResult(intent={self.intent.value}, "
            f"confidence={self.confidence:.2f}, "
            f"workflow={' → '.join(self.workflow_path)})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "workflow_path": self.workflow_path,
            "reasoning": self.reasoning
        }


class IntentDetectorV6:
    """
    Simple LLM-based intent detection for workflow routing.

    Example:
        detector = IntentDetectorV6()
        result = await detector.detect_intent(
            "Fix the TypeScript compilation errors",
            workspace_has_code=True
        )
        # → IntentResult(intent=FIX, workflow=[reviewfix])
    """

    WORKFLOW_PATHS = {
        UserIntent.CREATE: ["research", "architect", "codesmith", "reviewfix"],
        UserIntent.FIX: ["reviewfix"],  # 🎯 Direct to ReviewFix!
        UserIntent.REFACTOR: ["architect", "codesmith", "reviewfix"],
        UserIntent.EXPLAIN: ["research"]
    }

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=300
        )
        logger.debug("IntentDetectorV6 initialized (LLM-only)")

    async def detect_intent(
        self,
        user_query: str,
        workspace_has_code: bool = False
    ) -> IntentResult:
        """
        Detect user intent from query using GPT-4o-mini.

        Args:
            user_query: User's request/task description
            workspace_has_code: Whether workspace contains existing code

        Returns:
            IntentResult with intent, confidence, and workflow path
        """
        logger.info(f"🎯 Detecting intent: \"{user_query[:80]}...\"")

        system_prompt = """You are an intent classifier for a code generation system.

Classify the user's request into ONE of these intents:

1. CREATE - Build new application/project from scratch
   Examples: "Create a Todo app", "Build an API", "Generate a website"

2. FIX - Fix bugs/errors in existing code
   Examples: "Fix TypeScript errors", "Resolve compilation issues", "Debug the login bug"

3. REFACTOR - Restructure/reorganize existing code
   Examples: "Refactor the auth module", "Clean up the codebase", "Improve code structure"

4. EXPLAIN - Explain/document existing code
   Examples: "Explain how authentication works", "Document the API", "What does this code do?"

Rules:
- If workspace is EMPTY and user wants to build → CREATE
- If workspace HAS CODE and user mentions fixing/debugging → FIX
- If workspace HAS CODE and user wants to restructure → REFACTOR
- If user asks questions about code → EXPLAIN
- Default to CREATE if uncertain

Respond with JSON:
{
  "intent": "FIX",
  "confidence": 0.95,
  "reasoning": "User explicitly mentions fixing TypeScript compilation errors in existing code"
}"""

        user_prompt = f"""User request: "{user_query}"

Workspace has existing code: {workspace_has_code}

Classify the intent."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            intent_str = result.get("intent", "CREATE").upper()
            try:
                intent = UserIntent[intent_str]
            except KeyError:
                logger.warning(f"Invalid intent '{intent_str}', defaulting to CREATE")
                intent = UserIntent.CREATE

            confidence = float(result.get("confidence", 0.8))
            reasoning = result.get("reasoning", "LLM classification")

            logger.info(f"  ✅ Intent: {intent.value} (confidence: {confidence:.2f})")
            logger.debug(f"  Reasoning: {reasoning}")

            return IntentResult(
                intent=intent,
                confidence=confidence,
                workflow_path=self.WORKFLOW_PATHS[intent],
                reasoning=reasoning
            )

        except Exception as e:
            logger.error(f"Intent detection failed: {e}, defaulting to CREATE")
            return IntentResult(
                intent=UserIntent.CREATE,
                confidence=0.5,
                workflow_path=self.WORKFLOW_PATHS[UserIntent.CREATE],
                reasoning=f"Error during classification: {e}"
            )


__all__ = ["IntentDetectorV6", "UserIntent", "IntentResult"]
