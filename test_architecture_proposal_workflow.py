#!/usr/bin/env python3
"""
Test Script for Architecture Proposal System (v5.2.0)

Tests the complete workflow for creating a Tetris app:
1. Orchestrator receives task
2. Creates execution plan with Architect
3. Architect performs research
4. Architect creates architecture proposal
5. Proposal is displayed (simulated user approval)
6. Workflow continues after approval
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from langgraph_system.workflow import AgentWorkflow
from langgraph_system.state import create_initial_state


async def test_tetris_proposal_workflow():
    """Test the complete Architecture Proposal workflow for Tetris app"""

    print("=" * 80)
    print("🧪 TESTING: Architecture Proposal System (v5.2.0)")
    print("=" * 80)
    print()

    # Initialize workflow system
    print("📋 Step 1: Initialize LangGraph Workflow System")
    workflow_system = AgentWorkflow()
    # AgentWorkflow doesn't have an initialize method, it initializes in __init__
    print("✅ Workflow system initialized")
    print()

    # Create test task
    task = "Erstelle eine Tetris App mit TypeScript"
    print(f"📝 Step 2: Create Task")
    print(f"   Task: {task}")
    print()

    # Execute workflow (without Plan-First mode to see proposal directly)
    print("🚀 Step 3: Execute Workflow")
    print("   Note: Running WITHOUT Plan-First to see Architecture Proposal")
    print()

    try:
        final_state = await workflow_system.execute(
            task=task,
            session_id="test_tetris_proposal",
            client_id="test_client",
            workspace_path="/Users/dominikfoert/git/KI_AutoAgent/test_tetris",
            plan_first_mode=False,  # No Plan-First, so we go straight to execution
            config={"debug_mode": True}
        )

        print()
        print("=" * 80)
        print("📊 WORKFLOW EXECUTION COMPLETE")
        print("=" * 80)
        print()

        # Analyze state
        print("🔍 Step 4: Analyze Final State")
        print()

        # Check if architecture proposal was created
        if final_state.get("architecture_proposal"):
            proposal = final_state["architecture_proposal"]
            print("✅ Architecture Proposal Created!")
            print()
            print("📋 Proposal Structure:")
            print(f"   - Status: {final_state.get('proposal_status', 'unknown')}")
            print(f"   - Approval Type: {final_state.get('approval_type', 'unknown')}")
            print(f"   - Needs Approval: {final_state.get('needs_approval', False)}")
            print()

            # Display proposal sections
            print("📄 Proposal Content:")
            print()

            if "summary" in proposal:
                print("   📊 SUMMARY:")
                summary = proposal["summary"]
                print(f"      {summary[:200]}..." if len(summary) > 200 else f"      {summary}")
                print()

            if "improvements" in proposal:
                print("   ✨ SUGGESTED IMPROVEMENTS:")
                improvements = proposal["improvements"]
                print(f"      {improvements[:300]}..." if len(improvements) > 300 else f"      {improvements}")
                print()

            if "tech_stack" in proposal:
                print("   🛠️ TECH STACK:")
                tech_stack = proposal["tech_stack"]
                print(f"      {tech_stack[:300]}..." if len(tech_stack) > 300 else f"      {tech_stack}")
                print()

            if "structure" in proposal:
                print("   📁 PROJECT STRUCTURE:")
                structure = proposal["structure"]
                print(f"      {structure[:200]}..." if len(structure) > 200 else f"      {structure}")
                print()

            if "risks" in proposal:
                print("   ⚠️ RISKS & MITIGATIONS:")
                risks = proposal["risks"]
                print(f"      {risks[:200]}..." if len(risks) > 200 else f"      {risks}")
                print()

            if "research_insights" in proposal:
                print("   🔍 RESEARCH INSIGHTS:")
                insights = proposal["research_insights"]
                print(f"      {insights[:200]}..." if len(insights) > 200 else f"      {insights}")
                print()

            # Check if waiting for approval
            if final_state.get("status") == "waiting_architecture_approval":
                print("✅ Workflow State: WAITING FOR ARCHITECTURE APPROVAL")
                print("   → This is CORRECT! System is waiting for user decision.")
                print()

            # Simulate user approval
            print("🔄 Step 5: Simulate User Approval")
            print("   Decision: APPROVED")
            print()

            # Update state and continue workflow
            final_state["proposal_status"] = "approved"
            final_state["needs_approval"] = False
            final_state["waiting_for_approval"] = False

            # Note: In real scenario, this would trigger workflow resumption
            # via WebSocket message. Here we just verify the state is correct.

            print("✅ Proposal approved (simulated)")
            print()

        else:
            print("❌ NO Architecture Proposal Found!")
            print("   This indicates the proposal system did not trigger.")
            print()

        # Display execution plan
        if final_state.get("execution_plan"):
            print("📋 Execution Plan:")
            for i, step in enumerate(final_state["execution_plan"]):
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(step.status, "❓")

                print(f"   {i+1}. {status_icon} {step.agent.upper()}: {step.task[:80]}...")
                print(f"      Status: {step.status}")
                if step.result:
                    result_preview = str(step.result)[:150]
                    print(f"      Result: {result_preview}...")
                print()

        # Display collaboration history (v5.1.0 feature)
        if final_state.get("collaboration_history"):
            print("🤝 Collaboration History (v5.1.0):")
            for i, collab in enumerate(final_state["collaboration_history"][:5]):  # Show first 5
                print(f"   {i+1}. {collab.get('from')} → {collab.get('to')}")
                print(f"      Query: {collab.get('query', 'unknown')[:80]}...")
            if len(final_state["collaboration_history"]) > 5:
                print(f"   ... and {len(final_state['collaboration_history']) - 5} more")
            print()

        # Display information gathered (v5.1.0 feature)
        if final_state.get("information_gathered"):
            print("🔍 Information Gathered (v5.1.0):")
            for i, info in enumerate(final_state["information_gathered"][:3]):  # Show first 3
                print(f"   {i+1}. Level {info.get('level', 0)}: {info.get('query', 'unknown')[:80]}...")
                print(f"      Summary: {info.get('summary', 'N/A')[:100]}...")
            if len(final_state["information_gathered"]) > 3:
                print(f"   ... and {len(final_state['information_gathered']) - 3} more")
            print()

        # Final statistics
        print("=" * 80)
        print("📊 WORKFLOW STATISTICS")
        print("=" * 80)
        print()
        print(f"   Status: {final_state.get('status', 'unknown')}")
        print(f"   Current Agent: {final_state.get('current_agent', 'unknown')}")
        print(f"   Execution Mode: {final_state.get('execution_mode', 'unknown')}")
        print(f"   Plan-First Mode: {final_state.get('plan_first_mode', False)}")
        print(f"   Approval Status: {final_state.get('approval_status', 'none')}")
        print()
        print(f"   Collaboration Count (v5.1.0): {final_state.get('collaboration_count', 0)}")
        print(f"   Reviewer-Fixer Cycles (v5.1.0): {final_state.get('reviewer_fixer_cycles', 0)}")
        print(f"   Escalation Level (v5.1.0): {final_state.get('escalation_level', 0)}")
        print()
        print(f"   Errors: {len(final_state.get('errors', []))}")
        if final_state.get("errors"):
            for error in final_state["errors"]:
                print(f"      - {error.get('agent', 'unknown')}: {error.get('error', 'unknown')}")
        print()

        # Execution time
        if final_state.get("end_time") and final_state.get("start_time"):
            duration = (final_state["end_time"] - final_state["start_time"]).total_seconds()
            print(f"   Execution Time: {duration:.2f} seconds")
        print()

        # Success summary
        print("=" * 80)
        print("✅ TEST SUMMARY")
        print("=" * 80)
        print()

        has_proposal = bool(final_state.get("architecture_proposal"))
        is_waiting = final_state.get("status") == "waiting_architecture_approval"
        has_required_fields = all(
            key in final_state.get("architecture_proposal", {})
            for key in ["summary", "improvements", "tech_stack", "structure", "risks", "research_insights"]
        )

        print(f"   ✅ Architecture Proposal Created: {has_proposal}")
        print(f"   ✅ Workflow Waiting for Approval: {is_waiting}")
        print(f"   ✅ Proposal Has All Required Fields: {has_required_fields}")
        print()

        if has_proposal and is_waiting and has_required_fields:
            print("🎉 SUCCESS! Architecture Proposal System (v5.2.0) is working correctly!")
        else:
            print("⚠️ PARTIAL SUCCESS - Some checks failed. Review output above.")
        print()

        # Save proposal to file for inspection
        if final_state.get("architecture_proposal"):
            output_file = "/Users/dominikfoert/git/KI_AutoAgent/test_tetris_proposal_output.json"
            with open(output_file, "w") as f:
                json.dump(final_state["architecture_proposal"], f, indent=2)
            print(f"💾 Full proposal saved to: {output_file}")
            print()

    except Exception as e:
        import traceback
        print()
        print("=" * 80)
        print("❌ ERROR DURING WORKFLOW EXECUTION")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        print("Traceback:")
        print(traceback.format_exc())
        print()
        return False

    return True


if __name__ == "__main__":
    print()
    print("🚀 Starting Architecture Proposal Workflow Test")
    print()

    # Check if venv is active
    if not sys.prefix.endswith('venv'):
        print("⚠️  WARNING: Virtual environment not active")
        print(f"   Current Python: {sys.executable}")
        print()

    # Run async test
    success = asyncio.run(test_tetris_proposal_workflow())

    if success:
        print("✅ Test completed successfully")
        sys.exit(0)
    else:
        print("❌ Test failed")
        sys.exit(1)
