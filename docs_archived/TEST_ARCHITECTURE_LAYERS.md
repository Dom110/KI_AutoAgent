# 🔬 Test Architecture - 4 Layers Explained

**Version:** 1.0.0  
**Date:** 2025-11-12  
**Status:** Complete Architecture Definition  

---

## 🎯 The 4 Test Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: AI DEVELOPER (Me)                                      │
│ Develop new features for KI_AutoAgent                           │
└─────────┬───────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: BACKEND TESTS (backend/tests/)                         │
│ Unit Tests for MY feature development                           │
│ • pytest framework                                              │
│ • Isolated testing (no WebSocket)                               │
│ • Used DURING development                                       │
│ • Fast feedback loops                                           │
└─────────┬───────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3a: START KI_AGENT BACKEND                                │
│ Backend startup with MCP servers                                │
│ • python backend/workflow_v7_mcp.py                             │
│ • WebSocket on port 8002                                        │
│ • Workspace: ~/TestApps/e2e_test_run/                           │
└─────────┬───────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3b: E2E TESTS FOR THE AGENT (test_v7_e2e_*.py)           │
│ WebSocket tests of KI_AutoAgent itself                          │
│ • websockets framework                                          │
│ • Test Agent functionality                                      │
│ • Send tasks → Monitor progress → Validate                      │
│ • Used AFTER feature implementation                             │
│ • Tests THE AGENT - not generated apps                          │
└─────────┬───────────────────────────────────────────────────────┘
          ↓
      [Agent runs]
      [Agent creates application]
          ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: E2E TESTING FRAMEWORK (backend/e2e_testing/)           │
│ Framework INTERNAL to Agent                                      │
│ • Playwright browser automation                                 │
│ • Agent uses automatically                                      │
│ • Tests the GENERATED APP - not the Agent                       │
│ • Used by Agent during task execution                           │
│ • Not manually triggered by developer                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Test Files Classification

### **Layer 2: BACKEND TESTS (For Feature Development)**

```
/Users/dominikfoert/git/KI_AutoAgent/backend/tests/

ACTIVE (Current):
├── test_error_recovery_framework.py                ← Error Recovery Unit
├── test_codesmith_error_recovery_integration.py    ← CodeSmith Unit
├── test_research_error_recovery_integration.py     ← Research Unit
├── test_e2e_generator.py                           ← Generator Logic
├── test_workflow_planner_e2e.py                    ← Workflow Logic
└── test_e2e_complex_app_workflow.py                ← Workflow Integration

DEPRECATED (Legacy v6.x):
├── e2e_comprehensive_v6_2.py                       ❌ Old
├── e2e_test_v6_3.py                                ❌ Old
├── e2e_test_v6_3_websocket.py                      ❌ Old
└── e2e_test3_error_handling.py                     ❌ Old
```

**Purpose:**
- Unit tests for new features
- Fast validation during development
- No external dependencies (no WebSocket)
- **Run:** `pytest backend/tests/ -v`

---

### **Layer 3b: E2E TESTS FOR THE AGENT (WebSocket)**

```
/Users/dominikfoert/git/KI_AutoAgent/

ACTIVE (Current v7.0):
├── test_v7_e2e_app_creation.py                     ⭐ MAIN PATTERN
├── e2e_test_v7_0_supervisor.py                     ⭐ Supervisor Pattern
├── test_agent_websocket_real_e2e.py                ⭐ WebSocket Pattern
├── test_e2e_client.py                              ⭐ Client Utility
├── test_e2e_with_monitoring.py                     ⭐ Monitoring
└── e2e_test_live_monitor.py                        ⭐ Live Feed

DEPRECATED (Legacy):
├── comprehensive_e2e_test.py                       ❌ Old
├── e2e_test_v6_6_comprehensive.py                  ❌ Old
├── e2e_test_single.py                              ❌ Old
├── e2e_test_detailed_logs.py                       ❌ Old
└── validate_e2e_installation.py                    ⚠️  Installation only
```

**Purpose:**
- WebSocket tests of KI_AutoAgent
- Test Agent functionality via WebSocket
- Send tasks → Monitor → Validate
- **Run:** `python3 test_v7_e2e_app_creation.py`

---

### **Layer 4: E2E TESTING FRAMEWORK (Agent-Internal)**

```
/Users/dominikfoert/git/KI_AutoAgent/backend/e2e_testing/

FRAMEWORK FILES:
├── test_executor.py                                ← Playwright Runner
├── test_generator.py                               ← Test Generator
├── browser_engine.py                               ← Browser Automation
├── react_analyzer.py                               ← React Analysis
├── assertions.py                                   ← Validators
│
├── universal_framework/
│   ├── framework_detector.py                       ← Auto-detect Framework
│   ├── base_analyzer.py                            ← Base Analyzer
│   ├── universal_generator.py                      ← Auto Test Gen
│   └── adapters/
│       └── react_adapter.py                        ← React Adapter
│
└── __init__.py
```

**Purpose:**
- Framework INTERNAL to Agent
- Agent uses automatically when running tasks
- Tests generated applications (not the Agent)
- Not manually triggered by developer
- **Usage:** Agent calls automatically

---

## 🔄 Development Workflow Example

### **Feature: "Implement XYZ Error Handler"**

#### **Step 1: Write Backend Unit Test** (Layer 2)

```python
# File: backend/tests/test_xyz_error_handler.py
"""
LAYER 2: BACKEND TEST

Unit test for XYZ Error Handler
Framework: pytest
User: Developer during development
Time: ~2 minutes to run

Execution:
  cd /Users/dominikfoert/git/KI_AutoAgent
  pytest backend/tests/test_xyz_error_handler.py -v
  
Related:
  - Layer 3b E2E: test_e2e_xyz_feature.py
  - Implementation: backend/core/error_handlers/xyz.py
"""

import pytest
from backend.core.error_handlers.xyz import XyzErrorHandler

def test_xyz_handler_catches_errors():
    """[Layer 2] XYZ handler catches specific errors"""
    handler = XyzErrorHandler()
    
    # Test error catching
    result = handler.handle(ValueError("test"))
    assert result.handled == True
    assert result.error_type == "ValueError"
    
def test_xyz_handler_retries():
    """[Layer 2] XYZ handler retries on transient errors"""
    handler = XyzErrorHandler(max_retries=3)
    
    # Test retry logic
    result = handler.handle_with_retry(TimeoutError("timeout"))
    assert result.retry_count >= 1
```

✅ **Status:** Feature works in isolation

---

#### **Step 2: Implement Feature**

```python
# File: backend/core/error_handlers/xyz.py
# ============================================================
# Layer 2 Test: backend/tests/test_xyz_error_handler.py
# Layer 3b Test: test_e2e_xyz_feature.py
# ============================================================
# Unit-testable via: pytest backend/tests/
# E2E-testable via: WebSocket test (see Layer 3b)
# ============================================================

class XyzErrorHandler:
    """XYZ specific error handler"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    def handle(self, error: Exception) -> dict:
        """Handle XYZ error"""
        # ... implementation
        pass
```

---

#### **Step 3: Run Backend Tests**

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python3 -m pytest backend/tests/test_xyz_error_handler.py -v

# Output:
# test_xyz_handler_catches_errors PASSED
# test_xyz_handler_retries PASSED
# =============== 2 passed in 0.45s ===============
```

✅ **Status:** Unit tests passing

---

#### **Step 4: Write E2E WebSocket Test** (Layer 3b)

```python
# File: test_e2e_xyz_feature.py
"""
LAYER 3b: E2E TEST (WebSocket)

E2E test for XYZ Error Handler in Agent context
Framework: websockets
User: Developer after feature implementation
Time: ~5 minutes to run (includes Backend startup + Task execution)

Workflow:
  1. Prepare workspace (~/TestApps/e2e_xyz_test/)
  2. Start KI_Agent Backend (Layer 3a)
  3. Connect WebSocket client
  4. Send task that uses XYZ Handler
  5. Monitor progress
  6. Validate results
  7. Agent auto-tests generated app (Layer 4)

Execution:
  cd /Users/dominikfoert/git/KI_AutoAgent
  python3 test_e2e_xyz_feature.py
  
Related:
  - Layer 2 Unit: backend/tests/test_xyz_error_handler.py
  - Implementation: backend/core/error_handlers/xyz.py
  - Layer 4 Framework: backend/e2e_testing/ (automatic)
"""

import asyncio
import json
import shutil
import websockets
from pathlib import Path
from datetime import datetime

TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_xyz_feature"
BACKEND_WS_URL = "ws://localhost:8002/ws/chat"
TEST_TIMEOUT = 300  # 5 minutes

async def main():
    """[Layer 3b] E2E WebSocket Test for XYZ Feature"""
    
    # Step 1: Prepare workspace
    print(f"🧹 [E2E] Preparing workspace...")
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
    print(f"✅ [E2E] Workspace ready: {TEST_WORKSPACE}")
    
    # Step 2: Start backend
    print(f"🚀 [E2E] Starting backend...")
    process = await asyncio.create_subprocess_exec(
        "python", "backend/workflow_v7_mcp.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(TEST_WORKSPACE),
    )
    print(f"✅ [E2E] Backend started (PID: {process.pid})")
    await asyncio.sleep(3)
    
    try:
        # Step 3: Connect WebSocket
        print(f"📡 [E2E] Connecting WebSocket...")
        async with websockets.connect(BACKEND_WS_URL) as ws:
            print(f"✅ [E2E] WebSocket connected")
            
            # Step 4: Send task (uses XYZ Handler)
            task = {
                "type": "task",
                "content": "Create app that tests error handling with XYZ Handler",
                "workspace_path": str(TEST_WORKSPACE),
            }
            print(f"📤 [E2E] Sending task...")
            await ws.send(json.dumps(task))
            print(f"✅ [E2E] Task sent")
            
            # Step 5: Monitor progress
            print(f"⏳ [E2E] Monitoring progress...")
            start_time = datetime.now()
            
            while True:
                message = await ws.recv()
                data = json.loads(message)
                
                if data.get("type") == "progress":
                    progress = data.get("progress", 0)
                    print(f"⏳ [E2E] Progress: {progress}%")
                
                elif data.get("type") == "complete":
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"✅ [E2E] Task complete in {elapsed:.1f}s")
                    
                    # Step 6: Validate
                    print(f"🔍 [E2E] Running validations...")
                    
                    # Check files exist
                    assert (TEST_WORKSPACE / "README.md").exists()
                    assert (TEST_WORKSPACE / "src").is_dir()
                    print(f"✅ [E2E] Files validated")
                    
                    # Check XYZ handler in code
                    src_files = list((TEST_WORKSPACE / "src").rglob("*.py"))
                    assert any("error_handler" in f.read_text() for f in src_files)
                    print(f"✅ [E2E] XYZ Handler found in generated code")
                    
                    print(f"✅ [E2E] ALL VALIDATIONS PASSED")
                    print(f"📊 [E2E] Workspace: {TEST_WORKSPACE}")
                    return True
                
                elif data.get("type") == "error":
                    print(f"❌ [E2E] Agent error: {data.get('error')}")
                    raise Exception(data.get("error"))
                
                # Timeout check
                if (datetime.now() - start_time).total_seconds() > TEST_TIMEOUT:
                    raise TimeoutError(f"Test exceeded {TEST_TIMEOUT}s timeout")
    
    finally:
        # Cleanup (optional - keep for inspection on success)
        if process.returncode is None:
            process.terminate()
            await process.wait()

if __name__ == "__main__":
    asyncio.run(main())
```

✅ **Status:** Feature works via WebSocket in Agent

---

#### **Step 5: Run E2E WebSocket Test**

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python3 test_e2e_xyz_feature.py

# Output:
# 🧹 [E2E] Preparing workspace...
# ✅ [E2E] Workspace ready: /Users/.../TestApps/e2e_xyz_feature
# 🚀 [E2E] Starting backend...
# ✅ [E2E] Backend started (PID: 12345)
# 📡 [E2E] Connecting WebSocket...
# ✅ [E2E] WebSocket connected
# 📤 [E2E] Sending task...
# ✅ [E2E] Task sent
# ⏳ [E2E] Monitoring progress...
# ⏳ [E2E] Progress: 25%
# ⏳ [E2E] Progress: 50%
# ⏳ [E2E] Progress: 75%
# ✅ [E2E] Task complete in 45.3s
# 🔍 [E2E] Running validations...
# ✅ [E2E] Files validated
# ✅ [E2E] XYZ Handler found in generated code
# ✅ [E2E] ALL VALIDATIONS PASSED
```

✅ **Status:** Agent validated feature, created app, tested it (Layer 4)

---

#### **Step 6: Analyze Logs**

```bash
# Backend logs
tail -100 /tmp/backend.log | grep "xyz\|error_handler\|Layer"

# WebSocket logs
tail -100 /tmp/websocket.log | grep "xyz\|[E2E]"

# Layer 4 Framework (auto generated)
cat ~/TestApps/e2e_xyz_feature/test_results.json
```

---

#### **Step 7: Update Documentation**

```markdown
# XYZ Error Handler Implementation

## Features Implemented
- Catches XYZ specific errors
- Implements retry logic
- Circuit breaker support

## Tests
- **Layer 2:** backend/tests/test_xyz_error_handler.py (✅ 2/2)
- **Layer 3b:** test_e2e_xyz_feature.py (✅ PASSED)
- **Layer 4:** Auto-tested in generated apps

## Documentation
- Code: backend/core/error_handlers/xyz.py
- Doc: This file
```

---

## 📊 Test Matrix

| Test Type | Layer | User | Framework | Time | When | What |
|-----------|-------|------|-----------|------|------|------|
| **Unit** | 2 | Developer | pytest | 2 min | During dev | Feature logic |
| **Backend** | 2 | Developer | pytest | 5 min | During dev | Integration |
| **E2E WebSocket** | 3b | Developer | websockets | 10 min | After dev | Agent functionality |
| **E2E Framework** | 4 | Agent | Playwright | 10 min | Auto-run | Generated app |

---

## ✅ Key Rules

### **Layer 2 (Backend Tests)**
- ✅ Run during feature development
- ✅ Test feature logic isolated
- ✅ No WebSocket dependencies
- ❌ Don't test Agent communication
- ❌ Don't test generated apps

### **Layer 3b (E2E WebSocket Tests)**
- ✅ Run after feature implementation
- ✅ Test Agent handles feature correctly
- ✅ Test via WebSocket
- ✅ Test within Agent (not generated app)
- ❌ Don't test generated app functionality

### **Layer 4 (E2E Framework)**
- ✅ Agent runs automatically
- ✅ Tests generated applications
- ✅ Browser automation (Playwright)
- ✅ Real-world app validation
- ❌ Don't manually trigger (unless debugging)

---

## 📋 Workspace Isolation Rules

### **Critical for Layer 3b E2E Tests:**

```
✅ CORRECT:
TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_xyz_feature"
# Isolated, clean workspace

❌ WRONG:
TEST_WORKSPACE = Path(__file__).parent / "test_output"
# Pollutes development repo!
```

### **Backend Startup with CWD:**

```python
# ✅ CORRECT: Set working directory
process = await asyncio.create_subprocess_exec(
    "python", "backend/workflow_v7_mcp.py",
    cwd=str(TEST_WORKSPACE),  # 🎯 CRITICAL!
)

# ❌ WRONG: No CWD specified
process = await asyncio.create_subprocess_exec(
    "python", "backend/workflow_v7_mcp.py",
)
```

---

## 🔗 Related Documentation

- **Development Strategy**: `DEVELOPMENT_AI_ASSISTANT_STRATEGY.md`
- **E2E Guide**: `E2E_TESTING_GUIDE.md`
- **Backend Guidelines**: `backend/CLAUDE.md`
- **Python Best Practices**: `PYTHON_BEST_PRACTICES.md`

---

**Last Updated:** 2025-11-12
**Next Review:** When new test patterns emerge
