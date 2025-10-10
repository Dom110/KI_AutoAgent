# KI AutoAgent - Complete Project Roadmap 2025

**Last Updated:** 2025-10-10
**Current Version:** v6.1-alpha
**Target:** v7.0 with full MCP & Plugin Integration

---

## 📊 PROJECT STATUS OVERVIEW

| Component | Status | Version | Priority |
|-----------|--------|---------|----------|
| Backend v6.1 | ✅ Working | 6.1.0 | DONE |
| HITL Integration | ✅ Implemented | 6.1.0 | DONE |
| Research Agent | ✅ Tested | 6.1.0 | DONE |
| Codesmith Agent | ✅ Tested | 6.1.0 | DONE |
| ReviewFix Agent | ✅ Tested | 6.1.0 | DONE |
| Architect Agent | ⚠️ Not tested | 6.0.0 | HIGH |
| E2E Workflow | ⏸️ Slow (>320s) | 6.0.0 | HIGH |
| VS Code Extension | 🔴 Needs v6 update | 5.x | HIGH |
| MCP Servers | ⏳ Not started | - | MEDIUM |
| Plugin System | ⏳ Research phase | - | LOW |

---

## 🎯 MASTER TODO LIST - PRIORITIZED

### ═══════════════════════════════════════════════════════════════
### PHASE 1: STABILIZE v6.1 CORE (Current - 1-2 Weeks)
### ═══════════════════════════════════════════════════════════════

#### A. Backend Cleanup & Validation (HIGH PRIORITY)

- [x] ✅ Research subgraph working (~20-25s)
- [x] ✅ Codesmith subgraph working (~25-30s)
- [x] ✅ ReviewFix subgraph working (~15-20s)
- [x] ✅ HITL debug info implemented (ClaudeCLISimple)
- [ ] 🔥 **Test Architect subgraph** (update to v6.1 pattern if needed)
- [ ] 🔥 **Profile E2E workflow** (find why >320s)
  - Option A: Parallel initialization of v6 systems
  - Option B: Optimize sequential flow
  - Option C: Cache expensive operations
- [ ] 🔥 **Delete obsolete v6.0 files**
  - research_subgraph_v6.py
  - codesmith_subgraph_v6.py
  - reviewfix_subgraph_v6.py
  - Keep backups for reference
- [ ] 📝 **Update CHANGELOG.md** with v6.1 changes

---

#### B. HITL Frontend Integration (HIGH PRIORITY)

- [ ] 🔥 **Test HITL callbacks with WebSocket mock**
  - Create test_hitl_websocket.py
  - Verify all debug info transmitted
  - Test error scenarios
- [ ] 🔥 **Update all subgraphs with hitl_callback**
  - ✅ Research: Already has placeholder
  - ✅ Codesmith: Already has placeholder
  - ✅ ReviewFix: Already has placeholder
  - [ ] Architect: Add hitl_callback parameter
  - [ ] workflow_v6_integrated.py: Pass WebSocket callback
- [ ] 🔥 **VS Code Extension - BackendClient updates**
  - [ ] Handle new message types:
    - `hitl_debug` (debug info from agents)
    - `claude_cli_start` (before execution)
    - `claude_cli_complete` (after execution)
    - `claude_cli_error` (on error)
  - [ ] Create DebugInfoPanel component
  - [ ] Show CLI command in UI
  - [ ] Show prompts (system + user)
  - [ ] Show raw output + parsed events
  - [ ] Show duration + timing info
- [ ] 📝 **Documentation: HITL Integration Guide**

---

#### C. VS Code Extension v6 Update (HIGH PRIORITY)

**Current Issues (from EXTENSION_ANALYSIS.md):**
- MultiAgentChatPanel.ts (2478 lines) - Mostly v5 code
- BackendManager.ts - Should be DELETED (no auto-start in v6)
- Model Settings - Discovery endpoint missing

**Required Updates:**

- [ ] 🔥 **DELETE BackendManager.ts** completely
  - Remove auto-start logic
  - Remove spawn backend code
  - Update extension.ts to remove BackendManager import
- [ ] 🔥 **Update MultiAgentChatPanel.ts** for v6
  - Remove v5-only UI (pause/resume/rollback buttons)
  - Add HITL mode indicator (INTERACTIVE/AUTONOMOUS/DEBUG)
  - Add debug info panel (CLI commands + outputs)
  - Update message handlers for v6 types
  - Simplify agent selection (orchestrator only in v6)
- [ ] 🔥 **Fix or Remove Model Settings**
  - Option A: Remove model discovery (not needed in v6)
  - Option B: Update for v6.1 backend API
- [ ] 📝 **Update extension README** with v6 instructions
- [ ] 🧪 **Test extension with v6 backend**
  - Manual connection to ws://localhost:8002
  - Test all v6 message types
  - Test HITL debug info display

---

### ═══════════════════════════════════════════════════════════════
### PHASE 2: MCP SERVER DEVELOPMENT (2-4 Weeks)
### ═══════════════════════════════════════════════════════════════

#### A. MCP Protocol Research (1 Week)

- [ ] 📚 **Study MCP Specification**
  - Read: https://spec.modelcontextprotocol.io/
  - Understand JSON-RPC protocol
  - Study stdio vs SSE modes
  - Learn tool schema format
- [ ] 🔬 **Create minimal MCP server prototype**
  - Simple "hello world" tool
  - Register with Claude CLI: `claude mcp add hello ...`
  - Test: `claude "say hello"`
  - Debug: Check stdin/stdout communication
- [ ] 🔬 **Explore existing MCP servers**
  - Clone: https://github.com/anthropics/mcp-servers
  - Study implementations
  - Identify best practices
- [ ] 📝 **Document findings** in MCP_LEARNINGS.md

---

#### B. Perplexity MCP Server (1 Week)

- [ ] 💻 **Implement perplexity_server.py**
  - Use existing `utils/perplexity_service.py`
  - Expose `perplexity_search` tool
  - Parameters: query, max_results
  - Return: content, sources, metadata
- [ ] 🧪 **Test with Claude CLI**
  ```bash
  claude mcp add perplexity python mcp_servers/perplexity_server.py
  claude "Research Python async patterns using perplexity"
  ```
- [ ] 📝 **Write usage documentation**
- [ ] 🎁 **Package for distribution**
  - Create pyproject.toml
  - Entry point script
  - Installation instructions

---

#### C. Tree-sitter MCP Server (1 Week)

- [ ] 💻 **Implement tree_sitter_server.py**
  - Use existing `tools/tree_sitter_tools.py`
  - Expose tools:
    - `validate_syntax(code, language)` → bool
    - `parse_code(code, language)` → AST
    - `get_syntax_errors(code, language)` → errors[]
- [ ] 🧪 **Test with multiple languages**
  - Python, JavaScript, TypeScript, Go, Rust
  - Test syntax validation
  - Test AST parsing
- [ ] 📝 **Documentation + Examples**

---

#### D. Memory MCP Server (1 Week)

- [ ] 💻 **Implement memory_server.py**
  - Use existing `memory/memory_system_v6.py`
  - Expose tools:
    - `memory_store(content, metadata)` → success
    - `memory_search(query, k)` → results[]
    - `memory_get(id)` → content
- [ ] 🧪 **Test with workflows**
  - Store research findings
  - Search across sessions
  - Retrieve by ID
- [ ] 📝 **Documentation**

---

#### E. Combined MCP Server Package (1 Week)

- [ ] 📦 **Create ki-autoagent-mcp package**
  - Bundle all MCP servers
  - Single installation command
  - Configuration file support
- [ ] 📝 **Complete documentation**
  - Installation guide
  - Usage examples
  - API reference
- [ ] 🚀 **Publish to PyPI**
  ```bash
  pip install ki-autoagent-mcp
  claude mcp add-from-package ki-autoagent-mcp
  ```

---

### ═══════════════════════════════════════════════════════════════
### PHASE 3: PLUGIN DEVELOPMENT (4-8 Weeks)
### ═══════════════════════════════════════════════════════════════

#### A. Plugin API Research (1-2 Weeks)

- [ ] 📚 **Get official plugin documentation**
  - Contact Claude Code team
  - Request API reference
  - Join developer community
- [ ] 🔬 **Reverse-engineer plugin structure**
  - Install example plugin
  - Inspect plugin directory
  - Study manifest format
- [ ] 📝 **Document plugin architecture**

---

#### B. Agent Registration Plugin (2 Weeks)

- [ ] 💻 **Create agent registration manifest**
  ```json
  {
    "agents": {
      "ki-research": {...},
      "ki-architect": {...},
      "ki-codesmith": {...},
      "ki-reviewfix": {...}
    }
  }
  ```
- [ ] 🧪 **Test agent registration**
  ```bash
  claude --agent ki-research "Python async patterns"
  claude --agent ki-codesmith design.md
  ```
- [ ] 📝 **Documentation**

---

#### C. Custom Commands Plugin (2 Weeks)

- [ ] 💻 **Implement commands**
  - `/autoagent start` - Start backend
  - `/autoagent task "..."` - Execute task
  - `/autoagent status` - Show status
  - `/autoagent pause/resume` - HITL control
- [ ] 🧪 **Test command execution**
- [ ] 📝 **Documentation**

---

#### D. Hooks Plugin (2 Weeks)

- [ ] 💻 **Implement hooks**
  - `on_file_write` → Asimov Rule validation
  - `on_code_generate` → Tree-sitter validation
  - `on_agent_start` → HITL mode detection
  - `on_agent_complete` → Memory storage
- [ ] 🧪 **Test hook integration**
- [ ] 📝 **Documentation**

---

#### E. Full Plugin Package (2 Weeks)

- [ ] 📦 **Bundle everything**
  - Agents + Commands + Hooks + MCP
  - Single plugin: `ki-autoagent`
- [ ] 🧪 **End-to-end testing**
- [ ] 📝 **Complete documentation**
- [ ] 🚀 **Submit to Claude Code Marketplace**

---

### ═══════════════════════════════════════════════════════════════
### PHASE 4: TESTING & OPTIMIZATION (2-4 Weeks)
### ═══════════════════════════════════════════════════════════════

#### A. Performance Optimization

- [ ] 🔬 **Profile E2E workflow**
  - Identify bottlenecks
  - Measure each component
  - Create performance dashboard
- [ ] ⚡ **Optimize slow components**
  - Parallel v6 system initialization
  - Cache expensive operations
  - Optimize Memory searches
- [ ] 🎯 **Target: <60s for full workflow**

---

#### B. Comprehensive Testing

- [ ] 🧪 **Unit tests for all components**
  - MCP servers (mocked)
  - HITL manager
  - All agents (v6.1)
- [ ] 🧪 **Integration tests**
  - Research → Architect → Codesmith → ReviewFix
  - HITL callbacks
  - Memory persistence
- [ ] 🧪 **E2E tests**
  - Complete workflows
  - Error recovery
  - Edge cases
- [ ] 📊 **Coverage report** (target: >80%)

---

#### C. Documentation Complete

- [ ] 📝 **User Guide** (complete)
  - Installation
  - Quick start
  - Advanced usage
  - Troubleshooting
- [ ] 📝 **Developer Guide**
  - Architecture overview
  - Contributing guide
  - MCP server development
  - Plugin development
- [ ] 📝 **API Reference**
  - All public APIs documented
  - Examples for each API
- [ ] 🎥 **Video Tutorials**
  - Getting started (5 min)
  - Building your first agent (15 min)
  - MCP server development (20 min)

---

### ═══════════════════════════════════════════════════════════════
### PHASE 5: v7.0 RELEASE (1-2 Weeks)
### ═══════════════════════════════════════════════════════════════

#### A. Release Preparation

- [ ] 📝 **CHANGELOG.md** (complete)
- [ ] 📝 **MIGRATION_GUIDE.md** (v6.0 → v6.1 → v7.0)
- [ ] 🏷️ **Version bumps** (all packages)
- [ ] 🧪 **Final testing** (all platforms)

---

#### B. Release Artifacts

- [ ] 📦 **PyPI packages**
  - ki-autoagent-backend
  - ki-autoagent-mcp
- [ ] 📦 **npm packages**
  - ki-autoagent-vscode
  - ki-autoagent-plugin
- [ ] 📦 **Claude Code Marketplace**
  - Plugin submission
  - MCP server listing

---

#### C. Announcement & Marketing

- [ ] 📢 **Blog post** (launch announcement)
- [ ] 📢 **GitHub Release** (v7.0.0)
- [ ] 📢 **Community forums**
  - Claude Code forum
  - Reddit r/ClaudeAI
  - Twitter/X announcement
- [ ] 📢 **Documentation site** (live)

---

## 📅 TIMELINE ESTIMATES

```
PHASE 1: v6.1 Stabilization        [Weeks 1-2]  ████████░░░░░░░░░░
PHASE 2: MCP Server Development    [Weeks 3-6]  ░░░░░░░░██████████
PHASE 3: Plugin Development        [Weeks 7-14] ░░░░░░░░░░░░░░░░░░██████████████
PHASE 4: Testing & Optimization    [Weeks 11-14]░░░░░░░░░░░░░░░░████████
PHASE 5: v7.0 Release              [Week 15]    ░░░░░░░░░░░░░░░░░░░░░░░░██

Total: ~15 weeks (3.5 months)
```

---

## 🎯 MILESTONES

### Milestone 1: v6.1 Stable (Week 2)
- ✅ All agents tested and working
- ✅ HITL integration complete
- ✅ VS Code extension updated
- ✅ E2E workflow <60s
- 📦 Release: v6.1.0

### Milestone 2: MCP Servers Live (Week 6)
- ✅ Perplexity MCP server working
- ✅ Tree-sitter MCP server working
- ✅ Memory MCP server working
- ✅ Published to PyPI
- 📦 Release: v6.2.0-mcp

### Milestone 3: Plugin Beta (Week 10)
- ✅ Agents registered in Claude Code
- ✅ Custom commands working
- ✅ Hooks functional
- 📦 Release: v6.9.0-beta

### Milestone 4: v7.0 GA (Week 15)
- ✅ Full plugin in marketplace
- ✅ Complete documentation
- ✅ Video tutorials
- ✅ Community support ready
- 📦 Release: v7.0.0

---

## 🔄 ITERATION CYCLES

### Weekly Sprints:
```
Monday:    Sprint Planning
Tue-Thu:   Development
Friday:    Testing & Review
Weekend:   Documentation
```

### Bi-weekly Reviews:
- Demo new features
- Gather feedback
- Adjust priorities
- Update roadmap

---

## 🚨 RISK MITIGATION

### High Risk Items:

1. **Plugin API Unavailable**
   - **Risk:** Official docs not ready
   - **Mitigation:** Focus on MCP servers first (standard protocol)
   - **Fallback:** Continue with v6.1 + MCP

2. **E2E Performance**
   - **Risk:** Can't get <60s
   - **Mitigation:** Early profiling, parallel execution
   - **Fallback:** Document known limitation

3. **VS Code Extension Complexity**
   - **Risk:** Major refactor needed
   - **Mitigation:** Gradual updates, keep v5 working
   - **Fallback:** Release backend-only first

---

## 📊 SUCCESS METRICS

### Technical Metrics:
- [ ] All agents <30s execution time
- [ ] E2E workflow <60s
- [ ] Test coverage >80%
- [ ] Zero critical bugs
- [ ] MCP servers <100ms latency

### Adoption Metrics:
- [ ] 100+ PyPI downloads (first month)
- [ ] 50+ plugin installations (first month)
- [ ] 10+ community contributions
- [ ] 5-star average rating

---

## 🎯 CURRENT SPRINT (Week 1-2)

### This Week Focus:

#### Monday-Tuesday:
- [x] ✅ HITL debug info implementation
- [x] ✅ MCP server research & documentation
- [x] ✅ Project roadmap creation
- [ ] Test Architect subgraph
- [ ] Profile E2E workflow

#### Wednesday-Thursday:
- [ ] Delete v6.0 files
- [ ] Update all subgraphs with hitl_callback
- [ ] Create HITL WebSocket test
- [ ] Start VS Code extension cleanup

#### Friday:
- [ ] Testing & review
- [ ] Documentation updates
- [ ] Sprint retrospective

---

## 📝 DECISION LOG

### 2025-10-10: v6.1 vs v6.0
- **Decision:** Keep v6.1 (direct ainvoke), delete v6.0
- **Reason:** Better async, HITL, performance
- **Impact:** Simplified codebase, easier maintenance

### 2025-10-10: MCP First, Plugin Later
- **Decision:** Focus on MCP servers before full plugin
- **Reason:** MCP is standard protocol, plugin API unclear
- **Impact:** Faster time to value, less risk

### 2025-10-10: HITL Priority
- **Decision:** HITL debug info in Phase 1
- **Reason:** User requested, critical for UX
- **Impact:** Better debugging, transparency

---

## 📚 REFERENCES

**Documentation:**
- [HITL_WORKFLOW_RULES.md](./HITL_WORKFLOW_RULES.md) - HITL patterns
- [MCP_SERVER_GUIDE.md](./MCP_SERVER_GUIDE.md) - MCP implementation
- [CLAUDE_CODE_PLUGIN_ANALYSIS.md](./CLAUDE_CODE_PLUGIN_ANALYSIS.md) - Plugin system
- [REACT_AGENT_ANALYSIS.md](./REACT_AGENT_ANALYSIS.md) - v6 vs v6.1

**Test Results:**
- [TEST_RESULTS_2025-10-10.md](./TEST_RESULTS_2025-10-10.md) - Subgraph tests
- [CLAUDE_BEST_PRACTICES.md](./CLAUDE_BEST_PRACTICES.md) - CLI optimization

---

**Last Updated:** 2025-10-10 18:00 UTC
**Next Review:** 2025-10-17 (weekly)
**Owner:** KI AutoAgent Team
