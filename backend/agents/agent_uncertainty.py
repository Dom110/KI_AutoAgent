"""
Agent Uncertainty Detection System
Detects when agents are unsure and triggers HITL intervention

This module analyzes agent responses to detect uncertainty:
- Uses GPT-4o-mini for intelligent uncertainty detection
- Detects confusion, multiple approaches, missing information
- Generates structured HITL requests with options
- Threshold-based triggering (>0.7 = HITL required)

Author: KI AutoAgent Team
Version: 1.0.0
Date: 2025-10-14
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AgentUncertaintyDetector:
    """
    Detects uncertainty in agent responses and triggers HITL.

    Uses GPT-4o-mini to analyze agent thoughts/responses for:
    - Phrases indicating uncertainty ("I'm not sure", "unclear", "maybe")
    - Multiple conflicting approaches considered
    - Missing critical information
    - Requests for clarification
    """

    def __init__(self, threshold: float = 0.7):
        """
        Initialize Uncertainty Detector.

        Args:
            threshold: Uncertainty score threshold (0.0-1.0) to trigger HITL
        """
        self.threshold = threshold
        logger.debug(f"🤔 AgentUncertaintyDetector initialized (threshold={threshold})")

    async def analyze_response(
        self,
        agent_name: str,
        agent_response: str,
        context: dict[str, Any] | None = None,
        mcp_client: Any = None
    ) -> dict[str, Any]:
        """
        Analyze agent response for uncertainty.

        Args:
            agent_name: Name of agent being analyzed
            agent_response: Full response text from agent
            context: Additional context (task description, workspace info, etc.)
            mcp_client: MCP client for calling GPT-4o-mini

        Returns:
            {
                "uncertain": bool,
                "score": 0.0-1.0,
                "reasons": ["reason1", "reason2"],
                "detected_issues": [
                    {
                        "type": "missing_info|conflicting_approaches|unclear_requirements",
                        "description": "...",
                        "severity": 0.0-1.0
                    }
                ],
                "hitl_request": {
                    "title": "...",
                    "question": "...",
                    "options": [
                        {"label": "Option 1", "description": "...", "pros": [...], "cons": [...]},
                        ...
                    ]
                } or None
            }
        """
        logger.info(f"🔍 Analyzing {agent_name} response for uncertainty...")

        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(
            agent_name=agent_name,
            response=agent_response,
            context=context
        )

        # Call GPT-4o-mini via MCP
        if mcp_client is None:
            logger.warning("⚠️  No MCP client provided, using heuristic detection")
            return await self._heuristic_detection(agent_response)

        try:
            result = await mcp_client.call(
                server="claude",  # Uses GPT-4o-mini internally for fast analysis
                tool="claude_generate",
                arguments={
                    "prompt": analysis_prompt,
                    "system_prompt": self._get_system_prompt(),
                    "workspace_path": context.get("workspace_path", "") if context else "",
                    "agent_name": "uncertainty_detector",
                    "temperature": 0.2,  # Low temperature for consistent analysis
                    "max_tokens": 1024,
                    "tools": [],  # No tools needed
                    "model": "gpt-4o-mini"  # Fast, cheap, good for analysis
                },
                timeout=30.0
            )

            # Parse JSON response
            analysis = self._parse_analysis_result(result)

            # Generate HITL request if uncertain
            if analysis["uncertain"]:
                analysis["hitl_request"] = self._generate_hitl_request(
                    agent_name=agent_name,
                    analysis=analysis,
                    context=context
                )
            else:
                analysis["hitl_request"] = None

            logger.info(
                f"✅ Uncertainty analysis complete: "
                f"score={analysis['score']:.2f}, uncertain={analysis['uncertain']}"
            )

            return analysis

        except Exception as e:
            logger.error(f"❌ Uncertainty detection failed: {e}")
            # Fallback to heuristic
            return await self._heuristic_detection(agent_response)

    async def check_architect_design(
        self,
        design: dict[str, Any],
        mcp_client: Any = None
    ) -> dict[str, Any]:
        """
        Check if architect design is complete and confident.

        Args:
            design: Architecture design dict
            mcp_client: MCP client

        Returns:
            Same format as analyze_response()
        """
        logger.info("🏗️  Checking architect design completeness...")

        # Convert design to readable text
        design_text = json.dumps(design, indent=2)

        return await self.analyze_response(
            agent_name="architect",
            agent_response=design_text,
            context={"checking": "design_completeness"},
            mcp_client=mcp_client
        )

    async def check_codesmith_plan(
        self,
        plan: str,
        mcp_client: Any = None
    ) -> dict[str, Any]:
        """
        Check if codesmith implementation plan is clear.

        Args:
            plan: Implementation plan text
            mcp_client: MCP client

        Returns:
            Same format as analyze_response()
        """
        logger.info("🔨 Checking codesmith plan clarity...")

        return await self.analyze_response(
            agent_name="codesmith",
            agent_response=plan,
            context={"checking": "implementation_plan"},
            mcp_client=mcp_client
        )

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _get_system_prompt(self) -> str:
        """Get system prompt for uncertainty detection."""
        return """You are an uncertainty detection system analyzing AI agent responses.

Your task: Identify if the agent is uncertain, confused, or lacking information.

Analyze for:
1. **Uncertainty phrases**: "I'm not sure", "unclear", "maybe", "possibly", "I think", "it seems"
2. **Multiple approaches**: Agent considering 2+ conflicting solutions without clear winner
3. **Missing information**: Agent explicitly states they need more data/context
4. **Hedging language**: Excessive qualifiers, disclaimers, caveats
5. **Questions**: Agent asking questions instead of providing solutions

Return JSON:
{
    "uncertain": true/false,
    "score": 0.0-1.0,
    "reasons": ["reason1", "reason2"],
    "detected_issues": [
        {
            "type": "missing_info|conflicting_approaches|unclear_requirements|other",
            "description": "What is unclear or missing",
            "severity": 0.0-1.0
        }
    ]
}

Be objective. Some consideration of alternatives is healthy. Only flag HIGH uncertainty (score > 0.7)."""

    def _build_analysis_prompt(
        self,
        agent_name: str,
        response: str,
        context: dict[str, Any] | None
    ) -> str:
        """Build prompt for uncertainty analysis."""
        prompt = f"""Analyze this {agent_name} agent response for uncertainty:

AGENT RESPONSE:
```
{response[:2000]}  # Limit length
```
"""

        if context:
            prompt += f"\n\nCONTEXT:\n{json.dumps(context, indent=2)[:500]}\n"

        prompt += """
Provide uncertainty analysis in JSON format."""

        return prompt

    def _parse_analysis_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Parse GPT-4o-mini analysis result."""
        try:
            # Extract response text
            response_text = result.get("response", {}).get("content", [{}])[0].get("text", "")

            # Try to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")

            analysis = json.loads(json_text)

            # Validate structure
            if "uncertain" not in analysis:
                analysis["uncertain"] = analysis.get("score", 0.0) > self.threshold

            if "score" not in analysis:
                analysis["score"] = 0.8 if analysis.get("uncertain") else 0.3

            if "reasons" not in analysis:
                analysis["reasons"] = []

            if "detected_issues" not in analysis:
                analysis["detected_issues"] = []

            return analysis

        except Exception as e:
            logger.error(f"❌ Failed to parse analysis result: {e}")
            # Return safe default
            return {
                "uncertain": False,
                "score": 0.0,
                "reasons": [],
                "detected_issues": [],
                "error": str(e)
            }

    async def _heuristic_detection(self, response: str) -> dict[str, Any]:
        """
        Fallback heuristic uncertainty detection (no AI).

        Simple keyword matching for uncertainty phrases.
        """
        logger.debug("Using heuristic uncertainty detection")

        uncertainty_phrases = [
            "i'm not sure",
            "i'm unsure",
            "not clear",
            "unclear",
            "i think",
            "maybe",
            "possibly",
            "not certain",
            "hard to tell",
            "difficult to say",
            "need more information",
            "need clarification",
            "could be",
            "might be",
            "it seems",
            "appears to be"
        ]

        response_lower = response.lower()

        # Count matches
        matches = []
        for phrase in uncertainty_phrases:
            if phrase in response_lower:
                matches.append(phrase)

        score = min(1.0, len(matches) * 0.2)  # 0.2 per phrase, max 1.0
        uncertain = score > self.threshold

        return {
            "uncertain": uncertain,
            "score": score,
            "reasons": [f"Found uncertainty phrase: '{phrase}'" for phrase in matches],
            "detected_issues": [
                {
                    "type": "unclear_requirements",
                    "description": f"Response contains uncertainty phrases: {', '.join(matches)}",
                    "severity": score
                }
            ] if uncertain else [],
            "hitl_request": None,
            "method": "heuristic"
        }

    def _generate_hitl_request(
        self,
        agent_name: str,
        analysis: dict[str, Any],
        context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """
        Generate HITL request from uncertainty analysis.

        Creates structured request with clear options for user decision.
        """
        logger.debug(f"Generating HITL request for {agent_name}")

        # Extract main issue
        issues = analysis.get("detected_issues", [])
        primary_issue = issues[0] if issues else {"type": "unknown", "description": "Uncertainty detected"}

        # Generate title
        title = f"{agent_name.capitalize()} Requires Clarification"

        # Generate question
        question = f"""The {agent_name} agent is uncertain about how to proceed.

**Primary Issue:** {primary_issue.get('description', 'Unknown')}

**Reasons:**
{self._format_reasons(analysis.get('reasons', []))}

**How would you like to proceed?**
"""

        # Generate options based on issue type
        options = self._generate_options(primary_issue, agent_name)

        return {
            "title": title,
            "question": question,
            "options": options,
            "uncertainty_score": analysis.get("score", 0.0),
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        }

    def _format_reasons(self, reasons: list[str]) -> str:
        """Format reasons as bullet list."""
        if not reasons:
            return "- (No specific reasons provided)"
        return "\n".join(f"- {reason}" for reason in reasons)

    def _generate_options(self, issue: dict[str, Any], agent_name: str) -> list[dict[str, Any]]:
        """Generate appropriate options based on issue type."""
        issue_type = issue.get("type", "other")

        if issue_type == "missing_info":
            return [
                {
                    "label": "Provide Information",
                    "description": "I'll provide the missing information",
                    "pros": ["Direct resolution", "Agent can continue immediately"],
                    "cons": ["Requires user input"],
                    "action": "provide_info"
                },
                {
                    "label": "Research First",
                    "description": "Run research agent to gather information",
                    "pros": ["Automated information gathering", "No user input needed"],
                    "cons": ["Takes time", "May not find everything"],
                    "action": "research"
                },
                {
                    "label": "Skip This Step",
                    "description": "Continue without this information",
                    "pros": ["Fast", "Unblocks agent"],
                    "cons": ["May result in incomplete solution"],
                    "action": "skip"
                }
            ]

        elif issue_type == "conflicting_approaches":
            return [
                {
                    "label": "Choose Approach A",
                    "description": "Use first approach mentioned by agent",
                    "pros": ["Clear decision", "Agent can proceed"],
                    "cons": ["May not be optimal"],
                    "action": "approach_a"
                },
                {
                    "label": "Choose Approach B",
                    "description": "Use alternative approach",
                    "pros": ["Clear decision", "Different trade-offs"],
                    "cons": ["May not be optimal"],
                    "action": "approach_b"
                },
                {
                    "label": "Research Best Practice",
                    "description": "Research which approach is better",
                    "pros": ["Data-driven decision"],
                    "cons": ["Takes time"],
                    "action": "research"
                }
            ]

        else:  # unclear_requirements, other
            return [
                {
                    "label": "Clarify Requirements",
                    "description": "I'll provide clearer requirements",
                    "pros": ["Direct resolution", "Better end result"],
                    "cons": ["Requires user input"],
                    "action": "clarify"
                },
                {
                    "label": "Use Best Judgment",
                    "description": f"Let {agent_name} proceed with best judgment",
                    "pros": ["Fast", "No user input needed"],
                    "cons": ["May not match expectations"],
                    "action": "proceed"
                },
                {
                    "label": "Review & Decide Later",
                    "description": "Generate multiple options for later review",
                    "pros": ["Flexible", "Can compare approaches"],
                    "cons": ["More work overall"],
                    "action": "review_later"
                }
            ]
