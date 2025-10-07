#!/usr/bin/env python3
"""
Test Script for Enhanced System Understanding Capabilities

This script demonstrates how ArchitectAgent and CodeSmithAgent
can now deeply understand and analyze the codebase.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agents.specialized.architect_agent import ArchitectAgent
from agents.specialized.codesmith_agent import CodeSmithAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_architect_understanding():
    """Test ArchitectAgent's system understanding capabilities"""
    print("\n" + "=" * 80)
    print("🏗️  Testing ArchitectAgent System Understanding")
    print("=" * 80)

    architect = ArchitectAgent()

    # Test 1: Build complete system understanding
    print("\n📊 Building comprehensive system understanding...")
    try:
        system_knowledge = await architect.understand_system(".")

        print("\n✅ System Understanding Complete!")
        print(
            f"  - Files indexed: {len(system_knowledge['code_index'].get('ast', {}).get('files', {}))}"
        )
        print(
            f"  - Functions found: {len(system_knowledge['code_index'].get('ast', {}).get('functions', {}))}"
        )
        print(
            f"  - Classes found: {len(system_knowledge['code_index'].get('ast', {}).get('classes', {}))}"
        )
        print(
            f"  - API endpoints: {len(system_knowledge['code_index'].get('ast', {}).get('api_endpoints', {}))}"
        )

        # Security summary
        security = system_knowledge.get("security", {}).get("summary", {})
        print("\n🔒 Security Analysis:")
        print(f"  - Critical: {security.get('critical', 0)}")
        print(f"  - High: {security.get('high', 0)}")
        print(f"  - Medium: {security.get('medium', 0)}")
        print(f"  - Low: {security.get('low', 0)}")

        # Metrics summary
        metrics = system_knowledge.get("metrics", {}).get("summary", {})
        print("\n📈 Code Metrics:")
        print(f"  - Average Complexity: {metrics.get('average_complexity', 0):.1f}")
        print(f"  - Maintainability: {metrics.get('average_maintainability', 0):.1f}")
        print(f"  - Quality Score: {metrics.get('quality_score', 0):.1f}")

    except Exception as e:
        print(f"❌ Error building system understanding: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Infrastructure improvement analysis
    print("\n🔍 Analyzing infrastructure improvements...")
    try:
        improvements = await architect.analyze_infrastructure_improvements()

        # Just show summary, not full report
        print("\n✅ Infrastructure Analysis Complete!")
        print("Key improvements identified - see full report for details")

        # Save report to file
        with open("infrastructure_report.md", "w") as f:
            f.write(improvements)
        print("📄 Full report saved to: infrastructure_report.md")

    except Exception as e:
        print(f"❌ Error analyzing infrastructure: {e}")

    # Test 3: Generate architecture flowchart
    print("\n📊 Generating architecture flowchart...")
    try:
        flowchart = await architect.generate_architecture_flowchart()

        print("✅ Flowchart generated!")

        # Save flowchart to file
        with open("architecture_flowchart.md", "w") as f:
            f.write(flowchart)
        print("📄 Flowchart saved to: architecture_flowchart.md")

    except Exception as e:
        print(f"❌ Error generating flowchart: {e}")


async def test_codesmith_understanding():
    """Test CodeSmithAgent's code analysis capabilities"""
    print("\n" + "=" * 80)
    print("💻 Testing CodeSmithAgent Code Intelligence")
    print("=" * 80)

    codesmith = CodeSmithAgent()

    # Test 1: Analyze codebase
    print("\n📊 Analyzing codebase for patterns...")
    try:
        code_knowledge = await codesmith.analyze_codebase(".")

        print("\n✅ Code Analysis Complete!")

        # Pattern summary
        patterns = code_knowledge.get("patterns", {})
        print("\n📋 Patterns Found:")
        print(f"  - Design Patterns: {len(patterns.get('design_patterns', []))}")
        print(f"  - Anti-patterns: {len(patterns.get('anti_patterns', []))}")
        print(f"  - Code Smells: {len(patterns.get('code_smells', []))}")
        print(f"  - Performance Issues: {len(patterns.get('performance_issues', []))}")

        # Dead code summary
        dead_code = code_knowledge.get("dead_code", {}).get("summary", {})
        print("\n🧹 Dead Code:")
        print(f"  - Unused Functions: {dead_code.get('unused_functions', 0)}")
        print(f"  - Unused Variables: {dead_code.get('unused_variables', 0)}")
        print(f"  - Unused Imports: {dead_code.get('unused_imports', 0)}")
        print(f"  - Total Dead Code: {dead_code.get('total_dead_code', 0)}")

    except Exception as e:
        print(f"❌ Error analyzing codebase: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Generate dead code cleanup
    print("\n🧹 Generating dead code cleanup script...")
    try:
        cleanup_report = await codesmith.cleanup_dead_code()

        if "No dead code found" in cleanup_report:
            print("✅ No dead code found - codebase is clean!")
        else:
            print("✅ Cleanup script generated!")

            # Save cleanup report
            with open("dead_code_cleanup.md", "w") as f:
                f.write(cleanup_report)
            print("📄 Cleanup report saved to: dead_code_cleanup.md")

    except Exception as e:
        print(f"❌ Error generating cleanup: {e}")

    # Test 3: Find refactoring opportunities
    print("\n🔧 Identifying refactoring opportunities...")
    try:
        refactorings = await codesmith.refactor_complex_code()

        if refactorings:
            print(f"✅ Found {len(refactorings)} refactoring opportunities!")
            for i, ref in enumerate(refactorings, 1):
                original = ref["original"]
                print(
                    f"  {i}. {original.get('name', 'Unknown')} - Complexity: {original.get('complexity', 'N/A')}"
                )
        else:
            print("✅ No complex code requiring refactoring!")

    except Exception as e:
        print(f"❌ Error finding refactorings: {e}")


async def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("🚀 KI AutoAgent Enhanced System Understanding Test")
    print("=" * 80)
    print("\nThis test demonstrates the new capabilities for:")
    print("  ✅ Deep code indexing with Tree-sitter AST")
    print("  ✅ Security analysis with Semgrep patterns")
    print("  ✅ Dead code detection with Vulture")
    print("  ✅ Code metrics with Radon")
    print("  ✅ Architecture visualization with Mermaid")
    print("  ✅ Infrastructure improvement suggestions")

    # Test ArchitectAgent
    await test_architect_understanding()

    # Test CodeSmithAgent
    await test_codesmith_understanding()

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
    print("\n📄 Generated Files:")
    print("  - infrastructure_report.md - Complete infrastructure analysis")
    print("  - architecture_flowchart.md - System architecture diagram")
    print("  - dead_code_cleanup.md - Dead code cleanup script")
    print("\n🎯 Next Steps:")
    print("  1. Review the infrastructure_report.md for improvement suggestions")
    print("  2. View architecture_flowchart.md with a Mermaid renderer")
    print("  3. Run the cleanup script if dead code was found")


if __name__ == "__main__":
    asyncio.run(main())
