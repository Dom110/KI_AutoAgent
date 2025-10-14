# MCP MIGRATION PLAN - Detaillierte Roadmap zu Pure MCP v6.2

**Erstellt:** 2025-10-14
**Autor:** Claude Opus 4.1
**Branch:** v6.2-alpha-release
**Ziel:** Komplette Migration zu Pure MCP Architecture (NO fallbacks, NO legacy code)

---

## 🎯 Executive Summary

### Aktueller Stand (v6.2-alpha-release):
- **Hybrid-Architektur:** Teilweise MCP, teilweise direkte Imports
- **7 MCP Servers** existieren (Memory, Claude, Perplexity, etc.)
- **FEHLEN:** build_validation_server.py + file_tools_server.py
- **Problem:** 450+ Zeilen subprocess.run() Code in reviewfix_subgraph
- **Problem:** Direkte file_tools imports in 2 Subgraphs

### Ziel-Architektur (Pure MCP):
- **100% MCP-basiert:** KEINE direkten Service-Aufrufe
- **9 MCP Servers:** Alle Features als MCP Services
- **Streaming:** Real-time Output für alle Operations
- **NO Fallbacks:** System crasht bei Fehler (fail loudly!)
- **Parallel Execution:** asyncio.gather() für Performance

---

## 📊 Branch-Vergleich Analyse

### v6.2-alpha-release (CURRENT)
```
✅ Existierende MCP Servers (7):
   - asimov_server.py
   - claude_cli_server.py
   - memory_server.py
   - minimal_hello_server.py
   - perplexity_server.py
   - tree_sitter_server.py
   - workflow_server.py

❌ FEHLENDE MCP Servers:
   - build_validation_server.py (NOT EXISTS)
   - file_tools_server.py (NOT EXISTS)

❌ Probleme in Subgraphs:
   - reviewfix_subgraph: 10x subprocess.run(), file_tools import
   - codesmith_subgraph: file_tools import
   - research_subgraph: SAUBER (bereits MCP)
   - architect_subgraph: SAUBER (bereits MCP)
```

### pure-mcp-v6.2-migration (EXPERIMENTAL)
```
✅ Neue MCP Servers (2):
   - build_validation_server.py (1,303 Zeilen)
   - file_tools_server.py (884 Zeilen)

✅ Konvertierte Subgraphs:
   - reviewfix_subgraph: KOMPLETT MCP (450 Zeilen entfernt!)
   - codesmith_subgraph: NOCH OFFEN
```

---

## 🔧 PHASE 1: MCP Server Creation

### 1.1 build_validation_server.py (PRIORITY: CRITICAL)

**Zweck:** Ersetzt 450+ Zeilen subprocess.run() Code

**Features zu implementieren:**
```python
# MUST HAVE:
- TypeScript: tsc --noEmit (Quality Threshold: 0.90)
- Python: mypy type checking (Quality Threshold: 0.85)
- JavaScript: ESLint (Quality Threshold: 0.75)
- Go: go vet + go build -n (Quality Threshold: 0.85)
- Rust: cargo check + clippy (Quality Threshold: 0.85)
- Java: Maven/Gradle/javac (Quality Threshold: 0.80)

# TECHNICAL REQUIREMENTS:
- Streaming Output (Real-time compiler errors)
- Parallel Execution (asyncio.gather())
- Auto-Detection (Detect languages from files)
- Polyglot Support (Multiple languages in one project)
- DEBUG_MODE Support (Verbose logging when enabled)
```

**MCP Protocol Implementation:**
```python
@server.tool()
async def validate_all(
    workspace_path: str,
    generated_files: list[dict] | None = None,
    parallel: bool = True
) -> AsyncIterator[dict]:
    """
    Auto-detect and validate ALL languages in workspace.

    Yields:
    - {"type": "detection", "languages": [...]}
    - {"type": "stream", "language": "typescript", "line": "..."}
    - {"type": "result", "language": "typescript", "success": bool}
    - {"type": "summary", "total": N, "passed": N, "failed": N}
    """
```

### 1.2 file_tools_server.py (PRIORITY: HIGH)

**Zweck:** Ersetzt direkten Import von tools.file_tools

**Features zu implementieren:**
```python
# MUST HAVE:
- read_file() mit Streaming für große Dateien
- write_file() mit Progress Updates
- edit_file() für In-Place Modifikationen
- delete_file() mit Safety Checks
- list_files() mit Pattern Matching

# SECURITY:
- Workspace-Scoped (NO path traversal!)
- Permission Checks
- File Size Limits
- Encoding Detection
```

**MCP Protocol Implementation:**
```python
@server.tool()
async def stream_read_file(
    file_path: str,
    workspace_path: str,
    chunk_size: int = 8192
) -> AsyncIterator[dict]:
    """
    Read file with streaming support.

    Yields:
    - {"type": "start", "path": "...", "size": N}
    - {"type": "chunk", "content": "..."}
    - {"type": "complete", "lines": N}
    """
```

---

## 🔧 PHASE 2: Subgraph Migration

### 2.1 reviewfix_subgraph_v6_1.py (LINES TO CHANGE: 500+)

**CURRENT Problems:**
```python
# Line 31: Direct Import
from tools.file_tools import read_file, write_file

# Lines 119, 391: Direct file_tools calls
result = await read_file.ainvoke(...)

# Lines 512, 548: Direct write calls
await write_file.ainvoke(...)

# Lines 240-682: 450+ lines subprocess.run() for build validation
result = subprocess.run(['npx', 'tsc', '--noEmit'], ...)
result = subprocess.run(['python3', '-m', 'mypy'], ...)
# ... und so weiter für 6 Sprachen
```

**TARGET Implementation:**
```python
# REMOVE Line 31
# from tools.file_tools import read_file, write_file  # DELETE THIS

# REPLACE all file operations:
# OLD:
result = await read_file.ainvoke({...})

# NEW:
result = await mcp.call(
    server="file_tools",
    tool="read_file",
    arguments={...}
)

# REPLACE 450 lines of build validation with ONE call:
# OLD: Lines 240-682 (ALL subprocess.run calls)
# NEW:
validation_result = await mcp.call(
    server="build_validation",
    tool="validate_all",
    arguments={
        "workspace_path": workspace_path,
        "generated_files": generated_files,
        "parallel": True
    },
    timeout=300.0
)
```

### 2.2 codesmith_subgraph_v6_1.py (LINES TO CHANGE: ~50)

**CURRENT Problems:**
```python
# Line 30: Direct Import
from tools.file_tools import write_file, read_file

# Multiple locations: Direct calls
await write_file.ainvoke(...)
await read_file.ainvoke(...)
```

**TARGET Implementation:**
```python
# Same pattern as reviewfix:
# 1. Remove import
# 2. Replace all calls with mcp.call()
```

### 2.3 research_subgraph_v6_1.py
**STATUS:** ✅ BEREITS SAUBER (7 MCP calls, keine direkten Imports)

### 2.4 architect_subgraph_v6_1.py
**STATUS:** ✅ BEREITS SAUBER (3 MCP calls, keine direkten Imports)

---

## 🔧 PHASE 3: MCP Client Updates

### 3.1 backend/mcp/mcp_client.py

**Add to server list (Line ~75):**
```python
self.servers = servers or [
    "build_validation",  # NEW
    "file_tools",        # NEW
    "perplexity",
    "memory",
    "tree-sitter",
    "asimov",
    "workflow",
    "claude"
]
```

**Add to _server_paths (Line ~96):**
```python
self._server_paths = {
    "build_validation": project_root / "mcp_servers" / "build_validation_server.py",
    "file_tools": project_root / "mcp_servers" / "file_tools_server.py",
    # ... rest
}
```

---

## 🔧 PHASE 4: Legacy Code Removal

### Files to DELETE:
```
backend/tools/file_tools.py         # Replaced by file_tools_server.py
backend/adapters/claude_cli_simple.py  # Replaced by claude_cli_server.py
backend/tools/perplexity_tool.py    # Replaced by perplexity_server.py
```

### Code to REMOVE:
```python
# In ALL subgraphs:
# - Remove ALL try/except fallback logic
# - Remove ALL "if mcp else direct_call" patterns
# - Remove ALL subprocess.run() calls
```

---

## 🔧 PHASE 5: Testing Strategy

### 5.1 Unit Tests for MCP Servers
```python
# test_build_validation_server.py
async def test_typescript_validation():
    result = await validate_typescript(test_project)
    assert result["success"] == True

async def test_parallel_validation():
    # Test all 6 languages in parallel
    results = await validate_all(polyglot_project, parallel=True)
    assert results["summary"]["total"] == 6
```

### 5.2 Integration Tests
```python
# test_mcp_integration.py
async def test_reviewfix_with_mcp():
    # Test complete reviewfix flow with MCP
    state = await reviewfix_subgraph.ainvoke(test_state)
    assert state["quality_score"] >= 0.75
```

### 5.3 E2E Tests
```bash
# Run in ~/TestApps/ (NOT in dev repo!)
python -m pytest backend/tests/test_e2e_complex_app_workflow.py -xvs
```

---

## 📋 Implementation Checklist

### Week 1: Server Creation
- [ ] Create build_validation_server.py (1,300 lines)
  - [ ] TypeScript validation
  - [ ] Python validation
  - [ ] JavaScript validation
  - [ ] Go validation
  - [ ] Rust validation
  - [ ] Java validation
  - [ ] Streaming support
  - [ ] Parallel execution
- [ ] Create file_tools_server.py (900 lines)
  - [ ] read_file with streaming
  - [ ] write_file with progress
  - [ ] edit_file
  - [ ] delete_file
  - [ ] list_files

### Week 2: Subgraph Migration
- [ ] Migrate reviewfix_subgraph_v6_1.py
  - [ ] Remove file_tools import
  - [ ] Replace read_file calls (3x)
  - [ ] Replace write_file calls (2x)
  - [ ] Replace 450 lines of subprocess.run()
- [ ] Migrate codesmith_subgraph_v6_1.py
  - [ ] Remove file_tools import
  - [ ] Replace all file operations

### Week 3: Cleanup & Testing
- [ ] Update mcp_client.py
- [ ] Delete legacy files
- [ ] Remove all fallback code
- [ ] Unit tests for servers
- [ ] Integration tests
- [ ] E2E tests

---

## ⚠️ Critical Migration Rules

### 1. NO Backwards Compatibility
```python
# ❌ WRONG:
try:
    result = await mcp.call(...)
except:
    result = await direct_call(...)  # NO FALLBACKS!

# ✅ RIGHT:
result = await mcp.call(...)  # Crash if fails!
```

### 2. Streaming ALWAYS
```python
# ❌ WRONG:
return {"content": full_output}

# ✅ RIGHT:
async def stream_output():
    yield {"type": "start"}
    for line in output:
        yield {"type": "stream", "line": line}
    yield {"type": "complete"}
```

### 3. Parallel When Possible
```python
# ❌ WRONG:
result1 = await validate_typescript()
result2 = await validate_python()

# ✅ RIGHT:
results = await asyncio.gather(
    validate_typescript(),
    validate_python()
)
```

### 4. DEBUG_MODE Support
```python
# ALWAYS check:
if os.getenv("DEBUG_MODE"):
    logger.debug(f"Detailed info: {data}")
```

---

## 🚀 Expected Results

### Before Migration:
- 997 lines in reviewfix_subgraph
- Sequential build validation (slow)
- Mixed architecture (confusing)
- Hidden failures (try/except everywhere)

### After Migration:
- ~550 lines in reviewfix_subgraph (44% reduction!)
- Parallel validation (6x faster)
- Pure MCP architecture (clean)
- Loud failures (problems visible)
- Real-time streaming (better UX)

---

## 📚 References

- MCP Protocol Spec: https://github.com/anthropics/model-context-protocol
- AsyncIO Best Practices: https://docs.python.org/3/library/asyncio.html
- LangGraph MCP Integration: internal docs

---

## 🔴 STOP! Before You Start:

1. **This is a PLAN, not an implementation guide**
2. **Get approval before coding**
3. **Test in ~/TestApps/, NOT in main repo**
4. **Commit to feature branch first**
5. **NO production deployment without full E2E tests**

---

**END OF MIGRATION PLAN**

Total Estimated Work: 40 hours
Total Lines to Change: ~2,500
Total New Code: ~2,200 lines
Risk Level: HIGH (complete architecture change)
Benefit: HUGE (clean, fast, maintainable)