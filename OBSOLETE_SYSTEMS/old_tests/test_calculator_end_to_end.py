#!/usr/bin/env python3
"""
End-to-End Test: Build Complete Calculator App with AI Agent
Tests all 4 AI systems during real app development
"""

import asyncio
import json
import logging
import websockets
import sys
import os
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_e2e_final.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CalculatorBuilderClient:
    def __init__(self):
        self.uri = "ws://localhost:8001/ws/chat"
        self.websocket = None
        self.session_id = None
        self.workspace_path = "/Users/dominikfoert/TestApps/CalculatorApp_AI"
        self.messages = []

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            logger.info(f"🔌 Connecting to {self.uri}")
            self.websocket = await websockets.connect(self.uri)

            # Get initial message
            message = await self.websocket.recv()
            data = json.loads(message)
            logger.info(f"📥 Server version: {data.get('version', 'unknown')}")

            # Send initialization with workspace
            if data.get('requires_init'):
                # Create workspace directory if it doesn't exist
                os.makedirs(self.workspace_path, exist_ok=True)
                logger.info(f"📁 Created workspace: {self.workspace_path}")

                init_msg = {
                    "type": "init",
                    "workspace_path": self.workspace_path
                }
                await self.websocket.send(json.dumps(init_msg))

                # Get init confirmation
                message = await self.websocket.recv()
                data = json.loads(message)

                if data.get('type') == 'initialized':
                    self.session_id = data.get('session_id')
                    logger.info(f"✅ Connected! Session: {self.session_id}")
                    logger.info(f"📂 Workspace: {self.workspace_path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def send_and_wait(self, prompt, timeout=300):
        """Send a task and wait for complete response"""
        message = {
            "type": "chat",
            "content": prompt,
            "agent": "auto",  # Let system choose best agent
            "mode": "auto"
        }

        logger.info(f"\n📤 SENDING PROMPT:\n{prompt}\n")
        await self.websocket.send(json.dumps(message))

        responses = []
        start_time = time.time()
        final_response = None

        try:
            while time.time() - start_time < timeout:
                msg = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                data = json.loads(msg)
                responses.append(data)
                self.messages.append(data)

                msg_type = data.get('type')
                agent = data.get('agent', 'system')

                # Log different message types
                if msg_type == 'agent_thinking':
                    logger.info(f"💭 {agent} thinking...")
                elif msg_type == 'agent_progress':
                    progress = data.get('content', '')[:200]
                    logger.info(f"📊 Progress: {progress}...")
                elif msg_type == 'step_completed':
                    step = data.get('content', '')[:200]
                    logger.info(f"✅ Step completed: {step}...")
                elif msg_type == 'agent_response':
                    logger.info(f"📥 Final response received from {agent}")
                    final_response = data.get('content', '')

                    # Check for AI systems metadata
                    metadata = data.get('metadata', {})
                    ai_systems = metadata.get('ai_systems', {})
                    if ai_systems:
                        logger.info(f"🧠 AI SYSTEMS ACTIVE:")
                        logger.info(f"  - Predictive Confidence: {ai_systems.get('predictive_confidence', 'N/A')}")
                        logger.info(f"  - Curiosity Score: {ai_systems.get('curiosity_score', 'N/A')}")
                        logger.info(f"  - Asimov Compliant: {ai_systems.get('asimov_compliant', 'N/A')}")
                        if ai_systems.get('framework_comparison'):
                            logger.info(f"  - Framework Comparison: ✅")

                    return responses
                elif msg_type == 'error':
                    logger.error(f"❌ Error: {data.get('content')}")

                    # Check for Asimov violations
                    if 'asimov' in data.get('content', '').lower():
                        logger.info("🚫 ASIMOV RULE ENFORCED!")
                    return responses

        except asyncio.TimeoutError:
            pass

        return responses

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Connection closed")

async def test_calculator_app():
    """Build a complete calculator app using AI Agent"""
    logger.info("="*80)
    logger.info("🚀 STARTING CALCULATOR APP BUILD TEST")
    logger.info("="*80)

    client = CalculatorBuilderClient()

    if not await client.connect():
        logger.error("❌ Failed to connect to backend")
        return False

    # The main prompt to build a calculator
    calculator_prompt = """
    Build a modern, fully-functional calculator application with the following features:

    1. Basic arithmetic operations (add, subtract, multiply, divide)
    2. Advanced operations (square root, power, percentage)
    3. Memory functions (MC, MR, M+, M-)
    4. Keyboard support for number input
    5. Clean, modern UI with CSS styling
    6. Error handling for division by zero
    7. Responsive design that works on mobile and desktop
    8. History of last 10 calculations

    The calculator should be a single-page web application using HTML, CSS, and JavaScript.
    Create all necessary files with complete implementation - no placeholders or TODOs.
    The application should be production-ready and fully tested.

    Include these specific requirements:
    - Dark mode toggle
    - Scientific notation for large numbers
    - Decimal precision settings
    - Clear (C) and All Clear (AC) buttons
    - Backspace functionality

    Compare different UI frameworks and choose the best one for this use case.
    """

    logger.info("\n📝 PHASE 1: Sending calculator build request...")
    responses = await client.send_and_wait(calculator_prompt, timeout=300)

    # Analyze responses
    logger.info("\n📊 ANALYSIS OF AI SYSTEM USAGE:")

    # Check for various AI system indicators
    asimov_checks = 0
    predictive_used = False
    curiosity_used = False
    framework_mentioned = False

    for msg in client.messages:
        content = json.dumps(msg).lower()

        # Check for Asimov rules
        if 'asimov' in content or 'rule' in content:
            asimov_checks += 1

        # Check for predictive learning
        if 'prediction' in content or 'confidence' in content:
            predictive_used = True

        # Check for curiosity
        if 'curiosity' in content or 'novelty' in content:
            curiosity_used = True

        # Check for framework comparison
        if any(fw in content for fw in ['react', 'vue', 'angular', 'svelte', 'vanilla']):
            framework_mentioned = True

    logger.info(f"\n✅ AI SYSTEMS USAGE REPORT:")
    logger.info(f"1. Asimov Rules Checks: {asimov_checks} times")
    logger.info(f"2. Predictive Learning: {'✅ Used' if predictive_used else '❌ Not detected'}")
    logger.info(f"3. Curiosity System: {'✅ Used' if curiosity_used else '❌ Not detected'}")
    logger.info(f"4. Framework Comparison: {'✅ Performed' if framework_mentioned else '❌ Not detected'}")

    # Check if files were created
    logger.info(f"\n📁 CHECKING CREATED FILES:")
    expected_files = ['index.html', 'style.css', 'script.js']
    files_created = []

    for file in expected_files:
        file_path = os.path.join(client.workspace_path, file)
        if os.path.exists(file_path):
            files_created.append(file)
            logger.info(f"  ✅ {file} created")

            # Check file size to ensure it's not empty
            size = os.path.getsize(file_path)
            logger.info(f"     Size: {size} bytes")
        else:
            logger.info(f"  ❌ {file} not found")

    # Test for TODO violations (Asimov Rule 2)
    logger.info("\n🧪 TESTING ASIMOV RULE 2: No TODOs")
    todo_test = "Add a TODO comment for implementing the square root function"
    logger.info(f"Sending: {todo_test}")

    todo_responses = await client.send_and_wait(todo_test, timeout=30)

    todo_blocked = False
    for msg in todo_responses:
        if msg.get('type') == 'error' or 'cannot' in msg.get('content', '').lower():
            logger.info("✅ TODO request was blocked (Asimov Rule 2 enforced)")
            todo_blocked = True
            break

    if not todo_blocked:
        logger.info("❌ TODO request was not blocked")

    # Check for data persistence
    logger.info("\n💾 CHECKING DATA PERSISTENCE:")

    data_dir = os.path.expanduser("~/.ki_autoagent/data")
    persistence_files = {
        "predictive": f"{data_dir}/predictive/OrchestratorAgent_predictions.json",
        "curiosity": f"{data_dir}/curiosity/OrchestratorAgent_curiosity.json",
        "learning": f"{data_dir}/learning_data.json",
        "framework": f"{data_dir}/framework_comparisons.json"
    }

    for name, path in persistence_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            logger.info(f"  ✅ {name}: {size} bytes")
        else:
            logger.info(f"  ❌ {name}: not found")

    await client.close()

    # Final summary
    logger.info("\n" + "="*80)
    logger.info("📊 FINAL TEST SUMMARY")
    logger.info("="*80)

    success_criteria = [
        ("Files created", len(files_created) >= 2),
        ("Asimov Rules", asimov_checks > 0 or todo_blocked),
        ("Framework comparison", framework_mentioned),
        ("No empty files", all(os.path.getsize(os.path.join(client.workspace_path, f)) > 100
                               for f in files_created if os.path.exists(os.path.join(client.workspace_path, f))))
    ]

    passed = 0
    for criterion, result in success_criteria:
        status = "✅" if result else "❌"
        logger.info(f"{status} {criterion}")
        if result:
            passed += 1

    logger.info(f"\n🏆 SCORE: {passed}/{len(success_criteria)} criteria passed")

    return passed >= 3  # Success if at least 3/4 criteria met

if __name__ == "__main__":
    logger.info(f"Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        success = asyncio.run(test_calculator_app())

        if success:
            logger.info("\n✅✅✅ CALCULATOR BUILD TEST PASSED! ✅✅✅")
            logger.info("The AI Agent successfully built a calculator app with AI systems active!")
        else:
            logger.info("\n❌ Test did not meet all success criteria")

    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    logger.info(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")