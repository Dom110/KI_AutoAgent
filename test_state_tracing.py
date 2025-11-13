#!/usr/bin/env python3
"""
🔍 STATE TRACING TEST: Track workflow state through entire execution

This test logs the state at each agent execution to see:
1. What data enters each agent
2. What updates are returned  
3. What the state contains after each step
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("state_tracing")

sys.path.insert(0, str(Path(__file__).parent))

from backend.workflow_v7_mcp import build_supervisor_workflow_mcp, SupervisorState
from langgraph.graph import StateGraph
import tempfile


def log_state(label: str, state: SupervisorState, keys_to_show: list[str] = None):
    """Pretty print state for debugging"""
    print(f"\n{'='*70}")
    print(f"📊 STATE AT {label}")
    print(f"{'='*70}")
    
    if keys_to_show is None:
        keys_to_show = [
            "last_agent", 
            "iteration",
            "research_context",
            "architecture", 
            "generated_files",
            "validation_results",
            "user_response",
            "errors"
        ]
    
    for key in keys_to_show:
        value = state.get(key)
        if value is None:
            print(f"  ❌ {key}: None")
        elif isinstance(value, dict):
            print(f"  ✅ {key}: dict with keys {list(value.keys())[:5]}")
        elif isinstance(value, list):
            print(f"  ✅ {key}: list with {len(value)} items")
        elif isinstance(value, str):
            print(f"  ✅ {key}: str ({len(value)} chars)")
        else:
            print(f"  ✅ {key}: {type(value).__name__}")


async def test_workflow_state_tracing():
    """Run workflow and trace state changes"""
    
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "WORKFLOW STATE TRACING TEST" + " "*21 + "║")
    print("║" + " "*15 + "Track data flow through complete workflow" + " "*13 + "║")
    print("╚" + "="*68 + "╝\n")
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        logger.info(f"📁 Using temp workspace: {tmpdir}")
        
        # Create a simple Python project structure
        Path(tmpdir).joinpath("src").mkdir()
        Path(tmpdir).joinpath("tests").mkdir()
        Path(tmpdir).joinpath("requirements.txt").write_text("fastapi==0.117.1\nuvicorn==0.37.0\n")
        Path(tmpdir).joinpath("src/main.py").write_text("# Test app\nprint('Hello')\n")
        
        # Build workflow
        logger.info("🏗️ Building workflow...")
        compiled = build_supervisor_workflow_mcp()
        
        # Initial state
        initial_state: SupervisorState = {
            "messages": [],
            "goal": "Create a simple FastAPI calculator app",
            "user_query": "Build a calculator API with add, subtract, multiply endpoints",
            "workspace_path": tmpdir,
            "session_id": "test-trace-001",
            "last_agent": None,
            "iteration": 0,
            "is_self_invocation": False,
            "instructions": "Create a simple calculator API",
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
        
        log_state("INITIAL STATE", initial_state)
        
        # Run workflow with step-by-step tracing
        logger.info("\n🚀 Starting workflow execution...")
        
        try:
            step_count = 0
            current_state = initial_state
            
            # Stream events (async)
            async for event in compiled.astream(initial_state, stream_mode="updates"):
                step_count += 1
                
                # Update state with event
                for node_name, updates in event.items():
                    logger.info(f"\n📨 Node '{node_name}' returning updates:")
                    
                    # Log what each node is updating
                    if updates:
                        for key, value in updates.items():
                            if value is None:
                                print(f"     {key}: None")
                            elif isinstance(value, dict):
                                print(f"     {key}: dict({len(value)} keys)")
                            elif isinstance(value, list):
                                print(f"     {key}: list({len(value)} items)")
                            else:
                                print(f"     {key}: {str(value)[:50]}")
                        
                        # Merge updates into state
                        current_state = {**current_state, **updates}
                    
                    # Log state after update
                    log_state(f"AFTER {node_name.upper()}", current_state, keys_to_show=[
                        "iteration", "last_agent",
                        "research_context",
                        "architecture",
                        "generated_files",
                        "validation_results",
                        "user_response"
                    ])
                
                # Safety check
                if step_count > 20:
                    logger.warning("⚠️ Stopping after 20 steps (infinite loop protection)")
                    break
            
            # Final state analysis
            print("\n" + "="*70)
            print("🏁 FINAL STATE ANALYSIS")
            print("="*70)
            
            data_summary = {
                "research_context": "✅ Present" if current_state.get("research_context") else "❌ Missing",
                "architecture": "✅ Present" if current_state.get("architecture") else "❌ Missing",
                "generated_files": "✅ Present" if current_state.get("generated_files") else "❌ Missing",
                "validation_results": "✅ Present" if current_state.get("validation_results") else "❌ Missing",
                "user_response": "✅ Present" if current_state.get("user_response") else "❌ Missing",
            }
            
            for key, status in data_summary.items():
                print(f"  {status}: {key}")
            
            # Check if responder got all data
            print("\n📡 WHAT RESPONDER RECEIVED:")
            workflow_result = {
                "research_context": current_state.get("research_context"),
                "architecture": current_state.get("architecture"),
                "generated_files": current_state.get("generated_files"),
                "validation_results": current_state.get("validation_results"),
            }
            
            none_count = sum(1 for v in workflow_result.values() if v is None)
            print(f"  Data fields with None: {none_count}/4")
            
            if none_count > 0:
                print("  ❌ PROBLEM: Responder received incomplete data!")
            else:
                print("  ✅ PROBLEM SOLVED: Responder should have all data!")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_workflow_state_tracing())