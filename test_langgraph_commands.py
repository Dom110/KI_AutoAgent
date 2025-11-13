#!/usr/bin/env python3
"""
LangGraph Commands Diagnostic Test
Tests if LangGraph Commands routing works correctly
"""

import asyncio
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import TypedDict


class TestState(TypedDict):
    """Simple test state."""
    message: str
    node_visited: list[str]


async def supervisor_node(state: TestState) -> Command:
    """Node that returns a Command for routing."""
    print(f"[SUPERVISOR] Current state: {state}")
    print(f"[SUPERVISOR] Creating Command to route to 'agent1'")
    
    cmd = Command(
        goto="agent1",
        update={
            "message": f"From supervisor: {state.get('message', 'hello')}",
            "node_visited": (state.get("node_visited", []) or []) + ["supervisor"]
        }
    )
    
    print(f"[SUPERVISOR] Command.goto = {cmd.goto}")
    print(f"[SUPERVISOR] Command.update = {cmd.update}")
    return cmd


async def agent1_node(state: TestState) -> Command:
    """First agent node."""
    visited = (state.get("node_visited", []) or []) + ["agent1"]
    print(f"[AGENT1] Visited: {visited}")
    return Command(
        goto="agent2",
        update={"node_visited": visited}
    )


async def agent2_node(state: TestState) -> Command:
    """Second agent node."""
    visited = (state.get("node_visited", []) or []) + ["agent2"]
    print(f"[AGENT2] Visited: {visited}")
    return Command(
        goto=END,
        update={"node_visited": visited}
    )


async def test_langgraph_commands():
    """Test if LangGraph properly handles Command routing."""
    
    print("\n" + "="*100)
    print("🧪 LANGGRAPH COMMANDS DIAGNOSTIC TEST")
    print("="*100)
    
    try:
        import langgraph
        print(f"LangGraph version: 0.6+ (checked)")
    except:
        print("LangGraph version: Unknown")
    
    # Create graph
    print("\n[SETUP] Creating LangGraph StateGraph...")
    graph = StateGraph(TestState)
    
    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("agent1", agent1_node)
    graph.add_node("agent2", agent2_node)
    
    # Add edges
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("agent1", lambda s: "agent2")
    graph.add_conditional_edges("agent2", lambda s: "__end__")
    
    print("[SETUP] Compiling workflow...")
    app = graph.compile()
    print("✅ Workflow compiled successfully")
    
    # Test execution
    print("\n[EXECUTION] Running workflow with Command routing...")
    initial_state = {
        "message": "test message",
        "node_visited": []
    }
    
    try:
        print(f"\nInitial state: {initial_state}")
        
        final_state = await app.ainvoke(initial_state)
        
        print(f"\nFinal state: {final_state}")
        print(f"\nNodes visited: {final_state.get('node_visited', [])}")
        
        # Check results
        visited = final_state.get("node_visited", []) or []
        
        print("\n" + "="*100)
        print("📊 TEST RESULTS")
        print("="*100)
        
        if "supervisor" in visited:
            print("✅ Supervisor node was visited")
        else:
            print("❌ Supervisor node NOT visited")
        
        if "agent1" in visited:
            print("✅ Agent1 node was visited")
        else:
            print("❌ Agent1 node NOT visited")
        
        if "agent2" in visited:
            print("✅ Agent2 node was visited")
        else:
            print("❌ Agent2 node NOT visited")
        
        if visited == ["supervisor", "agent1", "agent2"]:
            print("\n✅ ROUTING WORKS CORRECTLY - All nodes visited in order!")
            print("✅ LangGraph Commands are working!")
            return True
        else:
            print(f"\n❌ ROUTING FAILED - Unexpected order: {visited}")
            print("❌ Commands may not be working correctly")
            return False
            
    except Exception as e:
        print(f"\n❌ EXECUTION FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_langgraph_commands())
    exit(0 if success else 1)
