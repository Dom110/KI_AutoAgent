#!/usr/bin/env python3
"""
Test Curiosity-Driven Task Selection System

Demonstrates how agents prioritize novel tasks over familiar ones
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from langgraph_system.extensions.curiosity_system import CuriosityModule, NoveltyCalculator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_curiosity_system():
    """Test the curiosity-driven exploration system"""
    logger.info("=" * 80)
    logger.info("🔍 Testing Curiosity-Driven Task Selection System")
    logger.info("=" * 80)

    # Create curiosity module for a test agent
    curiosity = CuriosityModule(agent_name="TestAgent")

    # =========================================================================
    # SCENARIO 1: Agent encounters authentication tasks multiple times
    # =========================================================================
    logger.info("\n📝 SCENARIO 1: Familiar Task (Authentication)")
    logger.info("-" * 80)

    # Agent has done authentication 5 times before
    for i in range(5):
        curiosity.record_task_encounter(
            task_id=f"auth_task_{i}",
            task_description="Build authentication system with JWT tokens",
            outcome="success",
            category="authentication"
        )

    # Now a new authentication task comes in
    auth_task = "Implement authentication system with OAuth"
    base_priority = 0.8  # High importance task

    final_priority = curiosity.calculate_task_priority_with_curiosity(
        task_description=auth_task,
        base_priority=base_priority,
        category="authentication"
    )

    logger.info(f"\n📊 Priority Calculation:")
    logger.info(f"   Task: {auth_task}")
    logger.info(f"   Base Priority: {base_priority:.2f} (Important)")
    logger.info(f"   Final Priority: {final_priority:.2f} (Adjusted for familiarity)")
    logger.info(f"   → Priority DECREASED because agent has done this 5 times before")

    # =========================================================================
    # SCENARIO 2: Agent encounters completely novel task
    # =========================================================================
    logger.info("\n📝 SCENARIO 2: Novel Task (WebRTC)")
    logger.info("-" * 80)

    # Brand new technology the agent has never worked with
    webrtc_task = "Implement WebRTC video chat with screen sharing"
    base_priority = 0.6  # Medium importance

    final_priority_novel = curiosity.calculate_task_priority_with_curiosity(
        task_description=webrtc_task,
        base_priority=base_priority,
        category="realtime_communication"
    )

    logger.info(f"\n📊 Priority Calculation:")
    logger.info(f"   Task: {webrtc_task}")
    logger.info(f"   Base Priority: {base_priority:.2f} (Medium importance)")
    logger.info(f"   Final Priority: {final_priority_novel:.2f} (Boosted by novelty!)")
    logger.info(f"   → Priority INCREASED because this is completely new territory")

    # =========================================================================
    # SCENARIO 3: Agent encounters similar but different task
    # =========================================================================
    logger.info("\n📝 SCENARIO 3: Related Task (Database)")
    logger.info("-" * 80)

    # Agent has done some database work before
    curiosity.record_task_encounter(
        task_id="db_task_1",
        task_description="Setup PostgreSQL database with migrations",
        outcome="success",
        category="database"
    )
    curiosity.record_task_encounter(
        task_id="db_task_2",
        task_description="Create MySQL database schema",
        outcome="success",
        category="database"
    )

    # Now a related but different database task
    db_task = "Implement MongoDB with aggregation pipelines"
    base_priority = 0.7

    final_priority_related = curiosity.calculate_task_priority_with_curiosity(
        task_description=db_task,
        base_priority=base_priority,
        category="database"
    )

    logger.info(f"\n📊 Priority Calculation:")
    logger.info(f"   Task: {db_task}")
    logger.info(f"   Base Priority: {base_priority:.2f}")
    logger.info(f"   Final Priority: {final_priority_related:.2f} (Slightly adjusted)")
    logger.info(f"   → Some database experience, but MongoDB is different enough to be interesting")

    # =========================================================================
    # SCENARIO 4: Failed task increases novelty
    # =========================================================================
    logger.info("\n📝 SCENARIO 4: Previously Failed Task")
    logger.info("-" * 80)

    # Agent tried this before and failed
    curiosity.record_task_encounter(
        task_id="ml_task_1",
        task_description="Build neural network for image classification",
        outcome="failure",
        category="machine_learning"
    )

    # Same type of task comes up again
    ml_task = "Implement CNN for image recognition"
    base_priority = 0.65

    final_priority_failed = curiosity.calculate_task_priority_with_curiosity(
        task_description=ml_task,
        base_priority=base_priority,
        category="machine_learning"
    )

    logger.info(f"\n📊 Priority Calculation:")
    logger.info(f"   Task: {ml_task}")
    logger.info(f"   Base Priority: {base_priority:.2f}")
    logger.info(f"   Final Priority: {final_priority_failed:.2f}")
    logger.info(f"   → Similar to failed task - still challenging, priority may be higher")

    # =========================================================================
    # SCENARIO 5: Adjusting exploration weight
    # =========================================================================
    logger.info("\n📝 SCENARIO 5: Adjusting Exploration Weight")
    logger.info("-" * 80)

    # Default: 30% curiosity, 70% importance
    logger.info("\n   Default (30% curiosity, 70% importance):")
    curiosity.set_exploration_weight(0.3)
    priority_default = curiosity.calculate_task_priority_with_curiosity(
        webrtc_task, base_priority=0.5
    )
    logger.info(f"   → Final Priority: {priority_default:.2f}")

    # High curiosity: 70% curiosity, 30% importance
    logger.info("\n   High Curiosity (70% curiosity, 30% importance):")
    curiosity.set_exploration_weight(0.7)
    priority_high_curiosity = curiosity.calculate_task_priority_with_curiosity(
        webrtc_task, base_priority=0.5
    )
    logger.info(f"   → Final Priority: {priority_high_curiosity:.2f}")
    logger.info(f"   → Novel tasks get MUCH higher priority with high curiosity!")

    # Pure exploitation: 0% curiosity, 100% importance
    logger.info("\n   Pure Exploitation (0% curiosity, 100% importance):")
    curiosity.set_exploration_weight(0.0)
    priority_no_curiosity = curiosity.calculate_task_priority_with_curiosity(
        webrtc_task, base_priority=0.5
    )
    logger.info(f"   → Final Priority: {priority_no_curiosity:.2f}")
    logger.info(f"   → Novelty ignored, only base priority matters")

    # Reset to default
    curiosity.set_exploration_weight(0.3)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    logger.info("\n📊 EXPLORATION SUMMARY:")
    logger.info("=" * 80)
    summary = curiosity.get_exploration_summary()
    logger.info(f"Total tasks encountered: {summary['total_tasks']}")
    logger.info(f"Unique categories: {summary['unique_categories']}")
    logger.info(f"Exploration breadth: {summary['exploration_breadth']:.2%}")
    logger.info("")
    logger.info("Category Statistics:")
    for category, stats in summary['category_stats'].items():
        success_rate = (stats['successes'] / stats['count'] * 100) if stats['count'] > 0 else 0
        logger.info(f"  {category}:")
        logger.info(f"    Total: {stats['count']}, Successes: {stats['successes']}, Failures: {stats['failures']}")
        logger.info(f"    Success Rate: {success_rate:.1f}%")

    # =========================================================================
    # PRACTICAL EXAMPLE: Task Queue Reordering
    # =========================================================================
    logger.info("\n🎯 PRACTICAL EXAMPLE: Task Queue Reordering")
    logger.info("=" * 80)

    tasks_to_prioritize = [
        ("Fix authentication bug", 0.9, "authentication"),  # Critical but familiar
        ("Implement blockchain smart contract", 0.5, "blockchain"),  # Novel but lower importance
        ("Add database index", 0.7, "database"),  # Moderately familiar
        ("Setup CI/CD pipeline", 0.6, "devops"),  # Somewhat novel
    ]

    logger.info("\nOriginal Task Order (by importance only):")
    for i, (task, priority, category) in enumerate(tasks_to_prioritize, 1):
        logger.info(f"{i}. {task} (priority: {priority:.2f})")

    # Calculate curiosity-adjusted priorities
    adjusted_tasks = []
    for task, base_priority, category in tasks_to_prioritize:
        final_priority = curiosity.calculate_task_priority_with_curiosity(
            task_description=task,
            base_priority=base_priority,
            category=category
        )
        adjusted_tasks.append((task, base_priority, final_priority, category))

    # Sort by final priority (descending)
    adjusted_tasks.sort(key=lambda x: x[2], reverse=True)

    logger.info("\nReordered Task Queue (with curiosity):")
    for i, (task, base_pri, final_pri, category) in enumerate(adjusted_tasks, 1):
        change = final_pri - base_pri
        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
        logger.info(f"{i}. {task}")
        logger.info(f"   Base: {base_pri:.2f} → Final: {final_pri:.2f} {arrow}")

    logger.info("\n✅ Curiosity System Test Completed!")
    logger.info("=" * 80)
    logger.info("\n💡 Key Takeaways:")
    logger.info("   1. Novel tasks get priority boost (exploration)")
    logger.info("   2. Familiar tasks get priority reduction (exploitation)")
    logger.info("   3. Failed tasks maintain higher novelty (still challenging)")
    logger.info("   4. Exploration weight controls balance (default 30% curiosity)")
    logger.info("   5. Agent learns what it has/hasn't explored")


if __name__ == "__main__":
    test_curiosity_system()
