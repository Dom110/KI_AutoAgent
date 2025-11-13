#!/usr/bin/env python3
"""
Supervisor Decision Debug Test
Tests the supervisor decision logic directly
"""

import asyncio
import sys
from pathlib import Path


async def test_supervisor_decision():
    """Test supervisor decision making directly."""
    
    print("\n" + "="*100)
    print("🧪 SUPERVISOR DECISION DEBUG TEST")
    print("="*100)
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    from backend.core.supervisor_mcp import create_supervisor_mcp
    from langgraph.types import Command
    
    # Create supervisor
    print("\n[1/3] Creating supervisor...")
    supervisor = create_supervisor_mcp(
        workspace_path="/tmp/test",
        session_id="test-123"
    )
    print("✅ Supervisor created")
    
    # Create initial state
    print("\n[2/3] Creating initial state...")
    state = {
        "messages": [],
        "goal": "List files",
        "user_query": "List files in current directory",
        "workspace_path": "/tmp/test",
        "session_id": "test-123",
        "last_agent": None,
        "iteration": 0,
        "is_self_invocation": False,
        "instructions": "",
        "research_context": None,
        "needs_research": False,
        "research_request": None,
        "architecture": None,
        "architecture_complete": False,
        "generated_files": None,
        "code_complete": False,
        "validation_results": None,
        "validation_passed": False,
        "issues": None,
        "user_response": None,
        "response_ready": False,
        "errors": [],
        "error_count": 0,
        "confidence": 0.5,
        "requires_clarification": False,
        "hitl_response": None,
        "awaiting_human": False,
    }
    print("✅ State created")
    
    # Call decide_next
    print("\n[3/3] Calling supervisor.decide_next()...")
    print("      Waiting for decision...")
    
    try:
        decision = await supervisor.decide_next(state)
        
        print("✅ Decision received!")
        print(f"\n📊 DECISION RESULT:")
        print(f"   Type: {type(decision).__name__}")
        print(f"   goto: {decision.goto}")
        print(f"   update: {decision.update if hasattr(decision, 'update') else 'None'}")
        
        # Check if Command
        if isinstance(decision, Command):
            print(f"✅ Decision is LangGraph Command")
            print(f"   goto value: {repr(decision.goto)}")
            
            # Check goto value
            valid_targets = ["research", "architect", "codesmith", "reviewfix", "responder", "hitl", "__end__"]
            if decision.goto in valid_targets:
                print(f"✅ goto target is VALID: {decision.goto}")
            else:
                print(f"❌ goto target is INVALID: {decision.goto}")
                print(f"   Valid targets: {valid_targets}")
        else:
            print(f"⚠️  Decision is NOT a Command: {type(decision)}")
        
        print("\n" + "="*100)
        print("✅ SUPERVISOR DECISION TEST PASSED")
        print("="*100)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*100)
        print("❌ SUPERVISOR DECISION TEST FAILED")
        print("="*100)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_supervisor_decision())
    sys.exit(0 if success else 1)
