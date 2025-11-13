#!/usr/bin/env python3
"""
🔍 SUPERVISOR DECISION TRACING TEST

This test tracks what the supervisor decides and what state updates 
it sends back after each agent execution.
"""

import asyncio
import sys
import logging
from pathlib import Path
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supervisor_tracing")

sys.path.insert(0, str(Path(__file__).parent))

from backend.workflow_v7_mcp import SupervisorState
from backend.core.supervisor_mcp import create_supervisor_mcp
from backend.utils.mcp_manager import get_mcp_manager


async def test_supervisor_decisions():
    """Test supervisor routing and state updates"""
    
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "SUPERVISOR DECISION TRACING TEST" + " "*21 + "║")
    print("║" + " "*12 + "Track what supervisor decides and what state it updates" + " "*1 + "║")
    print("╚" + "="*68 + "╝\n")
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        logger.info(f"📁 Using temp workspace: {tmpdir}")
        
        # Create a simple project structure
        Path(tmpdir).joinpath("src").mkdir()
        Path(tmpdir).joinpath("requirements.txt").write_text("fastapi\n")
        Path(tmpdir).joinpath("src/main.py").write_text("print('test')\n")
        
        # Initialize MCP manager
        logger.info("🔧 Initializing MCP manager...")
        mcp = get_mcp_manager(workspace_path=tmpdir)
        await mcp.initialize()
        
        # Create supervisor
        logger.info("🎯 Creating Supervisor MCP...")
        supervisor = create_supervisor_mcp(workspace_path=tmpdir, session_id="trace-001")
        
        # Initial state
        state: SupervisorState = {
            "messages": [],
            "goal": "Create a simple FastAPI app",
            "user_query": "Build an API with FastAPI",
            "workspace_path": tmpdir,
            "session_id": "trace-001",
            "last_agent": None,
            "iteration": 0,
            "is_self_invocation": False,
            "instructions": "Create a FastAPI app with basic endpoints",
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
        }
        
        print("\n" + "="*70)
        print("📊 ITERATION 1: Initial decision")
        print("="*70)
        
        # Get initial decision from supervisor
        logger.info("🤖 Asking supervisor for initial decision...")
        command = await supervisor.decide_next(state)
        
        print(f"✅ Supervisor decision: goto='{command.goto}'")
        print(f"   Update keys: {list(command.update.keys()) if command.update else 'None'}")
        
        if command.update:
            for key, value in command.update.items():
                if value is None:
                    print(f"   - {key}: None")
                elif isinstance(value, dict):
                    print(f"   - {key}: dict({len(value)} keys)")
                elif isinstance(value, list):
                    print(f"   - {key}: list({len(value)} items)")
                else:
                    print(f"   - {key}: {str(value)[:60]}")
        
        # Merge the update
        state = {**state, **command.update} if command.update else state
        
        # Now simulate what happens if research agent returns data
        print("\n" + "="*70)
        print("📊 SIMULATING: Research Agent returns data")
        print("="*70)
        
        # Get MCP result from research agent
        logger.info("📡 Calling Research Agent MCP...")
        research_result = await mcp.call(
            server="research_agent",
            tool="research",
            arguments={
                "instructions": "Analyze workspace",
                "workspace_path": tmpdir,
                "error_info": []
            }
        )
        
        # Extract data like workflow does
        import json
        content = research_result.get("content", [])
        if content and len(content) > 0:
            research_data = json.loads(content[0].get("text", "{}"))
            print(f"✅ Research returned data: {list(research_data.keys())}")
        else:
            research_data = {}
            print(f"❌ Research returned no data")
        
        # Simulate what research node does: update state with MCP result
        research_update = {
            "research_context": research_data,
            "last_agent": "research"
        }
        state = {**state, **research_update}
        print(f"   State updated with research data")
        print(f"   state['research_context'] now has keys: {list(state['research_context'].keys()) if state['research_context'] else 'None'}")
        
        # Now ask supervisor what to do next
        print("\n" + "="*70)
        print("📊 ITERATION 2: After research agent completes")
        print("="*70)
        
        state["iteration"] = 1
        logger.info("🤖 Asking supervisor for next decision...")
        command = await supervisor.decide_next(state)
        
        print(f"✅ Supervisor decision: goto='{command.goto}'")
        print(f"   Update keys: {list(command.update.keys()) if command.update else 'None'}")
        
        if command.update:
            for key, value in command.update.items():
                if value is None:
                    print(f"   - {key}: None")
                elif isinstance(value, dict):
                    print(f"   - {key}: dict({len(value)} keys)")
                elif isinstance(value, list):
                    print(f"   - {key}: list({len(value)} items)")
                else:
                    print(f"   - {key}: {str(value)[:60]}")
        
        # Merge the update
        state = {**state, **command.update} if command.update else state
        
        # Simulate architect agent
        print("\n" + "="*70)
        print("📊 SIMULATING: Architect Agent returns data")
        print("="*70)
        
        logger.info("📡 Calling Architect Agent MCP...")
        arch_result = await mcp.call(
            server="architect_agent",
            tool="design",
            arguments={
                "instructions": "Design architecture",
                "research_context": research_data,
                "workspace_path": tmpdir
            }
        )
        
        content = arch_result.get("content", [])
        if content and len(content) > 0:
            arch_data = json.loads(content[0].get("text", "{}"))
            print(f"✅ Architect returned data: {list(arch_data.keys())[:5]}")
        else:
            arch_data = {}
            print(f"❌ Architect returned no data")
        
        arch_update = {
            "architecture": arch_data,
            "last_agent": "architect"
        }
        state = {**state, **arch_update}
        print(f"   State updated with architecture data")
        print(f"   state['architecture'] now has keys: {list(state['architecture'].keys())[:5] if state['architecture'] else 'None'}")
        
        # Continue for codesmith
        print("\n" + "="*70)
        print("📊 SIMULATING: Codesmith Agent returns data")
        print("="*70)
        
        logger.info("📡 Calling Codesmith Agent MCP...")
        code_result = await mcp.call(
            server="codesmith_agent",
            tool="generate",
            arguments={
                "instructions": "Generate code",
                "architecture": arch_data,
                "workspace_path": tmpdir
            }
        )
        
        content = code_result.get("content", [])
        if content and len(content) > 0:
            code_data = json.loads(content[0].get("text", "{}"))
            print(f"✅ Codesmith returned data: {list(code_data.keys())}")
        else:
            code_data = {}
            print(f"❌ Codesmith returned no data")
        
        code_update = {
            "generated_files": code_data.get("generated_files", []),
            "code_complete": code_data.get("code_complete", False),
            "last_agent": "codesmith"
        }
        state = {**state, **code_update}
        print(f"   State updated with code data")
        print(f"   state['generated_files'] now has: {len(state['generated_files']) if state['generated_files'] else 0} files")
        
        # Final state check before responder
        print("\n" + "="*70)
        print("🏁 FINAL STATE CHECK (before responder)")
        print("="*70)
        
        workflow_result = {
            "research_context": state.get("research_context"),
            "architecture": state.get("architecture"),
            "generated_files": state.get("generated_files"),
            "validation_results": state.get("validation_results"),
        }
        
        print("\nData that RESPONDER will receive:")
        for key, value in workflow_result.items():
            if value is None:
                print(f"  ❌ {key}: None (PROBLEM!)")
            elif isinstance(value, dict):
                print(f"  ✅ {key}: dict with {len(value)} keys")
            elif isinstance(value, list):
                print(f"  ✅ {key}: list with {len(value)} items")
            else:
                print(f"  ✅ {key}: {type(value).__name__}")
        
        none_count = sum(1 for v in workflow_result.values() if v is None)
        print(f"\n✅ RESULT: {4-none_count}/4 data fields available for responder")
        
        if none_count == 0:
            print("✅ SUCCESS: Responder has all data!")
        else:
            print(f"❌ PROBLEM: {none_count} fields are None")


if __name__ == "__main__":
    asyncio.run(test_supervisor_decisions())