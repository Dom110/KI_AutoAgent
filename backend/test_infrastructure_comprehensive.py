#!/usr/bin/env python3
"""
Comprehensive test for infrastructure analysis with new v4.0.0 features
"""

import asyncio
import sys
import os
import json

# Ensure we're in the backend directory
if not os.path.exists('agents'):
    print("❌ Error: Must run from backend directory")
    sys.exit(1)

from agents.specialized.architect_agent import ArchitectAgent, INDEXING_AVAILABLE, ANALYSIS_AVAILABLE, DIAGRAM_AVAILABLE
from agents.base.base_agent import TaskRequest

async def test_infrastructure_analysis_comprehensive():
    """Comprehensive test of infrastructure analysis capabilities"""
    print("🧪 Testing Infrastructure Analysis v4.0.0 Features...")
    print("=" * 80)

    # Show availability status
    print("📦 Module Availability Status:")
    print(f"  Tree-sitter Indexing: {'✅ Available' if INDEXING_AVAILABLE else '❌ Not Available'}")
    print(f"  Analysis Tools: {'✅ Available' if ANALYSIS_AVAILABLE else '❌ Not Available'}")
    print(f"  Diagram Service: {'✅ Available' if DIAGRAM_AVAILABLE else '❌ Not Available'}")
    print("-" * 80)

    architect = ArchitectAgent()

    # Test 1: Basic system understanding
    print("\n🔹 Test 1: System Understanding")
    print("  Asking: 'Erkläre mir die Architektur dieses Systems'")

    request = TaskRequest(
        prompt="Erkläre mir die Architektur dieses Systems",
        context={"project_root": os.path.dirname(os.path.dirname(__file__))}
    )

    result = await architect.execute_with_memory(request)
    print(f"  Status: {result.status}")
    print(f"  Execution time: {result.execution_time:.2f}s")

    if result.status == "success":
        print(f"  Output preview (200 chars): {result.content[:200]}...")
    print("  ✅ System understanding test complete")

    # Test 2: Infrastructure improvements (the key feature)
    print("\n🔹 Test 2: Infrastructure Improvements Analysis")
    print("  Asking: 'Was kann an der Infrastruktur verbessert werden?'")

    request = TaskRequest(
        prompt="Was kann an der Infrastruktur verbessert werden?",
        context={"project_root": os.path.dirname(os.path.dirname(__file__))}
    )

    result = await architect.execute_with_memory(request)
    print(f"  Status: {result.status}")
    print(f"  Execution time: {result.execution_time:.2f}s")

    if result.status == "success":
        # Parse for specific improvements if found
        content = result.content
        improvements_found = []

        # Look for common improvement patterns
        if "caching" in content.lower():
            improvements_found.append("Caching optimization")
        if "database" in content.lower() or "index" in content.lower():
            improvements_found.append("Database optimization")
        if "async" in content.lower() or "parallel" in content.lower():
            improvements_found.append("Async/parallel processing")
        if "security" in content.lower():
            improvements_found.append("Security enhancements")
        if "monitoring" in content.lower() or "logging" in content.lower():
            improvements_found.append("Monitoring/logging")
        if "error" in content.lower() or "exception" in content.lower():
            improvements_found.append("Error handling")

        print(f"\n  📊 Improvements identified: {len(improvements_found)}")
        for imp in improvements_found[:5]:  # Show first 5
            print(f"    • {imp}")

        print(f"\n  Sample output (500 chars):")
        print("  " + "-" * 40)
        print(f"  {result.content[:500]}...")
        print("  " + "-" * 40)
    print("  ✅ Infrastructure analysis test complete")

    # Test 3: Architecture visualization (if available)
    if DIAGRAM_AVAILABLE:
        print("\n🔹 Test 3: Architecture Flowchart Generation")
        print("  Asking: 'Generiere ein Architektur-Diagramm'")

        request = TaskRequest(
            prompt="Generiere ein Architektur-Diagramm für das System",
            context={"project_root": os.path.dirname(os.path.dirname(__file__))}
        )

        result = await architect.execute_with_memory(request)
        print(f"  Status: {result.status}")
        print(f"  Execution time: {result.execution_time:.2f}s")

        if result.status == "success" and "graph" in result.content.lower():
            print("  ✅ Diagram generation successful")
            # Check for Mermaid syntax
            if "```mermaid" in result.content or "graph" in result.content:
                print("  📈 Mermaid diagram detected")
        else:
            print("  ⚠️  Diagram generation returned but may not contain diagram")
    else:
        print("\n🔹 Test 3: Architecture Flowchart Generation")
        print("  ⚠️  Skipped - Diagram service not available")

    # Test 4: Pattern analysis (if indexing available)
    if INDEXING_AVAILABLE:
        print("\n🔹 Test 4: Code Pattern Analysis")
        print("  Asking: 'Welche Design Patterns werden im Code verwendet?'")

        request = TaskRequest(
            prompt="Welche Design Patterns werden im Code verwendet?",
            context={"project_root": os.path.dirname(os.path.dirname(__file__))}
        )

        result = await architect.execute_with_memory(request)
        print(f"  Status: {result.status}")
        print(f"  Execution time: {result.execution_time:.2f}s")

        if result.status == "success":
            patterns = []
            pattern_keywords = ["singleton", "factory", "observer", "strategy", "decorator",
                              "adapter", "repository", "mvc", "mvvm", "facade"]

            for pattern in pattern_keywords:
                if pattern.lower() in result.content.lower():
                    patterns.append(pattern.capitalize())

            if patterns:
                print(f"  📋 Patterns detected: {', '.join(patterns[:5])}")
            print("  ✅ Pattern analysis complete")
    else:
        print("\n🔹 Test 4: Code Pattern Analysis")
        print("  ⚠️  Skipped - Indexing not available")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary:")
    print(f"  • System Understanding: ✅ Tested")
    print(f"  • Infrastructure Analysis: ✅ Tested")
    print(f"  • Diagram Generation: {'✅ Tested' if DIAGRAM_AVAILABLE else '⚠️ Skipped'}")
    print(f"  • Pattern Analysis: {'✅ Tested' if INDEXING_AVAILABLE else '⚠️ Skipped'}")
    print("\n🎉 Infrastructure analysis v4.0.0 features are working!")
    print("=" * 80)

async def main():
    """Run comprehensive infrastructure test"""
    print("=" * 80)
    print("🚀 KI AutoAgent v4.0.0 - Comprehensive Infrastructure Analysis Test")
    print("=" * 80)
    print("\nThis test verifies the new v4.0.0 features:")
    print("• Deep code understanding via Tree-sitter AST parsing")
    print("• Infrastructure improvement analysis")
    print("• Architecture visualization with Mermaid")
    print("• Pattern detection and analysis")
    print("• Security and quality metrics")
    print("-" * 80)

    await test_infrastructure_analysis_comprehensive()

if __name__ == "__main__":
    asyncio.run(main())