#!/usr/bin/env python3
"""
KI AutoAgent Server Startup Script with Port Management

This script:
1. Checks if the server is already running on port 8002
2. Automatically cleans up if needed (graceful kill, then force kill)
3. Validates all system requirements
4. Starts the server fresh

Usage:
    python start_server.py
    
    # Or with options:
    python start_server.py --port 8003 --no-cleanup
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# 🔒 STARTUP GUARD - Check environment FIRST!
venv_path = os.environ.get('VIRTUAL_ENV')
if not venv_path:
    print("\n" + "=" * 90)
    print("❌ CRITICAL ERROR: NOT RUNNING IN VIRTUAL ENVIRONMENT")
    print("=" * 90)
    print("\n✅ HOW TO FIX:")
    print("   1. cd /Users/dominikfoert/git/KI_AutoAgent")
    print("   2. source venv/bin/activate")
    print("   3. python start_server.py")
    print("\n" + "=" * 90 + "\n")
    sys.exit(1)

# ⚠️ LOAD ENVIRONMENT VARIABLES FIRST - BEFORE ANY DIAGNOSTICS!
print("🔄 Loading environment configuration...")
from dotenv import load_dotenv
home = Path.home()
env_file = home / ".ki_autoagent" / "config" / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)  # override=True ensures we use the .env values
    print(f"✅ Loaded API keys from: {env_file}")
else:
    print(f"⚠️  Environment file not found: {env_file}")

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.utils.health_check import (
    print_startup_header,
    SystemDiagnostics,
    Colors,
    print_port_status
)
from backend.utils.port_manager import ensure_port_available, PortManager
from backend.utils.error_handler import handle_startup_error, handle_critical_error
from backend.deprecation import DeprecationValidator, get_registry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def startup_sequence(port: int = 8002, auto_cleanup: bool = True):
    """
    Run the complete startup sequence before starting the server
    
    Args:
        port: Port to check/cleanup
        auto_cleanup: Whether to automatically kill existing processes
    
    Returns:
        True if startup sequence successful, False otherwise
    """
    
    print_startup_header()
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}🔄 STARTUP SEQUENCE INITIATED{Colors.END}\n")
    
    # Step 1: Check Python version
    print(f"{Colors.BOLD}Step 1: Checking Python Version...{Colors.END}")
    version = sys.version_info
    if version >= (3, 13, 8):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Requires 3.13.8+")
        return False
    print()
    
    # Step 2: Check environment
    print(f"{Colors.BOLD}Step 2: Checking Environment...{Colors.END}")
    home = Path.home()
    env_file = home / ".ki_autoagent" / "config" / ".env"
    
    if env_file.exists():
        print(f"   ✅ Environment file: {env_file}")
    else:
        print(f"   ❌ Environment file not found: {env_file}")
        handle_startup_error(
            f"Environment file not found at: {env_file}",
            suggestions=[
                f"Create the config directory: mkdir -p {env_file.parent}",
                f"Copy your .env template to: {env_file}",
                f"Add your API keys (OPENAI_API_KEY, etc.) to the .env file",
                "Run: python start_server.py again"
            ]
        )
        return False
    print()
    
    # Step 3: Check dependencies
    print(f"{Colors.BOLD}Step 3: Checking Dependencies...{Colors.END}")
    required_modules = [
        "fastapi",
        "uvicorn",
        "websockets",
        "langgraph",
        "langchain_openai",
        "pydantic",
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n   Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install -r backend/requirements.txt")
        handle_startup_error(
            f"Missing required packages: {', '.join(missing)}",
            suggestions=[
                "pip install -r backend/requirements.txt",
                "Verify virtual environment is activated: echo $VIRTUAL_ENV",
                "Try again: python start_server.py"
            ]
        )
        return False
    print()
    
    # Step 4: Check and cleanup port
    print(f"{Colors.BOLD}Step 4: Checking Port {port}...{Colors.END}")
    print_port_status(port=port)
    
    if auto_cleanup:
        print(f"{Colors.BOLD}Step 5: Cleaning up port if needed...{Colors.END}")
        # Run async cleanup in a temporary event loop
        loop = asyncio.new_event_loop()
        try:
            port_available = loop.run_until_complete(
                ensure_port_available(port=port, auto_cleanup=True, verbose=True)
            )
            if port_available:
                print(f"   ✅ Port {port} is available")
            else:
                print(f"   ❌ Could not cleanup port {port}")
                print(f"   Manual fix: kill -9 $(lsof -t -i:{port})")
                handle_startup_error(
                    f"Could not cleanup port {port}. Another process may be using it.",
                    suggestions=[
                        f"Kill existing process: kill -9 $(lsof -t -i:{port})",
                        f"Or use a different port: python start_server.py --port 8003",
                        "Then try again: python start_server.py"
                    ]
                )
                return False
        finally:
            loop.close()
        print()
    
    # Step 6: Run full diagnostics
    print(f"{Colors.BOLD}Step 6: Running Full Diagnostics...{Colors.END}")
    diag = SystemDiagnostics()
    # Run async diagnostics in a temporary event loop
    loop = asyncio.new_event_loop()
    try:
        success = loop.run_until_complete(diag.run_all_checks())
    finally:
        loop.close()
    print()
    
    # Step 7: Check for deprecated modules
    print(f"{Colors.BOLD}Step 7: Checking for Deprecated Modules...{Colors.END}")
    from backend.deprecation.registry import DeprecationSeverity
    
    validator = DeprecationValidator()
    registry = get_registry()
    summary = registry.get_summary()
    
    # Show deprecation summary
    if summary['total_deprecated'] > 0:
        print(f"   ℹ️  {summary['total_deprecated']} deprecated modules registered")
        print(f"      • CRITICAL: {summary['critical']} (blocks startup if loaded)")
        print(f"      • ERROR:    {summary['error']} (warns loudly)")
        print(f"      • WARNING:  {summary['warning']} (informational)")
    else:
        print(f"   ✅ No deprecated modules registered")
    
    # Install import hook to catch deprecated imports during startup
    validator.install_import_hook()
    print(f"   ✅ Import deprecation hook installed")
    print()
    
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL CHECKS PASSED - READY TO START SERVER{Colors.END}\n")
        return True
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ SOME CHECKS FAILED - FIX ERRORS BEFORE STARTING{Colors.END}\n")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="KI AutoAgent Server with Port Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py
  python start_server.py --port 8003
  python start_server.py --no-cleanup
        """
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Server port (default: 8002)"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't auto-cleanup existing processes on the port"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only run checks, don't start the server"
    )
    
    args = parser.parse_args()
    
    # Run startup sequence (synchronously)
    success = startup_sequence(
        port=args.port,
        auto_cleanup=not args.no_cleanup
    )
    
    if not success:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  STARTUP FAILED{Colors.END}")
        print(f"Please fix the errors above and try again.\n")
        handle_critical_error(
            "STARTUP_SEQUENCE_FAILED",
            "One or more startup checks failed. Review the error messages above for specific issues."
        )
        sys.exit(1)
    
    if args.check_only:
        print(f"{Colors.GREEN}✅ All checks passed!{Colors.END}\n")
        return
    
    # Start the server
    print(f"{Colors.CYAN}{Colors.BOLD}🚀 STARTING SERVER...{Colors.END}\n")
    print(f"    WebSocket: ws://localhost:{args.port}/ws/chat")
    print(f"    Health Check: http://localhost:{args.port}/health")
    print(f"    Diagnostics: http://localhost:{args.port}/diagnostics\n")
    
    try:
        # ✅ SET STARTUP MARKER - Indicates server started via script
        os.environ['KI_AUTOAGENT_STARTUP_SCRIPT'] = 'true'
        
        # ✅ SET SERVER ROOT - For workspace isolation checks
        os.environ['KI_AUTOAGENT_SERVER_ROOT'] = str(project_root.resolve())
        
        # Import and run the server
        from backend.api.server_v7_mcp import app
        import uvicorn
        
        # uvicorn.run() will create and manage its own event loop
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=args.port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Server interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Server error: {e}{Colors.END}")
        handle_critical_error(
            "SERVER_STARTUP_ERROR",
            f"An unexpected error occurred while starting the server:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Fatal error: {e}{Colors.END}\n")
        handle_critical_error(
            "FATAL_ERROR",
            f"An unexpected fatal error occurred:\n{str(e)}"
        )
        sys.exit(1)