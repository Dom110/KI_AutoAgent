"""
Human-in-the-Loop (HITL) Agent for v7.0

This agent handles low confidence situations and requests user clarification.
It implements Asimov Rule 3: HITL on low confidence.

Key Responsibilities:
- Request clarification when confidence < 0.5
- Present options for user to choose
- Gather additional requirements
- Handle ambiguous requests
- Validate user intent

Author: KI AutoAgent Team
Version: 7.0.0-alpha
Date: 2025-10-21
"""

from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)


class HITLAgent:
    """
    Human-in-the-Loop agent for user clarification.

    This agent is invoked when:
    - Supervisor confidence is low (< 0.5)
    - Multiple interpretations are possible
    - Critical decisions need confirmation
    - Errors require user guidance
    """

    def __init__(self):
        """Initialize the HITL agent."""
        logger.info("👤 HITLAgent initialized")

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute HITL to request user clarification.

        Args:
            state: Contains:
                - instructions: What clarification is needed
                - context: Current workflow context
                - confidence: Supervisor's confidence level
                - options: Possible interpretations (if any)

        Returns:
            Dictionary with user_input and clarification_received
        """
        instructions = state.get("instructions", "")
        context = state.get("context", {})
        confidence = context.get("confidence", 0.0)
        options = state.get("options", [])
        errors = context.get("errors", [])

        logger.info(f"❓ Requesting clarification: {instructions[:100]}...")
        logger.info(f"   Confidence level: {confidence:.2f}")

        # Build clarification request
        clarification_request = self._build_clarification_request(
            instructions,
            context,
            confidence,
            options,
            errors
        )

        # Format the request for user
        formatted_request = self._format_for_user(clarification_request)

        # In a real implementation, this would interact with the UI
        # For now, we return the formatted request
        # The actual user input would come through WebSocket

        logger.info("📤 Clarification request prepared")
        logger.info(f"   Type: {clarification_request['type']}")
        logger.info(f"   Priority: {clarification_request['priority']}")

        return {
            "clarification_request": formatted_request,
            "request_type": clarification_request["type"],
            "awaiting_user_input": True,
            "timestamp": datetime.now().isoformat(),
            "confidence_level": confidence
        }

    def _build_clarification_request(
        self,
        instructions: str,
        context: dict,
        confidence: float,
        options: list,
        errors: list
    ) -> dict[str, Any]:
        """
        Build structured clarification request.

        Returns different request types based on the situation:
        - ambiguity: Multiple interpretations possible
        - error_guidance: Error requires user help
        - confirmation: Critical action needs confirmation
        - additional_info: More details needed
        """
        request = {
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence,
            "goal": context.get("goal", ""),
            "priority": "high" if confidence < 0.3 else "normal"
        }

        # Determine request type based on context
        if errors:
            request["type"] = "error_guidance"
            request["errors"] = errors
            request["message"] = self._build_error_guidance_message(errors)

        elif options:
            request["type"] = "ambiguity"
            request["options"] = options
            request["message"] = self._build_ambiguity_message(options, context)

        elif "confirm" in instructions.lower() or "critical" in instructions.lower():
            request["type"] = "confirmation"
            request["action"] = instructions
            request["message"] = self._build_confirmation_message(instructions, context)

        else:
            request["type"] = "additional_info"
            request["message"] = self._build_info_request_message(instructions, context)

        return request

    def _build_error_guidance_message(self, errors: list) -> str:
        """Build message for error guidance."""
        message_parts = [
            "## ⚠️ Error Encountered - Need Your Guidance",
            "",
            "I've encountered an error that requires your input to proceed:",
            ""
        ]

        # Add error details
        for i, error in enumerate(errors[:3], 1):  # Show max 3 errors
            if isinstance(error, dict):
                message_parts.append(f"**Error {i}:** {error.get('message', str(error))}")
                if "suggestion" in error:
                    message_parts.append(f"   Suggestion: {error['suggestion']}")
            else:
                message_parts.append(f"**Error {i}:** {error}")

        if len(errors) > 3:
            message_parts.append(f"*... and {len(errors) - 3} more errors*")

        message_parts.extend([
            "",
            "**How would you like me to proceed?**",
            "",
            "Options:",
            "1. Try a different approach",
            "2. Skip this step and continue",
            "3. Provide specific instructions to fix the error",
            "4. Abort the current task"
        ])

        return "\n".join(message_parts)

    def _build_ambiguity_message(self, options: list, context: dict) -> str:
        """Build message for ambiguous request."""
        goal = context.get("goal", "your request")

        message_parts = [
            "## 🤔 Multiple Interpretations Possible",
            "",
            f"I found multiple ways to interpret: **{goal}**",
            "",
            "Please select which option best matches your intent:",
            ""
        ]

        # Add numbered options
        for i, option in enumerate(options, 1):
            if isinstance(option, dict):
                title = option.get("title", f"Option {i}")
                description = option.get("description", "")
                message_parts.append(f"**{i}. {title}**")
                if description:
                    message_parts.append(f"   {description}")
            else:
                message_parts.append(f"**{i}.** {option}")
            message_parts.append("")

        message_parts.append("Please respond with the number of your choice (1, 2, 3, etc.)")

        return "\n".join(message_parts)

    def _build_confirmation_message(self, instructions: str, context: dict) -> str:
        """Build message for critical action confirmation."""
        goal = context.get("goal", "the requested action")

        message_parts = [
            "## ⚠️ Confirmation Required",
            "",
            "This action requires your explicit confirmation:",
            "",
            f"**Action:** {instructions}",
            f"**Original Goal:** {goal}",
            ""
        ]

        # Add warning if destructive
        if any(word in instructions.lower() for word in ["delete", "remove", "drop", "reset"]):
            message_parts.extend([
                "**⚠️ WARNING:** This is a potentially destructive operation!",
                ""
            ])

        message_parts.extend([
            "**Do you want to proceed?**",
            "",
            "- Type **'yes'** or **'y'** to confirm",
            "- Type **'no'** or **'n'** to cancel",
            "- Or provide alternative instructions"
        ])

        return "\n".join(message_parts)

    def _build_info_request_message(self, instructions: str, context: dict) -> str:
        """Build message for additional information request."""
        goal = context.get("goal", "your request")

        message_parts = [
            "## 📋 Additional Information Needed",
            "",
            f"To complete **{goal}**, I need more details:",
            "",
            instructions,
            ""
        ]

        # Add context-specific prompts
        if "architecture" in instructions.lower():
            message_parts.extend([
                "Please provide:",
                "- System requirements",
                "- Expected scale/performance needs",
                "- Technology preferences",
                "- Any existing constraints"
            ])

        elif "test" in instructions.lower():
            message_parts.extend([
                "Please provide:",
                "- Test scenarios to cover",
                "- Expected behavior",
                "- Edge cases to consider",
                "- Performance requirements"
            ])

        elif "fix" in instructions.lower() or "debug" in instructions.lower():
            message_parts.extend([
                "Please provide:",
                "- Steps to reproduce the issue",
                "- Expected vs actual behavior",
                "- Any error messages",
                "- What you've already tried"
            ])

        return "\n".join(message_parts)

    def _format_for_user(self, clarification_request: dict) -> str:
        """
        Format the clarification request for user display.

        This creates the final markdown-formatted message that will
        be shown to the user in the UI.
        """
        message = clarification_request["message"]

        # Add metadata footer
        footer_parts = [
            "",
            "---",
            "",
            f"*Confidence Level: {clarification_request['confidence']:.1%}*",
            f"*Request Type: {clarification_request['type'].replace('_', ' ').title()}*",
            f"*Priority: {clarification_request['priority'].title()}*"
        ]

        return message + "\n".join(footer_parts)

    async def process_user_response(
        self,
        user_input: str,
        request_type: str,
        original_context: dict
    ) -> dict[str, Any]:
        """
        Process user's response to clarification request.

        This method would be called when user provides input
        through the WebSocket connection.

        Args:
            user_input: The user's response
            request_type: Type of clarification that was requested
            original_context: Original workflow context

        Returns:
            Processed response ready for supervisor
        """
        logger.info(f"📥 Processing user response: {user_input[:100]}...")

        processed = {
            "user_input": user_input,
            "request_type": request_type,
            "processed_at": datetime.now().isoformat(),
            "requires_clarification": False  # Reset flag
        }

        # Process based on request type
        if request_type == "ambiguity":
            # Extract option number
            if user_input.strip().isdigit():
                processed["selected_option"] = int(user_input.strip())
                processed["interpretation"] = f"User selected option {processed['selected_option']}"
            else:
                # User provided custom instructions
                processed["custom_instructions"] = user_input
                processed["interpretation"] = "User provided custom instructions"

        elif request_type == "confirmation":
            # Check for yes/no
            lower_input = user_input.lower().strip()
            if lower_input in ["yes", "y", "confirm", "proceed"]:
                processed["confirmed"] = True
                processed["interpretation"] = "User confirmed the action"
            elif lower_input in ["no", "n", "cancel", "abort"]:
                processed["confirmed"] = False
                processed["interpretation"] = "User cancelled the action"
            else:
                processed["alternative_instructions"] = user_input
                processed["interpretation"] = "User provided alternative instructions"

        elif request_type == "error_guidance":
            # Parse user's error handling choice
            if user_input.strip().isdigit():
                choice = int(user_input.strip())
                choices = {
                    1: "try_different_approach",
                    2: "skip_and_continue",
                    3: "custom_fix",
                    4: "abort_task"
                }
                processed["error_handling"] = choices.get(choice, "custom_fix")
            else:
                processed["error_handling"] = "custom_fix"
                processed["custom_instructions"] = user_input

        elif request_type == "additional_info":
            # Store additional information
            processed["additional_info"] = user_input
            processed["interpretation"] = "User provided additional information"

        logger.info(f"✅ User response processed: {processed['interpretation']}")

        return processed


# ============================================================================
# Export
# ============================================================================

__all__ = ["HITLAgent"]