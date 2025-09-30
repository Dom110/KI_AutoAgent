#!/usr/bin/env python3
"""
Test script to verify intelligent AI-based file creation
Tests ASIMOV Rule 1 compliance - NO FALLBACKS
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.agents.specialized.codesmith_agent import CodeSmithAgent
from backend.agents.specialized.orchestrator_agent_v2 import OrchestratorAgentV2
from backend.agents.base.base_agent import TaskRequest

async def test_intelligent_file_creation():
    """Test various implementation requests with AI detection"""

    print("\n" + "="*60)
    print("🧠 TESTING INTELLIGENT AI-BASED FILE CREATION")
    print("="*60)

    # Test requests that should create files
    test_requests = [
        # German request - should understand and create file
        "Erstelle einen Plan-First Button für die VS Code Extension",

        # Vague request - AI should understand it needs implementation
        "Add a button that shows the plan before executing",

        # No keywords but clear implementation intent
        "The system needs a way to preview plans before running them",

        # Direct implementation request
        "Implement a PlanFirstButton component in TypeScript",
    ]

    # Test requests that should NOT create files
    non_implementation_requests = [
        "What agents do we have?",
        "Explain how the system works",
        "Review the architecture",
        "What can be improved?"
    ]

    # Initialize CodeSmithAgent
    codesmith = CodeSmithAgent()

    print("\n📝 Testing IMPLEMENTATION requests (should create files):")
    print("-" * 50)

    for request_text in test_requests:
        print(f"\nRequest: '{request_text}'")

        request = TaskRequest(
            prompt=request_text,
            context={"workspace_path": os.getcwd()}
        )

        try:
            # Test AI detection
            should_create = await codesmith._ai_detect_implementation_request(request_text)
            print(f"  🧠 AI Detection: {'✅ Implementation' if should_create else '❌ Not Implementation'}")

            if should_create:
                # Test file path determination
                file_path = await codesmith._ai_determine_file_path(request_text, os.getcwd())
                print(f"  📁 AI File Path: {file_path}")

                # Test ASIMOV Rule 1 enforcement
                try:
                    codesmith._enforce_asimov_rule_1(file_path)
                    print(f"  ✅ ASIMOV Rule 1: PASSED")
                except Exception as e:
                    print(f"  ❌ ASIMOV Rule 1: {e}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n\n❓ Testing NON-IMPLEMENTATION requests (should NOT create files):")
    print("-" * 50)

    for request_text in non_implementation_requests:
        print(f"\nRequest: '{request_text}'")

        try:
            should_create = await codesmith._ai_detect_implementation_request(request_text)
            print(f"  🧠 AI Detection: {'❌ Incorrectly detected as implementation!' if should_create else '✅ Correctly identified as non-implementation'}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "="*60)
    print("✅ TEST COMPLETE - AI-based intelligent file creation")
    print("="*60)

async def test_orchestrator_decomposition():
    """Test orchestrator's intelligent task decomposition"""

    print("\n" + "="*60)
    print("🎯 TESTING ORCHESTRATOR INTELLIGENT DECOMPOSITION")
    print("="*60)

    orchestrator = OrchestratorAgentV2()

    test_prompt = "Create a Plan-First button that shows the execution plan before running tasks"

    print(f"\nTest Request: '{test_prompt}'")
    print("-" * 50)

    request = TaskRequest(
        prompt=test_prompt,
        context={"workspace_path": os.getcwd()}
    )

    try:
        # Test decomposition
        decomposition = await orchestrator._decompose_task_with_ai(test_prompt)

        print(f"\n📋 Main Goal: {decomposition.main_goal}")
        print(f"🔧 Complexity: {decomposition.complexity}")
        print(f"⚡ Execution Mode: {decomposition.execution_mode}")
        print(f"\n📝 Subtasks ({len(decomposition.subtasks)}):")

        for i, task in enumerate(decomposition.subtasks, 1):
            print(f"\n  {i}. {task.description}")
            print(f"     Agent: {task.agent}")

            # Check if file creation is properly specified
            if "implement_code_to_file" in task.description:
                print(f"     ✅ File creation directive found!")
            elif task.agent == "codesmith" and any(word in task.description.lower() for word in ['implement', 'create', 'build']):
                print(f"     ⚠️ Warning: CodeSmith task without explicit file directive")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*60)
    print("✅ ORCHESTRATOR TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    print("\n🚀 Starting Intelligent Agent Tests...")
    print("📌 ASIMOV RULE 1: No fallbacks allowed - all errors will be raised")

    # Run tests
    asyncio.run(test_intelligent_file_creation())
    asyncio.run(test_orchestrator_decomposition())

    print("\n✨ All tests completed!")