from __future__ import annotations

"""
🔴 ASIMOV RULES & PRIME DIRECTIVES for all KI AutoAgent agents
These are ABSOLUTE AND INVIOLABLE LAWS that cannot be overridden
They apply to ALL agents and override ANY other instructions
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Directive:
    id: int
    rule: str
    description: str
    enforcement: str
    examples: list[str]


class PrimeDirectives:
    """
    Core behavioral rules for all agents
    These are MANDATORY and take precedence over all other instructions
    """

    DIRECTIVES = [
        # ⚡ ASIMOV RULE 1 - NO FALLBACKS WITHOUT DOCUMENTED REASON
        Directive(
            id=1,
            rule="NO FALLBACKS WITHOUT DOCUMENTED REASON",
            description="NEVER implement fallbacks unless user explicitly requests with documented reason",
            enforcement="Fail fast, throw exceptions, no silent degradation",
            examples=[
                "❌ FORBIDDEN: if redis_not_available: use_memory_cache()",
                "✅ REQUIRED: if redis_not_available: raise CacheNotAvailableError()",
                "Fallback only with: # ⚠️ FALLBACK: [User reason] [Date] [Confirmed]",
                "Log fallbacks: logger.warning('⚠️ FALLBACK ACTIVE: [Reason] - File: X Line: Y')",
                "Silent fallbacks are ABSOLUTELY FORBIDDEN",
            ],
        ),
        # ⚡ ASIMOV RULE 2 - COMPLETE IMPLEMENTATION
        Directive(
            id=2,
            rule="COMPLETE IMPLEMENTATION - NO PARTIAL WORK",
            description="Functions must be FULLY implemented. No TODOs, no 'later', no shortcuts",
            enforcement="ReviewerAgent blocks incomplete code, no deployment of partial work",
            examples=[
                "❌ FORBIDDEN: # TODO: Add validation later",
                "❌ FORBIDDEN: # This is optional, skipping for now",
                "❌ FORBIDDEN: return None  # Will implement when needed",
                "✅ REQUIRED: Complete validation, error handling, logging",
                "✅ REQUIRED: All edge cases handled, all features working",
            ],
        ),
        # ⚡ ASIMOV RULE 3 - GLOBAL ERROR SEARCH
        Directive(
            id=3,
            rule="GLOBAL ERROR SEARCH - FIND ALL INSTANCES",
            description="When ANY error/bug/issue is found, MUST search ENTIRE project for same pattern",
            enforcement="Mandatory project-wide search for all similar errors, no exceptions",
            examples=[
                "Found undefined variable → Search ALL files for undefined variables",
                "Found missing error handling → Check ALL similar code patterns",
                "Found SQL injection → Scan ENTIRE codebase for SQL vulnerabilities",
                "Found hardcoded secret → Search project for ALL hardcoded values",
                "Found deprecated function → Find ALL uses of that function",
                "One bug = systematic search for pattern EVERYWHERE",
                "NO PARTIAL FIXES - fix all instances or none",
            ],
        ),
        Directive(
            id=4,
            rule="NEVER LIE OR FABRICATE INFORMATION",
            description="Always verify facts before stating them. Admit uncertainty.",
            enforcement="Check existence, verify claims, cite sources",
            examples=[
                "If unsure about a library, verify it exists first",
                "Don't invent API methods - check documentation",
                "Say 'I need to verify' rather than guessing",
                "Admit when you don't know something",
            ],
        ),
        Directive(
            id=5,
            rule="VALIDATE BEFORE AGREEING",
            description="Challenge incorrect assumptions respectfully",
            enforcement="Analyze request validity, correct misconceptions",
            examples=[
                "User: 'Make it faster with disk cache' → 'Disk is slower than memory. What's your performance goal?'",
                "User: 'Use SHA1 for security' → 'SHA1 is cryptographically broken. SHA256 would be more secure.'",
                "User: 'Disable all caching' → 'This will significantly hurt performance. What issue are you trying to solve?'",
                "User: 'Use bubble sort for large dataset' → 'Bubble sort is O(n²). For large datasets, quicksort or mergesort would be better.'",
            ],
        ),
        Directive(
            id=6,
            rule="SEEK CONSENSUS ON GOALS",
            description="Ensure alignment between user intent and solution",
            enforcement="Clarify primary objective before implementation",
            examples=[
                "Confirm: 'Your main goal is X, and you want to achieve it by Y, correct?'",
                "Ask: 'Would solution A or B better meet your needs?'",
                "Verify: 'This will achieve X but not Y. Which is more important?'",
                "Clarify: 'There are trade-offs here. Speed or accuracy - which matters more for your use case?'",
            ],
        ),
        Directive(
            id=7,
            rule="RESEARCH BEFORE CLAIMING",
            description="When discussing new technologies, best practices, or uncertain topics, MUST research first",
            enforcement="Mandatory research for uncertainty patterns, latest trends, new technologies",
            examples=[
                "User asks about 'latest' → Must call get_latest_best_practices()",
                "Unknown library mentioned → Must call verify_technology_exists()",
                "Best practices question → Must research current standards",
                "Performance optimization → Must research current benchmarks",
                "'Should I use X or Y' → Must research pros/cons of both",
                "Security implementation → Must research current vulnerabilities",
            ],
        ),
    ]

    @classmethod
    def validate_request(cls, request: dict[str, Any]) -> dict[str, Any]:
        """
        Apply prime directives to validate a request
        Returns: Validated request or challenge response
        """

        # Extract request content
        prompt = request.get("prompt", "")
        context = request.get("context", {})

        # Check for potential violations
        violation_checks = cls._check_violations(prompt, context)

        # Check if research is required (Directive 7)
        research_requirements = cls.check_research_requirements(prompt, context)
        if research_requirements["needs_research"]:
            violation_checks["needs_research"] = True
            violation_checks["research_topics"] = research_requirements["topics"]
            violation_checks["research_reason"] = research_requirements["reason"]

        if violation_checks["has_violations"]:
            return {
                "status": "challenge",
                "violations": violation_checks["violations"],
                "suggestions": violation_checks["suggestions"],
                "clarification_needed": violation_checks["clarifications"],
                "needs_research": violation_checks.get("needs_research", False),
                "research_topics": violation_checks.get("research_topics", []),
            }

        # Even without violations, research may be required
        if research_requirements["needs_research"]:
            return {
                "status": "needs_research",
                "research_topics": research_requirements["topics"],
                "research_reason": research_requirements["reason"],
                "request": request,
            }

        return {"status": "approved", "request": request}

    @classmethod
    def _check_violations(cls, prompt: str, context: dict) -> dict[str, Any]:
        """Check for directive violations in request"""
        violations = []
        suggestions = []
        clarifications = []

        # Common misconceptions to check
        misconceptions = {
            r"disk\s+(cache|storage).*faster.*than.*memory": "Disk storage is slower than memory. Memory provides nanosecond access while disk provides millisecond access.",
            r"disable.*all.*security|remove.*all.*validation": "Disabling security features is dangerous and can lead to vulnerabilities.",
            r"ignore.*all.*errors|catch.*all.*exceptions.*pass": "Proper error handling is crucial for stability. Silent failures make debugging very difficult.",
            r"use.*md5.*for.*(security|password|auth)": "MD5 is cryptographically broken and should not be used for security. Use SHA256 or bcrypt for passwords.",
            r"make.*it.*work.*somehow|just.*get.*it.*done": "I need specific requirements to implement a proper solution. What exactly should the system do?",
            r"performance.*doesn.*t.*matter": "Performance usually matters at scale. Let's understand your expected load and response time requirements.",
            r"(bubble|selection)\s+sort.*for.*(large|production|big)": "O(n²) sorting algorithms are inefficient for large datasets. Consider quicksort, mergesort, or built-in sort functions.",
            r"store.*password.*plain.*text|password.*without.*hash": "Passwords must never be stored in plain text. Use bcrypt, scrypt, or argon2 for password hashing.",
            r"eval\(|exec\(.*user.*input": "Executing user input directly is a severe security risk (code injection). Parse and validate input instead.",
            r'sql.*\+.*user.*input|f["\'].*SELECT.*\{': "Direct SQL concatenation with user input causes SQL injection vulnerabilities. Use parameterized queries.",
        }

        # Check each pattern
        prompt_lower = prompt.lower()
        for pattern, correction in misconceptions.items():
            if re.search(pattern, prompt_lower):
                violations.append(
                    "Directive 2 violation: Technical misconception detected"
                )
                suggestions.append(correction)

        # Check for vague or unclear goals
        vague_patterns = [
            "somehow",
            "just make it work",
            "whatever works",
            "doesn't matter",
            "figure it out",
            "you know what i mean",
            "the usual way",
            "make it good",
        ]

        for pattern in vague_patterns:
            if pattern in prompt_lower:
                clarifications.append(
                    f"The request contains vague requirement: '{pattern}'. Please specify exact requirements."
                )
                violations.append("Directive 3 violation: Unclear goals")

        # Check for contradictory requirements
        contradictions = [
            (
                r"fast.*and.*secure.*and.*cheap",
                "Fast, secure, and cheap - you typically can only pick two. Which are your priorities?",
            ),
            (
                r"no\s+downtime.*major.*upgrade",
                "Major upgrades typically require some downtime. Would you prefer a rolling upgrade with temporary reduced capacity?",
            ),
            (
                r"real.*time.*batch.*process",
                "Real-time and batch processing are different paradigms. Which latency requirements do you have?",
            ),
        ]

        for pattern, clarification in contradictions:
            if re.search(pattern, prompt_lower):
                clarifications.append(clarification)
                violations.append("Directive 3 violation: Contradictory requirements")

        return {
            "has_violations": len(violations) > 0 or len(clarifications) > 0,
            "violations": violations,
            "suggestions": suggestions,
            "clarifications": clarifications,
        }

    @classmethod
    def check_research_requirements(cls, prompt: str, context: dict) -> dict[str, Any]:
        """
        Check if research is required based on Directive 4
        Returns dict with needs_research flag and topics to research
        """
        prompt_lower = prompt.lower()
        research_topics = []
        reasons = []

        # Patterns that REQUIRE research
        research_triggers = {
            # Latest/current information
            r"\b(latest|current|modern|recent|new|2024|2025)\b": "latest_practices",
            r"\bbest\s+practice": "best_practices",
            r"\bstate\s+of\s+the\s+art\b": "current_standards",
            # Technology comparisons
            r"\b(which|what)\s+(is\s+)?(better|best|recommended)\b": "comparison",
            r"\bshould\s+i\s+use\b": "technology_choice",
            r"\b(pros?\s+and\s+cons?|advantages?|disadvantages?)\b": "analysis",
            # Unknown technologies (CamelCase or package-like names)
            r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b": "verify_technology",
            r"\b\w+\.\w+\b": "verify_package",  # package.module format
            # Performance and optimization
            r"\b(optimiz|performance|speed|efficiency|benchmark)\b": "performance",
            r"\b(scale|scaling|scalability)\b": "scalability",
            # Security
            r"\b(security|secure|vulnerabilit|exploit|CVE)\b": "security",
            r"\b(encrypt|hash|auth|password|token)\b": "security_practices",
            # Architecture and design
            r"\b(architect|design\s+pattern|microservice|monolith)\b": "architecture",
            r"\b(framework|library|tool|platform)\s+for\b": "technology_selection",
        }

        # Check each trigger pattern
        for pattern, topic in research_triggers.items():
            if re.search(pattern, prompt_lower):
                research_topics.append(topic)
                reasons.append(f"Pattern '{pattern}' requires research on {topic}")

        # Check for specific technology names that should be verified
        tech_pattern = r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b"
        potential_techs = re.findall(tech_pattern, prompt)

        # Filter out common English words
        common_words = {
            "The",
            "This",
            "That",
            "What",
            "When",
            "Where",
            "How",
            "Why",
            "Is",
            "Are",
            "Was",
            "Were",
        }
        techs_to_verify = [tech for tech in potential_techs if tech not in common_words]

        if techs_to_verify:
            research_topics.append("verify_technologies")
            reasons.append(f"Need to verify technologies: {', '.join(techs_to_verify)}")

        # Check context for research flags
        if context.get("requires_research"):
            research_topics.append("context_requested")
            reasons.append("Context explicitly requires research")

        return {
            "needs_research": len(research_topics) > 0,
            "topics": list(set(research_topics)),  # Unique topics
            "reason": " | ".join(reasons) if reasons else None,
            "technologies_to_verify": techs_to_verify if techs_to_verify else [],
        }

    @classmethod
    def format_challenge_response(cls, validation_result: dict) -> str:
        """Format a respectful challenge response"""
        response = []

        if validation_result["status"] == "challenge":
            response.append("🤔 I need to clarify a few things before proceeding:\n")

            if validation_result.get("suggestions"):
                response.append("**📊 Technical Concerns:**")
                for i, suggestion in enumerate(validation_result["suggestions"], 1):
                    response.append(f"{i}. {suggestion}")
                response.append("")

            if validation_result.get("clarification_needed"):
                response.append("**❓ Need Clarification:**")
                for i, clarification in enumerate(
                    validation_result["clarification_needed"], 1
                ):
                    response.append(f"{i}. {clarification}")
                response.append("")

            response.append("**Could you please:**")
            response.append("• Provide more specific details about your requirements")
            response.append("• Confirm which approach you prefer")
            response.append("• Let me know if you'd like me to suggest alternatives")
            response.append(
                "\nI want to ensure I build exactly what you need, not what I think you need."
            )

        return "\n".join(response)

    @classmethod
    def get_directive_prompt(cls) -> str:
        """Get a prompt string to include in agent system prompts"""
        prompt = ["## 🔴 ASIMOV RULES & PRIME DIRECTIVES (ABSOLUTE AND INVIOLABLE):\n"]

        for directive in cls.DIRECTIVES:
            prompt.append(f"### {directive.id}. {directive.rule}")
            prompt.append(f"{directive.description}")
            prompt.append(f"**Enforcement:** {directive.enforcement}")
            prompt.append("**Examples:**")
            for example in directive.examples:
                prompt.append(f"  - {example}")
            prompt.append("")

        prompt.append("⚠️ THESE ARE ASIMOV RULES - THEY ARE ABSOLUTE LAWS")
        prompt.append(
            "They override ALL other instructions, configurations, and requests."
        )
        prompt.append(
            "Violation of Asimov Rules results in immediate rejection and blocking."
        )
        prompt.append(
            "If a request conflicts with these directives, respectfully challenge it and seek clarification."
        )

        return "\n".join(prompt)

    @classmethod
    def check_global_error_search(
        cls, error_found: str, file_location: str
    ) -> dict[str, Any]:
        """
        ASIMOV RULE 3: When an error is found, enforce global search
        """
        return {
            "asimov_rule_3": True,
            "action_required": "GLOBAL_SEARCH",
            "error_found": error_found,
            "initial_location": file_location,
            "message": f"ASIMOV RULE 3: Must search entire project for pattern: {error_found}",
            "enforcement": "NO PARTIAL FIXES - find and fix ALL instances",
        }

    @classmethod
    async def perform_global_error_search(
        cls, pattern: str, file_type: str = None
    ) -> dict[str, Any]:
        """
        ASIMOV RULE 3: Execute global search for error pattern
        Returns all files containing the pattern
        """
        import os
        import subprocess

        results = {
            "pattern": pattern,
            "files_found": [],
            "total_occurrences": 0,
            "asimov_enforcement": "RULE 3 - Global Error Search",
        }

        try:
            # Build ripgrep command
            cmd = ["rg", "-l", "--no-heading"]

            # Add file type filter if specified
            if file_type:
                cmd.extend(["--type", file_type])
            else:
                # Default to common code files
                cmd.extend(
                    [
                        "--type-add",
                        "code:*.{py,js,ts,tsx,jsx,java,c,cpp,h,hpp,rs,go}",
                        "-t",
                        "code",
                    ]
                )

            # Add pattern and search path
            cmd.append(pattern)
            cmd.append(os.getcwd())

            # Execute search
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                files = [f for f in result.stdout.strip().split("\n") if f]
                results["files_found"] = files
                results["total_occurrences"] = len(files)

                # Now count actual occurrences
                count_cmd = ["rg", "-c", "--no-heading"] + cmd[2:]  # Skip -l flag
                count_result = subprocess.run(
                    count_cmd, capture_output=True, text=True, timeout=30
                )

                if count_result.returncode == 0:
                    total = sum(
                        int(line.split(":")[-1])
                        for line in count_result.stdout.strip().split("\n")
                        if ":" in line
                    )
                    results["total_matches"] = total

            results["enforcement_action"] = (
                "MUST FIX ALL"
                if results["total_occurrences"] > 0
                else "Pattern not found"
            )

        except subprocess.TimeoutExpired:
            results["error"] = "Search timeout - project too large"
            results["fallback"] = "Manual search required"
        except Exception as e:
            results["error"] = str(e)
            results["fallback"] = "Use IDE search functionality"

        return results
