"""
Test Orchestrator Step Creation

Verifies that Orchestrator creates multi-agent workflows for development tasks
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from langgraph_system.workflow import _create_execution_steps
from agents.base.base_agent import TaskRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


def test_development_task_detection():
    """Test if development tasks are correctly detected"""

    test_cases = [
        {
            'agent': 'orchestrator',
            'task': 'Entwickle eine Tetris Webapplikation',
            'expected': 'multi-step'
        },
        {
            'agent': 'orchestrator',
            'task': 'Create a web application with HTML',
            'expected': 'multi-step'
        },
        {
            'agent': 'orchestrator',
            'task': 'Build a game in HTML5 Canvas',
            'expected': 'multi-step'
        },
        {
            'agent': 'orchestrator',
            'task': 'Explain how TCP works',
            'expected': 'single-step'
        },
    ]

    logger.info("=" * 80)
    logger.info("🧪 TEST: Development Task Detection")
    logger.info("=" * 80)

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\n📝 Test {i}: {test['task'][:60]}...")

        # Create steps using workflow logic
        steps = _create_execution_steps(
            agent=test['agent'],
            task=test['task'],
            session_id='test',
            current_step_number=0
        )

        step_count = len(steps)
        result = 'multi-step' if step_count > 1 else 'single-step'
        success = result == test['expected']

        status_emoji = "✅" if success else "❌"
        logger.info(f"{status_emoji} Expected: {test['expected']}, Got: {result} ({step_count} steps)")

        if step_count > 1:
            logger.info("   Steps created:")
            for j, step in enumerate(steps, 1):
                logger.info(f"   {j}. {step.agent}: {step.task[:50]}...")

    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    test_development_task_detection()
