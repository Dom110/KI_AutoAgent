#!/usr/bin/env python3
"""
Test script to verify button implementation works correctly
Tests that agent doesn't hallucinate about JD Edwards
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.agents.specialized.codesmith_agent import CodeSmithAgent
from backend.agents.specialized.orchestrator_agent_v2 import OrchestratorAgentV2
from backend.agents.base.base_agent import TaskRequest


async def test_button_implementation():
    """Test that agent correctly implements Plan-First button"""

    print("\n" + "="*60)
    print("🧪 TESTING BUTTON IMPLEMENTATION - NO HALLUCINATIONS")
    print("="*60)

    # Initialize CodeSmithAgent
    codesmith = CodeSmithAgent()

    # Test request
    test_request = "Add a Plan-First button next to the Orchestrator button"

    print(f"\nTest Request: '{test_request}'")
    print("-" * 50)

    # Validate workspace context
    workspace_context = codesmith._validate_workspace_context()
    print(f"\n📁 Workspace Context:")
    print(f"  Project: {workspace_context['project']}")
    print(f"  Type: {workspace_context['type']}")
    print(f"  UI File: {workspace_context['ui_file']}")

    if workspace_context['project'] != 'KI_AutoAgent':
        print(f"❌ ERROR: Not in KI_AutoAgent workspace!")
        return

    # Create request
    request = TaskRequest(
        prompt=test_request,
        context={'workspace_path': os.getcwd()}
    )

    print("\n🎯 Testing implementation...")

    try:
        # Execute the request
        result = await codesmith.execute(request)

        print(f"\nResult Status: {result.status}")
        print(f"Content: {result.content[:500]}...")  # First 500 chars

        # Check for hallucinations
        hallucination_check = codesmith._check_for_hallucination(result.content)

        if hallucination_check:
            print("\n❌ FAILED: Agent hallucinated about enterprise systems!")
            print("This is KI_AutoAgent, not JD Edwards!")
        else:
            print("\n✅ PASSED: No hallucinations detected")

        # Check if correct file was identified
        if 'MultiAgentChatPanel.ts' in result.content:
            print("✅ Correct file identified")
        else:
            print("❌ Wrong file or file not mentioned")

        # Check if JD Edwards mentioned
        bad_words = ['JD Edwards', 'Oracle', 'P4310', 'Form Extension']
        for word in bad_words:
            if word.lower() in result.content.lower():
                print(f"❌ ERROR: Found '{word}' in response - hallucination!")
                break
        else:
            print("✅ No enterprise system references found")

    except Exception as e:
        print(f"❌ Error during test: {e}")


async def test_orchestrator_decomposition():
    """Test orchestrator's task decomposition with correct context"""

    print("\n" + "="*60)
    print("🎯 TESTING ORCHESTRATOR DECOMPOSITION")
    print("="*60)

    orchestrator = OrchestratorAgentV2()

    test_prompt = "Add a Plan-First button next to the Orchestrator button"

    print(f"\nTest Request: '{test_prompt}'")
    print("-" * 50)

    try:
        # Test decomposition with enhanced context
        decomposition = await orchestrator._decompose_task_with_ai(
            test_prompt,
            client_id="test",
            manager=None,
            conversation_history=""
        )

        print(f"\n📋 Main Goal: {decomposition.main_goal}")
        print(f"🔧 Complexity: {decomposition.complexity}")
        print(f"⚡ Execution Mode: {decomposition.execution_mode}")
        print(f"\n📝 Subtasks ({len(decomposition.subtasks)}):")

        for i, task in enumerate(decomposition.subtasks, 1):
            print(f"\n  {i}. {task.description}")
            print(f"     Agent: {task.agent}")

            # Check for correct file references
            if 'MultiAgentChatPanel.ts' in task.description:
                print(f"     ✅ Correct file mentioned!")

            # Check for hallucinations
            bad_words = ['JD Edwards', 'Oracle', 'P4310', 'Form Extension']
            for word in bad_words:
                if word in task.description:
                    print(f"     ❌ HALLUCINATION: Found '{word}'")
                    break

            # Check if file creation is specified
            if "implement_code_to_file" in task.description:
                print(f"     ✅ File creation directive found!")
            elif task.agent == "codesmith" and any(word in task.description.lower() for word in ['implement', 'create', 'add']):
                print(f"     ⚠️ Warning: CodeSmith task without explicit file directive")

    except Exception as e:
        print(f"❌ Error: {e}")


async def test_ai_detection():
    """Test AI-based implementation detection"""

    print("\n" + "="*60)
    print("🧠 TESTING AI DETECTION")
    print("="*60)

    codesmith = CodeSmithAgent()

    test_prompts = [
        "Add a Plan-First button next to the Orchestrator button",
        "Create a new button for planning",
        "Implement a button that shows plans before executing",
        "What is the Orchestrator button?",  # Should be NO
        "Explain how buttons work",  # Should be NO
    ]

    for prompt in test_prompts:
        print(f"\n📝 Testing: '{prompt}'")

        try:
            should_create = await codesmith._ai_detect_implementation_request(prompt)
            print(f"  🧠 AI Detection: {'✅ Implementation' if should_create else '❌ Not Implementation'}")

            if should_create:
                # Test file path determination
                file_path = await codesmith._ai_determine_file_path(prompt, os.getcwd())
                print(f"  📁 AI File Path: {file_path}")

                # Check if correct file
                if 'MultiAgentChatPanel.ts' in file_path:
                    print(f"  ✅ Correct file determined!")
                else:
                    print(f"  ❌ Wrong file determined")

        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    print("\n🚀 Starting Button Implementation Tests...")
    print("📌 Testing that agent knows this is KI_AutoAgent, not JD Edwards")

    # Run tests
    asyncio.run(test_button_implementation())
    asyncio.run(test_orchestrator_decomposition())
    asyncio.run(test_ai_detection())

    print("\n✨ All tests completed!")
    print("="*60)