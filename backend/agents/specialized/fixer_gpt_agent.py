from __future__ import annotations

"""
FixerGPT Agent - Alternative Bug Fixer using GPT Models
Provides fresh perspective when primary Claude fixer fails
"""

import logging
from datetime import datetime
from typing import Any, override

from backend.config.settings import Settings
from utils.openai_service import OpenAIService

from ..base.base_agent import (AgentCapability, AgentConfig, TaskRequest,
                               TaskResult)
from ..base.chat_agent import ChatAgent

logger = logging.getLogger(__name__)


class FixerGPTAgent(ChatAgent):
    """
    Alternative Bug Fixer using GPT Models

    Purpose: Provide fresh perspective with different AI when Claude FixerBot fails

    Key Differences from FixerBot:
    - Uses GPT instead of Claude (different training, different patterns)
    - System prompt emphasizes "think differently"
    - Receives full context of previous Claude attempts
    - Acts as "fresh eyes" on the problem

    Capabilities:
    - Bug fixing with alternative approach
    - Fresh perspective on stuck problems
    - Different pattern recognition than Claude
    """

    def __init__(self, model: str = None):
        """
        Initialize FixerGPTAgent

        Args:
            model: GPT model to use (default from Settings)
        """
        # Get model from settings if not specified
        if model is None:
            model = getattr(Settings, "ALTERNATIVE_FIXER_MODEL", "gpt-4o")

        config = AgentConfig(
            agent_id="fixer_gpt",
            name="FixerGPT",
            full_name="Alternative Bug Fixer (GPT)",
            description="Alternative bug fixer using GPT for fresh perspective",
            model=model,
            capabilities=[AgentCapability.BUG_FIXING, AgentCapability.CODE_GENERATION],
            temperature=getattr(Settings, "ALTERNATIVE_FIXER_TEMPERATURE", 0.7),
            max_tokens=getattr(Settings, "ALTERNATIVE_FIXER_MAX_TOKENS", 4096),
            icon="🔧🔄",
            instructions_path=".ki_autoagent/instructions/fixer-gpt-instructions.md",
        )
        super().__init__(config)

        # Initialize OpenAI service
        self.openai_service = OpenAIService()
        logger.info(f"✅ FixerGPT initialized with model: {model}")

    async def _get_architect_analysis(self) -> dict[str, Any] | None:
        """
        Get Architect's system analysis from shared_context (v5.8.2)
        Returns system_knowledge with metrics, dead_code, security, etc.
        """
        if not self.shared_context:
            logger.warning("⚠️ FixerGPT: shared_context not available")
            return None

        try:
            analysis = self.shared_context.get("architect:system_knowledge")
            if analysis:
                logger.info("✅ FixerGPT: Got Architect analysis from shared_context")
                return analysis
            else:
                logger.info("ℹ️ FixerGPT: No Architect analysis available yet")
                return None
        except Exception as e:
            logger.error(f"❌ FixerGPT: Failed to get Architect analysis: {e}")
            return None

    def _create_fresh_perspective_prompt(
        self, issue: str, previous_attempts: list[dict], research_results: list[dict]
    ) -> str:
        """
        Create system prompt emphasizing fresh perspective

        Args:
            issue: The issue to fix
            previous_attempts: List of previous fix attempts by Claude
            research_results: Research information gathered

        Returns:
            System prompt for GPT
        """
        system_prompt = """You are FixerGPT, an alternative bug fixing AI.

CRITICAL CONTEXT:
Another AI (Claude FixerBot) has attempted to fix this issue multiple times but failed.
Your job is to provide a FRESH PERSPECTIVE with a DIFFERENT APPROACH.

KEY PRINCIPLES:
1. Think DIFFERENTLY than Claude would
2. Don't repeat what was already tried
3. Consider alternative patterns and solutions
4. Question assumptions that might be wrong
5. Look for overlooked simple solutions

You have access to:
- The original issue
- All previous fix attempts (so you can avoid repeating them)
- Research results gathered specifically for this problem

Your advantage: You are a different neural network with different patterns.
Sometimes a fresh AI sees what another AI missed."""

        return system_prompt

    def _format_previous_attempts(self, attempts: list[dict]) -> str:
        """Format previous attempts for context"""
        if not attempts:
            return "No previous attempts recorded."

        formatted = "PREVIOUS FIX ATTEMPTS (DO NOT REPEAT THESE):\n"
        for i, attempt in enumerate(attempts, 1):
            formatted += f"\nAttempt {i}:"
            formatted += f"\n  Agent: {attempt.get('from', 'unknown')}"
            formatted += f"\n  Approach: {attempt.get('query', 'unknown')[:150]}..."
            formatted += "\n  Result: Failed\n"

        return formatted

    def _format_research_results(self, research: list[dict]) -> str:
        """Format research results for context"""
        if not research:
            return "No research results available."

        formatted = "RESEARCH RESULTS:\n"
        for i, result in enumerate(research, 1):
            formatted += f"\nResearch Level {result.get('level', i)}:"
            formatted += f"\n  Query: {result.get('query', 'unknown')[:100]}..."
            formatted += f"\n  Findings: {result.get('summary', 'unknown')[:200]}...\n"

        return formatted

    @override
    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute bug fixing with fresh GPT perspective

        Receives:
        - Issue to fix
        - Previous Claude attempts (in context)
        - Research results (in context)

        Approach:
        - Emphasize thinking differently
        - Avoid repeating previous attempts
        - Consider alternative solutions
        """
        try:
            logger.info("🔧🔄 FixerGPT executing with fresh perspective...")

            prompt = request.prompt
            context = request.context or {}

            # Extract context
            previous_attempts = context.get("previous_attempts", [])
            research_results = context.get("research_results", [])
            issue_description = context.get("issue", prompt)

            # Log what we received
            logger.info(
                f"📊 Context: {len(previous_attempts)} previous attempts, "
                f"{len(research_results)} research results"
            )

            # v5.8.2: Get Architect's analysis for refactoring suggestions
            architect_analysis = await self._get_architect_analysis()

            # Build refactoring context from Architect's metrics
            refactoring_context = ""
            if architect_analysis:
                metrics = architect_analysis.get("metrics", {})
                metrics_summary = metrics.get("summary", {})
                quality_score = metrics_summary.get("quality_score", 0)
                metrics_summary.get("average_complexity", 0)

                # Find high-complexity functions
                all_metrics = metrics.get("files", {})
                high_complexity_funcs = []
                for file_path, file_metrics in all_metrics.items():
                    for func in file_metrics.get("functions", []):
                        if func.get("complexity", 0) > 15:
                            high_complexity_funcs.append(
                                {
                                    "name": func.get("name"),
                                    "complexity": func.get("complexity"),
                                    "file": file_path,
                                    "line": func.get("line_number"),
                                }
                            )

                if high_complexity_funcs:
                    refactoring_context += """
📊 HIGH COMPLEXITY FUNCTIONS DETECTED (CC > 15):
Consider refactoring these functions to reduce complexity:
"""
                    for func in high_complexity_funcs[:10]:  # Top 10
                        refactoring_context += f"  - {func['name']} (CC={func['complexity']}) at {func['file']}:{func['line']}\n"

                    refactoring_context += """
REFACTORING STRATEGIES:
1. Extract Method: Break down large functions into smaller ones
2. Guard Clauses: Use early returns to reduce nesting
3. Strategy Pattern: Replace complex if/else with polymorphism
4. Replace Nested Conditionals: Use lookup tables or maps
"""

                if quality_score < 70:
                    refactoring_context += f"""
⚠️ OVERALL QUALITY SCORE LOW: {quality_score:.1f}/100
Focus on improving maintainability through refactoring.
"""

            # Build comprehensive prompt
            system_prompt = self._create_fresh_perspective_prompt(
                issue=issue_description,
                previous_attempts=previous_attempts,
                research_results=research_results,
            )

            # Format context sections
            attempts_text = self._format_previous_attempts(previous_attempts)
            research_text = self._format_research_results(research_results)

            # Full user prompt with refactoring context
            user_prompt = f"""FIX THIS ISSUE WITH A FRESH APPROACH:

ISSUE:
{issue_description}

{attempts_text}

{research_text}

{refactoring_context}

INSTRUCTIONS:
1. Analyze what previous attempts missed
2. Consider if the approach itself is wrong
3. Look for simple solutions that were overlooked
4. Think about the problem from a different angle
5. If high-complexity functions are involved, suggest refactoring
6. Provide your fix with explanation of why your approach is different

Provide the fix now:"""

            # Call OpenAI
            logger.info(f"🤖 Calling {self.config.model} for alternative fix...")

            response = await self.openai_service.chat_completion(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            fix_result = response.get("content", "")

            logger.info(f"✅ FixerGPT completed - {len(fix_result)} characters")

            return TaskResult(
                status="success",
                content=fix_result,
                agent=self.config.agent_id,
                metadata={
                    "model": self.config.model,
                    "perspective": "alternative_ai",
                    "previous_attempts_count": len(previous_attempts),
                    "research_count": len(research_results),
                    "approach": "fresh_perspective",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"FixerGPT execution error: {e}")
            return TaskResult(
                status="error",
                content=f"FixerGPT error: {str(e)}",
                agent=self.config.agent_id,
                metadata={"error_type": type(e).__name__},
            )

    async def analyze_fix_pattern(
        self, issue: str, previous_fixes: list[str]
    ) -> dict[str, Any]:
        """
        Analyze why previous fixes failed
        Uses GPT's pattern recognition to identify what's been missed

        Args:
            issue: The original issue
            previous_fixes: List of previous fix attempts

        Returns:
            Analysis of what might be wrong with the approach
        """
        logger.info("🔍 FixerGPT analyzing fix pattern...")

        analysis_prompt = f"""Analyze why these fix attempts failed:

ORIGINAL ISSUE:
{issue}

PREVIOUS FIX ATTEMPTS:
{chr(10).join(f"{i+1}. {fix[:200]}..." for i, fix in enumerate(previous_fixes))}

ANALYZE:
1. What pattern do you see in the failed attempts?
2. What might they all be missing?
3. Is the core approach wrong?
4. What alternative approach would you recommend?

Provide concise analysis:"""

        try:
            response = await self.openai_service.chat_completion(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing failed fix attempts.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.3,  # Lower temp for analysis
                max_tokens=1000,
            )

            return {
                "analysis": response.get("content", ""),
                "model": self.config.model,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return {"analysis": f"Analysis failed: {str(e)}", "error": True}
