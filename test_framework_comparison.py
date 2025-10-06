#!/usr/bin/env python3
"""
Test Framework Comparison System (Systemvergleich-Analyse)

Demonstrates how to compare KI_AutoAgent decisions with other frameworks
and extract best practices for learning.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from langgraph_system.extensions.framework_comparison import FrameworkComparator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_framework_comparison():
    """Test the framework comparison system"""
    logger.info("=" * 80)
    logger.info("🔍 Testing Framework Comparison System (Systemvergleich)")
    logger.info("=" * 80)

    comparator = FrameworkComparator()

    # =========================================================================
    # SCENARIO 1: Multi-Agent Architecture Decision
    # =========================================================================
    logger.info("\n📝 SCENARIO 1: Multi-Agent Architecture")
    logger.info("-" * 80)

    analysis = comparator.compare_architecture_decision(
        decision="Use multiple specialized agents for software development (Architect, CodeSmith, Reviewer, Fixer)",
        context={
            "task_type": "software_development",
            "complexity": "high"
        }
    )

    logger.info(f"\n📊 Analysis Results:")
    logger.info(f"   Patterns found: {len(analysis['similar_patterns'])}")
    logger.info(f"   Recommendations: {len(analysis['recommendations'])}")
    logger.info(f"   Best practices: {len(analysis['best_practices'])}")
    logger.info(f"   Risks identified: {len(analysis['risk_assessment'])}")

    logger.info("\n🔍 Similar Patterns in Other Frameworks:")
    for pattern_info in analysis['similar_patterns']:
        logger.info(f"\n   Pattern: {pattern_info['pattern']}")
        logger.info(f"   Frameworks: {', '.join(pattern_info['frameworks'])}")
        for approach in pattern_info['approaches']:
            logger.info(f"      • {approach['framework']}: {approach['approach']}")
            logger.info(f"        → Benefit: {approach['benefit']}")

    logger.info("\n💡 Recommendations:")
    for rec in analysis['recommendations']:
        logger.info(f"   • [{rec['priority'].upper()}] {rec['recommendation']}")
        logger.info(f"     Rationale: {rec['rationale']}")

    logger.info("\n⚠️ Risk Assessment:")
    for risk in analysis['risk_assessment']:
        logger.info(f"   • {risk['risk']} (Severity: {risk['severity']})")
        logger.info(f"     {risk['description']}")
        logger.info(f"     Mitigation: {risk['mitigation']}")

    # =========================================================================
    # SCENARIO 2: Human Oversight Decision
    # =========================================================================
    logger.info("\n📝 SCENARIO 2: Human Oversight with Approval Gates")
    logger.info("-" * 80)

    analysis2 = comparator.compare_architecture_decision(
        decision="Implement architecture approval gate before code generation",
        context={
            "has_approval": True,
            "human_oversight": True
        }
    )

    logger.info(f"\n📊 Analysis Results:")
    for pattern_info in analysis2['similar_patterns']:
        logger.info(f"\n   Pattern: {pattern_info['pattern']}")
        for approach in pattern_info['approaches']:
            logger.info(f"   • {approach['framework']}: {approach['approach']}")

    logger.info("\n💡 Key Recommendation:")
    if analysis2['recommendations']:
        top_rec = analysis2['recommendations'][0]
        logger.info(f"   {top_rec['recommendation']}")
        logger.info(f"   → {top_rec['rationale']}")

    # =========================================================================
    # SCENARIO 3: Task Decomposition Strategy
    # =========================================================================
    logger.info("\n📝 SCENARIO 3: Task Decomposition Strategy")
    logger.info("-" * 80)

    analysis3 = comparator.compare_architecture_decision(
        decision="Use AI-driven task decomposition with subtask creation",
        context={
            "autonomous": True,
            "dynamic_planning": True
        }
    )

    logger.info(f"\n📊 What Other Frameworks Do:")
    for pattern_info in analysis3['similar_patterns']:
        if pattern_info['pattern'] == "Task Decomposition":
            for approach in pattern_info['approaches']:
                logger.info(f"\n   {approach['framework']}:")
                logger.info(f"      Approach: {approach['approach']}")
                logger.info(f"      Benefit: {approach['benefit']}")

    # =========================================================================
    # SCENARIO 4: Framework Profiles
    # =========================================================================
    logger.info("\n📝 SCENARIO 4: Detailed Framework Profiles")
    logger.info("-" * 80)

    frameworks_to_explore = ["autogen", "crewai", "chatdev", "langgraph"]

    for fw_name in frameworks_to_explore:
        profile = comparator.get_framework_profile(fw_name)
        if profile:
            logger.info(f"\n🔍 {profile.name}:")
            logger.info(f"   Category: {profile.category.value}")
            logger.info(f"   Pattern: {profile.architecture_pattern}")
            logger.info(f"   Popularity: {profile.popularity_score:.0%}")
            logger.info(f"   Strengths: {', '.join(profile.strengths[:2])}")
            logger.info(f"   Best for: {profile.best_for[0]}")

    # =========================================================================
    # SCENARIO 5: Learning from Best Practices
    # =========================================================================
    logger.info("\n📝 SCENARIO 5: Extracting Best Practices")
    logger.info("-" * 80)

    # Collect all best practices
    all_best_practices = set()
    for pattern_info in analysis['similar_patterns']:
        for approach in pattern_info['approaches']:
            all_best_practices.add(approach['benefit'])

    logger.info("\n📚 Key Best Practices from Other Frameworks:")
    for i, practice in enumerate(list(all_best_practices)[:5], 1):
        logger.info(f"   {i}. {practice}")

    # =========================================================================
    # SCENARIO 6: Our Framework (LangGraph)
    # =========================================================================
    logger.info("\n📝 SCENARIO 6: Our Foundation - LangGraph")
    logger.info("-" * 80)

    langgraph = comparator.get_framework_profile("langgraph")
    if langgraph:
        logger.info(f"\n✅ KI_AutoAgent is built on: {langgraph.name}")
        logger.info(f"   Description: {langgraph.description}")
        logger.info(f"\n   Key Strengths:")
        for strength in langgraph.strengths:
            logger.info(f"      • {strength}")

        logger.info(f"\n   Key Features:")
        for feature in langgraph.key_features[:2]:
            logger.info(f"      • {feature.name}: {feature.description}")
            logger.info(f"        → {feature.benefit}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("📊 FRAMEWORK COMPARISON SUMMARY")
    logger.info("=" * 80)

    summary = comparator.get_comparison_summary()
    logger.info(f"\nTotal Comparisons: {summary['total_comparisons']}")
    logger.info(f"Frameworks in Database: {summary['frameworks_in_db']}")
    logger.info(f"Categories: {', '.join(summary['framework_categories'])}")

    logger.info("\n💡 How to Use This as Learning Tool:")
    logger.info("   1. Compare your architecture decisions with successful frameworks")
    logger.info("   2. Identify patterns that work well in other systems")
    logger.info("   3. Extract best practices and apply to KI_AutoAgent")
    logger.info("   4. Assess risks based on other frameworks' experiences")
    logger.info("   5. Stay informed about industry standards")

    logger.info("\n🎯 Example Use Cases:")
    logger.info("   • Architect: Validate design decisions before implementation")
    logger.info("   • Orchestrator: Learn task decomposition strategies")
    logger.info("   • ReviewBot: Check if patterns align with best practices")
    logger.info("   • Team Lead: Understand trade-offs between approaches")

    logger.info("\n✅ Framework Comparison Test Completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_framework_comparison()
