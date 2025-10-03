#!/usr/bin/env python3
"""
Complex App Request Test for KI AutoAgent v5.5.2
Tests the system with a sophisticated real-time collaborative whiteboard application
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.langgraph_system.workflow import create_extended_workflow
from backend.langgraph_system.state import create_initial_state
from backend.__version__ import __version__

print(f"🚀 KI AutoAgent v{__version__} - Complex App Generation Test")
print("=" * 70)

# Define the complex application request
COMPLEX_APP_REQUEST = """
Erstelle eine vollständige Real-Time Collaborative Whiteboard Web-Anwendung mit folgenden Features:

HAUPTFUNKTIONEN:
1. Mehrere Nutzer können gleichzeitig auf demselben Whiteboard zeichnen
2. Echtzeit-Synchronisation aller Zeichnungen über WebSockets
3. Verschiedene Zeichenwerkzeuge (Stift, Linien, Rechtecke, Kreise, Text)
4. Farbauswahl und Strichstärke einstellbar
5. Nutzer-Cursor werden für alle sichtbar angezeigt mit Namen
6. Undo/Redo Funktionalität pro Nutzer
7. Whiteboard-Sessions können gespeichert und geladen werden
8. Chat-Funktion neben dem Whiteboard
9. Nutzer können Räume erstellen und beitreten
10. Export als PNG/SVG

TECHNISCHE ANFORDERUNGEN:
- Frontend: Modernes HTML5 Canvas mit responsivem Design
- Backend: WebSocket-Server für Echtzeit-Kommunikation
- Persistenz: Speicherung der Zeichnungen und Sessions
- Performance: Optimiert für 10+ gleichzeitige Nutzer
- Mobile: Touch-Support für Tablets

Die Anwendung soll produktionsreif sein mit sauberer Architektur, Error Handling und guter Performance.
"""

async def test_complex_app_generation():
    """Test the KI AutoAgent with a complex application request"""

    print("\n📋 Complex Application: Real-Time Collaborative Whiteboard")
    print("-" * 70)
    print("Features requested:")
    print("• Multi-user real-time drawing")
    print("• WebSocket synchronization")
    print("• Multiple drawing tools")
    print("• User presence indicators")
    print("• Undo/Redo functionality")
    print("• Session persistence")
    print("• Chat functionality")
    print("• Room management")
    print("• Export capabilities")
    print("-" * 70)

    # Create workflow and initial state
    print("\n🔧 Initializing KI AutoAgent Workflow...")
    workflow_system = create_extended_workflow()

    # Create initial state with the complex request
    initial_state = create_initial_state(
        session_id=f"complex_app_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        client_id="test_client",
        workspace_path="/Users/dominikfoert/git/KI_AutoAgent",
        plan_first_mode=False,  # Let it run automatically
        debug_mode=True
    )

    # Add the complex request as a message
    initial_state["messages"] = [{
        "role": "user",
        "content": COMPLEX_APP_REQUEST
    }]
    initial_state["current_task"] = COMPLEX_APP_REQUEST

    print(f"Session ID: {initial_state['session_id']}")
    print(f"Debug Mode: {initial_state['debug_mode']}")

    # Track workflow metrics
    metrics = {
        "start_time": datetime.now(),
        "agents_used": set(),
        "steps_executed": 0,
        "errors": [],
        "safety_blocks": 0,
        "classifications": []
    }

    print("\n🚀 Starting Workflow Execution...")
    print("=" * 70)

    try:
        # Get the workflow
        app = workflow_system.workflow

        # Create config for execution
        config = {"configurable": {"thread_id": initial_state["session_id"]}}

        # Track execution steps
        step_count = 0

        # Stream the workflow execution
        async for event in app.astream(initial_state, config=config):
            step_count += 1

            # Log each step
            print(f"\n📍 Step {step_count}:")

            # Extract relevant information from the event
            if isinstance(event, dict):
                for node_name, node_output in event.items():
                    print(f"  Agent: {node_name}")
                    metrics["agents_used"].add(node_name)

                    if isinstance(node_output, dict):
                        # Check for execution plan
                        if "execution_plan" in node_output:
                            plan = node_output["execution_plan"]
                            if plan:
                                print(f"  Execution Plan: {len(plan)} steps")
                                for i, step in enumerate(plan[:3]):  # Show first 3 steps
                                    print(f"    {i+1}. {step.agent}: {step.task[:50]}...")
                                if len(plan) > 3:
                                    print(f"    ... and {len(plan)-3} more steps")

                        # Check for status
                        if "status" in node_output:
                            print(f"  Status: {node_output['status']}")

                        # Check for safety/classification (v5.5.2 features)
                        if "query_classification" in node_output:
                            classification = node_output["query_classification"]
                            metrics["classifications"].append(classification)
                            print(f"  Classification: {classification}")

                        if "safe_execution_enabled" in node_output:
                            print(f"  Safe Execution: {node_output['safe_execution_enabled']}")

                        if "blocked_queries" in node_output and node_output["blocked_queries"]:
                            metrics["safety_blocks"] += len(node_output["blocked_queries"])
                            print(f"  ⚠️ Blocked Queries: {node_output['blocked_queries']}")

                        # Check for errors
                        if "errors" in node_output and node_output["errors"]:
                            metrics["errors"].extend(node_output["errors"])
                            print(f"  ❌ Errors: {node_output['errors']}")

                        # Check for messages (results)
                        if "messages" in node_output:
                            for msg in node_output["messages"][-1:]:  # Show last message
                                if isinstance(msg, dict) and "content" in msg:
                                    content = msg["content"]
                                    if len(content) > 200:
                                        print(f"  Result: {content[:200]}...")
                                    else:
                                        print(f"  Result: {content}")

            metrics["steps_executed"] = step_count

            # Limit execution for testing
            if step_count >= 20:
                print("\n⚠️ Reached step limit (20) - stopping execution")
                break

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        metrics["errors"].append(str(e))
        import traceback
        traceback.print_exc()

    # Calculate execution time
    metrics["end_time"] = datetime.now()
    metrics["duration"] = (metrics["end_time"] - metrics["start_time"]).total_seconds()

    # Print evaluation results
    print("\n" + "=" * 70)
    print("📊 EVALUATION RESULTS")
    print("=" * 70)

    print(f"\n⏱️ Execution Metrics:")
    print(f"  Duration: {metrics['duration']:.2f} seconds")
    print(f"  Steps Executed: {metrics['steps_executed']}")
    print(f"  Agents Used: {', '.join(metrics['agents_used']) if metrics['agents_used'] else 'None'}")

    print(f"\n🛡️ Safety Metrics (v5.5.2):")
    print(f"  Safety Blocks: {metrics['safety_blocks']}")
    print(f"  Classifications Made: {len(metrics['classifications'])}")

    print(f"\n❌ Errors:")
    if metrics["errors"]:
        for error in metrics["errors"]:
            print(f"  • {error}")
    else:
        print("  ✅ No errors encountered")

    print("\n📈 Complexity Analysis:")
    print(f"  Request Complexity: HIGH (10+ features, real-time, multi-user)")
    print(f"  Expected Agents: architect, codesmith, reviewer, fixer")
    print(f"  Actual Agents Used: {len(metrics['agents_used'])}")

    # Evaluate success
    success_criteria = {
        "workflow_started": metrics["steps_executed"] > 0,
        "agents_activated": len(metrics["agents_used"]) > 0,
        "no_critical_errors": not any("critical" in str(e).lower() for e in metrics["errors"]),
        "safe_execution": metrics["safety_blocks"] == 0 or metrics["safety_blocks"] < 3,
    }

    print("\n✅ Success Criteria:")
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {criterion.replace('_', ' ').title()}")

    overall_success = all(success_criteria.values())

    print("\n" + "=" * 70)
    if overall_success:
        print("🎉 COMPLEX APP REQUEST TEST: PASSED")
    else:
        print("⚠️ COMPLEX APP REQUEST TEST: PARTIAL SUCCESS")
    print("=" * 70)

    return metrics

# Run the test
if __name__ == "__main__":
    print("\n🔬 Testing KI AutoAgent with Complex Application Request")
    print(f"Version: {__version__}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        metrics = loop.run_until_complete(test_complex_app_generation())
    finally:
        loop.close()

    print("\n✨ Test Complete!")
    print(f"Check the generated files in: collaborative_whiteboard/")
    print("The app should include:")
    print("  • HTML file with canvas and UI")
    print("  • JavaScript for drawing and WebSocket communication")
    print("  • Backend server code (if generated)")
    print("  • CSS for styling")
    print("\n📝 Review the execution steps above to understand the agent workflow!")