# Claude Code Instructions - Core Guidelines

**Version:** v7.0.0-alpha (MIGRATION IN PROGRESS)
**Last Updated:** 2025-10-20

---

## 🚨 WICHTIG: v7.0 Migration zu Supervisor Pattern läuft!

**Neue Architektur-Dokumente:**
- **Current Architecture:** `/ARCHITECTURE_CURRENT_v6.6.md` - Was wir haben
- **Target Architecture:** `/ARCHITECTURE_TARGET_v7.0.md` - Wohin wir wollen ⚠️ **READ THIS!**
- **Migration Guide:** `/MIGRATION_GUIDE_v7.0.md` - Wie wir migrieren
- **Quick Briefing:** `/SONNET_BRIEFING_v7.0.md` - Schnellübersicht

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

### Multi-Client Backend Architecture

```
$HOME/.ki_autoagent/              # Global Agent Service
├── backend/                      # Python Backend
├── config/instructions/          # Agent Base Instructions
└── data/embeddings/              # Agent Memories

$WORKSPACE/.ki_autoagent_ws/      # Workspace-Specific Data
├── instructions/                 # Project-specific instructions
├── cache/                        # Workspace cache
└── memory/                       # Workspace memories
```

### Key Principles:
1. **Backend is GLOBAL** - Runs once, serves all workspaces
2. **Multi-Client** - WebSocket protocol (ws://localhost:8002/ws/chat)
3. **Workspace Isolation** - Each client sends workspace_path on connect
4. **NO Spawning** - VS Code extension NEVER starts backend

**Full Details:** See `/ARCHITECTURE_v6.2_CURRENT.md`

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

## 🔍 Research Agent Modes (v6.2+)

**Three execution modes:**
1. **`research`** - Web search with Perplexity (CREATE workflows)
2. **`explain`** - Analyze existing codebase (EXPLAIN workflows)
3. **`analyze`** - Code quality/security analysis (ANALYZE workflows)

**AI-Based Planning:** GPT-4o-mini determines mode dynamically

**Breaking Change:** ResearchState now requires `mode` field

**Full Details:** See `/ARCHITECTURE_v6.2_CURRENT.md` section "Research Agent Modes System"

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

### Documentation:
- Critical Failure Instructions: `/CRITICAL_FAILURE_INSTRUCTIONS.md` ⚠️
- Claude CLI Integration: `/CLAUDE_CLI_INTEGRATION.md`
- Build Validation: `/BUILD_VALIDATION_GUIDE.md`
- E2E Testing: `/E2E_TESTING_GUIDE.md`
- Python Best Practices: `/PYTHON_BEST_PRACTICES.md`
- Claude Best Practices: `/CLAUDE_BEST_PRACTICES.md`
- Current Architecture: `/ARCHITECTURE_CURRENT_v6.6.md`
- Target Architecture: `/ARCHITECTURE_TARGET_v7.0.md`

### Migration Documents:
- Migration Guide: `/MIGRATION_GUIDE_v7.0.md`
- Quick Briefing: `/SONNET_BRIEFING_v7.0.md`

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
