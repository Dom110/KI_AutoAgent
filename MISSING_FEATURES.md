# Missing Features in v6.0

**Date:** 2025-10-09
**Current Status:** v6.0-alpha-production-ready
**Based On:** V6_COMPLETE_AUDIT.md

---

## ✅ ALREADY IMPLEMENTED (Iterations 0-2)

1. **End-to-End Workflow** - Research → Architect → Codesmith → ReviewFix
2. **Memory System** - FAISS + SQLite (WORKING! Agents use it)
3. **Tree-sitter Validation** - Syntax checking (Python/JS/TS)
4. **Asimov Security** - Rules 1 & 2 (no fallbacks, complete implementation)
5. **File Tools** - write_file, read_file, edit_file
6. **Multi-Client Server** - WebSocket protocol
7. **Claude CLI 100%** - All agents use it
8. **Performance Optimizations** - uvloop, orjson

---

## ❌ MISSING FROM v5 (9 Systems)

### 🔴 CRITICAL Priority

#### 1. **Perplexity API Integration**
**Current:** Placeholder that returns error
**Needed:** Real Perplexity Sonar API implementation
**Impact:** Research agent can't do web searches
**Effort:** 3-4 hours
**Files:** `backend/tools/perplexity_tool.py`

**Implementation:**
```python
# Add real API call
import httpx

async def perplexity_search(query: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
            json={
                "model": "sonar-small-online",
                "messages": [{"role": "user", "content": query}]
            }
        )
        return response.json()
```

**Test:** Research agent should find actual web results

---

#### 2. **Asimov Rule 3: Global Error Search**
**Current:** Not automated
**Needed:** Automatic project-wide error search when bug found
**Impact:** Ensures ALL instances of error are fixed
**Effort:** 4-5 hours
**Files:** New `backend/security/global_error_search.py`

**Implementation:**
```python
async def perform_global_search(
    error_pattern: str,
    workspace_path: str,
    file_types: list[str]
) -> list[dict]:
    """
    Search entire workspace for error pattern
    Returns all occurrences with file + line number
    """
    # Use ripgrep or grep
    # Return all matches
    # Block until ALL fixed
```

**Integration:** ReviewFix agent automatically triggers this

---

### 🟡 HIGH Priority

#### 3. **Learning System** (Pattern Recognition)
**Current:** Not implemented
**Needed:** Store successful patterns, reuse in similar tasks
**Impact:** Faster code generation, better quality over time
**Effort:** 6-8 hours
**Files:** New `backend/learning/learning_system_v6.py`

**Features:**
- Store successful code patterns in vector DB
- Search for similar patterns when generating new code
- Track pattern effectiveness (quality scores)
- Auto-suggest patterns to Codesmith

**Data Structure:**
```python
{
    "pattern_id": "uuid",
    "code_snippet": "...",
    "description": "React component with hooks",
    "used_count": 15,
    "avg_quality": 0.92,
    "tags": ["react", "typescript", "hooks"]
}
```

---

#### 4. **Curiosity System**
**Current:** Not implemented
**Needed:** Agent asks clarifying questions when requirements unclear
**Impact:** Better understanding → better code
**Effort:** 4-5 hours
**Files:** New `backend/agents/curiosity_agent.py`

**Triggers:**
- Ambiguous requirements
- Missing technical details
- Unclear architecture choices

**Example:**
```
User: "Create a web app"
Curiosity: "Which framework? React, Vue, or vanilla JS?"
User: "React"
Curiosity: "TypeScript or JavaScript?"
```

---

#### 5. **Predictive System**
**Current:** Not implemented
**Needed:** Predict likely issues before they occur
**Impact:** Proactive error prevention
**Effort:** 5-6 hours
**Files:** New `backend/prediction/predictive_system.py`

**Features:**
- Analyze architecture for potential issues
- Predict performance bottlenecks
- Suggest optimizations
- Warn about common pitfalls

**Example:**
```
Architect creates design with 10+ REST endpoints
Predictive: "⚠️ Consider API Gateway pattern for scalability"
```

---

### 🟢 MEDIUM Priority

#### 6. **Tool Registry** (Dynamic Tool Loading)
**Current:** Tools hardcoded in agents
**Needed:** Dynamic tool discovery and registration
**Impact:** Easier to add new tools
**Effort:** 3-4 hours
**Files:** New `backend/tools/tool_registry.py`

**Features:**
```python
registry = ToolRegistry()

# Auto-discover tools
registry.discover_tools("backend/tools/")

# Get tools for agent
tools = registry.get_tools_for_agent("codesmith")

# Register custom tool
registry.register(MyCustomTool())
```

---

#### 7. **Approval Manager** (User Confirmation)
**Current:** Agents execute without asking
**Needed:** Ask user before destructive operations
**Impact:** Safety, user control
**Effort:** 3-4 hours
**Files:** New `backend/approval/approval_manager.py`

**Triggers:**
- Delete files
- Modify existing files
- Install dependencies
- Run shell commands

**Flow:**
```
Codesmith: "About to modify 5 existing files. Approve? (y/n)"
User: "y"
Codesmith: *proceeds*
```

---

#### 8. **Dynamic Workflow** (Intelligent Routing)
**Current:** Fixed: Research → Architect → Codesmith → ReviewFix
**Needed:** Smart routing based on task type
**Impact:** Faster for simple tasks
**Effort:** 4-5 hours
**Files:** Modify `backend/workflow_v6.py`

**Examples:**
```
Task: "Fix bug in calculator.py"
Route: Codesmith → ReviewFix (skip Research + Architect)

Task: "Research best React patterns"
Route: Research only (skip others)

Task: "Design database schema"
Route: Research → Architect only
```

---

### 🔵 LOW Priority (Nice to Have)

#### 9. **Neurosymbolic Reasoning**
**Current:** Not implemented
**Needed:** Combine LLM reasoning with formal logic
**Impact:** Better logical consistency
**Effort:** 6-8 hours
**Files:** New `backend/reasoning/neurosymbolic.py`

---

#### 10. **Query Classifier**
**Current:** All queries go to full workflow
**Needed:** Classify query type to optimize routing
**Impact:** Performance optimization
**Effort:** 2-3 hours
**Files:** New `backend/classification/query_classifier.py`

**Types:**
- Code generation
- Bug fix
- Research
- Architecture design
- Code review

---

#### 11. **Self-Diagnosis System**
**Current:** No self-monitoring
**Needed:** Agent detects own failures and self-corrects
**Impact:** Better reliability
**Effort:** 4-5 hours
**Files:** New `backend/diagnosis/self_diagnosis.py`

**Features:**
- Monitor agent performance
- Detect degraded quality
- Auto-adjust parameters
- Fallback strategies (documented per Asimov Rule 1!)

---

## 📊 EFFORT SUMMARY

| Priority | Features | Total Effort |
|----------|----------|--------------|
| 🔴 CRITICAL | 2 | 7-9 hours |
| 🟡 HIGH | 3 | 15-19 hours |
| 🟢 MEDIUM | 3 | 10-13 hours |
| 🔵 LOW | 3 | 12-16 hours |
| **TOTAL** | **11** | **44-57 hours** |

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Production Essentials (8-10 hours)
1. Perplexity API Integration (3-4h)
2. Asimov Rule 3 - Global Error Search (4-5h)
3. Test with real projects

### Phase 2: Intelligence Layer (15-20 hours)
4. Learning System (6-8h)
5. Curiosity System (4-5h)
6. Predictive System (5-6h)
7. Test with complex projects

### Phase 3: Advanced Features (10-15 hours)
8. Tool Registry (3-4h)
9. Approval Manager (3-4h)
10. Dynamic Workflow (4-5h)
11. Test with diverse workloads

### Phase 4: Optimization (12-16 hours)
12. Neurosymbolic Reasoning (6-8h)
13. Query Classifier (2-3h)
14. Self-Diagnosis (4-5h)
15. Final testing + optimization

---

## 🚀 CURRENT v6 STATUS

**Production Ready:** ✅ YES
**Feature Complete:** ⚠️ 40% (core working, advanced features missing)
**Recommended:** Implement Phase 1 (Perplexity + Global Search) before production use

**Can Use Now For:**
- ✅ Single-file Python projects
- ✅ Simple CRUD apps
- ✅ Calculator/utility scripts
- ✅ Learning/testing

**Should Add Features For:**
- ⚠️ Complex multi-file projects → Learning System
- ⚠️ Production apps → Curiosity + Predictive
- ⚠️ Team collaboration → Approval Manager
- ⚠️ Large codebases → Dynamic Workflow

---

**Last Updated:** 2025-10-09
**Next Review:** After Phase 1 completion
