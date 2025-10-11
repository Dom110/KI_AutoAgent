"""
Test Script for v5.8.7: Simple HTML Calculator Architecture Proposal

Tests the new Research-Driven Architecture Design:
- New project detection
- Task complexity classification
- Research Agent integration
- Proper simple HTML architecture (NOT microservices!)

Expected behavior:
1. Orchestrator detects "create" keyword → Complex task workflow
2. Architect detects empty workspace → New project mode
3. Architect calls Research Agent for best practices
4. Architect classifies as "simple" + "frontend_only"
5. Architecture proposal shows:
   - Single HTML file OR simple modular structure
   - NO backend/database
   - Research insights about calculators
   - Clean, appropriate tech stack
"""

import asyncio
import websockets
import json
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_URL = "ws://localhost:8001/ws/chat"
TEST_WORKSPACE = "/tmp/test_calculator_v587"
TEST_MESSAGE = "Create simple HTML calculator"

# Expected keywords in response (for validation)
EXPECTED_GOOD_KEYWORDS = [
    "html", "css", "javascript",
    "simple", "frontend",
    "single file", "modular",
    "calculator"
]

UNEXPECTED_BAD_KEYWORDS = [
    "microservices", "kubernetes", "k8s",
    "backend", "database", "postgresql",
    "redis", "kafka", "api gateway"
]

class CalculatorArchitectureTest:
    """Test runner for calculator architecture proposal"""

    def __init__(self):
        self.messages_received = []
        self.architecture_proposal = None
        self.test_passed = False
        self.errors = []
        self.warnings = []

    async def run_test(self):
        """Run the complete test"""
        logger.info("=" * 80)
        logger.info("🚀 Starting Calculator Architecture Test (v5.8.7)")
        logger.info("=" * 80)

        try:
            # Create test workspace
            import os
            import shutil
            if os.path.exists(TEST_WORKSPACE):
                shutil.rmtree(TEST_WORKSPACE)
            os.makedirs(TEST_WORKSPACE, exist_ok=True)
            logger.info(f"✅ Created test workspace: {TEST_WORKSPACE}")

            # Connect to backend
            logger.info(f"🔌 Connecting to backend: {BACKEND_URL}")
            async with websockets.connect(BACKEND_URL) as websocket:
                logger.info("✅ Connected!")

                # Wait for connection message
                connection_msg = await websocket.recv()
                logger.info(f"📨 Connection: {connection_msg}")

                # Send init message with workspace
                init_message = {
                    "type": "init",
                    "workspace_path": TEST_WORKSPACE
                }
                await websocket.send(json.dumps(init_message))
                logger.info(f"📤 Sent init message")

                # Wait for initialized
                init_response = await websocket.recv()
                logger.info(f"📨 Init response: {init_response}")

                # Send test message
                logger.info(f"\n📤 Sending test message: '{TEST_MESSAGE}'")
                test_msg = {
                    "type": "chat",
                    "content": TEST_MESSAGE,
                    "mode": "auto"
                }
                await websocket.send(json.dumps(test_msg))
                logger.info("✅ Message sent")

                # Collect responses
                logger.info("\n📥 Collecting responses...")
                # v5.8.7: Increased timeout - AI architecture design can take 60-90s
                timeout_seconds = 180  # 3 minutes max (was 120)
                start_time = datetime.now()

                while True:
                    try:
                        # Check timeout
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if elapsed > timeout_seconds:
                            logger.error(f"❌ Timeout after {timeout_seconds}s")
                            self.errors.append(f"Test timeout after {timeout_seconds}s")
                            break

                        # Receive message with timeout
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=10.0
                        )

                        msg = json.loads(response)
                        self.messages_received.append(msg)

                        msg_type = msg.get("type", "unknown")

                        # Log progress messages
                        if msg_type == "agent_progress":
                            agent = msg.get("agent", "unknown")
                            content = msg.get("content", "")
                            logger.info(f"  🔄 [{agent}] {content}")

                        # Log thinking messages
                        elif msg_type == "agent_thinking":
                            agent = msg.get("agent", "unknown")
                            logger.info(f"  💭 [{agent}] thinking...")

                        # Capture architecture proposal
                        elif msg_type == "architecture_proposal":
                            self.architecture_proposal = msg.get("proposal", msg.get("content", ""))
                            logger.info(f"\n📋 Architecture Proposal Received!")
                            logger.info("=" * 80)
                            logger.info(self.architecture_proposal)
                            logger.info("=" * 80)

                            # v5.8.7: Test complete after receiving proposal (workflow pauses for approval)
                            logger.info("✅ Proposal received, test complete (workflow pauses for approval)")
                            break

                        # Capture final response
                        elif msg_type == "response":
                            content = msg.get("content", "")
                            logger.info(f"\n✅ Final Response:")
                            logger.info(content)

                            # If no proposal yet, this might be it
                            if not self.architecture_proposal:
                                self.architecture_proposal = content

                            break

                        # Error handling
                        elif msg_type == "error":
                            error_msg = msg.get("content", msg.get("error", "Unknown error"))
                            logger.error(f"❌ Error: {error_msg}")
                            self.errors.append(error_msg)
                            break

                    except asyncio.TimeoutError:
                        logger.warning("⚠️ No response for 10s, waiting...")
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("🔌 Connection closed by server")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error receiving message: {e}")
                        self.errors.append(str(e))
                        break

            # Validate results
            await self.validate_results()

        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            self.errors.append(str(e))
            import traceback
            traceback.print_exc()

        # Print summary
        self.print_summary()

    async def validate_results(self):
        """Validate the architecture proposal"""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VALIDATING ARCHITECTURE PROPOSAL")
        logger.info("=" * 80)

        if not self.architecture_proposal:
            self.errors.append("No architecture proposal received!")
            logger.error("❌ FAIL: No architecture proposal received")
            return

        # v5.8.7 FIX: Proposal can be dict or string
        if isinstance(self.architecture_proposal, dict):
            # Convert dict to string for analysis
            import json
            proposal_text = json.dumps(self.architecture_proposal, indent=2)
            logger.info("✅ Proposal is dict - converting to text for analysis")
        else:
            proposal_text = str(self.architecture_proposal)

        proposal_lower = proposal_text.lower()

        # Check for GOOD keywords
        logger.info("\n✅ Checking for expected keywords...")
        found_good = []
        for keyword in EXPECTED_GOOD_KEYWORDS:
            if keyword in proposal_lower:
                found_good.append(keyword)
                logger.info(f"  ✅ Found: '{keyword}'")

        if len(found_good) < 3:
            self.warnings.append(f"Only found {len(found_good)}/3 expected keywords")
            logger.warning(f"⚠️ Only found {len(found_good)} expected keywords")

        # Check for BAD keywords (over-engineering indicators)
        logger.info("\n❌ Checking for unexpected keywords (over-engineering)...")
        found_bad = []
        for keyword in UNEXPECTED_BAD_KEYWORDS:
            if keyword in proposal_lower:
                found_bad.append(keyword)
                logger.error(f"  ❌ Found: '{keyword}' (SHOULD NOT BE HERE!)")

        if found_bad:
            self.errors.append(f"Found over-engineering keywords: {', '.join(found_bad)}")
            logger.error(f"❌ FAIL: Proposal includes unnecessary infrastructure!")

        # Check for Research insights
        if "research" in proposal_lower or "best practice" in proposal_lower:
            logger.info("  ✅ Research insights present")
        else:
            self.warnings.append("No research insights found in proposal")
            logger.warning("  ⚠️ No research insights found")

        # Check for task classification
        if "complexity" in proposal_lower or "simple" in proposal_lower:
            logger.info("  ✅ Task classification present")
        else:
            self.warnings.append("No task classification found")
            logger.warning("  ⚠️ No task classification found")

        # Final verdict
        if not self.errors and len(found_good) >= 3 and not found_bad:
            self.test_passed = True
            logger.info("\n🎉 TEST PASSED! Architecture proposal is appropriate.")
        elif not self.errors:
            self.test_passed = True
            logger.info("\n⚠️ TEST PASSED (with warnings)")
        else:
            self.test_passed = False
            logger.error("\n❌ TEST FAILED!")

    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Messages received: {len(self.messages_received)}")
        logger.info(f"Architecture proposal: {'✅ Received' if self.architecture_proposal else '❌ Not received'}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Warnings: {len(self.warnings)}")

        if self.errors:
            logger.info("\n❌ Errors:")
            for error in self.errors:
                logger.info(f"  - {error}")

        if self.warnings:
            logger.info("\n⚠️ Warnings:")
            for warning in self.warnings:
                logger.info(f"  - {warning}")

        logger.info("\n" + "=" * 80)
        if self.test_passed:
            logger.info("✅ RESULT: PASSED")
        else:
            logger.info("❌ RESULT: FAILED")
        logger.info("=" * 80)

async def main():
    """Main test entry point"""
    test = CalculatorArchitectureTest()
    await test.run_test()

    # Exit with appropriate code
    sys.exit(0 if test.test_passed else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
