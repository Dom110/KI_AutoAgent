"""
E2E Tests for Query Classifier v6

Tests:
1. Code generation classification
2. Bug fix classification
3. Research classification
4. Complexity detection (trivial to very complex)
5. Entity extraction
6. Refinement suggestions
7. Multi-type ambiguous query

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from cognitive.query_classifier_v6 import (
    ComplexityLevel,
    QueryClassifierV6,
    QueryType,
)


async def test_1_code_generation():
    """Test 1: Classify code generation query"""
    print("\n" + "=" * 80)
    print("TEST 1: Code generation classification")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Create a new React component for user authentication"

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Complexity: {classification.complexity.value}")
    print(f"✅ Confidence: {classification.confidence:.2f}")
    print(f"✅ Agents: {classification.required_agents}")
    print(f"✅ Workflow: {classification.workflow_type}")
    print(f"✅ Entities: {classification.entities}")

    assert classification.query_type == QueryType.CODE_GENERATION, "Should be CODE_GENERATION"
    assert "architect" in classification.required_agents, "Should require architect"
    assert "codesmith" in classification.required_agents, "Should require codesmith"
    assert "react" in classification.entities["technologies"], "Should detect React"

    print("✅ Test 1 PASSED: Code generation classification works")
    return True


async def test_2_bug_fix():
    """Test 2: Classify bug fix query"""
    print("\n" + "=" * 80)
    print("TEST 2: Bug fix classification")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Fix the bug in login.py - authentication is failing"

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Agents: {classification.required_agents}")
    print(f"✅ Entities: {classification.entities}")

    assert classification.query_type == QueryType.BUG_FIX, "Should be BUG_FIX"
    assert "reviewer" in classification.required_agents, "Should require reviewer"
    assert "fixer" in classification.required_agents, "Should require fixer"
    assert "py" in classification.entities["file_types"], "Should detect .py file"

    print("✅ Test 2 PASSED: Bug fix classification works")
    return True


async def test_3_research():
    """Test 3: Classify research query"""
    print("\n" + "=" * 80)
    print("TEST 3: Research classification")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Research best practices for PostgreSQL connection pooling"

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Agents: {classification.required_agents}")
    print(f"✅ Entities: {classification.entities}")

    assert classification.query_type == QueryType.RESEARCH, "Should be RESEARCH"
    assert "research" in classification.required_agents, "Should require research agent"
    assert "postgresql" in classification.entities["technologies"], "Should detect PostgreSQL"

    print("✅ Test 3 PASSED: Research classification works")
    return True


async def test_4_complexity_trivial():
    """Test 4: Detect trivial complexity"""
    print("\n" + "=" * 80)
    print("TEST 4: Trivial complexity")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Add quick comment"

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Complexity: {classification.complexity.value}")
    print(f"✅ Word count: {classification.metadata['word_count']}")

    assert classification.complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE], \
        f"Should be TRIVIAL or SIMPLE, got {classification.complexity.value}"

    print("✅ Test 4 PASSED: Trivial complexity detection works")
    return True


async def test_5_complexity_complex():
    """Test 5: Detect complex complexity"""
    print("\n" + "=" * 80)
    print("TEST 5: Complex complexity")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = """Build a complete microservices architecture for an enterprise e-commerce system
    with user management, product catalog, shopping cart, payment processing, and order tracking.
    Use Docker and Kubernetes for deployment, PostgreSQL for database, Redis for caching,
    and implement comprehensive testing and monitoring."""

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Complexity: {classification.complexity.value}")
    print(f"✅ Word count: {classification.metadata['word_count']}")
    print(f"✅ Technologies: {classification.entities['technologies']}")

    assert classification.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX], \
        f"Should be COMPLEX or VERY_COMPLEX, got {classification.complexity.value}"

    # Should detect multiple technologies
    assert len(classification.entities["technologies"]) >= 3, "Should detect multiple technologies"

    print("✅ Test 5 PASSED: Complex complexity detection works")
    return True


async def test_6_entity_extraction():
    """Test 6: Entity extraction"""
    print("\n" + "=" * 80)
    print("TEST 6: Entity extraction")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Build a Python FastAPI backend with MongoDB and deploy to AWS using Docker"

    classification = await classifier.classify_query(query)

    print(f"✅ Technologies: {classification.entities['technologies']}")
    print(f"✅ Languages: {classification.entities['languages']}")
    print(f"✅ Actions: {classification.entities['actions']}")

    # Should detect technologies
    detected_techs = classification.entities["technologies"]
    assert "python" in detected_techs, "Should detect Python"
    assert "fastapi" in detected_techs, "Should detect FastAPI"
    assert "mongodb" in detected_techs, "Should detect MongoDB"
    assert "aws" in detected_techs, "Should detect AWS"
    assert "docker" in detected_techs, "Should detect Docker"

    # Should detect language
    assert "python" in classification.entities["languages"], "Should detect Python language"

    # Should detect actions
    actions = classification.entities["actions"]
    assert any(action in ["build", "deploy"] for action in actions), "Should detect build or deploy action"

    print("✅ Test 6 PASSED: Entity extraction works")
    return True


async def test_7_refinement_suggestions():
    """Test 7: Refinement suggestions for vague queries"""
    print("\n" + "=" * 80)
    print("TEST 7: Refinement suggestions")
    print("=" * 80)

    classifier = QueryClassifierV6()

    # Vague query with no technology context
    query = "Make it better"

    classification = await classifier.classify_query(query)
    suggestions = await classifier.suggest_refinements(classification)

    print(f"✅ Confidence: {classification.confidence:.2f}")
    print(f"✅ Suggestions ({len(suggestions)}):")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion[:80]}...")

    # Should have suggestions for vague query
    assert len(suggestions) > 0, "Should provide suggestions for vague query"

    # Should suggest specifying technology
    technology_suggestion = any("language" in s.lower() or "technology" in s.lower() for s in suggestions)
    assert technology_suggestion, "Should suggest specifying technology/language"

    print("✅ Test 7 PASSED: Refinement suggestions work")
    return True


async def test_8_code_review():
    """Test 8: Code review classification"""
    print("\n" + "=" * 80)
    print("TEST 8: Code review classification")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Review this TypeScript code for security issues"

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Agents: {classification.required_agents}")
    print(f"✅ Languages: {classification.entities['languages']}")

    assert classification.query_type == QueryType.CODE_REVIEW, "Should be CODE_REVIEW"
    assert "reviewer" in classification.required_agents, "Should require reviewer"
    assert "typescript" in classification.entities["languages"], "Should detect TypeScript"

    print("✅ Test 8 PASSED: Code review classification works")
    return True


async def test_9_architecture():
    """Test 9: Architecture design classification"""
    print("\n" + "=" * 80)
    print("TEST 9: Architecture design classification")
    print("=" * 80)

    classifier = QueryClassifierV6()

    query = "Design the system architecture for a real-time chat application"

    classification = await classifier.classify_query(query)

    print(f"✅ Type: {classification.query_type.value}")
    print(f"✅ Workflow: {classification.workflow_type}")
    print(f"✅ Agents: {classification.required_agents}")

    assert classification.query_type == QueryType.ARCHITECTURE, "Should be ARCHITECTURE"
    assert "architect" in classification.required_agents, "Should require architect"
    assert classification.workflow_type == "design_workflow", "Should use design workflow"

    print("✅ Test 9 PASSED: Architecture classification works")
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 QUERY CLASSIFIER V6 E2E TESTS")
    print("=" * 80)

    tests = [
        test_1_code_generation,
        test_2_bug_fix,
        test_3_research,
        test_4_complexity_trivial,
        test_5_complexity_complex,
        test_6_entity_extraction,
        test_7_refinement_suggestions,
        test_8_code_review,
        test_9_architecture,
    ]

    results = []

    for i, test in enumerate(tests, 1):
        try:
            result = await test()
            results.append(("PASS", test.__name__))
            print(f"\n✅ Test {i}/{len(tests)} PASSED")
        except AssertionError as e:
            results.append(("FAIL", test.__name__, str(e)))
            print(f"\n❌ Test {i}/{len(tests)} FAILED: {e}")
        except Exception as e:
            results.append(("ERROR", test.__name__, str(e)))
            print(f"\n💥 Test {i}/{len(tests)} ERROR: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    errors = sum(1 for r in results if r[0] == "ERROR")

    for result in results:
        status = result[0]
        name = result[1]
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "💥"
        print(f"{icon} {name}: {status}")
        if len(result) > 2:
            print(f"   {result[2]}")

    print(f"\n{'='*80}")
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print(f"{'='*80}")

    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n❌ {failed + errors} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
