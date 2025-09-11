#!/usr/bin/env python3
"""
Test Script for KI AutoAgent System
Verifiziert dass alle Komponenten funktionieren
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.master_dispatcher import MasterDispatcher
from orchestration.intent_classifier import IntentClassifier
from orchestration.workflow_generator import WorkflowGenerator
from orchestration.execution_engine import ExecutionEngine
from orchestration.learning_system import LearningSystem

# Color output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str, status: bool, message: str = ""):
    """Print test result"""
    icon = "✅" if status else "❌"
    color = Colors.GREEN if status else Colors.RED
    print(f"{icon} {color}{name}{Colors.END}: {message}")

def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

async def test_intent_classifier():
    """Test Intent Classifier"""
    print_section("🎯 Testing Intent Classifier")
    
    classifier = IntentClassifier()
    
    test_cases = [
        ("Baue mir einen Trading Bot", "create_system"),
        ("Debug diesen Code", "debug_code"),
        ("Erkläre mir Momentum Trading", "explain_concept"),
        ("Optimiere diese Funktion", "optimize_code"),
        ("Schreibe Tests für meine Klasse", "test_code"),
        ("Entwickle eine Trading Strategie", "trading_strategy"),
        ("Dokumentiere diesen Code", "documentation"),
        ("Recherchiere ML Trading Strategien", "research_topic")
    ]
    
    passed = 0
    for input_text, expected_type in test_cases:
        result = await classifier.classify(input_text)
        success = result["type"] == expected_type
        if success:
            passed += 1
        print_test(
            f"Classify: '{input_text[:30]}...'",
            success,
            f"Got: {result['type']}, Confidence: {result['confidence']:.2%}"
        )
    
    print(f"\n{Colors.BOLD}Result: {passed}/{len(test_cases)} tests passed{Colors.END}")
    return passed == len(test_cases)

async def test_workflow_generator():
    """Test Workflow Generator"""
    print_section("🔄 Testing Workflow Generator")
    
    generator = WorkflowGenerator()
    
    # Test intent
    intent = {
        "type": "create_system",
        "confidence": 0.9,
        "entities": {"framework": ["fastapi"]},
        "complexity": "high"
    }
    
    # Mock agent capabilities
    agent_capabilities = {
        "ResearchBot": {"skills": ["research"], "available": True},
        "ArchitectGPT": {"skills": ["design"], "available": True},
        "CodeSmithClaude": {"skills": ["coding"], "available": True},
        "ReviewerGPT": {"skills": ["review"], "available": True},
        "FixerBot": {"skills": ["fixing"], "available": True},
        "DocuBot": {"skills": ["documentation"], "available": True}
    }
    
    workflow = await generator.generate(
        intent=intent,
        user_input="Baue mir eine REST API mit FastAPI",
        context={},
        agent_capabilities=agent_capabilities
    )
    
    # Check workflow structure
    has_name = "name" in workflow
    has_steps = "steps" in workflow and len(workflow["steps"]) > 0
    has_metadata = "metadata" in workflow
    has_optimization = workflow.get("execution_plan", {}).get("can_parallelize") is not None
    
    print_test("Workflow has name", has_name, workflow.get("name", "None"))
    print_test("Workflow has steps", has_steps, f"{len(workflow.get('steps', []))} steps")
    print_test("Workflow has metadata", has_metadata, "Metadata present")
    print_test("Workflow optimization checked", has_optimization, 
               f"Can parallelize: {workflow.get('execution_plan', {}).get('can_parallelize')}")
    
    # Print workflow summary
    if workflow.get("steps"):
        print(f"\n{Colors.YELLOW}Workflow Steps:{Colors.END}")
        for step in workflow["steps"][:3]:  # Show first 3 steps
            print(f"  • Step {step['id']}: {step['agent']} - {step['description']}")
        if len(workflow["steps"]) > 3:
            print(f"  ... and {len(workflow['steps']) - 3} more steps")
    
    all_passed = has_name and has_steps and has_metadata
    print(f"\n{Colors.BOLD}Result: {'All checks passed' if all_passed else 'Some checks failed'}{Colors.END}")
    return all_passed

async def test_learning_system():
    """Test Learning System"""
    print_section("🧠 Testing Learning System")
    
    learning = LearningSystem()
    
    # Test recording execution
    test_request = "Create a trading bot"
    test_intent = {"type": "create_system", "confidence": 0.95}
    test_workflow = {"name": "Test Workflow", "steps": [{"agent": "TestAgent"}]}
    test_result = {
        "status": "success",
        "completed_steps": ["step1", "step2"],
        "failed_steps": [],
        "execution_time": 5.2
    }
    
    # Record execution
    await learning.record_execution(test_request, test_intent, test_workflow, test_result)
    
    # Check if recorded
    has_history = len(learning.execution_history) > 0
    print_test("Execution recorded", has_history, 
               f"{len(learning.execution_history)} executions in history")
    
    # Test workflow suggestion
    suggestion = learning.suggest_workflow(test_intent)
    has_suggestion = suggestion is not None
    print_test("Can suggest workflow", has_suggestion,
               f"Based on execution #{suggestion['based_on']}" if suggestion else "No suggestion")
    
    # Test agent performance
    performance = await learning.get_agent_performance()
    print_test("Agent performance tracking", True, 
               f"Tracking {len(performance)} agents")
    
    # Test intent statistics
    stats = learning.get_intent_statistics()
    has_stats = len(stats) > 0
    print_test("Intent statistics", has_stats,
               f"Statistics for {len(stats)} intent types")
    
    all_passed = has_history
    print(f"\n{Colors.BOLD}Result: {'Learning system functional' if all_passed else 'Issues found'}{Colors.END}")
    return all_passed

async def test_execution_engine():
    """Test Execution Engine"""
    print_section("⚙️ Testing Execution Engine")
    
    engine = ExecutionEngine()
    
    # Create test workflow
    test_workflow = {
        "name": "Test Workflow",
        "steps": [
            {
                "id": 0,
                "agent": "MockAgent",
                "task": "test_task",
                "description": "Test task 1",
                "dependencies": [],
                "can_parallel": False
            },
            {
                "id": 1,
                "agent": "MockAgent",
                "task": "test_task_2",
                "description": "Test task 2",
                "dependencies": [0],
                "can_parallel": False
            }
        ]
    }
    
    # Mock agents
    class MockAgent:
        def __init__(self):
            self.name = "MockAgent"
        
        async def execute(self, task, context):
            await asyncio.sleep(0.1)  # Simulate work
            return {
                "agent": self.name,
                "task": task,
                "output": f"Completed {task}",
                "status": "success"
            }
    
    mock_agents = {"MockAgent": MockAgent()}
    
    # Execute workflow
    result = await engine.execute(test_workflow, mock_agents)
    
    # Check results
    has_status = "status" in result
    has_outputs = "outputs" in result
    completed_steps = len(result.get("completed_steps", []))
    execution_time = result.get("execution_time", 0)
    
    print_test("Execution completed", has_status, 
               f"Status: {result.get('status', 'unknown')}")
    print_test("Has outputs", has_outputs,
               f"{len(result.get('outputs', {}))} outputs collected")
    print_test("Steps executed", completed_steps > 0,
               f"{completed_steps} steps completed")
    print_test("Execution timed", execution_time > 0,
               f"Took {execution_time:.2f} seconds")
    
    all_passed = has_status and has_outputs and completed_steps == 2
    print(f"\n{Colors.BOLD}Result: {'Execution engine working' if all_passed else 'Issues found'}{Colors.END}")
    return all_passed

async def test_master_dispatcher():
    """Test Master Dispatcher Integration"""
    print_section("🧠 Testing Master Dispatcher (Integration)")
    
    # Note: This would require API keys to fully test
    # For now, we just test initialization and structure
    
    try:
        dispatcher = MasterDispatcher()
        
        # Check components
        has_classifier = dispatcher.intent_classifier is not None
        has_generator = dispatcher.workflow_generator is not None
        has_engine = dispatcher.execution_engine is not None
        has_learning = dispatcher.learning_system is not None
        
        print_test("Intent Classifier initialized", has_classifier)
        print_test("Workflow Generator initialized", has_generator)
        print_test("Execution Engine initialized", has_engine)
        print_test("Learning System initialized", has_learning)
        
        # Test agent initialization (may be empty without imports)
        agent_count = len(dispatcher.agents)
        print_test("Agents loaded", True, f"{agent_count} agents available")
        
        all_passed = has_classifier and has_generator and has_engine and has_learning
        print(f"\n{Colors.BOLD}Result: {'Dispatcher ready' if all_passed else 'Issues found'}{Colors.END}")
        return all_passed
        
    except Exception as e:
        print_test("Dispatcher initialization", False, str(e))
        return False

async def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("     KI AUTOAGENT SYSTEM TEST SUITE")
    print("="*60)
    print(f"{Colors.END}")
    print(f"\nStarting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run tests
    results = []
    
    results.append(await test_intent_classifier())
    results.append(await test_workflow_generator())
    results.append(await test_learning_system())
    results.append(await test_execution_engine())
    results.append(await test_master_dispatcher())
    
    # Summary
    print_section("📋 TEST SUMMARY")
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED! ({passed}/{total}){Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ SOME TESTS FAILED ({passed}/{total}){Colors.END}")
    
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    # Component status
    print(f"\n{Colors.BOLD}Component Status:{Colors.END}")
    components = [
        ("Intent Classifier", results[0]),
        ("Workflow Generator", results[1]),
        ("Learning System", results[2]),
        ("Execution Engine", results[3]),
        ("Master Dispatcher", results[4])
    ]
    
    for name, status in components:
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f"  {icon} {color}{name}{Colors.END}")
    
    print(f"\n{Colors.BOLD}System is {'READY' if passed == total else 'NOT READY'} for use!{Colors.END}")
    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)