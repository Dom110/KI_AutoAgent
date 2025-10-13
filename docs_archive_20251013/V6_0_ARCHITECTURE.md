# KI AutoAgent v6.0 - Architecture Documentation

**Version:** 6.0.0-alpha.1
**Status:** In Development
**Last Updated:** 2025-10-08

---

## 🎯 Architecture Overview

### **Core Principle: LangGraph Best Practices**

v6.0 is a **complete architectural refactor** following LangGraph official best practices:

1. **Prebuilt Agents** (`create_react_agent()`) where possible
2. **Subgraphs** for complex multi-agent workflows
3. **Declarative Routing** (graph edges, not imperative code)
4. **Persistent State** (AsyncSqliteSaver)
5. **State Isolation** (separate state per subgraph)

**Reference:**
- [LangGraph create_react_agent docs](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/)
- [LangGraph subgraphs tutorial](https://langchain-ai.github.io/langgraph/how-tos/subgraph/)

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     VS Code Extension (TypeScript)              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Chat View   │  │  Status Bar  │  │   Commands   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket (ws://localhost:8001/ws/chat)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Python 3.13)                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SupervisorGraph (Orchestrator)              │  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │  Research   │→ │  Architect  │→ │  Codesmith  │     │  │
│  │  │  Subgraph   │  │  Subgraph   │  │  Subgraph   │     │  │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘     │  │
│  │                                            │             │  │
│  │                                            ▼             │  │
│  │                                     ┌─────────────┐     │  │
│  │                                     │  ReviewFix  │     │  │
│  │                                     │   Subgraph  │     │  │
│  │                                     │             │     │  │
│  │                                     │  ┌────────┐ │     │  │
│  │                                     │  │Reviewer│ │     │  │
│  │                                     │  └───┬────┘ │     │  │
│  │                                     │      │      │     │  │
│  │                                     │      ▼      │     │  │
│  │                                     │  ┌────────┐ │     │  │
│  │                                     │  │ Fixer  │ │     │  │
│  │                                     │  └───┬────┘ │     │  │
│  │                                     │      │      │     │  │
│  │                                     │      ▼      │     │  │
│  │                                     │   (Loop)    │     │  │
│  │                                     └─────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Infrastructure Layer                        │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │AsyncSqlite   │  │Memory System │  │Asimov Rules  │  │  │
│  │  │Saver         │  │(FAISS+SQLite)│  │(Security)    │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │Tree-Sitter   │  │Learning      │  │Visualization │  │  │
│  │  │(Code Parse)  │  │System        │  │(Mermaid/etc) │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   External Services                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  OpenAI API  │  │Anthropic API │  │Perplexity API│         │
│  │  (GPT-4o)    │  │(Claude 4.1)  │  │(Sonar)       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔀 Workflow Flow

### **Example: "Create Calculator App" Task**

```
1. User Message
   ↓
2. SupervisorGraph receives task
   ↓
3. Task Decomposition:
   - Research: Find best practices for React apps
   - Architect: Design component structure
   - Codesmith: Implement components
   - ReviewFix: Validate and fix issues
   ↓
4. ResearchSubgraph
   - Perplexity search: "React calculator best practices 2025"
   - Store findings in Memory
   - Generate research report (Markdown)
   ↓
5. ArchitectSubgraph
   - Read Research from Memory
   - Analyze existing codebase (Tree-Sitter)
   - Design: Vite + React 18 + TypeScript
   - Generate architecture diagram (Mermaid)
   - Store design in Memory
   ↓
6. CodesmithSubgraph
   - Read Architect Design from Memory
   - Generate Calculator.tsx
   - Validate syntax with Tree-Sitter
   - Write file (Asimov: check permissions)
   - Store implementation in Memory
   ↓
7. ReviewFixSubgraph (Loop)
   a. Reviewer:
      - Read Implementation from Memory
      - Analyze code with Tree-Sitter
      - Check Asimov compliance
      - Score quality: 0.85
      - Store review in Memory

   b. If quality < threshold (0.75):
      - Fixer reads Review from Memory
      - Locates issues with Tree-Sitter
      - Fixes code
      - Writes file (Asimov: check permissions)
      - Store fix in Memory
      - GOTO step a (max 3 iterations)

   c. If quality >= threshold:
      - Accept implementation
      - Store success in Learning System
   ↓
8. SupervisorGraph returns result
   ↓
9. User receives response in VS Code
```

---

## 🏗️ Subgraph Architecture

### **1. ResearchSubgraph**

**Purpose:** Web research, documentation gathering

**Architecture:**
```python
# Using create_react_agent() - LANGGRAPH BEST PRACTICE
from langgraph.prebuilt import create_react_agent

research_agent = create_react_agent(
    model=llm,  # Perplexity Sonar Huge 128k
    tools=[perplexity_search, fetch_documentation],
    state_modifier="You are a research agent..."
)

# Wrap in subgraph
research_subgraph = research_agent
```

**State:**
```python
class ResearchState(TypedDict):
    query: str
    findings: dict[str, Any]
    sources: list[str]
    report: str  # Markdown
    errors: list[dict[str, Any]]
```

**Tools:**
- `perplexity_search(query: str) -> dict`
- `fetch_documentation(url: str) -> str`

**Integration:**
- **Memory:** Stores findings with tags `["research", "documentation"]`
- **Asimov:** Permission `can_web_search`
- **Learning:** Stores successful search queries

---

### **2. ArchitectSubgraph**

**Purpose:** System design, architecture planning

**Architecture:**
```python
# Custom implementation (too specialized for create_react_agent)
def architect_node(state: ArchitectState) -> ArchitectState:
    # 1. Read research from Memory
    research = memory.search(
        query="technology recommendations",
        filters={"agent": "research"}
    )

    # 2. Analyze codebase with Tree-Sitter
    codebase_structure = tree_sitter.parse_directory(
        state["workspace_path"]
    )

    # 3. Generate design
    llm_response = llm.invoke([
        SystemMessage("You are an architect..."),
        HumanMessage(f"Research: {research}\nCodebase: {codebase_structure}")
    ])

    # 4. Generate Mermaid diagram
    diagram = generate_mermaid_diagram(llm_response.design)

    # 5. Store in Memory
    memory.store(
        content=llm_response.design,
        metadata={"agent": "architect", "type": "design"}
    )

    # 6. Store in Learning System
    learning.learn_from_success({
        "pattern": "vite_react_typescript",
        "context": state["workspace_path"]
    })

    return {
        **state,
        "design": llm_response.design,
        "diagram": diagram
    }

architect_subgraph = StateGraph(ArchitectState)
architect_subgraph.add_node("architect", architect_node)
architect_subgraph.set_entry_point("architect")
architect_subgraph.set_finish_point("architect")
```

**State:**
```python
class ArchitectState(TypedDict):
    workspace_path: str
    research_context: dict[str, Any]
    design: dict[str, Any]
    diagram: str  # Mermaid
    adr: str  # Architecture Decision Record (Markdown)
    errors: list[dict[str, Any]]
```

**Tools:**
- `analyze_codebase(path: str) -> dict` (Tree-Sitter)
- `generate_mermaid_diagram(design: dict) -> str`
- `suggest_patterns(context: dict) -> list`

**Integration:**
- **Memory:** Reads Research, stores Design
- **Asimov:** Permission `can_analyze_codebase`
- **Learning:** Stores design patterns
- **Tree-Sitter:** Analyzes codebase structure
- **Markdown:** Generates ADRs
- **Visualization:** Mermaid, GraphViz diagrams

---

### **3. CodesmithSubgraph**

**Purpose:** Code implementation, file operations

**Architecture:**
```python
# Using create_react_agent() - LANGGRAPH BEST PRACTICE
from langgraph.prebuilt import create_react_agent

codesmith_agent = create_react_agent(
    model=llm,  # Claude Sonnet 4.1
    tools=[read_file, write_file, edit_file, parse_code],
    state_modifier="You are a coding agent..."
)

# Wrap with pre/post hooks
def codesmith_node(state: CodesmithState) -> CodesmithState:
    # 1. Read design from Memory
    design = memory.search(
        query="architecture design",
        filters={"agent": "architect"}
    )

    # 2. Read research from Memory
    research = memory.search(
        query="best practices",
        filters={"agent": "research"}
    )

    # 3. Query Learning System
    past_successes = learning.suggest_approach({
        "task": "create_react_component",
        "language": "typescript"
    })

    # 4. Invoke agent with context
    result = codesmith_agent.invoke({
        **state,
        "design": design,
        "research": research,
        "past_successes": past_successes
    })

    # 5. Validate generated code with Tree-Sitter
    for file in result["generated_files"]:
        syntax_valid = tree_sitter.validate_syntax(
            file["content"],
            file["language"]
        )
        if not syntax_valid:
            # Retry or error
            pass

    # 6. Store in Memory
    memory.store(
        content=result["implementation"],
        metadata={"agent": "codesmith", "type": "implementation"}
    )

    return result

codesmith_subgraph = codesmith_agent
```

**State:**
```python
class CodesmithState(TypedDict):
    workspace_path: str
    design: dict[str, Any]
    requirements: str
    generated_files: list[dict[str, Any]]
    tests: list[dict[str, Any]]
    docs: str  # API documentation (Markdown)
    errors: list[dict[str, Any]]
```

**Tools:**
- `read_file(path: str) -> str`
- `write_file(path: str, content: str) -> bool` (Asimov check)
- `edit_file(path: str, old: str, new: str) -> bool` (Asimov check)
- `parse_code(path: str) -> dict` (Tree-Sitter)

**Integration:**
- **Memory:** Reads Design & Research, stores Implementation
- **Asimov:** Validates `can_write_files`, workspace boundaries
- **Learning:** Stores successful implementations
- **Tree-Sitter:** **Validates own generated code**
- **Markdown:** Generates API docs from code
- **File Tools:** Full suite (read, write, edit)

---

### **4. ReviewFixSubgraph (Loop)**

**Purpose:** Code review and iterative fixing

**Architecture:**
```python
# Custom loop subgraph
def reviewer_node(state: ReviewFixState) -> ReviewFixState:
    # 1. Read implementation from Memory
    implementation = memory.search(
        query="code implementation",
        filters={"agent": "codesmith"}
    )

    # 2. Read design from Memory
    design = memory.search(
        query="architecture design",
        filters={"agent": "architect"}
    )

    # 3. Deep code analysis with Tree-Sitter
    code_analysis = tree_sitter.parse_file(state["file_path"])

    # 4. Security check
    security_issues = check_security(code_analysis)

    # 5. Asimov enforcement
    asimov_validation = asimov.validate_implementation({
        "files": state["generated_files"],
        "actions": state["actions_taken"]
    })

    # 6. Score quality
    quality_score = calculate_quality(
        code_analysis,
        security_issues,
        asimov_validation
    )

    # 7. Store review in Memory
    memory.store(
        content={"score": quality_score, "issues": security_issues},
        metadata={"agent": "reviewer", "type": "review"}
    )

    return {
        **state,
        "quality_score": quality_score,
        "review_feedback": {"issues": security_issues, "asimov": asimov_validation}
    }

def fixer_node(state: ReviewFixState) -> ReviewFixState:
    # 1. Read review from Memory
    review = memory.search(
        query="code review",
        filters={"agent": "reviewer"}
    )

    # 2. Locate bugs with Tree-Sitter
    bug_locations = tree_sitter.find_issues(
        state["file_path"],
        review["issues"]
    )

    # 3. Generate fixes
    fixes = generate_fixes(bug_locations, review)

    # 4. Apply fixes (Asimov check)
    for fix in fixes:
        if asimov.validate("fixer", "can_write_files", {"path": fix["path"]}):
            edit_file(fix["path"], fix["old"], fix["new"])

    # 5. Store fix in Memory
    memory.store(
        content=fixes,
        metadata={"agent": "fixer", "type": "fix"}
    )

    # 6. Store in Learning System
    learning.learn_from_success({
        "pattern": "fix_type_error",
        "context": state["workspace_path"]
    })

    return {
        **state,
        "fixes_applied": fixes
    }

def should_continue_fixing(state: ReviewFixState) -> str:
    if state["quality_score"] >= 0.75:
        return "end"
    if state["iteration"] >= 3:
        return "end"
    return "continue"

# Build subgraph
reviewfix_graph = StateGraph(ReviewFixState)
reviewfix_graph.add_node("reviewer", reviewer_node)
reviewfix_graph.add_node("fixer", fixer_node)

reviewfix_graph.set_entry_point("reviewer")
reviewfix_graph.add_conditional_edges(
    "reviewer",
    should_continue_fixing,
    {"continue": "fixer", "end": END}
)
reviewfix_graph.add_edge("fixer", "reviewer")  # Loop back

reviewfix_subgraph = reviewfix_graph.compile()
```

**State:**
```python
class ReviewFixState(TypedDict):
    workspace_path: str
    generated_files: list[dict[str, Any]]
    quality_score: float
    review_feedback: dict[str, Any]
    fixes_applied: list[dict[str, Any]]
    iteration: int
    errors: list[dict[str, Any]]
```

**Integration:**
- **Reviewer:**
  - Memory: Reads Implementation, stores Review
  - Asimov: **Enforces ALL rules**
  - Learning: Stores review patterns
  - Tree-Sitter: Deep code analysis
  - Markdown: Test reports

- **Fixer:**
  - Memory: Reads Review, stores Fix
  - Asimov: Validates write permissions
  - Learning: Stores successful fixes
  - Tree-Sitter: Locates bugs
  - File Tools: Read, Write, Edit

---

### **5. SupervisorGraph**

**Purpose:** Orchestrate all subgraphs

**Architecture:**
```python
from langgraph.graph import StateGraph, END

def supervisor_node(state: SupervisorState) -> SupervisorState:
    # Task decomposition logic
    # Determine next subgraph to call
    return state

# Build graph
supervisor_graph = StateGraph(SupervisorState)

# Add subgraphs as nodes
supervisor_graph.add_node("research", research_subgraph)
supervisor_graph.add_node("architect", architect_subgraph)
supervisor_graph.add_node("codesmith", codesmith_subgraph)
supervisor_graph.add_node("reviewfix", reviewfix_subgraph)

# Declarative routing (NOT imperative!)
supervisor_graph.set_entry_point("research")
supervisor_graph.add_edge("research", "architect")
supervisor_graph.add_edge("architect", "codesmith")
supervisor_graph.add_edge("codesmith", "reviewfix")
supervisor_graph.add_edge("reviewfix", END)

# Compile with AsyncSqliteSaver
workflow = supervisor_graph.compile(
    checkpointer=async_sqlite_saver
)
```

**State:**
```python
class SupervisorState(TypedDict):
    user_query: str
    workspace_path: str
    research_results: dict[str, Any] | None
    architecture_design: dict[str, Any] | None
    generated_files: list[dict[str, Any]]
    review_feedback: dict[str, Any] | None
    final_result: Any | None
    errors: Annotated[list[dict[str, Any]], operator.add]
```

**State Transformations:**
```python
# Input: SupervisorState → ResearchState
def supervisor_to_research(state: SupervisorState) -> ResearchState:
    return {
        "query": state["user_query"],
        "findings": {},
        "sources": [],
        "report": "",
        "errors": []
    }

# Output: ResearchState → SupervisorState
def research_to_supervisor(state: ResearchState) -> dict:
    return {
        "research_results": {
            "findings": state["findings"],
            "sources": state["sources"],
            "report": state["report"]
        }
    }
```

---

## 🗃️ State Management

### **AsyncSqliteSaver Architecture**

```python
import aiosqlite
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver

# Setup (in workflow_v6.py)
async def setup_checkpointer(workspace_path: str) -> AsyncSqliteSaver:
    db_path = os.path.join(
        workspace_path,
        ".ki_autoagent_ws/cache/workflow_checkpoints_v6.db"
    )

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Create connection
    conn = await aiosqlite.connect(db_path)

    # Create checkpointer
    checkpointer = AsyncSqliteSaver(conn)

    # Initialize tables
    await checkpointer.setup()

    return checkpointer

# Usage
checkpointer = await setup_checkpointer(workspace_path)
workflow = supervisor_graph.compile(checkpointer=checkpointer)

# Invoke with thread_id for persistence
result = await workflow.ainvoke(
    {"user_query": "Create calculator"},
    config={"configurable": {"thread_id": "session_123"}}
)

# Resume from checkpoint
result = await workflow.ainvoke(
    {},  # Empty input = resume from last checkpoint
    config={"configurable": {"thread_id": "session_123"}}
)
```

**Storage Location:**
- `$WORKSPACE/.ki_autoagent_ws/cache/workflow_checkpoints_v6.db`
- SQLite database with LangGraph schema
- Isolated per workspace

**Benefits:**
- ✅ Persistent across sessions
- ✅ Crash recovery
- ✅ Workflow replay for debugging
- ✅ State inspection at any point

---

## 🧠 Memory System Architecture

### **FAISS + SQLite Hybrid**

```python
import faiss
import sqlite3
from openai import OpenAI

class MemorySystem:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.vector_store_path = os.path.join(
            workspace_path,
            ".ki_autoagent_ws/memory/vectors.faiss"
        )
        self.metadata_db_path = os.path.join(
            workspace_path,
            ".ki_autoagent_ws/memory/metadata.db"
        )

        # Initialize FAISS index
        self.dimension = 1536  # OpenAI text-embedding-3-small
        self.index = faiss.IndexFlatL2(self.dimension)

        # Initialize SQLite
        self.conn = sqlite3.connect(self.metadata_db_path)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata JSON NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        self.conn.commit()

    async def store(self, content: str, metadata: dict):
        # Generate embedding
        embedding = await self._get_embedding(content)

        # Add to FAISS
        vector_id = self.index.ntotal
        self.index.add(np.array([embedding]))

        # Store metadata in SQLite
        self.conn.execute(
            "INSERT INTO memory_items (vector_id, content, metadata, timestamp) VALUES (?, ?, ?, ?)",
            (vector_id, content, json.dumps(metadata), datetime.now().isoformat())
        )
        self.conn.commit()

        # Persist FAISS index
        faiss.write_index(self.index, self.vector_store_path)

    async def search(self, query: str, filters: dict = None, k: int = 5) -> list:
        # Generate query embedding
        query_embedding = await self._get_embedding(query)

        # Search FAISS
        distances, indices = self.index.search(np.array([query_embedding]), k)

        # Retrieve metadata from SQLite
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            cursor = self.conn.execute(
                "SELECT content, metadata, timestamp FROM memory_items WHERE vector_id = ?",
                (int(idx),)
            )
            row = cursor.fetchone()
            if row:
                content, metadata_json, timestamp = row
                metadata = json.loads(metadata_json)

                # Apply filters
                if filters:
                    if not all(metadata.get(k) == v for k, v in filters.items()):
                        continue

                results.append({
                    "content": content,
                    "metadata": metadata,
                    "timestamp": timestamp,
                    "similarity": 1 / (1 + distance)  # Convert distance to similarity
                })

        return results

    async def _get_embedding(self, text: str) -> np.ndarray:
        client = OpenAI()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(response.data[0].embedding)
```

**Storage:**
- Vectors: `$WORKSPACE/.ki_autoagent_ws/memory/vectors.faiss`
- Metadata: `$WORKSPACE/.ki_autoagent_ws/memory/metadata.db`

**Usage:**
```python
# Store
await memory.store(
    content="Vite + React 18 recommended for 2025",
    metadata={"agent": "research", "type": "technology", "confidence": 0.9}
)

# Search
results = await memory.search(
    query="modern frontend frameworks",
    filters={"agent": "research", "type": "technology"}
)
```

---

## 🛡️ Asimov Rules Integration

See `MASTER_FEATURES_v6.0.md` for complete Asimov documentation.

**Key Points:**
- ALL agents validate before actions
- Reviewer **enforces** rules (deep validation)
- File operations always checked
- Workspace boundaries enforced
- Permission model per agent

---

## 🌳 Tree-Sitter Integration

See `MASTER_FEATURES_v6.0.md` for complete Tree-Sitter documentation.

**Key Points:**
- Multi-language support (Python, JS, TS, Go, Rust)
- Used by: Architect (analysis), Codesmith (validation), Reviewer (deep analysis), Fixer (bug location)
- **Codesmith validates own code** before writing

---

## 📊 Complete Technology Stack

See `MASTER_FEATURES_v6.0.md` section "🚀 Technology Stack" for complete list.

**Core:**
- Python 3.13 (only)
- LangGraph 0.2.45
- AsyncSqliteSaver 2.0.1
- FAISS 1.12.0
- Tree-Sitter 0.25.1

---

## 📝 File Structure

```
backend/
├── workflow_v6.py                   # Main workflow orchestration
├── state_v6.py                      # All state schemas
├── agents/
│   ├── research_agent_v6.py
│   ├── architect_agent_v6.py
│   ├── codesmith_agent_v6.py
│   ├── reviewer_agent_v6.py
│   └── fixer_agent_v6.py
├── tools/
│   ├── perplexity_tools.py
│   ├── file_tools.py
│   ├── tree_sitter_tools.py
│   └── visualization_tools.py
├── memory/
│   ├── memory_system.py             # FAISS + SQLite
│   └── learning_system.py
├── security/
│   └── asimov_rules.py
└── tests/
    ├── unit/
    │   ├── test_workflow_v6.py
    │   ├── test_memory_v6.py
    │   └── test_agents_v6.py
    ├── integration/
    │   └── test_full_workflow_v6.py
    └── native/
        └── native_test_client.py    # WebSocket test client
```

---

## 🔍 Debugging Strategy

See `V6_0_DEBUGGING.md` for complete debugging guide.

**Tools:**
- Python debugger (pdb)
- LangGraph Studio (workflow visualization)
- Log analysis
- State inspection (AsyncSqliteSaver)

---

## 📚 References

**LangGraph Documentation:**
- [create_react_agent](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/)
- [Subgraphs](https://langchain-ai.github.io/langgraph/how-tos/subgraph/)
- [AsyncSqliteSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.aiosqlite.AsyncSqliteSaver)

**v6.0 Documentation:**
- `MASTER_FEATURES_v6.0.md` - Complete feature reference
- `V6_0_MIGRATION_PLAN.md` - Implementation roadmap
- `V6_0_COMPLETE_TEST_PLAN.md` - Testing strategy
- `PROGRESS_TRACKER_v6.0.md` - Current status

---

## 💻 Complete Code Example

### **Minimal Working v6.0 Workflow**

```python
"""
backend/workflow_v6.py - Minimal working example

This demonstrates the complete v6.0 architecture in ~200 lines.
"""

import asyncio
import os
from typing import Any

import aiosqlite
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from state_v6 import (
    SupervisorState,
    ResearchState,
    supervisor_to_research,
    research_to_supervisor
)


# ============================================================================
# 1. SETUP CHECKPOINTER
# ============================================================================

async def setup_checkpointer(workspace_path: str) -> AsyncSqliteSaver:
    """Setup AsyncSqliteSaver for persistent state."""
    db_path = os.path.join(
        workspace_path,
        ".ki_autoagent_ws/cache/workflow_checkpoints_v6.db"
    )
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()

    return checkpointer


# ============================================================================
# 2. BUILD RESEARCH SUBGRAPH (create_react_agent)
# ============================================================================

def build_research_subgraph() -> Any:
    """
    Build Research subgraph using create_react_agent().

    This is LANGGRAPH BEST PRACTICE - use prebuilt agents!
    """
    # Model
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    # Tools (simplified for example)
    from langchain_core.tools import tool

    @tool
    def web_search(query: str) -> str:
        """Search the web for information."""
        # In real implementation: Perplexity API call
        return f"Search results for: {query}"

    # Create agent using prebuilt function
    research_agent = create_react_agent(
        model=llm,
        tools=[web_search],
        state_modifier="You are a research agent. Find the latest information."
    )

    return research_agent


# ============================================================================
# 3. BUILD ARCHITECT SUBGRAPH (Custom)
# ============================================================================

def build_architect_subgraph() -> StateGraph:
    """
    Build Architect subgraph with custom implementation.

    Custom because architecture design is too specialized for create_react_agent.
    """
    from state_v6 import ArchitectState

    def architect_node(state: ArchitectState) -> ArchitectState:
        """Main architect logic."""
        llm = ChatOpenAI(model="gpt-4o")

        # 1. Query Memory for research (simplified)
        # research = memory.search("technology recommendations")

        # 2. Generate design
        response = llm.invoke([
            {"role": "system", "content": "You are an architect."},
            {"role": "user", "content": f"Design system for: {state['user_requirements']}"}
        ])

        # 3. Store in Memory (simplified)
        # memory.store(response.content, {"agent": "architect"})

        return {
            **state,
            "design": {"architecture": response.content},
            "tech_stack": ["React", "FastAPI", "PostgreSQL"],
            "diagram": "graph TD\n  A[Frontend] --> B[Backend]"
        }

    # Build graph
    graph = StateGraph(ArchitectState)
    graph.add_node("architect", architect_node)
    graph.set_entry_point("architect")
    graph.set_finish_point("architect")

    return graph.compile()


# ============================================================================
# 4. BUILD SUPERVISOR GRAPH
# ============================================================================

def build_supervisor_graph(checkpointer: AsyncSqliteSaver) -> Any:
    """
    Build main SupervisorGraph that orchestrates all subgraphs.

    This uses DECLARATIVE ROUTING (graph edges, not imperative code).
    """
    # Build subgraphs
    research_subgraph = build_research_subgraph()
    architect_subgraph = build_architect_subgraph()
    # codesmith_subgraph = build_codesmith_subgraph()  # TODO: Phase 5
    # reviewfix_subgraph = build_reviewfix_subgraph()  # TODO: Phase 6

    # Supervisor node (minimal for example)
    def supervisor_node(state: SupervisorState) -> SupervisorState:
        """Supervisor just passes state through in this example."""
        return state

    # Build graph
    graph = StateGraph(SupervisorState)

    # Add supervisor node
    graph.add_node("supervisor", supervisor_node)

    # Add subgraphs as nodes with input/output transformations
    graph.add_node("research", research_subgraph)
    graph.add_node("architect", architect_subgraph)

    # Declarative routing (NOT imperative!)
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "research")
    graph.add_edge("research", "architect")
    graph.add_edge("architect", END)

    # Compile with checkpointer
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# 5. MAIN EXECUTION
# ============================================================================

async def run_workflow(workspace_path: str, user_query: str) -> dict[str, Any]:
    """
    Run the complete v6.0 workflow.

    Usage:
        result = await run_workflow(
            workspace_path="/Users/.../MyProject",
            user_query="Create a calculator app"
        )
    """
    # Setup
    checkpointer = await setup_checkpointer(workspace_path)
    workflow = build_supervisor_graph(checkpointer)

    # Initial state
    initial_state: SupervisorState = {
        "user_query": user_query,
        "workspace_path": workspace_path,
        "research_results": None,
        "architecture_design": None,
        "generated_files": [],
        "review_feedback": None,
        "final_result": None,
        "errors": []
    }

    # Execute workflow with persistence
    result = await workflow.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "session_123"}}
    )

    return result


# ============================================================================
# 6. EXAMPLE USAGE
# ============================================================================

async def main():
    """Example usage of v6.0 workflow."""
    result = await run_workflow(
        workspace_path="/Users/dominikfoert/test-workspace",
        user_query="Create a React calculator app with TypeScript"
    )

    print("Workflow Result:")
    print(f"Research: {result.get('research_results')}")
    print(f"Architecture: {result.get('architecture_design')}")
    print(f"Files: {len(result.get('generated_files', []))} files generated")
    print(f"Errors: {len(result.get('errors', []))} errors")


if __name__ == "__main__":
    asyncio.run(main())
```

### **Key Differences from v5.9.0**

| Aspect | v5.9.0 (Old) | v6.0 (New) |
|--------|--------------|------------|
| **State** | Imperative dict manipulation | TypedDict schemas (state_v6.py) |
| **Agents** | Manual tool loops | create_react_agent() |
| **Routing** | execution_plan routing | Declarative graph edges |
| **Persistence** | MemorySaver (in-memory) | AsyncSqliteSaver (persistent) |
| **Subgraphs** | Single flat graph | Subgraphs with transformations |
| **Memory** | Single Redis cache | FAISS + SQLite hybrid |
| **Testing** | Mock-based unit tests | Native WebSocket tests |

### **Running This Example**

```bash
# 1. Install dependencies
cd backend
pip install -r requirements_v6.txt

# 2. Set environment variables
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Run workflow
python workflow_v6.py
```

**Expected Output:**
```
Workflow Result:
Research: {'findings': {...}, 'sources': [...], 'report': '...'}
Architecture: {'design': {...}, 'tech_stack': ['React', 'FastAPI', ...]}
Files: 3 files generated
Errors: 0 errors
```
