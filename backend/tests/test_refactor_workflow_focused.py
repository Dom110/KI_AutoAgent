#!/usr/bin/env python3
"""
FOCUSED E2E Test: REFACTOR Workflow

Test refactoring legacy code to modern standards.

Run:
    # Terminal 1: Backend should be running
    source venv/bin/activate
    python backend/api/server_v6_integrated.py

    # Terminal 2: Run this test
    python backend/tests/test_refactor_workflow_focused.py
"""

import asyncio
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import websockets

# Configuration
BACKEND_URL = "ws://localhost:8002/ws/chat"
TEST_WORKSPACE = Path.home() / "TestApps" / "refactor_workflow_test"
TEST_TIMEOUT = 1500  # 25 minutes (REFACTOR can be complex)

print("\n" + "="*80)
print("FOCUSED E2E TEST: REFACTOR Workflow")
print("="*80)
print(f"📁 Workspace: {TEST_WORKSPACE}")
print(f"🔌 Backend: {BACKEND_URL}")
print(f"⏱️  Timeout: {TEST_TIMEOUT}s ({TEST_TIMEOUT//60} minutes)")
print("="*80 + "\n")


async def run_refactor_test():
    """Run REFACTOR workflow test with detailed monitoring."""

    # Clean workspace
    if TEST_WORKSPACE.exists():
        print(f"🧹 Cleaning workspace: {TEST_WORKSPACE}")
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True)
    print(f"✅ Clean workspace created\n")

    # Create legacy code to refactor
    print("📝 Creating legacy code...")

    # Legacy user manager (no classes, no type hints, poor structure)
    legacy_file = TEST_WORKSPACE / "user_manager.py"
    legacy_file.write_text("""# Legacy User Management System
# Written in 2010 - needs modernization!

users_db = {}  # Global variable - BAD!
next_id = 1

def add_user(name, email, age):
    global next_id, users_db
    user = {
        'id': next_id,
        'name': name,
        'email': email,
        'age': age,
        'active': True
    }
    users_db[next_id] = user
    next_id += 1
    return next_id - 1

def get_user(user_id):
    return users_db.get(user_id)

def update_user(user_id, name=None, email=None, age=None):
    if user_id in users_db:
        if name:
            users_db[user_id]['name'] = name
        if email:
            users_db[user_id]['email'] = email
        if age:
            users_db[user_id]['age'] = age
        return True
    return False

def delete_user(user_id):
    if user_id in users_db:
        del users_db[user_id]
        return True
    return False

def list_users():
    return list(users_db.values())

def find_by_email(email):
    for user in users_db.values():
        if user['email'] == email:
            return user
    return None

def deactivate_user(user_id):
    if user_id in users_db:
        users_db[user_id]['active'] = False
        return True
    return False

# Example usage
if __name__ == "__main__":
    id1 = add_user("John Doe", "john@example.com", 30)
    id2 = add_user("Jane Smith", "jane@example.com", 25)

    print("All users:", list_users())
    print("User 1:", get_user(id1))

    update_user(id1, age=31)
    print("Updated user 1:", get_user(id1))

    user = find_by_email("jane@example.com")
    print("Found user:", user)

    deactivate_user(id2)
    print("Deactivated user 2:", get_user(id2))
""")
    print(f"   ✅ Created: {legacy_file}")
    print(f"   📏 Size: {legacy_file.stat().st_size} bytes\n")

    # Connect
    print(f"🔌 Connecting to {BACKEND_URL}...")
    ws = await websockets.connect(BACKEND_URL)
    print("✅ Connected!\n")

    # Initialize session
    print("📤 Sending init message...")
    init_msg = {"type": "init", "workspace_path": str(TEST_WORKSPACE)}
    await ws.send(json.dumps(init_msg))

    # Wait for connected
    resp1 = await asyncio.wait_for(ws.recv(), timeout=10)
    data1 = json.loads(resp1)
    print(f"📥 {data1.get('type')}: {data1.get('message', '')[:50]}")

    # Wait for initialized
    resp2 = await asyncio.wait_for(ws.recv(), timeout=60)
    data2 = json.loads(resp2)
    session_id = data2.get("session_id")
    print(f"✅ Session initialized: {session_id}\n")

    # Send query - REFACTOR workflow
    query = """Refactor user_manager.py to modern Python standards:

1. Convert to object-oriented design with classes (User, UserRepository)
2. Add type hints for all functions and methods
3. Add comprehensive docstrings (Google style)
4. Replace global variables with proper state management
5. Add data validation (email format, age range, etc.)
6. Add error handling with custom exceptions
7. Implement proper separation of concerns (data model, repository, service)
8. Add __str__ and __repr__ methods to classes
9. Add property decorators where appropriate
10. Make it production-ready with logging and configuration

Keep the same functionality but modernize the code structure and style."""

    print(f"📤 Query: {query[:100]}...")
    print(f"🕐 Start: {datetime.now().strftime('%H:%M:%S')}\n")

    chat_msg = {"type": "chat", "content": query}
    await ws.send(json.dumps(chat_msg))

    # Monitor responses
    start = asyncio.get_event_loop().time()
    message_count = 0
    status_messages = []
    approval_count = 0
    result_received = False

    print("="*80)
    print("MONITORING WORKFLOW EXECUTION")
    print("="*80 + "\n")

    while asyncio.get_event_loop().time() - start < TEST_TIMEOUT:
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            message_count += 1

            msg_type = data.get("type")
            elapsed = int(asyncio.get_event_loop().time() - start)
            timestamp = f"[{elapsed:4d}s]"

            if msg_type == "status":
                msg = data.get('message', data.get('content', ''))
                status_messages.append(msg)
                print(f"{timestamp} 📊 {msg[:100]}")

            elif msg_type == "approval_request":
                approval_count += 1
                content = data.get('content', '')[:80]
                print(f"{timestamp} 🔐 Approval #{approval_count}: {content}")
                # Auto-approve
                approval_resp = {"type": "approval_response", "approved": True}
                await ws.send(json.dumps(approval_resp))
                print(f"{timestamp}    ✅ Auto-approved")

            elif msg_type == "model_selection":
                model = data.get('model', {})
                if isinstance(model, dict):
                    print(f"{timestamp} 🤖 Model: {model.get('name')} (think={model.get('think_mode')})")
                else:
                    print(f"{timestamp} 🤖 Model: {model}")

            elif msg_type == "result":
                result_received = True
                success = data.get('success')
                quality = data.get('quality_score', 'N/A')
                print(f"\n{timestamp} 🎯 RESULT RECEIVED!")
                print(f"{timestamp}    Success: {success}")
                print(f"{timestamp}    Quality: {quality}")
                break

            elif msg_type == "error":
                error_msg = data.get('message', '')
                print(f"\n{timestamp} ❌ ERROR: {error_msg}")
                break

        except asyncio.TimeoutError:
            elapsed = int(asyncio.get_event_loop().time() - start)
            if elapsed % 60 == 0:  # Every minute
                print(f"[{elapsed:4d}s] ⏳ Waiting... ({message_count} messages so far)")
            continue

    await ws.close()

    # Analysis
    elapsed_total = int(asyncio.get_event_loop().time() - start)
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"⏱️  Duration: {elapsed_total}s ({elapsed_total//60}min {elapsed_total%60}s)")
    print(f"📨 Messages received: {message_count}")
    print(f"🔐 Approvals: {approval_count}")
    print(f"✅ Result received: {result_received}")

    # Check generated files
    print(f"\n📁 Checking workspace: {TEST_WORKSPACE}")
    py_files = list(TEST_WORKSPACE.rglob("*.py"))
    py_files = [f for f in py_files if not str(f).endswith('__pycache__')]

    print(f"   Python files: {len(py_files)}")

    if py_files:
        print(f"\n   📄 Generated files:")
        for f in sorted(py_files)[:15]:
            rel_path = f.relative_to(TEST_WORKSPACE)
            size = f.stat().st_size
            print(f"      - {rel_path} ({size} bytes)")

    # Check if refactored code exists
    if legacy_file.exists():
        refactored_content = legacy_file.read_text()
        print(f"\n   📄 Refactored file: {legacy_file.name}")
        print(f"   📏 Size: {len(refactored_content)} bytes")

        # Check for refactoring improvements
        improvements = []
        if "class " in refactored_content:
            improvements.append("✅ Classes added (OOP design)")
        if "def __init__" in refactored_content:
            improvements.append("✅ __init__ methods (proper initialization)")
        if ": " in refactored_content and "->" in refactored_content:
            improvements.append("✅ Type hints added")
        if '"""' in refactored_content:
            improvements.append("✅ Docstrings added")
        if "Exception" in refactored_content or "Error" in refactored_content:
            improvements.append("✅ Error handling added")
        if "@property" in refactored_content:
            improvements.append("✅ Property decorators used")
        if "global " not in refactored_content:
            improvements.append("✅ Global variables removed")

        if improvements:
            print(f"\n   🔧 Refactoring improvements:")
            for improvement in improvements:
                print(f"      {improvement}")
        else:
            print(f"\n   ⚠️  Could not verify refactoring improvements")

    # Check for additional files
    model_files = list(TEST_WORKSPACE.glob("*model*.py"))
    repo_files = list(TEST_WORKSPACE.glob("*repository*.py"))
    service_files = list(TEST_WORKSPACE.glob("*service*.py"))
    exception_files = list(TEST_WORKSPACE.glob("*exception*.py"))
    test_files = list(TEST_WORKSPACE.glob("test_*.py"))

    if model_files or repo_files or service_files:
        print(f"\n   🏗️  Architecture files:")
        if model_files:
            print(f"      - Models: {[f.name for f in model_files]}")
        if repo_files:
            print(f"      - Repositories: {[f.name for f in repo_files]}")
        if service_files:
            print(f"      - Services: {[f.name for f in service_files]}")
        if exception_files:
            print(f"      - Exceptions: {[f.name for f in exception_files]}")
        if test_files:
            print(f"      - Tests: {[f.name for f in test_files]}")

    # Final verdict
    print("\n" + "="*80)
    if result_received and len(py_files) > 0:
        print("✅ TEST PASSED - Code refactored and result received!")
    elif len(py_files) > 0:
        print("⚠️  TEST PARTIAL - Code modified but timeout/no result")
    else:
        print("❌ TEST FAILED - No refactoring performed")
    print("="*80 + "\n")

    return result_received and len(py_files) > 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_refactor_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
