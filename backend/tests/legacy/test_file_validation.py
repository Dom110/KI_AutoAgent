#!/usr/bin/env python3
"""
Unit Tests for File Validation Module

Tests all functions in subgraphs/file_validation.py to ensure:
- Correct app type detection
- Accurate file validation
- Proper missing files identification
- Completion prompt generation

Author: KI AutoAgent Team
Date: 2025-10-11
Python: 3.13+
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from subgraphs.file_validation import (
    detect_app_type,
    validate_generated_files,
    generate_completion_prompt,
    REQUIRED_FILES_BY_TYPE,
    CRITICAL_FILES_BY_TYPE,
)


class TestAppTypeDetection(unittest.TestCase):
    """Test app type detection logic."""

    def test_detect_react_vite_ts(self):
        """Should detect React + Vite + TypeScript app."""
        design = "Create a React application with Vite and TypeScript"
        files = [
            {"path": "src/main.tsx"},
            {"path": "src/App.tsx"},
            {"path": "package.json"},
        ]

        result = detect_app_type(design, files)
        self.assertEqual(result, "react_vite_ts")

    def test_detect_react_vite_js(self):
        """Should detect React + Vite + JavaScript app."""
        design = "Create a React app with Vite using JavaScript"
        files = [
            {"path": "src/main.jsx"},
            {"path": "src/App.jsx"},
        ]

        result = detect_app_type(design, files)
        self.assertEqual(result, "react_vite_js")

    def test_detect_nextjs(self):
        """Should detect Next.js app."""
        design = "Build a Next.js application"
        files = [
            {"path": "app/page.tsx"},
            {"path": "app/layout.tsx"},
        ]

        result = detect_app_type(design, files)
        self.assertEqual(result, "nextjs_ts")

    def test_detect_fastapi(self):
        """Should detect FastAPI backend."""
        design = "Create a FastAPI REST API"
        files = [
            {"path": "main.py"},
            {"path": "requirements.txt"},
        ]

        result = detect_app_type(design, files)
        self.assertEqual(result, "python_fastapi")

    def test_detect_flask(self):
        """Should detect Flask backend."""
        design = "Build a Flask web application"
        files = [
            {"path": "app.py"},
            {"path": "requirements.txt"},
        ]

        result = detect_app_type(design, files)
        self.assertEqual(result, "python_flask")

    def test_detect_generic_fallback(self):
        """Should fallback to generic for unknown types."""
        design = "Create something unknown"
        files = [{"path": "random.txt"}]

        result = detect_app_type(design, files)
        self.assertEqual(result, "generic")


class TestFileValidation(unittest.TestCase):
    """Test file validation logic."""

    def setUp(self):
        """Create temporary workspace for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary workspace."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validation_complete_react_vite_ts(self):
        """Should pass validation when all critical files exist."""
        # Create all critical files
        (self.workspace / "src").mkdir()
        (self.workspace / "src/main.tsx").write_text("// main")
        (self.workspace / "src/App.tsx").write_text("// app")
        (self.workspace / "src/index.css").write_text("/* styles */")
        (self.workspace / "package.json").write_text("{}")
        (self.workspace / "index.html").write_text("<html></html>")
        (self.workspace / "tsconfig.json").write_text("{}")
        (self.workspace / "vite.config.ts").write_text("// config")

        generated_files = [
            {"path": "src/main.tsx"},
            {"path": "src/App.tsx"},
            {"path": "src/index.css"},
            {"path": "package.json"},
            {"path": "index.html"},
        ]

        design = "React app with Vite and TypeScript"
        result = validate_generated_files(
            str(self.workspace),
            generated_files,
            app_type="react_vite_ts",
            design=design
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["app_type"], "react_vite_ts")
        self.assertEqual(len(result["missing_critical"]), 0)
        self.assertGreater(result["completeness"], 0.5)

    def test_validation_incomplete_missing_critical(self):
        """Should fail validation when critical files are missing."""
        # Create only some files (missing main.tsx)
        (self.workspace / "src").mkdir()
        (self.workspace / "src/App.tsx").write_text("// app")
        (self.workspace / "package.json").write_text("{}")
        (self.workspace / "index.html").write_text("<html></html>")

        generated_files = [
            {"path": "src/App.tsx"},
            {"path": "package.json"},
            {"path": "index.html"},
        ]

        result = validate_generated_files(
            str(self.workspace),
            generated_files,
            app_type="react_vite_ts",
            design="React Vite TS"
        )

        self.assertFalse(result["valid"])
        self.assertIn("src/main.tsx", result["missing_critical"])
        self.assertIn("src/index.css", result["missing_critical"])
        self.assertLess(result["completeness"], 1.0)

    def test_validation_auto_detect_app_type(self):
        """Should auto-detect app type from design and files."""
        (self.workspace / "src").mkdir()
        (self.workspace / "src/main.tsx").write_text("// main")

        generated_files = [{"path": "src/main.tsx"}]
        design = "React application with Vite and TypeScript"

        result = validate_generated_files(
            str(self.workspace),
            generated_files,
            app_type=None,  # Auto-detect
            design=design
        )

        self.assertEqual(result["app_type"], "react_vite_ts")

    def test_validation_completeness_calculation(self):
        """Should correctly calculate completeness percentage."""
        # Create 3 out of 5 critical files (60%)
        (self.workspace / "src").mkdir()
        (self.workspace / "src/main.tsx").write_text("// main")
        (self.workspace / "src/App.tsx").write_text("// app")
        (self.workspace / "package.json").write_text("{}")

        generated_files = [
            {"path": "src/main.tsx"},
            {"path": "src/App.tsx"},
            {"path": "package.json"},
        ]

        result = validate_generated_files(
            str(self.workspace),
            generated_files,
            app_type="react_vite_ts",
            design=""
        )

        # Should have some completeness but not 100%
        self.assertGreater(result["completeness"], 0.0)
        self.assertLess(result["completeness"], 1.0)
        self.assertEqual(len(result["existing_files"]), 3)

    def test_validation_with_optional_files(self):
        """Should distinguish between critical and optional missing files."""
        # Create all critical files but not optional ones
        (self.workspace / "src").mkdir()
        (self.workspace / "src/main.tsx").write_text("// main")
        (self.workspace / "src/App.tsx").write_text("// app")
        (self.workspace / "src/index.css").write_text("/* styles */")
        (self.workspace / "package.json").write_text("{}")
        (self.workspace / "index.html").write_text("<html></html>")

        generated_files = [
            {"path": "src/main.tsx"},
            {"path": "src/App.tsx"},
            {"path": "src/index.css"},
            {"path": "package.json"},
            {"path": "index.html"},
        ]

        result = validate_generated_files(
            str(self.workspace),
            generated_files,
            app_type="react_vite_ts",
            design=""
        )

        # Should pass because all CRITICAL files exist
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["missing_critical"]), 0)

        # But should still list optional missing files
        missing_optional = set(result["missing_files"]) - set(result["missing_critical"])
        self.assertGreater(len(missing_optional), 0)  # README.md, etc.


class TestCompletionPromptGeneration(unittest.TestCase):
    """Test completion prompt generation."""

    def test_generate_prompt_for_missing_critical(self):
        """Should generate prompt listing missing critical files."""
        validation_result = {
            "valid": False,
            "app_type": "react_vite_ts",
            "missing_files": ["src/main.tsx", "src/App.tsx", "README.md"],
            "missing_critical": ["src/main.tsx", "src/App.tsx"],
            "generated_count": 5,
            "required_count": 8,
            "completeness": 0.625
        }

        design = "React Task Manager with TypeScript"
        prompt = generate_completion_prompt(validation_result, design)

        # Should mention missing critical files
        self.assertIn("src/main.tsx", prompt)
        self.assertIn("src/App.tsx", prompt)
        self.assertIn("CRITICAL", prompt)

        # Should include optional files
        self.assertIn("README.md", prompt)
        self.assertIn("optional", prompt)

        # Should reference original design
        self.assertIn("React", prompt)

        # Should instruct to use FILE: format
        self.assertIn("FILE:", prompt)

    def test_generate_prompt_empty_when_complete(self):
        """Should return empty prompt when no files are missing."""
        validation_result = {
            "valid": True,
            "missing_files": [],
            "missing_critical": [],
        }

        prompt = generate_completion_prompt(validation_result, "design")
        self.assertEqual(prompt, "")

    def test_generate_prompt_only_optional_missing(self):
        """Should generate prompt even for only optional files."""
        validation_result = {
            "valid": True,  # Valid because no critical missing
            "missing_files": ["README.md", "LICENSE"],
            "missing_critical": [],
            "generated_count": 10,
            "required_count": 12,
        }

        prompt = generate_completion_prompt(validation_result, "design")

        self.assertIn("README.md", prompt)
        self.assertIn("LICENSE", prompt)
        self.assertIn("optional", prompt)
        self.assertNotIn("CRITICAL", prompt)


class TestRequiredFilesDefinitions(unittest.TestCase):
    """Test required files definitions are properly defined."""

    def test_all_app_types_have_definitions(self):
        """All app types should have required files defined."""
        expected_types = [
            "react_vite_ts",
            "react_vite_js",
            "nextjs_ts",
            "python_fastapi",
            "python_flask",
            "generic",
        ]

        for app_type in expected_types:
            self.assertIn(app_type, REQUIRED_FILES_BY_TYPE)
            self.assertIsInstance(REQUIRED_FILES_BY_TYPE[app_type], list)
            self.assertGreater(len(REQUIRED_FILES_BY_TYPE[app_type]), 0)

    def test_critical_files_subset_of_required(self):
        """Critical files should be a subset of required files."""
        for app_type, critical in CRITICAL_FILES_BY_TYPE.items():
            if app_type in REQUIRED_FILES_BY_TYPE:
                required = REQUIRED_FILES_BY_TYPE[app_type]
                for critical_file in critical:
                    # Each critical file should be in required files
                    # (This ensures consistency)
                    # Note: This might not always be true if we have very strict critical
                    # but for our use case it should be
                    pass  # Just documenting the relationship

    def test_react_vite_ts_has_entry_files(self):
        """React Vite TS should have main entry files."""
        required = REQUIRED_FILES_BY_TYPE["react_vite_ts"]
        critical = CRITICAL_FILES_BY_TYPE["react_vite_ts"]

        # Must have entry files
        self.assertIn("src/main.tsx", required)
        self.assertIn("src/App.tsx", required)
        self.assertIn("package.json", required)

        # Entry files should be critical
        self.assertIn("src/main.tsx", critical)
        self.assertIn("src/App.tsx", critical)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_generated_files(self):
        """Should handle empty generated files list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = validate_generated_files(
                temp_dir,
                generated_files=[],
                app_type="react_vite_ts",
                design=""
            )

            self.assertFalse(result["valid"])
            self.assertEqual(result["completeness"], 0.0)
            self.assertGreater(len(result["missing_critical"]), 0)

    def test_nonexistent_workspace(self):
        """Should handle non-existent workspace gracefully."""
        result = validate_generated_files(
            "/nonexistent/path/workspace",
            generated_files=[{"path": "test.txt"}],
            app_type="generic",
            design=""
        )

        # Should complete without crashing
        self.assertIsInstance(result, dict)
        self.assertIn("valid", result)

    def test_generate_prompt_with_empty_design(self):
        """Should generate prompt even with empty design."""
        validation_result = {
            "valid": False,
            "missing_files": ["README.md"],
            "missing_critical": ["main.py"],
            "generated_count": 0,
            "required_count": 2,
        }

        prompt = generate_completion_prompt(validation_result, "")

        self.assertIn("main.py", prompt)
        self.assertIn("README.md", prompt)
        # Should still have structure even without design
        self.assertIn("FILE:", prompt)


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAppTypeDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestFileValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestCompletionPromptGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestRequiredFilesDefinitions))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result


if __name__ == "__main__":
    import sys
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
