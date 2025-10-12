"""
Architect Response Parser

Extracts structured data from Architect LLM responses:
- Tech Stack: Technologies, frameworks, libraries, tools
- Patterns: Architectural patterns and best practices
- Components: System components and their responsibilities
- Data Flow: How data flows through the system

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_architect_response(llm_response: str) -> dict[str, Any]:
    """
    Parse structured architecture data from LLM response.

    Args:
        llm_response: Raw LLM response text

    Returns:
        {
            "tech_stack": ["React", "TypeScript", "Node.js", ...],
            "patterns": ["MVC", "Repository Pattern", ...],
            "components": [{"name": "...", "responsibility": "..."}, ...],
            "data_flow": str,
            "rationale": str
        }
    """
    logger.debug("Parsing architect LLM response...")

    result = {
        "tech_stack": [],
        "patterns": [],
        "components": [],
        "data_flow": "",
        "rationale": ""
    }

    # Parse Tech Stack section
    tech_stack = _extract_section_list(llm_response, "Tech Stack")
    if tech_stack:
        result["tech_stack"] = tech_stack
        logger.debug(f"Extracted {len(tech_stack)} tech stack items")

    # Alternative Tech Stack patterns
    if not result["tech_stack"]:
        tech_stack = _extract_section_list(llm_response, "Technology Stack")
        if tech_stack:
            result["tech_stack"] = tech_stack

    if not result["tech_stack"]:
        tech_stack = _extract_section_list(llm_response, "Technologies")
        if tech_stack:
            result["tech_stack"] = tech_stack

    # Parse Patterns section
    patterns = _extract_section_list(llm_response, "Patterns")
    if patterns:
        result["patterns"] = patterns
        logger.debug(f"Extracted {len(patterns)} architectural patterns")

    # Alternative Patterns patterns
    if not result["patterns"]:
        patterns = _extract_section_list(llm_response, "Architectural Patterns")
        if patterns:
            result["patterns"] = patterns

    if not result["patterns"]:
        patterns = _extract_section_list(llm_response, "Design Patterns")
        if patterns:
            result["patterns"] = patterns

    # Parse Components section
    components = _extract_components(llm_response)
    if components:
        result["components"] = components
        logger.debug(f"Extracted {len(components)} components")

    # Parse Data Flow section
    data_flow = _extract_section_text(llm_response, "Data Flow")
    if data_flow:
        result["data_flow"] = data_flow.strip()
        logger.debug(f"Extracted data flow description ({len(data_flow)} chars)")

    # Parse Rationale section
    rationale = _extract_section_text(llm_response, "Rationale")
    if rationale:
        result["rationale"] = rationale.strip()
        logger.debug(f"Extracted rationale ({len(rationale)} chars)")

    # Alternative Rationale patterns
    if not result["rationale"]:
        rationale = _extract_section_text(llm_response, "Reasoning")
        if rationale:
            result["rationale"] = rationale.strip()

    if not result["rationale"]:
        rationale = _extract_section_text(llm_response, "Why")
        if rationale:
            result["rationale"] = rationale.strip()

    logger.info(f"✅ Parsed architecture: {len(result['tech_stack'])} tech items, "
                f"{len(result['patterns'])} patterns, {len(result['components'])} components")

    return result


def _extract_section_list(text: str, section_name: str) -> list[str]:
    """
    Extract bulleted/numbered list from a section.

    Matches patterns like:
    ## Tech Stack
    - React
    - TypeScript
    - Node.js

    OR:

    **Tech Stack:**
    1. React
    2. TypeScript
    """
    # Try markdown heading patterns
    patterns = [
        rf"##\s+{section_name}\s*\n(.*?)(?=\n##|\Z)",  # ## Section
        rf"###\s+{section_name}\s*\n(.*?)(?=\n###|\n##|\Z)",  # ### Section
        rf"\*\*{section_name}:?\*\*\s*\n(.*?)(?=\n\*\*|\n##|\Z)",  # **Section:**
        rf"{section_name}:\s*\n(.*?)(?=\n[A-Z][^:]*:|\n##|\Z)",  # Section: (plain)
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            section_text = match.group(1)
            # Extract list items
            items = []

            # Bullet points (-, *, •)
            bullet_items = re.findall(r"^[\s]*[-*•]\s+(.+)$", section_text, re.MULTILINE)
            if bullet_items:
                items.extend([item.strip() for item in bullet_items])

            # Numbered lists (1., 2., etc.)
            if not items:
                numbered_items = re.findall(r"^[\s]*\d+\.\s+(.+)$", section_text, re.MULTILINE)
                if numbered_items:
                    items.extend([item.strip() for item in numbered_items])

            # Comma-separated (if no list format found)
            if not items and "," in section_text:
                comma_items = [item.strip() for item in section_text.split(",") if item.strip()]
                # Only use if reasonable (2-20 items)
                if 2 <= len(comma_items) <= 20:
                    items.extend(comma_items)

            if items:
                return items

    return []


def _extract_section_text(text: str, section_name: str) -> str:
    """
    Extract full text from a section.

    Returns the content between the section header and the next section.
    """
    # Try markdown heading patterns
    patterns = [
        rf"##\s+{section_name}\s*\n(.*?)(?=\n##|\Z)",  # ## Section
        rf"###\s+{section_name}\s*\n(.*?)(?=\n###|\n##|\Z)",  # ### Section
        rf"\*\*{section_name}:?\*\*\s*\n(.*?)(?=\n\*\*|\n##|\Z)",  # **Section:**
        rf"{section_name}:\s*\n(.*?)(?=\n[A-Z][^:]*:|\n##|\Z)",  # Section: (plain)
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            section_text = match.group(1).strip()
            if section_text:
                return section_text

    return ""


def _extract_components(text: str) -> list[dict[str, str]]:
    """
    Extract components with their responsibilities.

    Matches patterns like:
    ## Components
    - **ComponentName**: Does X, Y, Z
    - **AnotherComponent**: Handles A, B, C

    OR:

    ## Components
    1. ComponentName - Does X
    2. AnotherComponent - Handles Y
    """
    components = []

    # Extract Components section first
    component_section = _extract_section_text(text, "Components")
    if not component_section:
        component_section = _extract_section_text(text, "System Components")
    if not component_section:
        component_section = _extract_section_text(text, "Key Components")

    if not component_section:
        return []

    # Pattern 1: **Name**: Description
    bold_pattern = r"\*\*([^*]+)\*\*:\s*(.+?)(?=\n\*\*|\n-|\n\d+\.|\Z)"
    matches = re.findall(bold_pattern, component_section, re.DOTALL)
    if matches:
        for name, responsibility in matches:
            components.append({
                "name": name.strip(),
                "responsibility": responsibility.strip().replace("\n", " ")
            })
        return components

    # Pattern 2: - Name: Description or - Name - Description
    bullet_pattern = r"^[\s]*[-*•]\s+([^:\-]+)[\:\-]\s*(.+)$"
    matches = re.findall(bullet_pattern, component_section, re.MULTILINE)
    if matches:
        for name, responsibility in matches:
            components.append({
                "name": name.strip(),
                "responsibility": responsibility.strip()
            })
        return components

    # Pattern 3: 1. Name: Description
    numbered_pattern = r"^\d+\.\s+([^:\-]+)[\:\-]\s*(.+)$"
    matches = re.findall(numbered_pattern, component_section, re.MULTILINE)
    if matches:
        for name, responsibility in matches:
            components.append({
                "name": name.strip(),
                "responsibility": responsibility.strip()
            })
        return components

    return []


def parse_tech_stack_only(llm_response: str) -> list[str]:
    """
    Quick extraction of tech stack only.

    Args:
        llm_response: LLM response text

    Returns:
        List of technologies
    """
    tech_stack = _extract_section_list(llm_response, "Tech Stack")
    if tech_stack:
        return tech_stack

    tech_stack = _extract_section_list(llm_response, "Technology Stack")
    if tech_stack:
        return tech_stack

    tech_stack = _extract_section_list(llm_response, "Technologies")
    if tech_stack:
        return tech_stack

    return []


def parse_patterns_only(llm_response: str) -> list[str]:
    """
    Quick extraction of patterns only.

    Args:
        llm_response: LLM response text

    Returns:
        List of architectural patterns
    """
    patterns = _extract_section_list(llm_response, "Patterns")
    if patterns:
        return patterns

    patterns = _extract_section_list(llm_response, "Architectural Patterns")
    if patterns:
        return patterns

    patterns = _extract_section_list(llm_response, "Design Patterns")
    if patterns:
        return patterns

    return []


# Convenience exports
__all__ = [
    "parse_architect_response",
    "parse_tech_stack_only",
    "parse_patterns_only"
]
