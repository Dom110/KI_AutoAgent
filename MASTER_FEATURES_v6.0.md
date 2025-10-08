# KI AutoAgent v6.0 - Master Features Documentation

**Version:** 6.0.0-alpha.1
**Status:** In Development
**Architecture:** LangGraph Subgraphs + Best Practices
**Python:** 3.13 only

---

## 🎯 Core Architecture

### **LangGraph Best Practices Implementation**

```python
# v6.0 Architecture Pattern
SupervisorGraph (Orchestrator)
├── ResearchSubgraph (create_react_agent)
├── ArchitectSubgraph (Custom)
├── CodesmithSubgraph (create_react_agent)
└── ReviewFixSubgraph (Loop)
    ├── ReviewerAgent
    └── FixerAgent

# State Management
- AsyncSqliteSaver (persistent checkpointing)
- Workspace-isolated state per session
- Input/Output transformations between subgraphs
```

**Key Principles:**
- ✅ **Declarative routing** (graph edges, not imperative code)
- ✅ **Prebuilt agents** (`create_react_agent()` where possible)
- ✅ **Subgraphs** for complex workflows
- ✅ **Persistent state** (AsyncSqliteSaver)
- ✅ **State isolation** (separate state per subgraph)

---

## 🤖 Agent System

### **1. Supervisor Agent (Orchestrator)**
**Role:** Workflow coordination, task decomposition
**Model:** GPT-4o (fast reasoning)
**State Management:** SupervisorState (TypedDict)

**Capabilities:**
- Task decomposition
- Agent routing (declarative edges)
- Workflow planning
- Error handling & recovery

**Tools:** None (routing only)

### **2. Research Agent**
**Role:** Web research, documentation gathering
**Model:** Perplexity Sonar Huge 128k
**Implementation:** `create_react_agent()` + Perplexity tools

**Capabilities:**
- Web search (real-time)
- Documentation analysis
- Technology research
- Best practices gathering

**Tools:**
- `perplexity_search(query: str) -> dict`
- `fetch_documentation(url: str) -> str`

**Memory Integration:**
- Stores research results in FAISS
- Tags: "research", "documentation", "technology"
- Cross-session knowledge accumulation

### **3. Architect Agent**
**Role:** System design, architecture planning
**Model:** GPT-4o (architecture reasoning)
**Implementation:** Custom (too specialized for prebuilt)

**Capabilities:**
- Architecture design
- Technology stack selection
- Design pattern recommendations
- Mermaid diagram generation

**Tools:**
- `analyze_codebase(path: str) -> dict` (Tree-Sitter)
- `generate_architecture_diagram() -> str` (Mermaid)
- `suggest_patterns(context: dict) -> list`

**Memory Integration:**
- Reads Research results
- Stores architecture decisions
- Tags: "architecture", "design", "patterns"

**Asimov Integration:**
- Permission: `can_analyze_codebase`
- Validates: No sensitive data exposure

### **4. Codesmith Agent**
**Role:** Code implementation, file operations
**Model:** Claude Sonnet 4.1 (best for coding)
**Implementation:** `create_react_agent()` + file tools

**Capabilities:**
- Code generation (multi-language)
- File creation/editing
- Test generation
- Code refactoring

**Tools:**
- `read_file(path: str) -> str`
- `write_file(path: str, content: str) -> bool`
- `edit_file(path: str, old: str, new: str) -> bool`
- `parse_code(path: str) -> dict` (Tree-Sitter)

**Memory Integration:**
- Reads Architect design
- Reads Research best practices
- Stores implementation decisions
- Tags: "implementation", "code", "files"

**Asimov Integration:**
- Permission: `can_write_files`
- Validates: Workspace boundaries, no overwrites without permission

**Tree-Sitter Integration:**
- Parses own generated code
- Validates syntax before writing
- Extracts functions/classes for documentation

### **5. Reviewer Agent**
**Role:** Code review, quality validation
**Model:** GPT-4o-mini (fast reviews)
**Implementation:** Custom (validation logic)

**Capabilities:**
- Code quality analysis
- Security vulnerability detection
- Best practices validation
- Asimov rule enforcement

**Tools:**
- `analyze_code_quality(code: str) -> dict`
- `check_security(code: str) -> list`
- `validate_asimov_rules(action: dict) -> bool`

**Memory Integration:**
- Reads Codesmith implementation
- Reads Architect design
- Stores review feedback
- Tags: "review", "quality", "security"

**Asimov Integration:**
- **Enforcer Role**: Validates ALL agent actions
- Checks: File permissions, security rules, workspace boundaries
- Can block actions that violate rules

### **6. Fixer Agent**
**Role:** Bug fixing, code correction
**Model:** Claude Sonnet 4.1 (debugging)
**Implementation:** Custom (fix loops)

**Capabilities:**
- Bug analysis & fixing
- Code optimization
- Error correction
- Iterative improvement

**Tools:**
- `read_file(path: str) -> str`
- `edit_file(path: str, old: str, new: str) -> bool`
- `parse_code(path: str) -> dict` (Tree-Sitter)
- `run_tests(path: str) -> dict`

**Memory Integration:**
- Reads Reviewer feedback
- Reads Codesmith implementation
- Stores fix history
- Tags: "fix", "debugging", "optimization"

**Asimov Integration:**
- Permission: `can_write_files`
- Reads Reviewer's Asimov validation results

---

## 🧠 Memory System (Shared Infrastructure)

### **Architecture**
```python
# FAISS Vector Store + SQLite Metadata
class MemorySystem:
    vector_store: FAISS  # Embeddings (OpenAI text-embedding-3)
    metadata_db: SQLite  # Structured data

    def store(self, content: str, metadata: dict):
        """Store with vector + metadata"""

    def search(self, query: str, filters: dict) -> list:
        """Semantic search with filters"""
```

**Storage:**
- Vectors: `$WORKSPACE/.ki_autoagent_ws/memory/vectors.faiss`
- Metadata: `$WORKSPACE/.ki_autoagent_ws/memory/metadata.db`

### **Agent Communication via Memory**

**Example Flow:**
```python
# 1. Research stores findings
memory.store(
    content="Vite + React 18 recommended for 2025",
    metadata={"agent": "research", "type": "technology", "timestamp": "..."}
)

# 2. Architect reads research
research_results = memory.search(
    query="modern frontend frameworks",
    filters={"agent": "research", "type": "technology"}
)

# 3. Architect stores design
memory.store(
    content="Architecture: Vite, React 18, TypeScript, Vitest",
    metadata={"agent": "architect", "type": "design"}
)

# 4. Codesmith reads design
design = memory.search(
    query="architecture design",
    filters={"agent": "architect"}
)

# 5. Codesmith implements
memory.store(
    content="Implemented Calculator.tsx with TypeScript",
    metadata={"agent": "codesmith", "type": "implementation", "file": "Calculator.tsx"}
)

# 6. Reviewer validates
implementation = memory.search(
    query="Calculator implementation",
    filters={"agent": "codesmith", "file": "Calculator.tsx"}
)
```

**Cross-Session Learning:**
- Successful patterns stored permanently
- Failed approaches tagged as "anti-pattern"
- Queries include historical context

---

## 🛡️ Asimov Rules (Security System)

### **Permission Model**
```python
class AsimovRules:
    permissions: dict[str, list[str]] = {
        "research": ["can_web_search", "can_read_docs"],
        "architect": ["can_analyze_codebase", "can_read_files"],
        "codesmith": ["can_write_files", "can_edit_files", "can_create_directories"],
        "reviewer": ["can_read_files", "can_analyze_code", "can_validate_actions"],
        "fixer": ["can_write_files", "can_edit_files"]
    }

    workspace_boundaries: str  # Must be within workspace
    no_overwrite_without_permission: bool = True
    no_delete_without_confirmation: bool = True
```

### **Enforcement Points**

**1. Before Tool Execution**
```python
# Codesmith attempts file write
if not asimov.validate("codesmith", "can_write_files", {"path": "/workspace/file.py"}):
    raise PermissionDenied("Outside workspace boundary")
```

**2. Reviewer Validation**
```python
# Reviewer checks ALL agent actions
review_result = reviewer.validate_action({
    "agent": "codesmith",
    "action": "write_file",
    "path": "/workspace/file.py",
    "asimov_rules": asimov.get_rules()
})
```

**3. Multi-Agent Validation**
- ALL agents check Asimov before actions
- Reviewer performs deep validation
- Failed validations logged to Memory

---

## 🌳 Tree-Sitter (Code Parsing)

### **Capabilities**
```python
class TreeSitterParser:
    languages: list[str] = ["python", "javascript", "typescript", "go", "rust"]

    def parse_file(self, path: str) -> dict:
        """Parse code structure"""
        return {
            "functions": [...],
            "classes": [...],
            "imports": [...],
            "errors": [...]
        }

    def validate_syntax(self, code: str, language: str) -> bool:
        """Check if code is syntactically valid"""
```

### **Agent Integration**

**Architect:**
- Analyzes codebase structure
- Extracts patterns and dependencies

**Codesmith:**
- **Validates own code** before writing
- Parses generated code for documentation
- Extracts functions/classes for tests

**Reviewer:**
- Deep code analysis
- Security pattern detection
- Complexity metrics

**Fixer:**
- Locates bugs via AST analysis
- Validates fixes before applying

---

## 📊 Visualization (Graphs & Diagrams)

### **Mermaid.js Integration**
```python
def generate_architecture_diagram(design: dict) -> str:
    """Generate Mermaid diagram from architecture"""
    return f"""
    graph TD
        A[Frontend] -->|API| B[Backend]
        B --> C[Database]
        B --> D[Cache]
    """
```

**Generated by:**
- Architect (architecture diagrams)
- Orchestrator (workflow visualization)

### **GraphViz Integration**
```python
def generate_dependency_graph(codebase: dict) -> str:
    """Generate .dot file for dependencies"""
```

**Generated by:**
- Architect (module dependencies)
- Reviewer (complexity analysis)

### **Pyvis (Interactive Graphs)**
```python
def generate_interactive_graph(data: dict) -> str:
    """Generate HTML interactive graph"""
```

**Generated by:**
- Architect (system architecture)
- Memory System (knowledge graph)

---

## 📝 Markdown Generation

### **Document Types**

**1. ADRs (Architecture Decision Records)**
```python
# Generated by: Architect
def generate_adr(decision: dict) -> str:
    return f"""
    # ADR-001: {decision['title']}

    ## Status
    {decision['status']}

    ## Context
    {decision['context']}

    ## Decision
    {decision['decision']}

    ## Consequences
    {decision['consequences']}
    """
```

**2. API Documentation**
```python
# Generated by: Codesmith (from Tree-Sitter)
def generate_api_docs(functions: list) -> str:
    """Generate Markdown API docs from parsed code"""
```

**3. Test Reports**
```python
# Generated by: Reviewer
def generate_test_report(results: dict) -> str:
    """Markdown test coverage report"""
```

**4. Progress Reports**
```python
# Generated by: Orchestrator
def generate_progress_report(workflow_state: dict) -> str:
    """Markdown workflow progress"""
```

---

## 📚 Learning System (Cross-Session)

### **Architecture**
```python
class LearningSystem:
    def learn_from_success(self, workflow: dict):
        """Store successful patterns"""
        memory.store(
            content=f"Successful: {workflow['pattern']}",
            metadata={
                "type": "learning",
                "pattern": workflow["pattern"],
                "success_rate": 1.0,
                "timestamp": "..."
            }
        )

    def learn_from_failure(self, error: dict):
        """Store anti-patterns"""
        memory.store(
            content=f"Failed: {error['pattern']} - {error['reason']}",
            metadata={
                "type": "anti_pattern",
                "pattern": error["pattern"],
                "error_type": error["type"]
            }
        )

    def suggest_approach(self, task: dict) -> dict:
        """Query historical successes"""
        similar_successes = memory.search(
            query=task["description"],
            filters={"type": "learning", "success_rate": ">0.8"}
        )
        return {"suggested_approach": similar_successes[0]}
```

### **Agent Integration**

**ALL agents:**
- Query Learning System before starting tasks
- Store successful approaches after completion
- Store failures with error context

**Example:**
```python
# Codesmith before implementing
past_successes = learning.suggest_approach({
    "task": "Create React component",
    "language": "TypeScript"
})
# Returns: "Use functional components + TypeScript interfaces"
```

---

## 🔧 File Operations

### **Tool Suite**
```python
class FileTools:
    # Read
    def read_file(self, path: str) -> str:
        """Read file content"""

    # Write
    def write_file(self, path: str, content: str) -> bool:
        """Create or overwrite file"""

    # Edit
    def edit_file(self, path: str, old: str, new: str) -> bool:
        """Replace text in file"""

    # Directory
    def create_directory(self, path: str) -> bool:
        """Create directory"""

    def list_files(self, path: str) -> list[str]:
        """List directory contents"""

    # Analysis
    def parse_file(self, path: str) -> dict:
        """Parse with Tree-Sitter"""
```

**Asimov Integration:**
- All operations validated
- Workspace boundary enforcement
- Permission checks

**Used By:**
- Codesmith (primary)
- Fixer (editing)
- Architect (analysis)

---

## 📈 Feature Matrix (Agent × Feature)

| Feature | Research | Architect | Codesmith | Reviewer | Fixer |
|---------|----------|-----------|-----------|----------|-------|
| **Memory System** | ✅ Store | ✅ Read/Store | ✅ Read/Store | ✅ Read/Store | ✅ Read/Store |
| **Asimov Rules** | ✅ Validate | ✅ Validate | ✅ Validate | ✅ **Enforce** | ✅ Validate |
| **Learning** | ✅ Store patterns | ✅ Learn designs | ✅ Learn code | ✅ Learn issues | ✅ Learn fixes |
| **Tree-Sitter** | ❌ | ✅ Analyze | ✅ **Validate own code** | ✅ Deep analysis | ✅ Locate bugs |
| **Markdown** | ✅ Reports | ✅ ADRs, Diagrams | ✅ API Docs | ✅ Test Reports | ⚠️ Fix Logs |
| **File Tools** | ❌ | ⚠️ Read only | ✅ Full suite | ✅ Read only | ✅ Read/Write |
| **Graphs** | ❌ | ✅ Mermaid, GraphViz, Pyvis | ⚠️ Simple | ⚠️ Complexity | ❌ |

Legend:
- ✅ Full support
- ⚠️ Limited support
- ❌ Not used

---

## 🗂️ Workspace Structure

```
$WORKSPACE/
├── .ki_autoagent_ws/              # Workspace-specific data
│   ├── cache/
│   │   └── workflow_checkpoints_v6.db  # AsyncSqliteSaver
│   ├── memory/
│   │   ├── vectors.faiss          # FAISS vector store
│   │   └── metadata.db            # SQLite metadata
│   ├── instructions/              # Project-specific instructions
│   │   └── architect-custom.md
│   └── artifacts/                 # Generated outputs
│       ├── architecture/          # ADRs, diagrams
│       ├── code/                  # Generated code
│       ├── tests/                 # Generated tests
│       └── reports/               # Markdown reports
```

---

## 🚀 Technology Stack

### **Core**
- **Python:** 3.13 (only, no backwards compatibility)
- **LangGraph:** 0.2.45 (workflow orchestration)
- **LangChain:** 0.3.9 (agent framework)
- **AsyncSqliteSaver:** 2.0.1 (state persistence)

### **AI Providers**
- **OpenAI:** GPT-4o, GPT-4o-mini (openai==1.109.1)
- **Anthropic:** Claude Sonnet 4.1 (anthropic==0.68.0)
- **Perplexity:** Sonar Huge 128k (aiohttp==3.10.5)

### **Memory & Storage**
- **FAISS:** Vector similarity (faiss-cpu==1.12.0)
- **SQLite:** Async operations (aiosqlite==0.20.0)
- **Redis:** Caching with orjson (redis==6.4.0)

### **Code Analysis**
- **Tree-Sitter:** 0.25.1 (Python 3.13 compatible)
  - tree-sitter-python==0.25.0
  - tree-sitter-javascript==0.25.0
  - tree-sitter-typescript==0.23.2

### **Visualization**
- **Mermaid:** mermaid-py==0.5.0
- **GraphViz:** graphviz==0.20.3
- **Pyvis:** pyvis==0.3.2

### **Performance**
- **uvloop:** 0.21.0 (2-4x faster event loop)
- **orjson:** 3.10.12 (2-3x faster JSON)
- **tenacity:** 9.0.0 (Circuit Breaker, Retry)

### **Backend**
- **FastAPI:** 0.117.1
- **uvicorn:** 0.37.0
- **WebSockets:** 10.4

---

## 📝 Version Info

**Current Version:** 6.0.0-alpha.1
**Release Date:** 2025-10-08
**Status:** In Active Development

**Previous Version:** 5.9.0 (skipped 5.9.2)
**Migration Strategy:** Direct v6.0 (complete refactor)

**Documentation:**
- See `V6_0_MIGRATION_PLAN.md` for implementation roadmap
- See `V6_0_COMPLETE_TEST_PLAN.md` for testing strategy
- See `V6_0_ARCHITECTURE.md` for detailed architecture (to be created)
