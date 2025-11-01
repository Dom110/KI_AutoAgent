# Pure MCP Architecture - Testing Plan

**Created:** 2025-10-31
**Step:** 7/7 (Final Step)
**Status:** In Progress

---

## 🎯 Testing Objectives

Verify that the Pure MCP migration is fully functional:

1. ✅ All MCP servers start correctly
2. ✅ MCPManager can communicate with all servers
3. ✅ Workflow can execute MCP tool calls
4. ✅ Progress notifications are forwarded correctly
5. ✅ No import errors in MCP architecture
6. ✅ End-to-end workflow execution works

---

## 📋 Test Categories

### 1. MCP Server Startup Tests

**Goal:** Verify each MCP server can start and respond to JSON-RPC

**Servers to test:**
- `openai_server.py`
- `research_agent_server.py`
- `architect_agent_server.py`
- `codesmith_agent_server.py`
- `reviewfix_agent_server.py`
- `responder_agent_server.py`

**Test method:**
```bash
# Start server
python mcp_servers/openai_server.py

# Send initialize request via stdin
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | python mcp_servers/openai_server.py

# Expected: JSON response with capabilities
```

**Success criteria:**
- Server starts without errors
- Responds to initialize with capabilities
- tools/list returns expected tools
- Process exits cleanly on EOF

### 2. MCPManager Initialization Tests

**Goal:** Verify MCPManager can connect to all servers

**Test script:** `test_mcp_manager.py`

**Test cases:**
- Initialize MCPManager
- Verify all servers are connected
- Test singleton pattern (get_mcp_manager returns same instance)
- Test server reconnection on failure

**Success criteria:**
- All 10 servers connected
- No subprocess errors
- Singleton returns same instance
- Reconnection works

### 3. MCP Tool Call Tests

**Goal:** Verify MCPManager can execute tool calls

**Test cases:**
- Call openai.complete with simple prompt
- Call responder.format_response with sample data
- Test error handling for invalid server
- Test error handling for invalid tool

**Success criteria:**
- Tool calls return valid MCP responses
- Results can be extracted correctly
- Errors are handled gracefully

### 4. Workflow Execution Tests

**Goal:** Verify workflow_v7_mcp.py works end-to-end

**Test cases:**
- Simple EXPLAIN workflow (no web search)
- Verify research_node calls research_agent MCP server
- Verify architect_node calls architect_agent MCP server
- Verify supervisor routing works

**Success criteria:**
- Workflow completes without errors
- MCP tool calls are executed
- State updates correctly
- Final response is generated

### 5. Progress Notification Tests

**Goal:** Verify $/progress notifications are forwarded

**Test cases:**
- Monitor progress callbacks in MCPManager
- Verify progress events are sent to event_manager
- Test WebSocket forwarding in server_v7_mcp.py

**Success criteria:**
- Progress notifications received from MCP servers
- Callbacks are invoked correctly
- Events are forwarded to WebSocket clients

### 6. Import Verification Tests

**Goal:** Ensure no old code is imported

**Test method:**
```bash
# Search for old imports in MCP files
grep -r "from backend.agents.architect_agent import" backend/
grep -r "from backend.utils.ai_factory import" backend/
grep -r "from backend.workflow_v7_supervisor import" backend/
```

**Success criteria:**
- No matches found for old imports
- Only MCP imports present
- No broken dependencies

### 7. Integration Tests

**Goal:** Test real workflow with actual AI calls

**Test cases:**
- Start backend server
- Connect WebSocket client
- Send user query: "Explain the MCP architecture"
- Monitor events

**Success criteria:**
- Workflow executes completely
- MCP progress events received
- Final response generated
- No errors or timeouts

---

## 🔧 Test Scripts

### `test_mcp_manager.py`

```python
"""Test MCPManager initialization and basic functionality"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.mcp_manager import get_mcp_manager, close_mcp_manager

async def test_initialization():
    print("🧪 Test 1: MCPManager Initialization")

    mcp = get_mcp_manager(workspace_path="/tmp/test_workspace")

    try:
        await mcp.initialize()
        print("✅ MCPManager initialized successfully")

        # Check connected servers
        for server in mcp.servers:
            if server in mcp.processes:
                print(f"✅ Server '{server}' connected")
            else:
                print(f"❌ Server '{server}' NOT connected")

        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    finally:
        await close_mcp_manager()

async def test_singleton():
    print("\n🧪 Test 2: Singleton Pattern")

    mcp1 = get_mcp_manager(workspace_path="/tmp/test1")
    mcp2 = get_mcp_manager(workspace_path="/tmp/test2")

    if mcp1 is mcp2:
        print("✅ Singleton pattern works (same instance returned)")
        return True
    else:
        print("❌ Singleton pattern broken (different instances)")
        return False

async def main():
    results = []

    results.append(await test_initialization())
    results.append(await test_singleton())

    print(f"\n📊 Results: {sum(results)}/{len(results)} tests passed")
    return all(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

### `test_mcp_tool_call.py`

```python
"""Test MCP tool calls"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.mcp_manager import get_mcp_manager, close_mcp_manager

async def test_responder_format():
    print("🧪 Test: Responder Format Response")

    mcp = get_mcp_manager(workspace_path="/tmp/test")

    try:
        await mcp.initialize()

        # Call responder (no AI, should be fast)
        result = await mcp.call(
            server="responder_agent",
            tool="format_response",
            arguments={
                "user_query": "Test query",
                "context": {"test": "data"},
                "workspace_path": "/tmp/test"
            }
        )

        print(f"✅ Tool call successful!")
        print(f"📦 Result: {json.dumps(result, indent=2)}")

        # Verify result structure
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            print("✅ Result structure valid")
            return True
        else:
            print("❌ Invalid result structure")
            return False

    except Exception as e:
        print(f"❌ Tool call failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_mcp_manager()

if __name__ == "__main__":
    success = asyncio.run(test_responder_format())
    sys.exit(0 if success else 1)
```

---

## 📊 Test Execution Order

1. **Import Verification** (fastest, no setup needed)
2. **MCP Server Startup** (individual servers)
3. **MCPManager Initialization** (requires all servers)
4. **MCP Tool Calls** (requires MCPManager)
5. **Workflow Execution** (requires full stack)
6. **Progress Notifications** (requires WebSocket)
7. **Integration Test** (full end-to-end)

---

## ✅ Success Criteria

**Migration is COMPLETE when:**
- [ ] All MCP servers start without errors
- [ ] MCPManager connects to all 10 servers
- [ ] Tool calls execute and return valid responses
- [ ] Workflow completes without errors
- [ ] Progress notifications are forwarded
- [ ] No old code imports found
- [ ] Integration test passes

**Expected Issues:**
- API keys may need to be configured
- Some tools may timeout (expected for long operations)
- Progress notifications may be noisy (expected behavior)

---

## 🎯 Next Steps After Testing

1. Create `MCP_MIGRATION_STEP7_COMPLETE.md`
2. Create `MCP_MIGRATION_FINAL_SUMMARY.md`
3. Update CLAUDE.md to reference v7.0 MCP as current architecture
4. Archive old architecture documents

---

**Testing Status:** Ready to Execute
