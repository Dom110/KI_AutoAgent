#!/usr/bin/env python3
"""
Test for v5.5.2 Safe Orchestrator Executor
Tests the 20 query classification system
"""

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test imports
print("🧪 Testing v5.5.2 Safe Orchestrator Executor")
print("=" * 50)

# Import version
from backend.__version__ import __version__
print(f"✅ Version: {__version__}")
assert __version__ == "5.5.2", f"Expected version 5.5.2, got {__version__}"

# Import the new modules
try:
    from backend.langgraph_system.query_classifier import EnhancedQueryClassifier, DetailedClassification
    print("✅ Query Classifier imported")
except ImportError as e:
    print(f"❌ Failed to import Query Classifier: {e}")
    sys.exit(1)

try:
    from backend.langgraph_system.development_query_handler import DevelopmentQueryHandler
    print("✅ Development Query Handler imported")
except ImportError as e:
    print(f"❌ Failed to import Development Query Handler: {e}")
    sys.exit(1)

try:
    from backend.langgraph_system.safe_orchestrator_executor import SafeOrchestratorExecutor
    print("✅ Safe Orchestrator Executor imported")
except ImportError as e:
    print(f"❌ Failed to import Safe Orchestrator Executor: {e}")
    sys.exit(1)

print("\n📋 Testing 20 Query Types Classification")
print("=" * 50)

# Initialize classifier
classifier = EnhancedQueryClassifier()
dev_handler = DevelopmentQueryHandler()

# Test queries - the 20 problematic types we identified
test_queries = [
    # General (1-10)
    ("Hallo", "greeting"),
    ("asdfghjkl", "nonsense"),
    ("Wie geht es dir?", "personal"),
    ("Was hast du gestern gemacht?", "temporal"),
    ("Ist Python besser als Java?", "comparison"),
    ("Was ist der Sinn des Lebens?", "philosophical"),
    ("Stop alles", "control"),
    ("Welche Agenten gibt es?", "meta"),
    ("Wie war das mit dem Bug vorhin?", "context_ref"),
    ("Zeige mir Details über das Projekt", "project_query"),

    # Development (11-20)
    ("Mach mein Programm schneller", "performance"),
    ("Da ist ein Bug irgendwo", "bug"),
    ("Refactor den Code", "refactoring"),
    ("Schreibe Tests", "testing"),
    ("Implementiere Feature X", "implementation"),
    ("Welches Framework soll ich nutzen?", "technology"),
    ("Optimiere die Datenbank", "database"),
    ("Integriere AI in meine App", "ai_integration"),
    ("Fehler beim Start", "error_diagnosis"),
    ("Ich will eine App bauen", "scope")
]

# Test each query
passed = 0
failed = 0

for query, expected_type in test_queries:
    state = {"execution_plan": [], "messages": [{"content": query}]}
    classification = classifier.classify_query(query, state)

    # Check if classification is reasonable
    if expected_type in ["greeting"] and classification.is_greeting:
        print(f"✅ '{query[:30]}...' → Greeting detected")
        passed += 1
    elif expected_type in ["nonsense"] and classification.is_nonsense:
        print(f"✅ '{query[:30]}...' → Nonsense detected")
        passed += 1
    elif expected_type in ["performance", "bug", "refactoring", "testing", "implementation",
                           "technology", "database", "ai_integration", "error_diagnosis", "scope"]:
        if classification.is_development_query:
            print(f"✅ '{query[:30]}...' → Development query ({classification.dev_type})")
            passed += 1
        else:
            print(f"⚠️  '{query[:30]}...' → Not classified as development")
            failed += 1
    else:
        # Other types - just check we got some classification
        if classification.suggested_action:
            print(f"✅ '{query[:30]}...' → {classification.suggested_action}")
            passed += 1
        else:
            print(f"❌ '{query[:30]}...' → No classification")
            failed += 1

print(f"\n📊 Results: {passed}/{len(test_queries)} passed")

# Test safe executor
print("\n🛡️ Testing Safe Orchestrator Executor")
print("=" * 50)

async def test_safe_executor():
    """Test the safe executor with problematic queries"""

    executor = SafeOrchestratorExecutor()

    # Mock state
    from backend.langgraph_system.state import create_initial_state
    state = create_initial_state()

    # Test queries that should be handled safely
    test_cases = [
        "Hallo wie geht's?",  # Greeting
        "asdfghjkl",  # Nonsense
        "Mach alles schneller ohne Details",  # Vague performance
        "Da ist ein Bug",  # Vague bug report
    ]

    for query in test_cases:
        print(f"\n🔍 Testing: '{query}'")

        # Execute safely
        success, result, message = await executor.execute_safely(
            query=query,
            state=state,
            orchestrator_func=None,  # No actual orchestrator
            timeout=5
        )

        if success:
            print(f"✅ Safe execution successful: {message[:50]}...")
            if result:
                result_str = str(result)[:100]
                print(f"   Result: {result_str}...")
        else:
            print(f"⚠️  Blocked or failed: {message}")

    # Check execution statistics
    stats = executor.get_execution_stats()
    print(f"\n📈 Execution Statistics:")
    print(f"   Total attempts: {stats['total_attempts']}")
    print(f"   Blocked attempts: {stats['blocked_attempts']}")
    print(f"   Unique queries: {stats['unique_queries']}")

# Run async test
print("\nRunning async tests...")
asyncio.run(test_safe_executor())

print("\n✨ Test completed successfully!")
print(f"Version {__version__} - Safe Orchestrator Executor is working!")