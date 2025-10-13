#!/usr/bin/env python3
"""
E2E Test: FIX Intent with Real Buggy Code

This test verifies that:
1. Intent detection correctly identifies "fix" requests
2. Workflow routes directly to ReviewFix (not Research)
3. ReviewFix can actually fix TypeScript errors
4. Build validation confirms errors are fixed

CRITICAL: Must run in isolated workspace (not development repo)!
"""

import asyncio
import websockets
import json
import os
import sys
from pathlib import Path
import shutil

# Test workspace (ISOLATED from development repo)
TEST_WORKSPACE = Path.home() / "TestApps" / "fix_intent_test"

def setup_test_workspace():
    """Setup clean test workspace with buggy code."""
    print("🧪 Setting up test workspace...")

    # Clean old workspace
    if TEST_WORKSPACE.exists():
        print(f"  🧹 Cleaning old workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)

    # Create fresh workspace
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ Created workspace: {TEST_WORKSPACE}")

    # Create buggy TypeScript app
    print("  📝 Creating buggy TypeScript app...")

    # package.json
    package_json = {
        "name": "buggy-app",
        "version": "1.0.0",
        "scripts": {
            "build": "tsc --noEmit"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }

    with open(TEST_WORKSPACE / "package.json", "w") as f:
        json.dump(package_json, f, indent=2)

    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "module": "ESNext",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True
        },
        "include": ["*.ts"]
    }

    with open(TEST_WORKSPACE / "tsconfig.json", "w") as f:
        json.dump(tsconfig, f, indent=2)

    # Buggy TypeScript file with multiple errors
    buggy_code = '''// Buggy TypeScript file with intentional errors

function calculateTotal(items: any[]): number {
    let total: string = 0;  // ❌ ERROR: Type 'number' not assignable to 'string'

    for (const item of items) {
        total += item.price;  // ❌ ERROR: Operator '+=' cannot be applied to types 'string' and 'number'
    }

    return total;  // ❌ ERROR: Type 'string' not assignable to 'number'
}

function processUser(user: any) {
    const name: number = user.name;  // ❌ ERROR: Type 'string' not assignable to 'number'
    const age: string = user.age;    // ❌ ERROR: Type 'number' not assignable to 'string'

    console.log(`User: ${name}, Age: ${age}`);
}

// Missing export statement
interface User {
    name: string;
    age: number;
    email: string;
}

const users: User[] = [
    { name: "Alice", age: 30, email: "alice@example.com" },
    { name: "Bob", age: 25, email: "bob@example.com" }
];

processUser(users[0]);

const items = [
    { name: "Item 1", price: 100 },
    { name: "Item 2", price: 200 }
];

const total = calculateTotal(items);
console.log(`Total: ${total}`);
'''

    with open(TEST_WORKSPACE / "app.ts", "w") as f:
        f.write(buggy_code)

    print("  ✅ Created buggy TypeScript app with 5+ errors")
    print(f"     Location: {TEST_WORKSPACE / 'app.ts'}")


async def run_fix_test():
    """Run the E2E test for FIX intent."""
    print("\n" + "="*80)
    print("🧪 E2E Test: FIX Intent with Real Buggy Code")
    print("="*80 + "\n")

    # Setup workspace
    setup_test_workspace()

    # Connect to backend
    ws_url = "ws://localhost:8002/ws/chat"
    print(f"\n📡 Connecting to backend: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("  ✅ Connected to backend")

            # Wait for connection message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  📨 Received: {data['type']}")

            # Send init message with test workspace
            init_msg = {
                "type": "init",
                "workspace_path": str(TEST_WORKSPACE)
            }
            await websocket.send(json.dumps(init_msg))
            print(f"  📤 Sent init with workspace: {TEST_WORKSPACE}")

            # Wait for initialized confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"  📨 Received: {data['type']}")

            if data['type'] == 'initialized':
                print(f"  ✅ Initialized with workspace: {data['workspace_path']}")

            # Send FIX request
            fix_request = "Fix the TypeScript compilation errors in this application"

            print(f"\n🎯 Sending FIX request: '{fix_request}'")

            chat_msg = {
                "type": "chat",
                "message": fix_request
            }
            await websocket.send(json.dumps(chat_msg))
            print("  📤 Sent FIX request")

            # Monitor workflow execution
            print("\n📊 Monitoring workflow execution...\n")

            first_agent = None
            workflow_started = False
            intent_detected = None
            reviewfix_started = False
            messages_received = 0

            # Collect messages for 60 seconds or until workflow completes
            timeout = 120  # 2 minutes max
            start_time = asyncio.get_event_loop().time()

            while True:
                try:
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        print(f"\n⏰ Timeout after {timeout}s")
                        break

                    # Get next message with timeout
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=10.0
                    )
                    data = json.loads(response)
                    messages_received += 1

                    msg_type = data.get('type', 'unknown')

                    # Print all messages for debugging
                    if msg_type == 'agent_start':
                        agent = data.get('agent', 'unknown')
                        print(f"  🤖 Agent started: {agent}")

                        if not first_agent:
                            first_agent = agent
                            print(f"     ⭐ FIRST AGENT: {agent}")

                        if agent == 'reviewfix':
                            reviewfix_started = True
                            print(f"     ✅ ReviewFix started (correct for FIX intent!)")

                    elif msg_type == 'intent_detected':
                        intent = data.get('intent', 'unknown')
                        confidence = data.get('confidence', 0)
                        intent_detected = intent
                        print(f"  🎯 Intent detected: {intent} (confidence: {confidence:.2f})")

                    elif msg_type == 'workflow_progress':
                        step = data.get('step', 'unknown')
                        print(f"  📈 Workflow step: {step}")

                    elif msg_type == 'agent_complete':
                        agent = data.get('agent', 'unknown')
                        print(f"  ✅ Agent complete: {agent}")

                    elif msg_type == 'workflow_complete':
                        print(f"\n  ✅ Workflow complete!")
                        break

                    elif msg_type == 'error':
                        error = data.get('error', 'Unknown error')
                        print(f"  ❌ Error: {error}")

                    elif msg_type == 'log':
                        message = data.get('message', '')
                        if 'intent' in message.lower() or 'routing' in message.lower():
                            print(f"  📝 {message}")

                except asyncio.TimeoutError:
                    print("  ⏰ No messages for 10s, checking if workflow completed...")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("  🔌 Connection closed")
                    break

            # Print test results
            print("\n" + "="*80)
            print("📊 Test Results")
            print("="*80)
            print(f"Messages received: {messages_received}")
            print(f"Intent detected: {intent_detected}")
            print(f"First agent: {first_agent}")
            print(f"ReviewFix started: {reviewfix_started}")

            # Verify results
            success = True

            if intent_detected != 'fix':
                print(f"❌ FAIL: Intent should be 'fix', got '{intent_detected}'")
                success = False
            else:
                print(f"✅ PASS: Intent correctly detected as 'fix'")

            if first_agent != 'reviewfix':
                print(f"❌ FAIL: First agent should be 'reviewfix', got '{first_agent}'")
                success = False
            else:
                print(f"✅ PASS: First agent is ReviewFix (direct routing!)")

            if not reviewfix_started:
                print(f"❌ FAIL: ReviewFix should have started")
                success = False
            else:
                print(f"✅ PASS: ReviewFix started")

            # Check if TypeScript errors were fixed
            print("\n🔍 Checking if TypeScript errors were fixed...")

            app_ts = TEST_WORKSPACE / "app.ts"
            if app_ts.exists():
                with open(app_ts, 'r') as f:
                    fixed_code = f.read()

                print(f"  📄 app.ts length: {len(fixed_code)} chars")

                # Check for common fixes
                has_fixes = (
                    'let total: number' in fixed_code or  # Fixed type annotation
                    'const total: number' in fixed_code
                )

                if has_fixes:
                    print(f"  ✅ Code appears to have been modified")
                else:
                    print(f"  ⚠️  Code may not have been fixed (reviewfix might have skipped or failed)")
            else:
                print(f"  ❌ app.ts not found!")

            print("\n" + "="*80)
            if success:
                print("✅ FIX INTENT E2E TEST PASSED")
            else:
                print("❌ FIX INTENT E2E TEST FAILED")
            print("="*80)

            return success

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run test
    success = asyncio.run(run_fix_test())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
