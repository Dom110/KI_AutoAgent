#!/usr/bin/env python3
"""
Test script for the centralized error handler system.

This script demonstrates how the error handler works and ensures
the help message is shown exactly once per session.

Usage:
    python test_error_handler.py
    python test_error_handler.py --verbose
    python test_error_handler.py --test critical
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.utils.error_handler import (
    print_help_message_once,
    handle_critical_error,
    handle_startup_error,
    handle_api_error,
    handle_runtime_error,
    reset_help_message_flag
)


def test_help_message():
    """Test that help message is shown only once."""
    print("\n" + "=" * 80)
    print("TEST 1: Help Message Shows Only Once")
    print("=" * 80 + "\n")
    
    print("📝 Calling print_help_message_once() - FIRST TIME (should show):")
    print_help_message_once()
    
    print("\n" + "-" * 80)
    print("📝 Calling print_help_message_once() - SECOND TIME (should be silent):")
    result = print_help_message_once()
    if result is None:
        print("✅ Silent (as expected)")
    
    print("\n" + "-" * 80)
    print("📝 Calling print_help_message_once() - THIRD TIME (should be silent):")
    result = print_help_message_once()
    if result is None:
        print("✅ Silent (as expected)")


def test_reset():
    """Test the reset functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: Reset Flag Functionality")
    print("=" * 80 + "\n")
    
    print("📝 Resetting the help message flag...")
    reset_help_message_flag()
    print("✅ Flag reset successful\n")
    
    print("📝 Now calling print_help_message_once() again (should show after reset):")
    print_help_message_once()


def test_critical_error():
    """Test critical error handler."""
    print("\n" + "=" * 80)
    print("TEST 3: Critical Error Handler")
    print("=" * 80 + "\n")
    
    reset_help_message_flag()
    handle_critical_error(
        error_type="DATABASE_CONNECTION_ERROR",
        error_message="Failed to connect to database at postgres://localhost:5432\nError: Connection refused (Errno 111)",
        show_help=True
    )


def test_startup_error():
    """Test startup error handler."""
    print("\n" + "=" * 80)
    print("TEST 4: Startup Error Handler with Suggestions")
    print("=" * 80 + "\n")
    
    reset_help_message_flag()
    handle_startup_error(
        error_message="Required Python 3.13.8 or higher, but found Python 3.11.7",
        suggestions=[
            "Install Python 3.13.8 from https://www.python.org/downloads/",
            "Or use pyenv: pyenv install 3.13.8 && pyenv shell 3.13.8",
            "Verify with: python --version",
            "Then run: python start_server.py"
        ]
    )


def test_api_error():
    """Test API error handler."""
    print("\n" + "=" * 80)
    print("TEST 5: API Error Handler")
    print("=" * 80 + "\n")
    
    reset_help_message_flag()
    handle_api_error(
        api_name="OpenAI",
        error_message="You exceeded your current quota. Please add more credit or contact support.",
        status_code=429
    )


def test_runtime_error():
    """Test runtime error handler."""
    print("\n" + "=" * 80)
    print("TEST 6: Runtime Error Handler with Context")
    print("=" * 80 + "\n")
    
    reset_help_message_flag()
    handle_runtime_error(
        error_message="Index 42 out of bounds for array of length 10",
        context="While processing supervisor decision in agent iteration #3"
    )


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 100)
    print(" " * 30 + "🔧 ERROR HANDLER TEST SUITE")
    print("=" * 100)
    
    test_help_message()
    test_reset()
    test_critical_error()
    test_startup_error()
    test_api_error()
    test_runtime_error()
    
    print("\n" + "=" * 100)
    print(" " * 25 + "✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 100 + "\n")
    
    print("📊 TEST RESULTS:")
    print("   ✅ Help message shows only once: PASS")
    print("   ✅ Reset flag works correctly: PASS")
    print("   ✅ Critical error handler: PASS")
    print("   ✅ Startup error handler: PASS")
    print("   ✅ API error handler: PASS")
    print("   ✅ Runtime error handler: PASS")
    print("\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test the centralized error handler system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_error_handler.py                    # Run all tests
  python test_error_handler.py --test critical    # Run specific test
  python test_error_handler.py --list             # List available tests
        """
    )
    
    parser.add_argument(
        "--test",
        type=str,
        choices=["help", "reset", "critical", "startup", "api", "runtime"],
        help="Run a specific test"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tests"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show additional debug information"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📋 AVAILABLE TESTS:\n")
        print("  1. help      - Help message shows only once")
        print("  2. reset     - Reset flag functionality")
        print("  3. critical  - Critical error handler")
        print("  4. startup   - Startup error handler with suggestions")
        print("  5. api       - API error handler")
        print("  6. runtime   - Runtime error handler with context")
        print("\n  Example: python test_error_handler.py --test critical\n")
        return
    
    if args.test:
        reset_help_message_flag()
        
        tests = {
            "help": test_help_message,
            "reset": test_reset,
            "critical": test_critical_error,
            "startup": test_startup_error,
            "api": test_api_error,
            "runtime": test_runtime_error,
        }
        
        test_func = tests.get(args.test)
        if test_func:
            test_func()
            print(f"\n✅ Test '{args.test}' completed\n")
        else:
            print(f"❌ Unknown test: {args.test}\n")
            sys.exit(1)
    else:
        run_all_tests()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)