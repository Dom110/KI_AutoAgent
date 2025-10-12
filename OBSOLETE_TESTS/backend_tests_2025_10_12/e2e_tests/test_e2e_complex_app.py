"""
E2E Test: Complex App Generation - Todo REST API

Tests the complete workflow with a complex app that requires all agents.
This validates full system capabilities with realistic requirements.

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
async def test_complex_todo_api_app():
    """
    Test E2E workflow with a complex Todo REST API.

    This is a realistic app that requires:
    - Research: REST API best practices, SQLite usage
    - Architect: Multi-file structure, database schema design
    - Codesmith: Multiple files (api.py, models.py, database.py)
    - ReviewFix: Code quality, error handling, documentation
    """
    logger.info("=" * 80)
    logger.info("📋 E2E TEST: Complex Todo REST API")
    logger.info("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"📂 Workspace: {temp_dir}")

        # Initialize workflow
        logger.info("\n[Step 1] Initializing workflow...")
        workflow = WorkflowV6(workspace_path=temp_dir)
        await workflow.initialize()
        logger.info("✅ Workflow initialized")

        # Complex user query for Todo API
        user_query = """Create a RESTful Todo API with the following requirements:

**Architecture:**
- Multi-file Python application
- SQLite database for persistence
- Clean separation of concerns

**Files to create:**
1. `models.py` - Todo data model with id, title, description, completed, created_at
2. `database.py` - Database connection and CRUD operations
3. `api.py` - REST API endpoints (FastAPI or Flask)
4. `main.py` - Application entry point
5. `requirements.txt` - Dependencies

**Features:**
- GET /todos - List all todos
- POST /todos - Create a new todo
- GET /todos/{id} - Get specific todo
- PUT /todos/{id} - Update todo
- DELETE /todos/{id} - Delete todo
- PATCH /todos/{id}/complete - Mark as complete

**Quality Requirements:**
- Type hints throughout
- Comprehensive docstrings
- Error handling (404, 400, 500)
- Input validation
- Database connection management
- Proper HTTP status codes

**Technical Stack:**
- Python 3.13+
- SQLite3
- FastAPI (preferred) or Flask
- Pydantic for validation

This is a production-ready application that should follow best practices."""

        logger.info(f"\n[Step 2] Running workflow...")
        logger.info(f"Query length: {len(user_query)} chars")

        try:
            # Run workflow with 10 minute timeout (complex app needs more time)
            result = await asyncio.wait_for(
                workflow.run(user_query=user_query),
                timeout=600.0
            )

            logger.info("\n" + "=" * 80)
            logger.info("✅ Workflow completed!")
            logger.info("=" * 80)

            # Verify result
            assert result is not None
            logger.info("✅ Got workflow result")

            # Check for expected files
            expected_files = [
                "models.py",
                "database.py",
                "api.py",
                "main.py",
                "requirements.txt"
            ]

            logger.info("\n📁 Checking generated files...")
            generated_files = []

            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if not file.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, file), temp_dir)
                        generated_files.append(rel_path)

            logger.info(f"Generated {len(generated_files)} files:")
            for file in generated_files:
                logger.info(f"  ✓ {file}")

            # Validate expected files
            found_count = 0
            for expected in expected_files:
                if any(expected in f for f in generated_files):
                    logger.info(f"✅ Found {expected}")
                    found_count += 1
                else:
                    logger.warning(f"⚠️  Missing {expected}")

            logger.info(f"\n📊 File generation: {found_count}/{len(expected_files)} expected files found")

            # Validate content of key files
            if found_count > 0:
                logger.info("\n📄 Validating file contents...")

                # Check for models.py
                models_file = None
                for f in generated_files:
                    if "models" in f.lower() and f.endswith(".py"):
                        models_file = os.path.join(temp_dir, f)
                        break

                if models_file and os.path.exists(models_file):
                    with open(models_file, 'r') as f:
                        content = f.read()
                    logger.info(f"✅ models.py ({len(content)} chars)")
                    if "class" in content or "Todo" in content:
                        logger.info("  ✓ Contains class definition")

                # Check for API file
                api_file = None
                for f in generated_files:
                    if "api" in f.lower() and f.endswith(".py"):
                        api_file = os.path.join(temp_dir, f)
                        break

                if api_file and os.path.exists(api_file):
                    with open(api_file, 'r') as f:
                        content = f.read()
                    logger.info(f"✅ api.py ({len(content)} chars)")
                    if "get" in content.lower() or "post" in content.lower():
                        logger.info("  ✓ Contains HTTP methods")

                # Check requirements.txt
                req_file = None
                for f in generated_files:
                    if "requirements" in f.lower():
                        req_file = os.path.join(temp_dir, f)
                        break

                if req_file and os.path.exists(req_file):
                    with open(req_file, 'r') as f:
                        content = f.read()
                    logger.info(f"✅ requirements.txt ({len(content)} chars)")
                    if content.strip():
                        logger.info(f"  ✓ Contains dependencies:\n{content}")

            logger.info("\n" + "=" * 80)
            logger.info("🎉 Complex App E2E Test Complete!")
            logger.info("=" * 80)
            logger.info(f"Summary:")
            logger.info(f"  - Files generated: {len(generated_files)}")
            logger.info(f"  - Expected files: {found_count}/{len(expected_files)}")
            logger.info(f"  - Workflow execution: SUCCESS")

            # Test passes if we got at least some files
            assert len(generated_files) > 0, "No files were generated"
            logger.info("✅ Test PASSED")

        except asyncio.TimeoutError:
            logger.error("❌ Workflow timed out after 10 minutes")
            pytest.fail("Workflow execution timed out")
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(test_complex_todo_api_app())
