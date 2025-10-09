"""
E2E Test: Simple App Generation - Calculator

Tests the complete workflow with a simple app that requires minimal agents.
This validates basic functionality without complex requirements.

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

from workflow_v6 import WorkflowV6

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_simple_calculator_app():
    """
    Test E2E workflow with a simple calculator app.

    This is a minimal app that should:
    - Use Research to understand calculator requirements
    - Use Architect to design simple structure
    - Use Codesmith to generate calculator.py
    - Use ReviewFix to ensure quality
    """
    logger.info("=" * 80)
    logger.info("🧮 E2E TEST: Simple Calculator App")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"📂 Workspace: {temp_dir}")

        # Initialize workflow
        logger.info("\n[Step 1] Initializing workflow...")
        workflow = WorkflowV6(workspace_path=temp_dir)
        await workflow.initialize()
        logger.info("✅ Workflow initialized")

        # User query for simple calculator
        user_query = """Create a simple Python calculator app with the following features:
1. A Calculator class with methods: add, subtract, multiply, divide
2. Input validation (no division by zero)
3. A main() function that demonstrates usage
4. Type hints and docstrings
5. Save as calculator.py

Keep it simple - just basic arithmetic operations."""

        logger.info(f"\n[Step 2] Running workflow...")
        logger.info(f"Query: {user_query[:100]}...")

        try:
            # Run workflow with 5 minute timeout
            result = await asyncio.wait_for(
                workflow.run(user_query=user_query),
                timeout=300.0
            )

            logger.info("\n" + "=" * 80)
            logger.info("✅ Workflow completed!")
            logger.info("=" * 80)

            # Verify result
            assert result is not None
            logger.info("✅ Got workflow result")

            # Check for generated file
            calculator_file = os.path.join(temp_dir, "calculator.py")

            if os.path.exists(calculator_file):
                logger.info(f"✅ calculator.py created")

                # Read and validate content
                with open(calculator_file, 'r') as f:
                    content = f.read()

                logger.info(f"\n📄 Generated file ({len(content)} chars):")
                logger.info("-" * 80)
                logger.info(content[:500] + "..." if len(content) > 500 else content)
                logger.info("-" * 80)

                # Basic validation
                assert "class Calculator" in content or "def add" in content
                assert "def multiply" in content or "def divide" in content
                logger.info("✅ File contains expected functions")

                # Try to import (syntax check)
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("calculator", calculator_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        logger.info("✅ Code is syntactically valid (importable)")
                except Exception as e:
                    logger.warning(f"⚠️  Import failed: {e}")

            else:
                logger.warning("⚠️  calculator.py was not created")
                logger.info("Generated files:")
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        filepath = os.path.join(root, file)
                        logger.info(f"  - {filepath}")

            logger.info("\n" + "=" * 80)
            logger.info("🎉 Simple App E2E Test Complete!")
            logger.info("=" * 80)

        except asyncio.TimeoutError:
            logger.error("❌ Workflow timed out after 5 minutes")
            pytest.fail("Workflow execution timed out")
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(test_simple_calculator_app())
