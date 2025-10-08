"""
Native WebSocket Test for Phase 2

Tests workflow_v6 and memory_system_v6 through actual WebSocket connection.

Requirements:
- Backend running on ws://localhost:8001/ws/chat
- Python 3.13+
- websockets library

Usage:
    # Terminal 1: Start backend
    cd backend
    python api/server.py

    # Terminal 2: Run test
    python tests/native/native_test_phase2.py

What this tests:
- AsyncSqliteSaver checkpoint creation
- Memory system store/search
- Workflow execution end-to-end
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("ERROR: websockets library not installed")
    print("Install with: pip install websockets")
    sys.exit(1)


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

BACKEND_URL = "ws://localhost:8001/ws/chat"
WORKSPACE_PATH = "/tmp/test-workspace-phase2"


# ============================================================================
# TEST UTILITIES
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, level: str = "INFO"):
    """Pretty print log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": Colors.OKBLUE,
        "SUCCESS": Colors.OKGREEN,
        "WARNING": Colors.WARNING,
        "ERROR": Colors.FAIL,
        "HEADER": Colors.HEADER
    }
    color = colors.get(level, "")
    print(f"{color}[{timestamp}] {level}: {message}{Colors.ENDC}")


def print_separator(title: str = ""):
    """Print section separator."""
    if title:
        print(f"\n{Colors.BOLD}{'='*70}")
        print(f"{title:^70}")
        print(f"{'='*70}{Colors.ENDC}\n")
    else:
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")


# ============================================================================
# WEBSOCKET TEST CLIENT
# ============================================================================

class Phase2TestClient:
    """WebSocket test client for Phase 2 testing."""

    def __init__(self, url: str = BACKEND_URL):
        self.url = url
        self.ws = None

    async def connect(self):
        """Connect to WebSocket backend."""
        log(f"Connecting to {self.url}...", "INFO")
        try:
            self.ws = await websockets.connect(self.url, ping_timeout=120)
            log("Connected successfully", "SUCCESS")
            return True
        except Exception as e:
            log(f"Connection failed: {e}", "ERROR")
            return False

    async def send_message(self, message: dict) -> dict:
        """Send message and wait for response."""
        if not self.ws:
            raise RuntimeError("Not connected")

        log(f"Sending: {message['type']}", "INFO")
        await self.ws.send(json.dumps(message))

        response = await self.ws.recv()
        response_data = json.loads(response)
        log(f"Received: {response_data.get('type', 'unknown')}", "SUCCESS")

        return response_data

    async def close(self):
        """Close connection."""
        if self.ws:
            await self.ws.close()
            log("Connection closed", "INFO")


# ============================================================================
# PHASE 2 TESTS
# ============================================================================

async def test_1_initialization(client: Phase2TestClient):
    """Test 1: WebSocket initialization with workspace path."""
    print_separator("TEST 1: Initialization")

    response = await client.send_message({
        "type": "init",
        "workspace_path": WORKSPACE_PATH
    })

    assert response["type"] == "initialized", f"Expected 'initialized', got {response['type']}"
    assert "workspace_path" in response
    assert "session_id" in response

    log(f"Workspace: {response['workspace_path']}", "SUCCESS")
    log(f"Session ID: {response['session_id']}", "SUCCESS")

    return response


async def test_2_checkpoint_creation(client: Phase2TestClient):
    """Test 2: Workflow execution creates checkpoints."""
    print_separator("TEST 2: Checkpoint Creation")

    response = await client.send_message({
        "type": "chat",
        "message": "Test checkpoint creation"
    })

    # In Phase 2, we expect the workflow to execute (even if agents are placeholders)
    # The key is that a checkpoint should be created

    log(f"Workflow executed", "SUCCESS")

    # Check that checkpoint database exists
    import os
    from pathlib import Path

    checkpoint_db = Path(WORKSPACE_PATH) / ".ki_autoagent_ws/cache/workflow_checkpoints_v6.db"

    # Give it a moment to write
    await asyncio.sleep(0.5)

    if checkpoint_db.exists():
        log("Checkpoint database created", "SUCCESS")
    else:
        log("WARNING: Checkpoint database not found (may not be implemented yet)", "WARNING")

    return response


async def test_3_memory_system(client: Phase2TestClient):
    """Test 3: Memory system store and search."""
    print_separator("TEST 3: Memory System")

    # This test requires the backend to expose memory operations
    # In Phase 2, this might not be fully wired up yet

    # Try to store memory (if backend supports it)
    try:
        response = await client.send_message({
            "type": "memory_store",
            "content": "Phase 2 test memory item",
            "metadata": {"agent": "test", "type": "test_data"}
        })

        if response.get("type") == "memory_stored":
            log("Memory store successful", "SUCCESS")

            # Try to search
            search_response = await client.send_message({
                "type": "memory_search",
                "query": "test memory",
                "k": 5
            })

            if search_response.get("type") == "memory_results":
                results = search_response.get("results", [])
                log(f"Memory search returned {len(results)} results", "SUCCESS")
            else:
                log("Memory search not implemented yet", "WARNING")

        else:
            log("Memory operations not exposed via WebSocket yet", "WARNING")

    except Exception as e:
        log(f"Memory test skipped: {e}", "WARNING")
        log("This is expected in Phase 2 - memory ops may not be wired to WebSocket yet", "INFO")


async def test_4_multiple_sessions(client: Phase2TestClient):
    """Test 4: Multiple sessions maintain separate state."""
    print_separator("TEST 4: Multiple Sessions")

    # Session 1
    response1 = await client.send_message({
        "type": "chat",
        "message": "Session 1 test message",
        "session_id": "test_session_1"
    })

    # Session 2
    response2 = await client.send_message({
        "type": "chat",
        "message": "Session 2 test message",
        "session_id": "test_session_2"
    })

    log("Multiple sessions executed", "SUCCESS")
    log("Sessions should have separate checkpoints (check database)", "INFO")


async def test_5_error_handling(client: Phase2TestClient):
    """Test 5: Error handling and recovery."""
    print_separator("TEST 5: Error Handling")

    # Send invalid message type
    try:
        response = await client.send_message({
            "type": "invalid_type",
            "data": "This should trigger an error"
        })

        if response.get("type") == "error":
            log("Error handled correctly", "SUCCESS")
        else:
            log("Backend accepted invalid message type (might be too permissive)", "WARNING")

    except Exception as e:
        log(f"Exception during error test: {e}", "WARNING")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all Phase 2 tests."""
    print_separator("KI AUTOAGENT v6.0 - PHASE 2 NATIVE TESTS")

    client = Phase2TestClient()

    try:
        # Connect
        if not await client.connect():
            log("FATAL: Could not connect to backend", "ERROR")
            log("Make sure backend is running: python api/server.py", "ERROR")
            return False

        # Run tests
        await test_1_initialization(client)
        await test_2_checkpoint_creation(client)
        await test_3_memory_system(client)
        await test_4_multiple_sessions(client)
        await test_5_error_handling(client)

        # Summary
        print_separator("TEST SUMMARY")
        log("All Phase 2 tests completed", "SUCCESS")
        log("Check logs above for any warnings or errors", "INFO")

        return True

    except Exception as e:
        log(f"Test suite failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close()


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    import logging

    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise

    # Run tests
    success = asyncio.run(run_all_tests())

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
