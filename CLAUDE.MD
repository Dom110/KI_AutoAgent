# Claude Code Instructions - Core Guidelines

**Version:** v7.0.0-mcp (PURE MCP ARCHITECTURE)
**Last Updated:** 2025-10-31

---

## ✅ v7.0 Pure MCP Architecture - COMPLETE!

**⚠️ MCP BLEIBT:** This project uses Pure MCP (Model Context Protocol) architecture!

**Current Architecture:**
- **MCP Migration Complete:** `/MCP_MIGRATION_FINAL_SUMMARY.md` - ✅ **READ THIS!**
- **Implementation Plan:** `/PURE_MCP_IMPLEMENTATION_PLAN.md` - 7-step migration plan
- **Testing Documentation:** `/MCP_TESTING_PLAN.md` - Testing strategy
- **Step-by-step Docs:** `/MCP_MIGRATION_STEP[1-7]_COMPLETE.md` - Detailed completion reports

**Previous Architecture (ARCHIVED):**
- Old v6.6 Architecture: `/ARCHITECTURE_CURRENT_v6.6.md` (obsolete)
- Old v7.0 Supervisor Plan: `/ARCHITECTURE_TARGET_v7.0.md` (superseded by MCP)

---

## 📋 Document Structure

This document contains ONLY core instructions. Detailed guides have been split into separate files:

- **Critical Failure Detection:** `/CRITICAL_FAILURE_INSTRUCTIONS.md` ⚠️
- **Claude CLI Integration:** `/CLAUDE_CLI_INTEGRATION.md`
- **Build Validation System:** `/BUILD_VALIDATION_GUIDE.md`
- **E2E Testing Best Practices:** `/E2E_TESTING_GUIDE.md`
- **Python Coding Standards:** `/PYTHON_BEST_PRACTICES.md`
- **Claude Best Practices:** `/CLAUDE_BEST_PRACTICES.md`

---

## 🚨 CRITICAL: Error Handling Rules

**MANDATORY:** Read `/CRITICAL_FAILURE_INSTRUCTIONS.md` before any code changes!

**Core Principle:** **ANY ERROR = SYSTEM FAILURE**

- Test failures = System failures (no "partial success")
- Backend log activity ≠ Working system
- Code existence ≠ Working features
- Production-ready ONLY when ALL tests pass

**User's Explicit Instruction:**
> "Dein optimismus bei der Softwareentwicklung geht gar nicht!"
> (Your optimism in software development is unacceptable!)

**Translation:** Be pessimistic. Treat every error as critical. Never assume partial success.

---

## 🏗️ System Architecture (Quick Reference)

### Pure MCP Architecture (v7.0)

**⚠️ MCP BLEIBT:** ALL agents are MCP servers communicating via JSON-RPC!

```
FastAPI Server (server_v7_mcp.py)
    ↓
Workflow (workflow_v7_mcp.py)
    ↓
MCPManager (mcp_manager.py)
    ↓
MCP Servers (11 servers via JSON-RPC)
    ├── Agent Servers (6)
    │   ├── openai_server.py
    │   ├── research_agent_server.py
    │   ├── architect_agent_server.py
    │   ├── codesmith_agent_server.py
    │   ├── reviewfix_agent_server.py
    │   └── responder_agent_server.py
    └── Utility Servers (5)
        ├── perplexity_server.py
        ├── memory_server.py
        ├── build_validation_server.py
        ├── file_tools_server.py
        └── tree_sitter_server.py
```

### Key Principles:
1. **Pure MCP** - ALL agents communicate via JSON-RPC 2.0 over stdin/stdout
2. **Process Isolation** - Each MCP server runs as separate subprocess
3. **Progress Streaming** - $/progress notifications forwarded to clients
4. **Global MCPManager** - Singleton manages all server connections
5. **On-Demand Startup** - MCP servers start when first needed
6. **Multi-Client** - WebSocket protocol (ws://localhost:8002/ws/chat)
7. **Workspace Isolation** - Each client sends workspace_path on connect
8. **NO Spawning** - VS Code extension NEVER starts backend

**Full Details:** See `/MCP_MIGRATION_FINAL_SUMMARY.md`

---

## 🤖 Claude CLI Integration (Quick Reference)

**Model:** `claude-sonnet-4-20250514` (Sonnet 4.5)

**Valid Tools:** ONLY `["Read", "Edit", "Bash"]`
- ❌ **"Write" does NOT exist!**
- ✅ Use "Edit" to create/modify files

**Critical:** Always set `cwd=workspace_path` in subprocess calls!

**Full Details:** See `/CLAUDE_CLI_INTEGRATION.md`

---

## 🏗️ Build Validation (Quick Reference)

**Supported Languages:**
- TypeScript (tsc --noEmit) - Threshold: 0.90
- Python (mypy) - Threshold: 0.85
- JavaScript (eslint) - Threshold: 0.75

**Polyglot Support:** Multiple checks run for mixed-language projects

**When Build Fails:** Quality score → 0.50 (forces iteration)

**Full Details:** See `/BUILD_VALIDATION_GUIDE.md`

---

## 🧪 E2E Testing (Quick Reference)

### GOLDEN RULE:
```
🚨 NEVER run E2E tests in development repository!
🚨 ALWAYS use separate test workspace (~/TestApps/)
```

**Why:** Claude CLI finds old test artifacts, gets confused, crashes

**Critical:** Set `cwd=workspace_path` in subprocess!

**Full Details:** See `/E2E_TESTING_GUIDE.md`

---

## 🐍 Python Coding Standards (Quick Reference)

**Python Version:** 3.13+ (no backward compatibility required)

**Key Rules:**
1. Initialize variables BEFORE try blocks
2. Use specific exception types
3. Type hints for all public functions (use `|` not `Union`)
4. Context managers for all resources
5. `asyncio.gather()` for concurrent execution

**Full Details:** See `/PYTHON_BEST_PRACTICES.md`

---

## 🔧 MCP Architecture Rules (v7.0 - CRITICAL!)

**⚠️ MCP BLEIBT:** This section is MANDATORY reading for all code changes!

### Core MCP Principles

1. **ALL agents are MCP servers** - No direct instantiation!
   ```python
   # ❌ WRONG (old way)
   agent = ResearchAgent(workspace_path)
   result = await agent.execute(state)

   # ✅ CORRECT (MCP way)
   mcp = get_mcp_manager(workspace_path)
   result = await mcp.call("research_agent", "research", {...})
   ```

2. **MCPManager is singleton** - Use `get_mcp_manager()`
   ```python
   from backend.utils.mcp_manager import get_mcp_manager
   mcp = get_mcp_manager(workspace_path=workspace_path)
   ```

3. **MCP servers run from project root** - NOT workspace!
   - Servers start with `cwd=project_root`
   - Workspace path passed as tool argument
   - Allows testing with non-existent workspaces

4. **Progress notifications via $/progress** - Enable real-time updates
   ```python
   def progress_callback(server: str, message: str, progress: float):
       event_manager.send_event(session_id, {
           "type": "mcp_progress",
           "server": server,
           "message": message,
           "progress": progress
       })
   ```

5. **NO AI Factory** - Each MCP server manages its own AI provider
   - OpenAI via `openai_server.py`
   - Claude via existing Claude CLI MCP wrapper
   - Perplexity via `perplexity_server.py`

### MCP Server Registry (11 servers)

**Agent Servers:**
- `openai` - OpenAI GPT-4o wrapper
- `research_agent` - Research capabilities
- `architect_agent` - Architecture design (uses OpenAI)
- `codesmith_agent` - Code generation (uses Claude CLI)
- `reviewfix_agent` - Code review/fixes (uses Claude CLI)
- `responder_agent` - Response formatting (no AI)

**Utility Servers:**
- `perplexity` - Web search
- `memory` - Memory system
- `build_validation` - Build validation
- `file_tools` - File operations
- `tree_sitter` - Code parsing

### When Modifying MCP Code

**NEVER:**
- ❌ Remove "⚠️ MCP BLEIBT" comments
- ❌ Create direct agent instances
- ❌ Add AI Factory references
- ❌ Import old agent classes

**ALWAYS:**
- ✅ Use `mcp.call(server, tool, arguments)`
- ✅ Add "⚠️ MCP BLEIBT" comments to new code
- ✅ Forward $/progress notifications
- ✅ Run servers from project root

**Full Details:** See `/MCP_MIGRATION_FINAL_SUMMARY.md`

---

## 🔧 Code Refactoring Protocol

When removing code:
1. **Mark as OBSOLETE first** (NEVER delete directly!)
2. **Test thoroughly** (validate functionality)
3. **Only then remove** (after successful tests)

**Why:** Safe, trackable, revertable, team-friendly

---

## 🚨 Architecture Rules (MUST FOLLOW!)

**Backend ↔ Frontend Separation:**
1. **Backend** → Python (`$HOME/.ki_autoagent/backend/`)
2. **UI** → TypeScript (`vscode-extension/`)
3. **AI Calls** → ONLY Python Backend
4. **Communication** → ONLY WebSocket (ws://localhost:8002)
5. **Workspace Analysis** → ONLY `session["workspace_path"]`
6. **NO Spawning** → VS Code Extension NEVER starts backend!

**Violation = Duplikat und Chaos!**

---

## 📚 Quick Reference Links

### Core Documentation:
- Critical Failure Instructions: `/CRITICAL_FAILURE_INSTRUCTIONS.md` ⚠️
- Claude CLI Integration: `/CLAUDE_CLI_INTEGRATION.md`
- Build Validation: `/BUILD_VALIDATION_GUIDE.md`
- E2E Testing: `/E2E_TESTING_GUIDE.md`
- Python Best Practices: `/PYTHON_BEST_PRACTICES.md`
- Claude Best Practices: `/CLAUDE_BEST_PRACTICES.md`

### MCP Architecture (v7.0 - CURRENT):
- **MCP Migration Summary:** `/MCP_MIGRATION_FINAL_SUMMARY.md` ⚠️ **READ THIS!**
- **MCP Implementation Plan:** `/PURE_MCP_IMPLEMENTATION_PLAN.md`
- **MCP Testing Plan:** `/MCP_TESTING_PLAN.md`
- **Step 1-7 Completion:** `/MCP_MIGRATION_STEP[1-7]_COMPLETE.md`
- **Old Code Deletion:** `/OLD_CODE_DELETION_SUMMARY.md`

### Archived Architecture (v6.x - OBSOLETE):
- Old v6.6 Architecture: `/ARCHITECTURE_CURRENT_v6.6.md` (superseded)
- Old v7.0 Supervisor Plan: `/ARCHITECTURE_TARGET_v7.0.md` (superseded)
- Old Migration Guide: `/MIGRATION_GUIDE_v7.0.md` (superseded)
- Old Briefing: `/SONNET_BRIEFING_v7.0.md` (superseded)

### Official Claude Docs:
- **Claude 4 Best Practices:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
- **Prompt Caching:** https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- **Streaming:** https://docs.claude.com/en/docs/build-with-claude/streaming

---

## ⚠️ Before ANY Code Changes

**Checklist:**
- [ ] Read `/CRITICAL_FAILURE_INSTRUCTIONS.md`
- [ ] Understand error handling rules (ANY error = system failure)
- [ ] Check if tests exist for the area you're modifying
- [ ] Verify workspace isolation (E2E tests in ~/TestApps/)
- [ ] Follow Python best practices (see `/PYTHON_BEST_PRACTICES.md`)
- [ ] Set `cwd=workspace_path` in subprocess calls
- [ ] Never use optimistic language for test failures

---

## 🎯 Success Criteria

**System is production-ready ONLY IF:**
- ✅ ALL E2E tests pass completely
- ✅ 100% of planned features validated
- ✅ NO errors, timeouts, or disconnections
- ✅ All assertions passed
- ✅ Test suite completed successfully

**System is NOT production-ready IF:**
- ❌ ANY test failed
- ❌ Test disconnected/timed out
- ❌ <100% test pass rate
- ❌ Features not validated (even if code exists)
- ❌ Any KeyError, database error, or routing error

---

**This document is MUCH shorter now (161 lines vs 1,298 lines previously)!**

**All detailed content has been extracted to specialized guides.**

**For detailed information, see the referenced files above.**
