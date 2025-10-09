#!/usr/bin/env python3
"""
E2E Test: Asimov Rule 3 - Global Error Search

Tests the global error search functionality:
1. Search for error patterns across entire workspace
2. Find ALL instances (not just one)
3. Ripgrep integration (with Python fallback)
4. Multi-file pattern detection

Expected behavior:
- Finds ALL instances of an error pattern
- Works with ripgrep (fast) and Python fallback (slow but reliable)
- Returns structured results with file paths and line numbers
- Handles regex patterns and literal strings

Debug mode: All logs enabled for troubleshooting

Author: KI AutoAgent Team
Created: 2025-10-09
Phase: 1.2 - Asimov Rule 3 Implementation
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)


async def test_ripgrep_search():
    """Test 1: Search with ripgrep (fast path)"""
    logger.info("=" * 80)
    logger.info("TEST 1: Ripgrep Global Search")
    logger.info("=" * 80)

    try:
        from security.asimov_rules import perform_global_error_search

        # Create test workspace with intentional errors
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            logger.info(f"📁 Created test workspace: {workspace}")

            # Create test files with typo "databse_connection" (should be "database_connection")
            # Note: Comments don't contain the typo to get accurate code-only match count
            test_files = {
                "api.py": """
def get_users():
    # TYPO: should be database_connection
    result = databse_connection.execute("SELECT * FROM users")
    return result
""",
                "models.py": """
class User:
    def save(self):
        # CORRECT usage
        database_connection.execute("INSERT INTO users VALUES (?)", self.data)

    def delete(self):
        # TYPO in code below
        databse_connection.execute("DELETE FROM users WHERE id=?", self.id)
""",
                "utils.py": """
def init_db():
    # CORRECT usage
    database_connection = connect()
    return database_connection

def close_db():
    # TYPO in code below
    databse_connection.close()
"""
            }

            # Write test files
            for filename, content in test_files.items():
                file_path = workspace / filename
                file_path.write_text(content)
                logger.debug(f"   Created: {filename}")

            # Search for the typo pattern
            pattern = "databse_connection"
            logger.info(f"🔍 Searching for pattern: '{pattern}'")

            result = await perform_global_error_search(
                workspace_path=str(workspace),
                error_pattern=pattern,
                file_extensions=[".py"]
            )

            # Validate results
            logger.info(f"📊 Search results:")
            logger.info(f"   Total matches: {result['total_matches']}")
            logger.info(f"   Files: {result['files']}")
            logger.info(f"   Pattern: {result['search_pattern']}")

            # Expected: 3 instances of "databse_connection" across 3 files
            assert result["total_matches"] == 3, f"Expected 3 matches, got {result['total_matches']}"
            assert len(result["files"]) == 3, f"Expected 3 files, got {len(result['files'])}"

            # Check each match
            logger.info(f"🔎 Match details:")
            for match in result["matches"]:
                logger.info(f"   {match['file']}:{match['line']} - {match['content'][:60]}...")

            # Verify expected files are in results
            expected_files = {"api.py", "models.py", "utils.py"}
            actual_files = set(result["files"])
            assert expected_files == actual_files, f"File mismatch: expected {expected_files}, got {actual_files}"

            logger.info("✅ Ripgrep search successful!")
            return True

    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}", exc_info=True)
        return False


async def test_python_fallback():
    """Test 2: Python fallback when ripgrep not available"""
    logger.info("=" * 80)
    logger.info("TEST 2: Python Fallback Global Search")
    logger.info("=" * 80)

    try:
        from security.asimov_rules import _python_global_search

        # Create test workspace
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            logger.info(f"📁 Created test workspace: {workspace}")

            # Create test files
            test_files = {
                "config.py": "API_KEY = 'hardcoded_secret_123'",
                "settings.py": "DATABASE_PASSWORD = 'hardcoded_secret_456'",
                "auth.py": "TOKEN = 'hardcoded_secret_789'"
            }

            for filename, content in test_files.items():
                (workspace / filename).write_text(content)

            # Search for hardcoded secrets pattern
            pattern = "hardcoded_secret"
            logger.info(f"🔍 Searching for pattern: '{pattern}'")

            result = await _python_global_search(
                workspace_path=str(workspace),
                error_pattern=pattern,
                file_extensions=[".py"]
            )

            # Validate
            logger.info(f"📊 Search results:")
            logger.info(f"   Total matches: {result['total_matches']}")
            logger.info(f"   Files: {result['files']}")

            assert result["total_matches"] == 3, f"Expected 3 matches, got {result['total_matches']}"
            assert len(result["files"]) == 3, f"Expected 3 files, got {len(result['files'])}"

            logger.info("✅ Python fallback successful!")
            return True

    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}", exc_info=True)
        return False


async def test_regex_patterns():
    """Test 3: Regex pattern search"""
    logger.info("=" * 80)
    logger.info("TEST 3: Regex Pattern Search")
    logger.info("=" * 80)

    try:
        from security.asimov_rules import perform_global_error_search

        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            logger.info(f"📁 Created test workspace: {workspace}")

            # Create files with various TODO patterns
            test_files = {
                "feature1.py": """
# TODO: Implement this function
def process_data():
    pass

# FIXME: This is broken
def broken_function():
    pass
""",
                "feature2.py": """
# TODO: Add error handling
def save_user():
    user.save()
""",
                "feature3.py": """
# No TODOs here
def working_function():
    return True
"""
            }

            for filename, content in test_files.items():
                (workspace / filename).write_text(content)

            # Search for TODO pattern (regex)
            pattern = r"#\s*TODO"
            logger.info(f"🔍 Searching for regex pattern: '{pattern}'")

            result = await perform_global_error_search(
                workspace_path=str(workspace),
                error_pattern=pattern,
                file_extensions=[".py"]
            )

            logger.info(f"📊 Search results:")
            logger.info(f"   Total matches: {result['total_matches']}")
            logger.info(f"   Files: {result['files']}")

            # Expected: 2 TODO comments
            assert result["total_matches"] == 2, f"Expected 2 TODOs, got {result['total_matches']}"
            assert len(result["files"]) == 2, f"Expected 2 files with TODOs, got {len(result['files'])}"

            logger.info("✅ Regex pattern search successful!")
            return True

    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}", exc_info=True)
        return False


async def test_multifile_consistency():
    """Test 4: Find inconsistent naming across multiple files"""
    logger.info("=" * 80)
    logger.info("TEST 4: Multi-file Consistency Check")
    logger.info("=" * 80)

    try:
        from security.asimov_rules import perform_global_error_search

        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            logger.info(f"📁 Created test workspace: {workspace}")

            # Create files with inconsistent variable naming
            test_files = {
                "file1.py": "user_id = 123",  # Correct: snake_case
                "file2.py": "userId = 456",   # Inconsistent: camelCase
                "file3.py": "user_id = 789",  # Correct: snake_case
                "file4.py": "userId = 999"    # Inconsistent: camelCase
            }

            for filename, content in test_files.items():
                (workspace / filename).write_text(content)

            # Search for camelCase pattern (inconsistent)
            pattern = "userId"
            logger.info(f"🔍 Searching for inconsistent pattern: '{pattern}'")

            result = await perform_global_error_search(
                workspace_path=str(workspace),
                error_pattern=pattern,
                file_extensions=[".py"]
            )

            logger.info(f"📊 Search results:")
            logger.info(f"   Total matches: {result['total_matches']}")
            logger.info(f"   Files: {result['files']}")

            # Expected: 2 files using camelCase (inconsistent)
            assert result["total_matches"] == 2, f"Expected 2 camelCase instances, got {result['total_matches']}"
            assert "file2.py" in result["files"], "Should find file2.py"
            assert "file4.py" in result["files"], "Should find file4.py"

            # Now search for correct pattern
            pattern2 = "user_id"
            logger.info(f"🔍 Searching for correct pattern: '{pattern2}'")

            result2 = await perform_global_error_search(
                workspace_path=str(workspace),
                error_pattern=pattern2,
                file_extensions=[".py"]
            )

            logger.info(f"📊 Correct pattern results:")
            logger.info(f"   Total matches: {result2['total_matches']}")
            logger.info(f"   Files: {result2['files']}")

            assert result2["total_matches"] == 2, "Should find 2 snake_case instances"

            logger.info("✅ Multi-file consistency check successful!")
            return True

    except Exception as e:
        logger.error(f"❌ Test 4 failed: {e}", exc_info=True)
        return False


async def test_no_matches():
    """Test 5: Pattern not found (should return empty results)"""
    logger.info("=" * 80)
    logger.info("TEST 5: No Matches Found")
    logger.info("=" * 80)

    try:
        from security.asimov_rules import perform_global_error_search

        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "test.py").write_text("def hello(): return 'world'")

            pattern = "nonexistent_pattern_xyz123"
            result = await perform_global_error_search(
                workspace_path=str(workspace),
                error_pattern=pattern,
                file_extensions=[".py"]
            )

            logger.info(f"📊 Search results:")
            logger.info(f"   Total matches: {result['total_matches']}")

            assert result["total_matches"] == 0, "Should find 0 matches"
            assert len(result["files"]) == 0, "Should have no files"
            assert result["matches"] == [], "Matches list should be empty"

            logger.info("✅ No matches test successful!")
            return True

    except Exception as e:
        logger.error(f"❌ Test 5 failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Asimov Rule 3 (Global Error Search) E2E Tests")
    logger.info(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if ripgrep is available
    try:
        import subprocess
        subprocess.run(["rg", "--version"], capture_output=True, check=True)
        logger.info("✅ ripgrep is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("⚠️  ripgrep is NOT available - will use Python fallback")

    # Run tests
    results = {}

    results["test_1_ripgrep"] = await test_ripgrep_search()
    results["test_2_python_fallback"] = await test_python_fallback()
    results["test_3_regex"] = await test_regex_patterns()
    results["test_4_consistency"] = await test_multifile_consistency()
    results["test_5_no_matches"] = await test_no_matches()

    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("-" * 80)
    logger.info(f"Total: {total_tests} tests")
    logger.info(f"Passed: {passed_tests} tests")
    logger.info(f"Failed: {failed_tests} tests")

    if failed_tests == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"❌ {failed_tests} TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
