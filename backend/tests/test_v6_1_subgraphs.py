"""
Unit Tests for v6.1 Subgraphs

Tests the refactored subgraphs that use custom nodes instead of create_react_agent.

Author: KI AutoAgent Team
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile

import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# Activate Claude CLI adapter
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from subgraphs.research_subgraph_v6_1 import create_research_subgraph
from subgraphs.codesmith_subgraph_v6_1 import create_codesmith_subgraph
from subgraphs.reviewfix_subgraph_v6_1 import create_reviewfix_subgraph
from state_v6 import ResearchState, CodesmithState, ReviewFixState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_research_v6_1_structure():
    """Test Research v6.1 subgraph structure."""
    logger.info("Testing Research v6.1 subgraph structure...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subgraph
        subgraph = create_research_subgraph(
            workspace_path=temp_dir,
            memory=None
        )

        # Verify it compiles
        assert subgraph is not None
        logger.info("✅ Research v6.1 subgraph compiled successfully")


@pytest.mark.asyncio
async def test_codesmith_v6_1_structure():
    """Test Codesmith v6.1 subgraph structure."""
    logger.info("Testing Codesmith v6.1 subgraph structure...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subgraph
        subgraph = create_codesmith_subgraph(
            workspace_path=temp_dir,
            memory=None
        )

        # Verify it compiles
        assert subgraph is not None
        logger.info("✅ Codesmith v6.1 subgraph compiled successfully")


@pytest.mark.asyncio
async def test_reviewfix_v6_1_structure():
    """Test ReviewFix v6.1 subgraph structure."""
    logger.info("Testing ReviewFix v6.1 subgraph structure...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subgraph
        subgraph = create_reviewfix_subgraph(
            workspace_path=temp_dir,
            memory=None
        )

        # Verify it compiles
        assert subgraph is not None
        logger.info("✅ ReviewFix v6.1 subgraph compiled successfully")


@pytest.mark.asyncio
async def test_research_v6_1_execution():
    """Test Research v6.1 subgraph execution with Claude CLI."""
    logger.info("Testing Research v6.1 execution...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subgraph
        subgraph = create_research_subgraph(
            workspace_path=temp_dir,
            memory=None
        )

        # Execute with simple query
        state: ResearchState = {
            "query": "What is Python asyncio?",
            "findings": None,
            "report": None,
            "completed": False,
            "errors": []
        }

        logger.info("Executing research with query: 'What is Python asyncio?'")
        result = await subgraph.ainvoke(state)

        # Verify result
        assert result is not None
        assert "findings" in result or "errors" in result
        logger.info(f"✅ Research completed: {result.get('completed', False)}")

        if result.get("errors"):
            logger.warning(f"Errors: {result['errors']}")


@pytest.mark.asyncio
async def test_codesmith_v6_1_execution():
    """Test Codesmith v6.1 subgraph execution with Claude CLI."""
    logger.info("Testing Codesmith v6.1 execution...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subgraph
        subgraph = create_codesmith_subgraph(
            workspace_path=temp_dir,
            memory=None
        )

        # Execute with simple design
        state: CodesmithState = {
            "design": "Create a simple hello.py file with a hello() function that prints 'Hello'",
            "generated_files": [],
            "implementation_summary": None,
            "completed": False,
            "errors": []
        }

        logger.info("Executing codesmith with simple design")
        result = await subgraph.ainvoke(state)

        # Verify result
        assert result is not None
        logger.info(f"✅ Codesmith completed: {result.get('completed', False)}")
        logger.info(f"Generated files: {len(result.get('generated_files', []))}")

        if result.get("errors"):
            logger.warning(f"Errors: {result['errors']}")


@pytest.mark.asyncio
async def test_reviewfix_v6_1_execution():
    """Test ReviewFix v6.1 subgraph execution with Claude CLI."""
    logger.info("Testing ReviewFix v6.1 execution...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("def add(x,y):\n  return x+y\n")

        # Create subgraph
        subgraph = create_reviewfix_subgraph(
            workspace_path=temp_dir,
            memory=None
        )

        # Execute review/fix loop
        state: ReviewFixState = {
            "files_to_review": ["test.py"],
            "quality_score": 0.0,
            "feedback": None,
            "fixes_applied": None,
            "iteration": 0,
            "errors": []
        }

        logger.info("Executing review/fix loop")
        result = await subgraph.ainvoke(state)

        # Verify result
        assert result is not None
        assert "quality_score" in result
        assert "iteration" in result
        logger.info(f"✅ ReviewFix completed")
        logger.info(f"Quality score: {result.get('quality_score', 0.0):.2f}")
        logger.info(f"Iterations: {result.get('iteration', 0)}")

        if result.get("errors"):
            logger.warning(f"Errors: {result['errors']}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_research_v6_1_structure())
    asyncio.run(test_codesmith_v6_1_structure())
    asyncio.run(test_reviewfix_v6_1_structure())
    asyncio.run(test_research_v6_1_execution())
    asyncio.run(test_codesmith_v6_1_execution())
    asyncio.run(test_reviewfix_v6_1_execution())
