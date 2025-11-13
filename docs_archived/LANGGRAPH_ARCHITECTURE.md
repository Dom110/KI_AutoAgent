# 🧠 LangGraph Architecture - Workflow Engine Explained

**Version:** v7.0 Pure MCP  
**Date:** 2025-11-10  
**Framework:** LangGraph v0.1+

---

## Overview: What is LangGraph?

**LangGraph** ist die moderne Workflow-Engine von LangChain für Multi-Agent Systeme.

**Warum LangGraph?**
- ✅ State Management (Shared State zwischen Agenten)
- ✅ Graph-Based Workflow (Visual & Code)
- ✅ Conditional Routing (if/then/else)
- ✅ Checkpoint Management (Persistence)
- ✅ Streaming Support (Real-time Updates)
- ✅ Error Handling & Retries

**vs. Traditional Approaches:**
```
Traditional:
  Sequential if/elif/else chains
  ❌ Schwer zu verstehen
  ❌ Schwer zu debuggen
  ❌ Schwer zu erweitern

LangGraph:
  Visual State Graph
  ✅ Klar strukturiert
  ✅ Leicht zu debuggen
  ✅ Leicht zu erweitern
```

---

## 🏗️ KI AutoAgent Workflow Architecture

### Workflow Structure
```
┌─────────────────────────────────────────────────────┐
│              SupervisorState (TypedDict)             │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ messages: list[dict]                        │   │
│  │ goal: str                                   │   │
│  │ user_query: str                             │   │
│  │ workspace_path: str                         │   │
│  │ session_id: str                             │   │
│  ├─────────────────────────────────────────────┤   │
│  │ AGENT TRACKING:                             │   │
│  │ last_agent: str | None (Reducer!)           │   │
│  │ iteration: int                              │   │
│  ├─────────────────────────────────────────────┤   │
│  │ AGENT OUTPUTS:                              │   │
│  │ research_context: dict | None               │   │
│  │ architecture: dict | None                   │   │
│  │ generated_files: list | None                │   │
│  │ validation_results: dict | None             │   │
│  │ user_response: str | None                   │   │
│  ├─────────────────────────────────────────────┤   │
│  │ TRACKING FLAGS (mit Reducers!):             │   │
│  │ architecture_complete: bool                 │   │
│  │ code_complete: bool                         │   │
│  │ validation_passed: bool                     │   │
│  │ response_ready: bool                        │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### File Location
**`backend/workflow_v7_mcp.py`** - Zeilen 63-125

---

## 🔴 CRITICAL: The Reducer Pattern

### Problem: Concurrent Updates

Wenn mehrere Nodes gleichzeitig State aktualisieren (parallel execution):
```python
# Node 1 aktualisiert architecture_complete
state["architecture_complete"] = True

# Node 2 versucht zur gleichen Zeit:
state["architecture_complete"] = False

# ❌ CONFLICT! Welcher Wert gewinnt?
```

### Solution: Annotated mit Reducer

```python
from typing import Annotated

def last_value_reducer(current: Any, new: Any) -> Any:
    """Reducer that returns the last non-None value"""
    return new if new is not None else current

class SupervisorState(TypedDict):
    # ✅ Mit Reducer - sicher für parallel updates!
    architecture_complete: Annotated[bool, last_value_reducer]
    code_complete: Annotated[bool, last_value_reducer]
    validation_passed: Annotated[bool, last_value_reducer]
    response_ready: Annotated[bool, last_value_reducer]
    
    # ❌ OHNE Reducer - Konflikt möglich!
    # architecture_complete: bool
```

### How It Works
```
Zeitpunkt  Node1                Node2                State
t0         architecture=False   code=False           {}
t1         architecture=True    (waiting)            {arch: T}
t2         (done)               code=True            {arch: T}
t3         -                    validation=True      {arch: T, code: T, val: T}
           
Mit Reducer: last_value_reducer wählt neueste Value → Keine Konflikte!
```

### Alle Reducer-Fields in SupervisorState
```python
# backend/workflow_v7_mcp.py:95-127
last_agent: Annotated[str | None, last_value_reducer]           # Welcher Agent zuletzt lief
architecture_complete: Annotated[bool, last_value_reducer]       # Architektur fertig?
code_complete: Annotated[bool, last_value_reducer]               # Code fertig?
validation_passed: Annotated[bool, last_value_reducer]           # Validation ok?
response_ready: Annotated[bool, last_value_reducer]              # Response bereit?
```

**WICHTIG für AI Developer:** Wenn du neue Flags hinzufügst die parallel aktualisiert werden:
```python
# ✅ CORRECT für parallel updates:
my_flag: Annotated[bool, last_value_reducer]

# ❌ WRONG für parallel updates:
my_flag: bool
```

---

## 🎯 Graph Structure

### Nodes (Funktionen)
```python
async def supervisor_node(state: SupervisorState) -> Command[...]:
    """Central routing decision maker"""
    # Uses GPT-4o to decide which agent to call next

async def research_node(state: SupervisorState) -> Command:
    """Call research_agent MCP server"""
    # await mcp.call("research_agent", "research", {...})

async def architect_node(state: SupervisorState) -> Command:
    """Call architect_agent MCP server"""
    # await mcp.call("architect_agent", "design", {...})

async def codesmith_node(state: SupervisorState) -> Command:
    """Call codesmith_agent MCP server"""
    # await mcp.call("codesmith_agent", "generate", {...})

async def reviewfix_node(state: SupervisorState) -> Command:
    """Call reviewfix_agent MCP server"""
    # await mcp.call("reviewfix_agent", "review", {...})

async def responder_node(state: SupervisorState) -> Command:
    """Call responder_agent MCP server"""
    # await mcp.call("responder_agent", "format", {...})

async def hitl_node(state: SupervisorState) -> Command:
    """Human-in-the-loop interaction"""
    # Wait for user approval
```

### Edges (Connections)
```
supervisor_node
    ├─[research]──→ research_node ──→ back to supervisor
    ├─[architect]──→ architect_node ──→ back to supervisor
    ├─[codesmith]──→ codesmith_node ──→ back to supervisor
    ├─[reviewfix]──→ reviewfix_node ──→ back to supervisor
    ├─[responder]──→ responder_node ──→ back to supervisor
    ├─[hitl]──────→ hitl_node ──→ back to supervisor
    └─[__end__]───→ FINISH WORKFLOW
```

---

## 🔄 Routing: Command vs Conditional

### Old Way (Deprecated)
```python
# ❌ Conditional edges - schwer zu lesen
def should_research(state):
    return "research" if state["needs_research"] else "next"

graph.add_conditional_edges(
    "supervisor",
    should_research,
    {
        "research": "research",
        "next": "architect"
    }
)
```

### New Way: Command (v7.0)
```python
# ✅ Command-based routing - viel besser!
async def supervisor_node(state: SupervisorState) -> Command[Literal["research", "architect", "codesmith", "reviewfix", "responder", "hitl", "__end__"]]:
    # Supervisor decides and RETURNS command
    
    if needs_research:
        return Command(
            goto="research",
            update={
                "last_agent": "supervisor",
                "iteration": state["iteration"] + 1
            }
        )
    elif needs_architecture:
        return Command(
            goto="architect",
            update={...}
        )
    else:
        return Command(goto="__end__")
```

**Advantages:**
- ✅ Clearer routing logic (all in one node)
- ✅ Type-safe (Literal["research", "architect", ...])
- ✅ State updates explicit (Command.update)
- ✅ Easier debugging (visible decisions)

---

## 💾 Checkpointing: Persistence

### What is Checkpointing?
Speichert State zwischen Nodes damit bei Fehler weitermachen kann:

```python
# backend/workflow_v7_mcp.py:52
from langgraph.checkpoint.sqlite import SqliteSaver

# Checkpoint Store
checkpointer = SqliteSaver(conn=sqlite3.connect(":memory:"))

graph = StateGraph(SupervisorState)
graph.compile(checkpointer=checkpointer)
```

### Benefits
```
Ohne Checkpoint:
  Start → Node1 (OK) → Node2 (ERROR!) → START OVER

Mit Checkpoint:
  Start → Node1 (OK) ✓ SAVE STATE
         → Node2 (ERROR!) → RESUME FROM CHECKPOINT
                         ✓ Node2 Retry
                         → Continue
```

### Checkpoint Database
```bash
# SQLite Database speichert:
# - Graph state at each checkpoint
# - Node execution history
# - Timestamps
# - Thread IDs (for multi-user)

# Automatisch erstellt bei:
# checkpoint = SqliteSaver(conn=sqlite3.connect(":memory:"))
# (In-memory DB in diesem Fall)
```

---

## 🌊 Streaming: Real-Time Updates

### How Streaming Works

```python
# backend/workflow_v7_mcp.py:770+
async def execute_supervisor_workflow_streaming_mcp(...) -> AsyncGenerator:
    """Stream events as they happen"""
    
    async def stream_workflow_events():
        # LangGraph yields events as they occur
        async for event in graph.astream(...):
            # Event Types:
            # - "on_chain_start"
            # - "on_chain_end" 
            # - "on_llm_start"
            # - "on_llm_end"
            # - "on_tool_start"
            # - "on_tool_end"
            
            yield event
    
    async for event in stream_workflow_events():
        yield event
```

### Event Types Streamed
```
Event Name              When                           Content
─────────────────────  ───────────────────────────    ─────────────────
on_chain_start         Node starts executing          Node name, input
on_chain_end           Node finishes                  Node name, output
on_llm_start           LLM call starts (GPT-4o)       Prompts, tokens
on_llm_end             LLM call finishes              Response, usage
on_tool_start          MCP call starts                Tool name, args
on_tool_end            MCP call finishes              Result
on_parser_start        JSON parsing starts           Raw output
on_parser_end          JSON parsing finishes         Parsed result
```

### Real-time UI Updates
```
┌─────────────────────────────────┐
│  Browser WebSocket Client       │
│  ws://localhost:8002/ws/chat    │
└──────────────┬──────────────────┘
               │
         receives events:
               │
               ▼
    ┌────────────────────┐
    │ Supervisor active  │
    │ ... thinking ...   │  ← Real-time UI update!
    │                    │
    │ Decision: research │
    │ ... loading ...    │  ← Real-time UI update!
    │                    │
    │ Researching:       │
    │ ████░░░░░░ 40%    │  ← Progress bar!
    │                    │
    │ Architecture:      │
    │ Complete! ✅       │  ← Instant notification!
    └────────────────────┘
```

---

## 🚀 Execution Flow

### Step-by-Step Execution

```python
# 1. Start workflow with user query
query = "Create a Python FastAPI app"
workspace_path = "/tmp/my_app"

# 2. Initialize state
state = {
    "messages": [],
    "goal": query,
    "user_query": query,
    "workspace_path": workspace_path,
    "session_id": "unique-id",
    
    # Agent outputs (initially None)
    "research_context": None,
    "architecture": None,
    "generated_files": None,
    
    # Flags (initially False)
    "architecture_complete": False,
    "code_complete": False,
    "validation_passed": False,
    "response_ready": False,
    
    # Tracking
    "last_agent": None,
    "iteration": 0,
}

# 3. Compile graph
graph = build_supervisor_workflow_mcp()
compiled = graph.compile(checkpointer=checkpointer)

# 4. Execute workflow
async for event in compiled.astream(state):
    # Real-time event streaming
    print(f"Event: {event}")

# 5. Get final state
final_state = state
print(f"Result: {final_state['user_response']}")
```

### Supervisor Decision Logic

```python
# backend/workflow_v7_mcp.py:126+
async def supervisor_node(state: SupervisorState):
    """
    Central decision maker using GPT-4o
    """
    
    # Build context for GPT-4o
    context = f"""
    User Query: {state['user_query']}
    Workspace: {state['workspace_path']}
    
    Progress:
    - Research: {'✓' if state['research_context'] else '✗'}
    - Architecture: {'✓' if state['architecture'] else '✗'}
    - Code: {'✓' if state['generated_files'] else '✗'}
    - Validation: {'✓' if state['validation_passed'] else '✗'}
    
    Last Agent: {state['last_agent']}
    Iteration: {state['iteration']}
    """
    
    # Call GPT-4o via OpenAI MCP server
    response = await mcp.call("openai", "chat", {
        "messages": [
            {"role": "system", "content": "You are a supervisor..."},
            {"role": "user", "content": context}
        ]
    })
    
    # Parse decision
    decision = json.loads(response)
    
    # Return routing command
    if decision["action"] == "research":
        return Command(goto="research", update={...})
    elif decision["action"] == "architect":
        return Command(goto="architect", update={...})
    # ... etc
```

---

## 🔧 Common Patterns

### Pattern 1: Data Passing Between Nodes

```python
# Node 1 outputs data
async def research_node(state: SupervisorState) -> Command:
    result = await mcp.call("research_agent", "research", {...})
    
    return Command(
        goto="supervisor",
        update={
            "research_context": result,  # ← Pass to next node
            "last_agent": "research"
        }
    )

# Node 2 uses data from Node 1
async def architect_node(state: SupervisorState) -> Command:
    research_context = state["research_context"]  # ← Use data from Node 1
    
    result = await mcp.call("architect_agent", "design", {
        "research_context": research_context,
        ...
    })
    
    return Command(
        goto="supervisor",
        update={"architecture": result}
    )
```

### Pattern 2: Conditional Logic in Supervisor

```python
async def supervisor_node(state: SupervisorState) -> Command:
    """Make intelligent routing decisions"""
    
    # Check prerequisites
    if not state["research_context"]:
        return Command(goto="research")
    
    if not state["architecture"]:
        return Command(goto="architect")
    
    if not state["generated_files"]:
        return Command(goto="codesmith")
    
    if not state["validation_passed"]:
        return Command(goto="reviewfix")
    
    if not state["response_ready"]:
        return Command(goto="responder")
    
    # All done!
    return Command(goto="__end__")
```

### Pattern 3: Error Handling

```python
async def research_node(state: SupervisorState) -> Command:
    try:
        result = await mcp.call("research_agent", "research", {...})
        
        return Command(
            goto="supervisor",
            update={"research_context": result}
        )
    
    except MCPConnectionError as e:
        # Log error but continue
        logger.error(f"Research failed: {e}")
        
        return Command(
            goto="supervisor",
            update={
                "research_context": None,
                "errors": [..., str(e)]
            }
        )
```

---

## 📊 Execution Visualization

```
START
  │
  ▼
┌─────────────────┐
│    SUPERVISOR   │ ← Decides which agent to call
└────────┬────────┘
         │
    ┌────┴─────────────────────────────────┐
    │                                       │
    ▼                                       ▼
┌──────────────┐                   ┌──────────────┐
│   RESEARCH   │                   │  ARCHITECT   │
│   (MCP)      │                   │    (MCP)     │
└──────┬───────┘                   └──────┬───────┘
       │                                  │
       ▼                                  ▼
    research_context               architecture
       │                                  │
       └──────────────┬───────────────────┘
                      │
                      ▼
              ┌─────────────────┐
              │    SUPERVISOR   │
              └────────┬────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   ┌──────────────┐           ┌──────────────┐
   │  CODESMITH   │           │  REVIEWFIX   │
   │    (MCP)     │           │    (MCP)     │
   └──────┬───────┘           └──────┬───────┘
          │                         │
          ▼                         ▼
    generated_files         validation_results
          │                         │
          └──────────────┬──────────┘
                         │
                         ▼
                ┌─────────────────┐
                │    SUPERVISOR   │
                └────────┬────────┘
                         │
                         ▼
                   ┌──────────────┐
                   │  RESPONDER   │
                   │    (MCP)     │
                   └──────┬───────┘
                          │
                          ▼
                    user_response
                          │
                          ▼
                       FINISH (__end__)
```

---

## ✅ Best Practices

### DO ✅
- Use Annotated with Reducer for concurrent-safe fields
- Return Command objects explicitly
- Keep nodes focused on single responsibility
- Use checkpointing for persistence
- Stream events for real-time UI

### DON'T ❌
- Don't mutate state directly (use Command.update)
- Don't have long-running Node operations (break into substeps)
- Don't forget to update last_agent tracking
- Don't mix MCP calls with direct imports
- Don't ignore error handling

---

## ⚙️ LLM Configuration & Flexibility (v7.0 Status)

### Current State: Hard-Coded LLM Assignments

**PROBLEM:** LLMs are currently **hard-coded** in agent servers. You cannot dynamically change which LLM an agent uses.

**Current Assignments:**

```python
# backend/core/supervisor_mcp.py:187-188
self.llm = ChatOpenAI(
    model="gpt-4o-2024-11-20",  # ← HARD-CODED!
    temperature=0.4,
)

# mcp_servers/codesmith_agent_server.py:393
cmd = [
    claude_cmd,
    "--model", "claude-sonnet-4-20250514",  # ← HARD-CODED!
    "--tools", "Read,Edit,Bash",
]
```

**What Exists (But Unused):**
The `config/config/agent-models.json` file defines flexible model selection:
```json
{
  "agentId": "codesmith",
  "selectedModel": "claude-sonnet-4-20250514",
  "availableModels": [
    "claude-opus-4-1-20250805",
    "claude-sonnet-4-20250514",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18"
  ]
}
```

**⚠️ BUT:** This config is from v6.x and is **NOT loaded or used** in v7.0!

---

### Your Question: Can I Use Zencoder for Codesmith?

**Short Answer:** ❌ **Not with v7.0 architecture**

**Why?**

1. **Zencoder is not in dependencies**
   ```bash
   # requirements.txt has:
   openai==1.109.1
   anthropic==0.69.0
   langchain-openai==0.2.10
   langchain-anthropic==0.3.22
   
   # Zencoder is not present!
   ```

2. **Zencoder is not a LangChain provider**
   - LangChain has built-in support for OpenAI (ChatOpenAI)
   - LangChain has built-in support for Anthropic (ChatAnthropic)
   - Zencoder would need custom integration

3. **Codesmith uses Claude CLI directly**
   - Not via Python API
   - Would need complete rewrite to support Zencoder

4. **Supervisor uses LangChain**
   - Relies on `structured_output()` method
   - Zencoder might not support this pattern

---

### Three Approaches to Add Zencoder Support

#### **Approach 1: Make LLMs Configurable (Minimal Change)**

**Effort:** ⭐⭐ (Medium)  
**Impact:** ⭐⭐⭐⭐ (High - Enables any LangChain provider)

**How it works:**
```python
# Instead of: self.llm = ChatOpenAI(model="gpt-4o-2024-11-20")

# Load from environment or config:
llm_model = os.getenv("SUPERVISOR_LLM_MODEL", "gpt-4o-2024-11-20")
llm_provider = os.getenv("SUPERVISOR_LLM_PROVIDER", "openai")  # openai, anthropic

if llm_provider == "openai":
    from langchain_openai import ChatOpenAI
    self.llm = ChatOpenAI(model=llm_model)
elif llm_provider == "anthropic":
    from langchain_anthropic import ChatAnthropic
    self.llm = ChatAnthropic(model=llm_model)
else:
    raise ValueError(f"Unsupported provider: {llm_provider}")
```

**Pros:**
- Simple to implement
- Works with all LangChain providers
- Backward compatible

**Cons:**
- Need to support each provider separately
- Zencoder still not supported unless you add LangChain integration

---

#### **Approach 2: Zencoder MCP Server Wrapper (Recommended for Zencoder)**

**Effort:** ⭐⭐⭐ (High)  
**Impact:** ⭐⭐⭐⭐⭐ (Very High - Full flexibility)

**How it works:**

1. Create a new MCP server: `mcp_servers/zencoder_server.py`
   ```python
   class ZencoderServer:
       def __init__(self):
           self.client = ZencoderClient(api_key=os.getenv("ZENCODER_API_KEY"))
       
       async def handle_tool(self, tool: str, params: dict) -> dict:
           if tool == "generate_code":
               return await self.client.generate_code(**params)
           elif tool == "review_code":
               return await self.client.review_code(**params)
   ```

2. Register it in supervisor:
   ```python
   # backend/core/supervisor_mcp.py
   available_models = {
       "gpt-4o": ("openai", "chat"),
       "claude-3": ("anthropic", "chat"),
       "zencoder": ("zencoder", "generate"),  # ← New!
   }
   ```

3. Use it from anywhere:
   ```python
   result = await mcp.call("zencoder", "generate", {
       "instructions": "...",
       "context": "..."
   })
   ```

**Pros:**
- Native MCP architecture (no special cases)
- Uniform treatment of all LLMs
- Easy to swap providers
- Testable in isolation

**Cons:**
- Requires implementing Zencoder SDK in Python
- Need to handle Zencoder-specific features

---

#### **Approach 3: Agent Factory Pattern (Most Flexible)**

**Effort:** ⭐⭐⭐⭐ (Very High)  
**Impact:** ⭐⭐⭐⭐⭐ (Maximum flexibility)

**How it works:**

Create an abstraction layer:

```python
# backend/core/agent_factory.py
from dataclasses import dataclass

@dataclass
class AgentConfig:
    agent_id: str
    llm_provider: str      # "openai", "anthropic", "zencoder"
    llm_model: str         # "gpt-4o", "claude-3", etc.
    tools: list[str]
    system_prompt: str
    temperature: float
    max_tokens: int

class AgentFactory:
    @staticmethod
    async def create_agent(config: AgentConfig):
        """Create LLM client based on provider"""
        
        if config.llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=config.llm_model,
                temperature=config.temperature
            )
        elif config.llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=config.llm_model,
                temperature=config.temperature
            )
        elif config.llm_provider == "zencoder":
            llm = ZencoderLLMAdapter(
                model=config.llm_model,
                temperature=config.temperature
            )
        else:
            raise ValueError(f"Unknown provider: {config.llm_provider}")
        
        return llm.bind_tools(
            tools=config.tools,
            system_prompt=config.system_prompt
        )

# Usage:
supervisor_config = AgentConfig(
    agent_id="supervisor",
    llm_provider="openai",  # or "zencoder"
    llm_model="gpt-4o-2024-11-20",
    tools=["route_decision"],
    system_prompt="You are the supervisor...",
    temperature=0.4,
    max_tokens=2000
)

supervisor_llm = await AgentFactory.create_agent(supervisor_config)
```

**Pros:**
- Maximum flexibility
- Easy to test different configurations
- Configuration-driven
- Supports any provider

**Cons:**
- Most complex to implement
- Requires loading config from somewhere
- More code to maintain

---

### Recommended Path Forward (v7.1+)

**Phase 1: Make Supervisor Model-Agnostic (Week 1)**
```bash
1. Update supervisor_mcp.py to load LLM from env variables
2. Test with OPENAI_API_KEY and ANTHROPIC_API_KEY
3. Add to CLAUDE.md
```

**Phase 2: Extend to All Agents (Week 2)**
```bash
1. Update codesmith_agent_server.py to support env-based model selection
2. Update architect_agent_server.py 
3. Create agent-config.yaml with agent→model mappings
```

**Phase 3: Add Zencoder Support (Week 3+)**
```bash
1. Create zencoder_adapter.py with LangChain-compatible interface
   OR
   Create zencoder_mcp_server.py for full MCP integration
2. Update AgentFactory to support zencoder
3. Test with all agents
4. Document in updated LANGGRAPH_ARCHITECTURE.md
```

---

### Implementation Checklist for AI Developer

**For Flexible LLM Selection:**

- [ ] Read `backend/core/supervisor_mcp.py` lines 170-200
- [ ] Read `mcp_servers/codesmith_agent_server.py` lines 380-410
- [ ] Check `config/config/agent-models.json` structure
- [ ] Create `.env` with `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`
- [ ] Implement **Approach 1** (configurable env vars) as first step
- [ ] Add tests in `backend/tests/` for LLM selection
- [ ] Update logging with debug output showing which LLM is used
- [ ] Document in `backend/CLAUDE.md`

**For Zencoder Support:**

- [ ] Install Zencoder Python SDK: `pip install zencoder` (if available)
- [ ] Create `backend/core/zencoder_adapter.py` with LangChain interface
- [ ] Verify `structured_output()` compatibility
- [ ] Create `mcp_servers/zencoder_mcp_server.py` 
- [ ] Register in MCPManager
- [ ] Add `.env` variable: `ZENCODER_API_KEY`
- [ ] Test codesmith with Zencoder backend
- [ ] Benchmark performance vs Claude CLI
- [ ] Document pros/cons in updated guide

---

### Debugging LLM Selection

**Log Output Examples (what to add):**

```python
# In supervisor_mcp.py __init__
logger.info(f"🤖 Supervisor LLM Configuration:")
logger.info(f"   Provider: {llm_provider}")
logger.info(f"   Model: {model}")
logger.info(f"   Temperature: {temperature}")
logger.info(f"   Max Tokens: {max_tokens}")

# In codesmith_agent_server.py generate()
logger.info(f"🔧 Codesmith LLM Configuration:")
logger.info(f"   CLI Command: {' '.join(cmd[:6])}...")
logger.info(f"   Model: {extracted_model}")
logger.info(f"   Workspace: {workspace_path}")
logger.info(f"   Max Turns: {max_turns}")
```

---

## 🔗 References

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Workflow Code:** `backend/workflow_v7_mcp.py`
- **Supervisor Code:** `backend/core/supervisor_mcp.py`
- **MCP Manager:** `backend/utils/mcp_manager.py`

---

**Updated:** 2025-11-10  
**Status:** ✅ Complete  
**Related:** MCP_MIGRATION_FINAL_SUMMARY.md, STARTUP_REQUIREMENTS.md
