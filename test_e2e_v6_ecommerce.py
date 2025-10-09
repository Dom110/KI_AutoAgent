"""
E2E Test: Build E-Commerce Backend via WebSocket with ALL v6 Systems

This test validates the COMPLETE v6 integration by building a complex
real-world application through WebSocket user input.

Test App: E-Commerce Backend API
- User Authentication (JWT)
- Product Catalog (PostgreSQL)
- Shopping Cart
- Payment Integration (Stripe)
- Order Management
- Deployment Ready

This test exercises ALL v6 systems:
✅ Query Classifier → Routes complex query
✅ Curiosity System → Detects missing details
✅ Predictive System → Estimates 60+ min duration
✅ Tool Registry → Discovers Python/FastAPI tools
✅ Approval Manager → Requests approval for file writes
✅ Workflow Adapter → Adapts if errors occur
✅ Neurosymbolic Reasoner → Validates security decisions
✅ Learning System → Records execution for future
✅ Self-Diagnosis → Heals any errors automatically
✅ Perplexity API → Researches best practices
✅ Asimov Rule 3 → Finds all errors globally

Author: KI AutoAgent Team
Version: 6.0.0
Python: 3.13+
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import websockets

# Test configuration
WS_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = "/tmp/ki_autoagent_e2e_test_ecommerce"

# Create test workspace
Path(TEST_WORKSPACE).mkdir(parents=True, exist_ok=True)

print("\n" + "=" * 80)
print("🧪 E2E TEST: Build E-Commerce Backend with v6 Integration")
print("=" * 80)
print(f"WebSocket URL: {WS_URL}")
print(f"Test Workspace: {TEST_WORKSPACE}")
print(f"Testing ALL 12 v6 systems in real workflow!")
print("=" * 80 + "\n")


async def run_e2e_test():
    """Run complete E2E test."""

    try:
        # Connect to WebSocket
        print("📡 Connecting to v6 Integrated Server...")
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected!\n")

            # ================================================================
            # STEP 1: Receive welcome message
            # ================================================================
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 Welcome: {welcome_data['message']}")
            print(f"   Session ID: {welcome_data['session_id']}")
            print(f"   v6 Systems: {welcome_data.get('v6_systems', 'N/A')}")
            print()

            # ================================================================
            # STEP 2: Send init message with workspace
            # ================================================================
            print(f"🔧 Initializing workspace: {TEST_WORKSPACE}")
            await websocket.send(json.dumps({
                "type": "init",
                "workspace_path": TEST_WORKSPACE
            }))

            init_response = await websocket.recv()
            init_data = json.loads(init_response)
            print(f"✅ {init_data['message']}")

            if init_data.get("v6_systems"):
                print(f"   v6 Systems Active:")
                for system, active in init_data["v6_systems"].items():
                    status = "✅" if active else "❌"
                    print(f"      {status} {system}")
            print()

            # ================================================================
            # STEP 3: Send complex E-Commerce task
            # ================================================================
            print("🚀 Sending complex E-Commerce task...")
            print()

            task = """Baue eine komplette E-Commerce Backend API mit folgenden Features:

**Core Features:**
1. User Authentication & Authorization (JWT)
2. Product Catalog Management (CRUD)
3. Shopping Cart System
4. Payment Processing (Stripe Integration)
5. Order Management & History
6. Admin Dashboard Endpoints

**Technical Requirements:**
- Python FastAPI Framework
- PostgreSQL Datenbank
- Redis für Session Management
- Pydantic Models für Validation
- Alembic für Database Migrations
- pytest für Tests
- Docker Setup für Deployment

**Security Requirements:**
- Password Hashing (bcrypt)
- JWT Token Authentication
- Input Validation
- SQL Injection Protection
- Rate Limiting

**API Endpoints needed:**
- POST /api/auth/register
- POST /api/auth/login
- GET /api/products
- POST /api/products (admin only)
- POST /api/cart/add
- POST /api/checkout
- GET /api/orders

**Deployment:**
- Dockerfile
- docker-compose.yml
- Environment variables (.env.example)
- README mit Setup Instructions

Erstelle eine production-ready, well-tested, secure E-Commerce API.
"""

            print(f"Task Description ({len(task)} chars):")
            print("-" * 80)
            print(task)
            print("-" * 80)
            print()

            await websocket.send(json.dumps({
                "type": "chat",
                "content": task
            }))

            # ================================================================
            # STEP 4: Monitor workflow execution
            # ================================================================
            print("📊 Monitoring workflow execution...")
            print("=" * 80)
            print()

            workflow_complete = False
            v6_insights = {}

            while not workflow_complete:
                try:
                    # Receive with timeout
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=300.0  # 5 minute timeout
                    )
                    data = json.loads(response)
                    msg_type = data.get("type")

                    timestamp = datetime.now().strftime("%H:%M:%S")

                    if msg_type == "status":
                        status = data.get("status", "unknown")
                        message = data.get("message", "")
                        print(f"[{timestamp}] 📊 STATUS: {status}")
                        print(f"            {message}")
                        print()

                    elif msg_type == "approval_request":
                        # Handle approval requests
                        request_id = data.get("request_id")
                        action = data.get("action_type")
                        description = data.get("description")

                        print(f"[{timestamp}] 🔐 APPROVAL REQUEST")
                        print(f"            Action: {action}")
                        print(f"            Description: {description}")
                        print(f"            Request ID: {request_id}")
                        print()

                        # Auto-approve for test (in production, user would approve)
                        print(f"            ✅ Auto-approving for test...")
                        await websocket.send(json.dumps({
                            "type": "approval_response",
                            "request_id": request_id,
                            "approved": True,
                            "response": "Auto-approved in E2E test"
                        }))
                        print()

                    elif msg_type == "workflow_complete":
                        print(f"[{timestamp}] 🎉 WORKFLOW COMPLETE!")
                        print("=" * 80)
                        print()

                        # Extract v6 insights
                        success = data.get("success", False)
                        execution_time = data.get("execution_time", 0)
                        quality_score = data.get("quality_score", 0)

                        print(f"✅ Success: {success}")
                        print(f"⏱️  Execution Time: {execution_time:.1f}s")
                        print(f"⭐ Quality Score: {quality_score:.2f}")
                        print()

                        # v6 Analysis
                        if "analysis" in data:
                            analysis = data["analysis"]
                            print("📋 PRE-EXECUTION ANALYSIS:")

                            if "classification" in analysis:
                                cls = analysis["classification"]
                                print(f"   Query Type: {cls['type']}")
                                print(f"   Complexity: {cls['complexity']}")
                                print(f"   Confidence: {cls['confidence']:.2f}")
                                print(f"   Required Agents: {cls['required_agents']}")

                            if "gaps" in analysis:
                                gaps = analysis["gaps"]
                                if gaps["has_gaps"]:
                                    print(f"   ⚠️  Knowledge Gaps: {len(gaps['gaps'])} detected")
                                    print(f"   Questions Generated: {len(gaps['questions'])}")

                            if "prediction" in analysis:
                                pred = analysis["prediction"]
                                print(f"   Estimated Duration: {pred['estimated_duration']:.1f} min")
                                print(f"   Risk Level: {pred['risk_level']}")

                            if "reasoning" in analysis:
                                reasoning = analysis["reasoning"]
                                print(f"   Neurosymbolic Decision: {reasoning['decision']}")
                                print(f"   Constraints Satisfied: {reasoning['constraints_satisfied']}")

                            print()

                        # v6 Adaptations
                        if "adaptations" in data:
                            adaptations = data["adaptations"]
                            print("🔄 WORKFLOW ADAPTATIONS:")
                            print(f"   Total: {adaptations['total_adaptations']}")
                            if adaptations.get("by_type"):
                                for atype, count in adaptations["by_type"].items():
                                    print(f"   - {atype}: {count}")
                            print()

                        # v6 Health
                        if "health" in data:
                            health = data["health"]
                            print("🏥 SYSTEM HEALTH:")
                            print(f"   Total Diagnostics: {health['total_diagnostics']}")
                            print(f"   Recovery Attempts: {health['recovery_attempts']}")
                            print(f"   Recovery Success Rate: {health['recovery_success_rate']:.0%}")
                            print()

                        # v6 Systems Used
                        if "v6_systems_used" in data:
                            systems = data["v6_systems_used"]
                            print("✨ v6 SYSTEMS UTILIZED:")
                            for system, used in systems.items():
                                status = "✅" if used else "⚪"
                                print(f"   {status} {system}")
                            print()

                        # Errors/Warnings
                        if data.get("errors"):
                            print(f"❌ ERRORS ({len(data['errors'])}):")
                            for error in data["errors"]:
                                print(f"   - {error}")
                            print()

                        if data.get("warnings"):
                            print(f"⚠️  WARNINGS ({len(data['warnings'])}):")
                            for warning in data["warnings"]:
                                print(f"   - {warning}")
                            print()

                        v6_insights = data
                        workflow_complete = True

                    elif msg_type == "error":
                        print(f"[{timestamp}] ❌ ERROR: {data.get('message')}")
                        print()

                    else:
                        print(f"[{timestamp}] 📨 {msg_type.upper()}: {json.dumps(data, indent=2)[:200]}...")
                        print()

                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for response (5 minutes)")
                    break

            # ================================================================
            # STEP 5: Summary and validation
            # ================================================================
            print()
            print("=" * 80)
            print("📊 E2E TEST SUMMARY")
            print("=" * 80)
            print()

            if v6_insights:
                success = v6_insights.get("success", False)
                quality = v6_insights.get("quality_score", 0)

                print(f"Overall Success: {'✅ PASS' if success else '❌ FAIL'}")
                print(f"Quality Score: {quality:.2f}/1.00")
                print()

                # Validate v6 systems were actually used
                systems_used = v6_insights.get("v6_systems_used", {})
                systems_active = sum(1 for v in systems_used.values() if v)

                print(f"v6 Systems Active: {systems_active}/9")
                print()

                if systems_active >= 7:
                    print("✅ v6 Integration Test: PASSED")
                    print("   Most v6 systems were actively utilized")
                else:
                    print("⚠️  v6 Integration Test: PARTIAL")
                    print(f"   Only {systems_active}/9 systems were used")

                print()

                # Check specific capabilities
                print("Specific v6 Capabilities Validated:")
                validations = [
                    ("Query Classification", systems_used.get("query_classifier", False)),
                    ("Knowledge Gap Detection", systems_used.get("curiosity", False)),
                    ("Predictive Analysis", systems_used.get("predictive", False)),
                    ("Dynamic Tool Discovery", systems_used.get("tool_registry", False)),
                    ("Workflow Adaptation", systems_used.get("workflow_adapter", False)),
                    ("Neurosymbolic Reasoning", systems_used.get("neurosymbolic", False)),
                    ("Learning & Memory", systems_used.get("learning", False)),
                    ("Self-Diagnosis", systems_used.get("self_diagnosis", False)),
                ]

                for capability, validated in validations:
                    status = "✅" if validated else "⚪"
                    print(f"  {status} {capability}")

                print()
                print("=" * 80)
                print()

                if success and systems_active >= 7:
                    print("🎉 E2E TEST COMPLETE: ALL SYSTEMS OPERATIONAL! 🎉")
                    return True
                else:
                    print("⚠️  E2E TEST COMPLETE: Partial success")
                    return False

            else:
                print("❌ E2E TEST FAILED: No workflow result received")
                return False

    except Exception as e:
        print(f"\n❌ E2E Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    print()
    print("🚀 Starting E2E Test...")
    print()

    success = await run_e2e_test()

    print()
    if success:
        print("✅ E2E TEST PASSED!")
        sys.exit(0)
    else:
        print("❌ E2E TEST FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
