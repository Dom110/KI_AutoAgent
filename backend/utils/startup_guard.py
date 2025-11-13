"""
🔒 Startup Guard - Enforce proper startup procedure

This module ensures:
1. Server MUST be started via `python start_server.py` (not direct execution)
2. Server MUST be run from virtual environment
3. All critical checks are performed

Author: KI AutoAgent v7.0
Date: 2025-11-03
"""

import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def check_startup_method():
    """
    Check if server was started via start_server.py
    
    Raises:
        SystemExit: If startup method is invalid
    """
    startup_marker = os.environ.get('KI_AUTOAGENT_STARTUP_SCRIPT')
    
    if startup_marker != 'true':
        print("\n" + "=" * 90)
        print("❌ CRITICAL ERROR: INVALID STARTUP METHOD")
        print("=" * 90)
        
        print("\n🚫 PROBLEM:")
        print("   ❌ Server was NOT started via start_server.py")
        print("   ❌ Critical startup checks were SKIPPED")
        print("   ❌ Port conflicts may occur")
        print("   ❌ System diagnostics were NOT performed")
        print("   ❌ Dependencies were NOT validated")
        
        print("\n✅ CORRECT STARTUP PROCEDURE:")
        print("\n   1. Activate virtual environment:")
        print("      source venv/bin/activate")
        print("\n   2. Start server using the startup script:")
        print("      python start_server.py")
        print("\n   3. (Optional) Use port 8003 instead:")
        print("      python start_server.py --port 8003")
        print("\n   4. (Optional) Only check configuration:")
        print("      python start_server.py --check-only")
        
        print("\n❌ WHAT NOT TO DO:")
        print("   ❌ python backend/api/server_v7_mcp.py          (BLOCKED!)")
        print("   ❌ python -m uvicorn backend.api.server_v7_mcp:app  (BLOCKED!)")
        print("   ❌ Running without venv                        (BLOCKED!)")
        
        print("\n" + "=" * 90)
        print("STARTUP REJECTED - Use: python start_server.py")
        print("=" * 90 + "\n")
        
        sys.exit(1)


def check_virtual_environment():
    """
    Check if running from virtual environment
    
    Raises:
        SystemExit: If not in virtual environment
    """
    venv_path = os.environ.get('VIRTUAL_ENV')
    
    if not venv_path:
        print("\n" + "=" * 90)
        print("❌ CRITICAL ERROR: NOT RUNNING IN VIRTUAL ENVIRONMENT")
        print("=" * 90)
        
        print("\n🚫 PROBLEM:")
        print("   ❌ Python is running WITHOUT virtual environment")
        print("   ❌ This causes dependency conflicts")
        print("   ❌ May crash with missing modules")
        
        print("\n✅ HOW TO FIX:")
        print("\n   1. Go to project root:")
        print("      cd /Users/dominikfoert/git/KI_AutoAgent")
        print("\n   2. Activate virtual environment:")
        print("      source venv/bin/activate")
        print("\n   3. Verify activation (should show (venv) in prompt):")
        print("      # You should see: (venv) $ ")
        print("\n   4. Then start the server:")
        print("      python start_server.py")
        
        print("\n" + "=" * 90)
        print("STARTUP REJECTED - Activate venv first")
        print("=" * 90 + "\n")
        
        sys.exit(1)


def check_project_root():
    """
    Check if running from project root
    
    Raises:
        SystemExit: If not in project root
    """
    project_root = Path(__file__).parent.parent.parent  # backend/utils/startup_guard.py -> KI_AutoAgent
    
    if not (project_root / "start_server.py").exists():
        print("\n" + "=" * 90)
        print("❌ CRITICAL ERROR: NOT IN PROJECT ROOT")
        print("=" * 90)
        
        print("\n🚫 PROBLEM:")
        print(f"   ❌ Project root not found at: {project_root}")
        print(f"   ❌ Missing start_server.py")
        
        print("\n✅ HOW TO FIX:")
        print("\n   1. Change to project directory:")
        print("      cd /Users/dominikfoert/git/KI_AutoAgent")
        print("\n   2. Verify start_server.py exists:")
        print("      ls -la start_server.py")
        print("\n   3. Then start the server:")
        print("      python start_server.py")
        
        print("\n" + "=" * 90)
        print("STARTUP REJECTED - Run from project root")
        print("=" * 90 + "\n")
        
        sys.exit(1)


def run_all_checks():
    """
    Run all startup checks
    
    Raises:
        SystemExit: If any check fails
    """
    check_virtual_environment()
    check_project_root()
    check_startup_method()
    
    logger.info("✅ All startup checks passed!")