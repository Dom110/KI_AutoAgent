# KI AutoAgent - System Interactions & Complex Relationships

**Version:** 6.1.0-alpha
**Date:** 2025-10-11

---

## 🔗 Complex System Interactions

### 1. **Claude CLI Integration Challenge**

#### Problem
Claude CLI doesn't natively support LangChain's async interface, requiring a custom adapter.

#### Solution Chain
```
LangChain Agent Request
    ↓
ClaudeCLISimple Adapter (claude_cli_simple.py)
    ├── Extract System/User prompts from messages
    ├── Build --agents JSON structure
    ├── Handle FILE: format for Codesmith
    └── Parse stream-json output
        ↓
subprocess.create_subprocess_exec()
    ├── Set workspace_path as CWD
    └── Execute claude CLI command
        ↓
Parse JSONL Response
    └── Return as AIMessage
```

#### Critical Details
- **Timeout Issue:** System prompt in `agent.prompt` alone causes timeout
- **Format Issue:** Long prompts lose FILE: format instructions
- **Fix:** Codesmith uses special handling with focused prompt

---

### 2. **Memory System Architecture**

#### Hybrid Storage Strategy
```
Agent Output
    ↓
MemorySystem (memory_system_v6.py)
    ├── Content → FAISS Vector Index
    │   ├── OpenAI Embeddings (1536 dim)
    │   ├── Semantic Search
    │   └── faiss_index.idx file
    │
    └── Metadata → SQLite Database
        ├── Agent name, type, confidence
        ├── Timestamps, workspace
        └── metadata.db file
```

#### Inter-Agent Communication
```
Research Agent
    ↓ stores findings
Memory System
    ↓ retrieved by
Architect Agent
    ↓ stores design
Memory System
    ↓ retrieved by
Codesmith Agent
```

---

### 3. **Workflow State Management**

#### State Transformation Pipeline
```python
# Each agent has its own state type
ResearchState → research_to_supervisor → SupervisorState
SupervisorState → supervisor_to_architect → ArchitectState
ArchitectState → architect_to_supervisor → SupervisorState
# ... and so on

# Transformations handle:
- Type conversions (dict ↔ string)
- Field mappings
- Error handling
```

#### State Persistence
```
LangGraph StateGraph
    ↓
AsyncSqliteSaver (Checkpointing)
    ├── Thread ID (unique per session)
    ├── Checkpoint ID (incremental)
    └── Serialized state blob
```

---

### 4. **Tool Registry & Dynamic Loading**

#### Tool Discovery Flow
```
Agent Initialization
    ↓
ToolRegistryV6.discover_tools()
    ├── Scan tools/ directory
    ├── Load Python modules
    ├── Extract @tool decorated functions
    └── Build tool catalog
        ↓
Agent receives tools based on:
    - Agent type (research, architect, etc.)
    - Permission level
    - Workspace context
```

---

### 5. **Intelligence Systems Integration**

#### Query Classification → Workflow Selection
```python
User Query: "Build an e-commerce site with payment"
    ↓
QueryClassifierV6.classify()
    ├── Complexity: COMPLEX
    ├── Type: DEVELOPMENT
    ├── Agents: [research, architect, codesmith, reviewfix]
    └── Duration: ~480 seconds
        ↓
WorkflowAdapter selects pipeline
```

#### Predictive System → Resource Allocation
```python
PredictiveSystemV6.estimate()
    ├── Analyze historical data
    ├── Consider query complexity
    └── Return:
        - Expected duration
        - Memory requirements
        - Token usage estimate
        - Risk factors
```

---

### 6. **Error Recovery Mechanisms**

#### Self-Diagnosis → Auto-Healing
```
Agent Execution
    ↓ on error
SelfDiagnosisV6.diagnose()
    ├── Categorize error type
    ├── Check recovery strategies
    └── Execute healing:
        - Retry with backoff
        - Switch to fallback model
        - Simplify prompt
        - Alert user
```

#### Workflow Adapter → Dynamic Routing
```
Pipeline Failure at Codesmith
    ↓
WorkflowAdapterV6.adapt()
    ├── Analyze failure reason
    ├── Check alternative paths
    └── Options:
        - Retry with different prompt
        - Skip to ReviewFix
        - Fallback to simpler approach
        - Request user clarification
```

---

### 7. **MCP Server Communication**

#### Optional Enhancement Layer
```
Agent Request: "Search for React best practices"
    ↓
Choice Point:
    ├── Direct: perplexity_tool.py → Perplexity API
    └── MCP: → perplexity_server.py → MCP Protocol → Tool

MCP Benefits:
    - Standardized protocol
    - Tool versioning
    - External tool integration
    - Language agnostic
```

---

### 8. **WebSocket Message Flow**

#### Bidirectional Communication
```
Client → Server:
{
    "type": "init",
    "workspace_path": "/path"
}

Server → Client:
{
    "type": "initialized",
    "workspace_path": "/path",
    "v6_systems": {...}
}

Client → Server:
{
    "type": "chat",
    "message": "Create app..."
}

Server → Client (streaming):
{
    "type": "agent_message",
    "agent": "research",
    "content": "Researching..."
}
...
{
    "type": "result",
    "subtype": "workflow_complete",
    "files_generated": 42
}
```

---

### 9. **File Generation Pipeline**

#### Codesmith → File System
```
Architecture Design (from Architect)
    ↓
Codesmith Agent
    ├── Generate code with Claude CLI
    ├── Parse FILE: format response
    ├── For each file:
    │   ├── Tree-sitter syntax validation
    │   ├── Asimov security check
    │   └── Write to workspace
    └── Store in memory
```

#### Critical Format Requirement
```
Claude must output:
FILE: src/app.py
```python
code here
```

NOT:
"I've generated the following files..."
```

---

### 10. **Approval Manager Flow**

#### Human-in-the-Loop Integration
```
Critical Operation Request
    ↓
ApprovalManagerV6.request_approval()
    ├── Check approval rules
    ├── If required:
    │   ├── Send via WebSocket
    │   ├── Wait for response
    │   └── Timeout handling
    └── Log decision
```

---

## 🔄 Circular Dependencies & Solutions

### Problem 1: Memory ↔ Agent Circular Reference
```
❌ Agent needs Memory for context
❌ Memory needs Agent metadata for storage
```

**Solution:** Lazy initialization
```python
# Memory initialized first without agents
memory = MemorySystem()
# Agents created with memory reference
agent = Agent(memory=memory)
# Agent registers with memory post-init
memory.register_agent(agent)
```

### Problem 2: State ↔ Workflow Coupling
```
❌ State defines workflow structure
❌ Workflow modifies state
```

**Solution:** Immutable state transformations
```python
# State is never modified directly
new_state = transform_state(old_state, changes)
# Workflow only sees snapshots
```

---

## 🎯 Critical Integration Points

### 1. **Claude CLI Subprocess**
- **File:** `backend/adapters/claude_cli_simple.py`
- **Critical:** Must set `cwd=workspace_path`
- **Issue:** Without CWD, finds wrong files

### 2. **Memory SQLite Permissions**
- **File:** `backend/memory/memory_system_v6.py`
- **Critical:** Must chmod 664 after creation
- **Issue:** "readonly database" errors

### 3. **FILE: Format Parser**
- **File:** `backend/subgraphs/codesmith_subgraph_v6_1.py`
- **Critical:** Must handle exact format
- **Issue:** No files generated if format wrong

### 4. **WebSocket Init Protocol**
- **File:** `backend/api/server_v6_integrated.py`
- **Critical:** Must send init before chat
- **Issue:** No workspace context without init

---

## 🔍 Debugging Paths

### When Files Aren't Generated
```
1. Check /tmp/claude_cli_command.txt
2. Verify FILE: format in prompt
3. Check Memory for Codesmith output
4. Verify workspace_path in subprocess
```

### When Agents Timeout
```
1. Check prompt length in /tmp/*_prompt.txt
2. Verify --verbose flag in CLI command
3. Check agent.prompt complexity
4. Monitor subprocess execution time
```

### When Memory Fails
```
1. Check SQLite permissions
2. Verify FAISS index exists
3. Check OpenAI API key
4. Monitor embedding generation
```

---

## 💡 Design Decisions & Rationale

### Why Claude CLI Instead of API?
- **Pros:** Tool support, streaming, lower cost
- **Cons:** Subprocess overhead, format requirements
- **Decision:** Tool support critical for code generation

### Why FAISS + SQLite Hybrid?
- **FAISS:** Fast semantic search
- **SQLite:** Structured metadata queries
- **Decision:** Best of both worlds

### Why Supervisor Pattern?
- **Flexibility:** Dynamic agent routing
- **Scalability:** Easy to add agents
- **Decision:** Better than fixed pipelines

### Why MCP Servers Optional?
- **Complexity:** Additional protocol layer
- **Performance:** Direct calls faster
- **Decision:** Progressive enhancement

---

**This document explains the complex interactions that make KI AutoAgent work.**