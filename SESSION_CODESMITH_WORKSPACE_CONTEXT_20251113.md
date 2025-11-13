# 📝 SESSION CONTEXT: Codesmith Workspace Isolation Feature

**Date:** November 13, 2025  
**Status:** Requirements Gathering & Planning Phase  
**Token Budget:** Considering budget for implementation

---

## 🎯 New Feature Requirement

**Feature:** Isolierte Code-Generierungs-Workspaces für Codesmith  
**Goal:** Each code generation job gets its own isolated, temporary workspace  
**Priority:** AFTER completing FIX #2 V2 validation (already done)  
**Tokens:** Check before implementation if reachable

---

## 📋 Background: Previous Session (FIX #2 V2)

### ✅ Completed
- FIX #2 V2 (Timeout-Free Async Stdin) implemented in all 6 MCP servers
- Changed from: `await asyncio.wait_for(..., timeout=300.0)` (arbitrary 300s)
- Changed to: `await loop.run_in_executor(None, _read)` (no timeout)
- All servers validated (6/6 pass)
- Rationale: EOF-based shutdown instead of arbitrary timeouts

### 📁 Files Modified
1. `mcp_servers/openai_server.py` (~63 lines)
2. `mcp_servers/architect_agent_server.py` (~63 lines)
3. `mcp_servers/codesmith_agent_server.py` (~63 lines)
4. `mcp_servers/research_agent_server.py` (~28 lines)
5. `mcp_servers/responder_agent_server.py` (~63 lines)
6. `mcp_servers/reviewfix_agent_server.py` (~63 lines)

### ✅ Documentation
- `FIX_2_V2_TIMEOUT_FREE_STDIN.md` - 348 lines, complete guide
- `SESSION_FIX2_V2_TIMEOUT_FREE_20251113.md` - 9.38 KB summary
- Validation script: `test_fix2_v2_validation.py`

---

## 🔍 New Feature: Codesmith Isolated Workspaces

### Requirements to Clarify
1. **Workspace Lifecycle:**
   - Create temporary workspace per code generation job? OR
   - Create persistent workspace with versioning? OR
   - Hybrid (temp for intermediate, persistent for finals)?

2. **Isolation Level:**
   - Complete file-level isolation per job?
   - Shared dependencies/config but isolated output?
   - Namespace-based isolation?

3. **Cleanup Policy:**
   - Auto-delete after job completion?
   - Retention period (e.g., 24h)?
   - Manual cleanup?
   - Archive old workspaces?

4. **Parallel Execution:**
   - Support concurrent code generation jobs?
   - How to handle resource conflicts?
   - Max concurrent workspaces?

5. **Workspace Discovery:**
   - How does Claude find which workspace for which job?
   - Workspace ID generation (UUID/timestamp/counter)?
   - Directory naming convention?

### Initial Research Findings
**Python Best Practice for Isolated Workspaces:**
- ✅ Use `tempfile.TemporaryDirectory()` context manager
- ✅ Automatic cleanup on exit
- ✅ Platform-independent (Linux/macOS/Windows)
- ✅ Secure: randomized names, restricted permissions
- ✅ Nested structure support

**Example Pattern:**
```python
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="codesmith_") as workspace:
    # Code generation happens here
    workspace_path = Path(workspace)
    # Files auto-delete when context exits
```

### Existing Codebase Context
- Current `codesmith_agent_server.py`: Line 246-248 uses `workspace_path` parameter
- Already receives workspace_path in requests
- Currently grants access via `--add-dir workspace_path`
- Current implementation expects client to provide workspace_path

### Proposed Architecture

**Option A: Server-Side Temp Workspace**
```
Request → Codesmith generates temp workspace → Code generation → Response → Cleanup
```
- Pros: Client doesn't manage workspaces, automatic cleanup
- Cons: Temp workspace info needs to be returned to client

**Option B: Client Provides, Server Isolates**
```
Request (workspace_path) → Codesmith isolates subdirs → Generation → Response
```
- Pros: Compatible with current architecture
- Cons: Client responsible for cleanup

**Option C: Hybrid with Versioning**
```
Request → Create versioned workspace → Generation → Keep history → Cleanup old
```
- Pros: Can review previous generations, audit trail
- Cons: More complex, needs retention policy

---

## 🏗️ Implementation Strategy (If Proceeding)

### Phase 1: Design & Simulation
1. **Clarify requirements** (HITL - ask user)
2. **Create simulation** (`test_codesmith_workspace_isolation.py`)
3. **Test patterns** before production code
4. **Document design** in separate spec

### Phase 2: Core Implementation
1. Create `CodesmithWorkspaceManager` class
2. Implement workspace creation/isolation
3. Integrate into `CodesmithAgentMCPServer`
4. Add comprehensive debug logging `[codesmith_ws]`
5. Add cleanup handlers

### Phase 3: Integration & Testing
1. Modify workspace handling in `generate()` method
2. Update progress notifications with workspace info
3. E2E tests for concurrent generation
4. Workspace cleanup verification
5. Performance benchmarks

### Phase 4: Documentation
1. Update `codesmith_agent_server.py` docstrings
2. Create `CODESMITH_WORKSPACE_ISOLATION_GUIDE.md`
3. Document workspace lifecycle
4. Troubleshooting guide

---

## ⚠️ Dependencies & Considerations

### Python Requirements
- ✅ `tempfile` (stdlib, no external dependency)
- ✅ `pathlib.Path` (stdlib)
- ✅ `asyncio` (already used)
- ? UUID generation (uuid stdlib)
- ? Thread-safe access (threading.Lock if needed)

### MCP Architecture Compatibility
- Must maintain pure MCP design
- Must not break stdin/stdout JSON-RPC protocol
- Must handle $/progress notifications during workspace creation
- Must support `--add-dir` for Claude CLI access

### Current System Status (from CLAUDE.md)
- Architecture: Pure MCP v7.0 (✅ stable)
- FIX #2 V2: Timeout-free stdin (✅ validated)
- FIX #3: Response routing (🔴 still debugging)
- E2E Testing: Needs work (timeout issues)

---

## 📊 Token Estimate

**If Proceeding with Implementation:**
- Research & Clarification: ~2,000 tokens
- Simulation & Testing: ~3,000 tokens
- Implementation: ~4,000 tokens
- Documentation: ~2,000 tokens
- **Total: ~11,000 tokens**

**Current Budget:** Check before starting

---

## 🎬 Next Steps

**BLOCKING QUESTION for User:**
1. Which workspace isolation model? (A/B/C above)
2. Can workspaces be auto-deleted or should they persist?
3. Any maximum concurrent workspace limit?

**Then:**
1. Create simulation test (`test_codesmith_workspace_isolation.py`)
2. Validate pattern with debug logging
3. Implement in actual `codesmith_agent_server.py`
4. E2E testing
5. Update documentation

---

## 📝 Related Files
- `mcp_servers/codesmith_agent_server.py` - Main implementation location
- `test_workspace_isolation.py` - Existing workspace security tests
- `FIX_2_V2_TIMEOUT_FREE_STDIN.md` - FIX #2 V2 documentation
- `PYTHON_BEST_PRACTICES.md` - Coding standards
- `CLAUDE.md` - Core guidelines (1,268 lines)

---

**READY TO PROCEED?** 
- Ask user above clarification questions
- Create simulation when ready
- Implement if tokens available
