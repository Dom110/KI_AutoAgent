#!/usr/bin/env python3
"""
Debug Supervisor Iterations
Analysiert genau, was in jeder Iteration passiert.
"""

import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
import websockets
import sys

# Configuration
TEST_WORKSPACE = Path.home() / "TestApps" / "debug_iterations"
SERVER_URL = "ws://localhost:8002/ws/chat"


async def debug_iterations():
    """Debug supervisor iterations with recursion limit 10."""

    print("\n" + "="*120)
    print("🔬 DEBUG: SUPERVISOR ITERATION ANALYSIS (Recursion Limit = 10)")
    print("="*120)
    print(f"📁 Workspace: {TEST_WORKSPACE}")
    print("="*120)
    print()

    # Clean workspace
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)

    # Track iterations
    iterations = []
    current_iteration = 0
    agent_calls = {}
    routing_decisions = []

    try:
        async with websockets.connect(SERVER_URL) as ws:
            print("✅ Connected\n")

            # Initialize
            await ws.send(json.dumps({"type": "init", "workspace_path": str(TEST_WORKSPACE)}))

            # Skip connection message
            await ws.recv()
            # Get init confirmation
            await ws.recv()

            # Send simple task
            task = "Create a function that adds two numbers."
            await ws.send(json.dumps({"type": "chat", "query": task}))
            print(f"📤 Task: {task}\n")

            print("-"*120)
            print("ITERATION TRACKING:")
            print("-"*120)
            print(f"{'Iter':>4} | {'Time':>6} | {'Event Type':20} | {'Agent':15} | {'Details'}")
            print("-"*120)

            start_time = datetime.now()
            event_count = 0

            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    event = json.loads(msg)
                    event_count += 1

                    elapsed = (datetime.now() - start_time).total_seconds()
                    event_type = event.get("type")

                    # Track iteration changes
                    if event_type == "agent_event":
                        details = event.get("details", {})
                        if "iteration" in details:
                            iter_num = details["iteration"]
                            if iter_num != current_iteration:
                                current_iteration = iter_num
                                iterations.append({
                                    "number": iter_num,
                                    "time": elapsed,
                                    "agent": details.get("last_agent")
                                })

                            agent = event.get("agent", "unknown")
                            print(f"{iter_num:4d} | {elapsed:6.1f}s | {event_type:20} | {agent:15} | last_agent={details.get('last_agent')}")

                    elif event_type == "supervisor_event":
                        next_agent = event.get("next_agent")
                        reasoning = event.get("reasoning", "")[:80]
                        routing_decisions.append({
                            "iteration": current_iteration,
                            "to_agent": next_agent,
                            "reasoning": reasoning
                        })
                        print(f"{current_iteration:4d} | {elapsed:6.1f}s | {event_type:20} | → {next_agent:13} | {reasoning}")

                    elif event_type == "workflow_event":
                        node = event.get("node")
                        state = event.get("state_update", {})
                        if "last_agent" in state:
                            last = state["last_agent"]
                            if last not in agent_calls:
                                agent_calls[last] = 0
                            agent_calls[last] += 1

                        if "iteration" in state:
                            current_iteration = state["iteration"]

                    elif event_type == "error":
                        error = event.get("error", "")
                        print(f"\n❌ ERROR at iteration {current_iteration}: {error}")

                        if "Recursion limit" in error:
                            print("\n🔴 HIT RECURSION LIMIT!")
                        break

                    elif event_type == "workflow_complete":
                        print("\n✅ Workflow completed successfully!")
                        break

                except asyncio.TimeoutError:
                    print("\n⏱️ Timeout - no events for 30s")
                    break

            print("\n" + "="*120)
            print("📊 ITERATION ANALYSIS:")
            print("-"*120)

            # Show iteration progression
            print("\n🔢 Iteration Progression:")
            for i, iter_info in enumerate(iterations):
                print(f"  Iter {iter_info['number']:2d} at {iter_info['time']:5.1f}s - Last agent: {iter_info['agent']}")

            # Show routing decisions
            print(f"\n🎯 Routing Decisions (Total: {len(routing_decisions)}):")
            for i, decision in enumerate(routing_decisions[:15]):  # Show first 15
                print(f"  [{decision['iteration']:2d}] → {decision['to_agent']:12s} | {decision['reasoning'][:60]}")

            if len(routing_decisions) > 15:
                print(f"  ... and {len(routing_decisions) - 15} more decisions")

            # Show agent call frequency
            print(f"\n📈 Agent Call Frequency:")
            for agent, count in sorted(agent_calls.items(), key=lambda x: x[1], reverse=True):
                print(f"  {agent:15s}: {count:3d} calls")

            # Detect patterns
            print(f"\n🔍 Pattern Detection:")
            if len(routing_decisions) >= 3:
                # Check for repeated sequences
                last_3 = [d['to_agent'] for d in routing_decisions[-3:]]
                if len(set(last_3)) == 1:
                    print(f"  ⚠️ STUCK PATTERN: Calling '{last_3[0]}' repeatedly!")

                # Check for loops
                if len(routing_decisions) >= 6:
                    last_6 = [d['to_agent'] for d in routing_decisions[-6:]]
                    if last_6[:3] == last_6[3:]:
                        print(f"  ⚠️ LOOP DETECTED: {' → '.join(last_6[:3])} repeating!")

            print("\n" + "="*120)
            print(f"Summary: {event_count} events, {current_iteration} iterations, recursion limit = 10")
            print("="*120)

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_iterations())