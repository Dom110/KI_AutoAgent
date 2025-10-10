# HITL Integration & Plugin System Analysis - Complete Summary

**Date:** 2025-10-10
**Session Type:** ULTRATHINK Systematic Analysis
**Topics:** v6/v6_1 Versions, HITL Debug Info, Claude Code Plugin System

---

## 📋 USER FRAGEN BEANTWORTET

### ✅ FRAGE 1: Warum v6.0 und v6.1 Versionen?

**Antwort:**

| Aspect | v6.0 | v6.1 |
|--------|------|------|
| **Import** | `from langchain_anthropic import ChatAnthropic` | `from adapters.claude_cli_simple import ClaudeCLISimple` |
| **Agent Creation** | `create_react_agent` (nicht async) | Direct `ainvoke()` calls |
| **Tool Calling** | Automatic ReAct loop | Manual mit Claude CLI tools |
| **Status** | ❌ Broken (Pydantic conflicts, timeouts) | ✅ Working (alle Tests bestanden) |
| **Async Support** | ❌ Sync mit Workarounds | ✅ Native async/await |
| **HITL Integration** | ❌ Black box, schwer zu debuggen | ✅ Volle Kontrolle, alle Infos verfügbar |

**ENTSCHEIDUNG: v6.1 behalten, v6.0 löschen**

**Grund:**
- ✅ v6.1 funktioniert einwandfrei (100% success rate in tests)
- ✅ Volle async/await Unterstützung
- ✅ Einfach für HITL debug info zu erweitern
- ✅ Bessere Performance (keine ReAct overhead)
- ✅ Klare Error Handling

**Dokumentation:** `/Users/dominikfoert/git/KI_AutoAgent/REACT_AGENT_ANALYSIS.md`

---

### ✅ FRAGE 2: HITL Debug Info Implementation

**Anforderung:**
> "Das Ziel ist auch dem Nutzer bei HITL sämtliche Informationen von Eingabe,
> in unserem Fall das komplette CLI Kommando und alle Ausgabewerte, sowie Debug
> Infos zur Verfügung zu stellen im HITL."

**IMPLEMENTIERT ✅**

#### Was wurde hinzugefügt:

**1. ClaudeCLISimple erweitert:**

```python
# New __init__ parameter
def __init__(
    self,
    # ... existing parameters ...
    hitl_callback: Any = None  # NEW!
):
    # ... existing code ...

    # HITL Debug Info Storage
    self.last_command: list[str] | None = None
    self.last_system_prompt: str | None = None
    self.last_user_prompt: str | None = None
    self.last_combined_prompt: str | None = None
    self.last_raw_output: str | None = None
    self.last_events: list[dict] | None = None
    self.last_duration_ms: float = 0.0
    self.last_error: str | None = None
```

**2. HITL Callbacks in _call_cli():**

```python
async def _call_cli(self, messages):
    start_time = time.time()

    # Extract prompts
    system_prompt, user_prompt = self._extract_system_and_user_prompts(messages)
    combined_prompt = f"{system_prompt}\n\n{user_prompt}"

    # Capture for HITL
    self.last_system_prompt = system_prompt
    self.last_user_prompt = user_prompt
    self.last_combined_prompt = combined_prompt

    # Build command
    cmd = [...]
    self.last_command = cmd.copy()

    # HITL: Send BEFORE execution
    if self.hitl_callback:
        await self.hitl_callback({
            "type": "claude_cli_start",
            "agent": self.agent_name,
            "model": self.model,
            "command": cmd,
            "system_prompt": system_prompt,
            "system_prompt_length": len(system_prompt),
            "user_prompt": user_prompt,
            "user_prompt_length": len(user_prompt),
            "combined_prompt_length": len(combined_prompt),
            "tools": self.agent_tools,
            "permission_mode": self.permission_mode,
            "timestamp": start_time
        })

    # Execute CLI
    result = await subprocess_exec(...)

    # Parse output
    events = parse_jsonl(output_str)

    # Calculate duration
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    # Capture for HITL
    self.last_raw_output = output_str
    self.last_events = events
    self.last_duration_ms = duration_ms

    # HITL: Send AFTER successful execution
    if self.hitl_callback:
        await self.hitl_callback({
            "type": "claude_cli_complete",
            "agent": self.agent_name,
            "model": self.model,
            "duration_ms": duration_ms,
            "output_length": len(output_str),
            "raw_output": output_str,
            "events_count": len(events),
            "events": events,
            "final_event_type": final_event.get('type'),
            "result_preview": str(final_event.get('result', ''))[:500],
            "success": True,
            "timestamp": end_time
        })
```

**3. Error Handling mit HITL:**

```python
except Exception as e:
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    # Capture error
    self.last_error = str(e)
    self.last_duration_ms = duration_ms

    # HITL: Send error info
    if self.hitl_callback:
        await self.hitl_callback({
            "type": "claude_cli_error",
            "agent": self.agent_name,
            "model": self.model,
            "duration_ms": duration_ms,
            "error": str(e),
            "error_type": type(e).__name__,
            "success": False,
            "timestamp": end_time
        })

    raise
```

#### Wie verwenden:

```python
# Define HITL callback
async def hitl_debug_callback(debug_info: dict):
    """
    Receive ALL debug info from Claude CLI execution.

    Debug info includes:
    - type: "claude_cli_start" | "claude_cli_complete" | "claude_cli_error"
    - agent: Agent name
    - model: Model name
    - command: Complete CLI command (list)
    - system_prompt: Full system prompt
    - user_prompt: Full user prompt
    - raw_output: Complete CLI output (JSONL)
    - events: Parsed JSONL events
    - duration_ms: Execution time
    - error: Error message (if failed)
    """
    # Send to frontend via WebSocket
    await websocket.send_json({
        "type": "debug_info",
        "data": debug_info
    })

    # Or log to file
    with open("/tmp/hitl_debug.log", "a") as f:
        f.write(json.dumps(debug_info, indent=2))

# Create LLM with HITL callback
llm = ClaudeCLISimple(
    model="claude-sonnet-4-20250514",
    agent_name="codesmith",
    agent_tools=["Read", "Edit", "Bash"],
    hitl_callback=hitl_debug_callback  # 👈 NEW!
)

# Use as normal - callback is called automatically
response = await llm.ainvoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_prompt)
])

# After execution, access captured info
print(f"Command: {llm.last_command}")
print(f"Duration: {llm.last_duration_ms}ms")
print(f"Events: {len(llm.last_events)}")
print(f"Output: {llm.last_raw_output[:500]}")
```

#### Was der User bekommt:

**Vor Execution:**
```json
{
  "type": "claude_cli_start",
  "agent": "codesmith",
  "model": "claude-sonnet-4-20250514",
  "command": [
    "claude",
    "--model", "claude-sonnet-4-20250514",
    "--permission-mode", "acceptEdits",
    "--allowedTools", "Read Edit Bash",
    "--agents", "{\"codesmith\": {...}}",
    "--output-format", "stream-json",
    "--verbose",
    "-p", "SYSTEM_PROMPT\n\nUSER_PROMPT"
  ],
  "system_prompt": "You are an expert code generator...",
  "system_prompt_length": 473,
  "user_prompt": "Generate code for...",
  "user_prompt_length": 2272,
  "combined_prompt_length": 2745,
  "tools": ["Read", "Edit", "Bash"],
  "permission_mode": "acceptEdits",
  "timestamp": 1728577920.123
}
```

**Nach Execution (Success):**
```json
{
  "type": "claude_cli_complete",
  "agent": "codesmith",
  "model": "claude-sonnet-4-20250514",
  "duration_ms": 25430.5,
  "output_length": 11067,
  "raw_output": "{\"type\":\"system\"...}\n{\"type\":\"assistant\"...}\n...",
  "events_count": 3,
  "events": [
    {"type": "system", "subtype": "init", ...},
    {"type": "assistant", "message": {...}},
    {"type": "result", "result": "FILE: calculator.py\n..."}
  ],
  "final_event_type": "result",
  "result_preview": "FILE: calculator.py\n```python\nclass Calculator...",
  "success": true,
  "timestamp": 1728577945.553
}
```

**Nach Execution (Error):**
```json
{
  "type": "claude_cli_error",
  "agent": "codesmith",
  "model": "claude-sonnet-4-20250514",
  "duration_ms": 20123.8,
  "error": "Claude CLI failed: timeout",
  "error_type": "TimeoutError",
  "success": false,
  "timestamp": 1728577940.246
}
```

#### Benefits:

✅ **Volle Transparenz**
- User sieht EXAKT was ausgeführt wird
- Komplettes CLI Kommando
- Alle Prompts (system + user)
- Kompletter Output (raw JSONL)
- Alle parsed events
- Genaue Timing Infos

✅ **Debugging**
- Bei Problemen: User kann EXAKT sehen was schief lief
- Kann CLI command manuell ausführen
- Kann Prompts untersuchen
- Kann Output analysieren

✅ **HITL Collaboration**
- User kann Execution in Echtzeit folgen
- Kann bei Problemen eingreifen
- Hat alle Infos für Troubleshooting
- Kann Entscheidungen treffen (pause/continue)

---

### ✅ FRAGE 3: Claude Code Plugin System

**Anforderung:** Nutzen für bessere Integration?

**ANALYSE COMPLETE ✅**

**Dokumentation:** `/Users/dominikfoert/git/KI_AutoAgent/CLAUDE_CODE_PLUGIN_ANALYSIS.md`

#### Was ist das Plugin System?

Neu in Claude Code:
```
/plugin install    - Install plugins
/plugin enable     - Enable plugins
/plugin disable    - Disable plugins
/plugin marketplace - Browse available plugins
```

#### Plugin Types:

1. **Custom Commands**
   ```
   /autoagent task "Build calculator"
   /autoagent status
   ```

2. **Custom Agents**
   ```
   claude --agent ki-autoagent-research "Python async patterns"
   claude --agent ki-autoagent-codesmith design.md
   ```

3. **Hooks**
   ```
   on_file_write → Asimov Rule validation
   on_code_generate → Tree-sitter validation
   on_agent_start → HITL mode detection
   ```

4. **MCP Servers**
   ```
   Perplexity Search MCP Server
   Tree-sitter Validation MCP Server
   Memory System MCP Server
   ```

#### Empfohlene Strategie:

**Phase 1 (Jetzt):**
- ✅ v6.1 Backend fertig und funktionierend

**Phase 2 (1-2 Wochen):**
- 🎯 MCP Server für Perplexity erstellen
- 🎯 MCP Server für Tree-sitter erstellen
- 🎯 Als `ki-autoagent-mcp` Plugin veröffentlichen

**Phase 3 (2-4 Wochen):**
- 🎯 Agents als Claude Code agents registrieren
- 🎯 Hooks für Asimov + Tree-sitter
- 🎯 Custom Commands (`/autoagent`)

**Phase 4 (2-3 Monate):**
- 🎯 Full Plugin im Marketplace
- 🎯 One-command installation
- 🎯 Native Integration

#### Vision: Future State

**Installation:**
```bash
# Current (complex)
cd /path/to/KI_AutoAgent
./install.sh
$HOME/.ki_autoagent/start.sh

# Future (simple)
/plugin install ki-autoagent
```

**Usage:**
```bash
# Native commands
/autoagent task "Build e-commerce API"

# Native agents
claude --agent research "AI trends 2025"
claude --agent codesmith design.md

# Native tools
claude --tool perplexity "Latest React features"
claude --tool validate_syntax app.py

# Automatic hooks (no manual setup)
# Asimov Rules enforce on every file write
# Tree-sitter validates every code generation
```

---

## 📊 IMPLEMENTATION STATUS

### ✅ COMPLETED

| Item | Status | Documentation |
|------|--------|---------------|
| v6 vs v6_1 Analysis | ✅ Done | REACT_AGENT_ANALYSIS.md |
| HITL Debug Info Design | ✅ Done | This document |
| HITL Implementation | ✅ Done | claude_cli_simple.py |
| Plugin System Research | ✅ Done | CLAUDE_CODE_PLUGIN_ANALYSIS.md |
| HITL Workflow Rules | ✅ Done | HITL_WORKFLOW_RULES.md |
| HITL Manager Implementation | ✅ Done | hitl_manager_v6.py |

### ⏳ PENDING

| Item | Priority | Timeline | Notes |
|------|----------|----------|-------|
| Delete v6.0 files | Low | Next session | Keep for reference until v6.1 fully validated |
| Test HITL callbacks | High | Next session | Create test with WebSocket integration |
| MCP Server Prototype | Medium | 1-2 weeks | Perplexity + Tree-sitter |
| Plugin API Research | Medium | Ongoing | Need official docs |
| Full Plugin | Low | 2-3 months | After MCP servers working |

---

## 📁 FILES CREATED/MODIFIED

### Documentation (New):
1. **REACT_AGENT_ANALYSIS.md** - v6 vs v6_1 detailed comparison
2. **HITL_WORKFLOW_RULES.md** - Complete HITL patterns (15 chapters, 1200 lines)
3. **CLAUDE_CODE_PLUGIN_ANALYSIS.md** - Plugin system analysis & roadmap
4. **HITL_AND_PLUGIN_SUMMARY_2025-10-10.md** - This document

### Code (Modified):
1. **backend/adapters/claude_cli_simple.py**
   - Added `hitl_callback` parameter
   - Added debug info storage (8 new instance variables)
   - Added HITL callback before execution
   - Added HITL callback after execution
   - Added HITL callback on error
   - Added duration tracking

### Code (New):
1. **backend/workflow/hitl_manager_v6.py**
   - Complete HITL manager implementation
   - Mode detection (INTERACTIVE, AUTONOMOUS, DEBUG, PRODUCTION)
   - Task management with non-blocking failures
   - Session reporting
   - WebSocket integration

---

## 🎯 USAGE EXAMPLES

### Example 1: Simple HITL Integration

```python
from adapters.claude_cli_simple import ClaudeCLISimple

# Define callback
async def my_hitl_callback(info: dict):
    print(f"[{info['type']}] {info['agent']}")
    if info['type'] == 'claude_cli_start':
        print(f"  Command: {' '.join(info['command'][:5])}...")
        print(f"  System: {info['system_prompt_length']} chars")
        print(f"  User: {info['user_prompt_length']} chars")
    elif info['type'] == 'claude_cli_complete':
        print(f"  Duration: {info['duration_ms']:.1f}ms")
        print(f"  Output: {info['output_length']} chars")
        print(f"  Events: {info['events_count']}")

# Create LLM with HITL
llm = ClaudeCLISimple(
    agent_name="test",
    hitl_callback=my_hitl_callback
)

# Use it
response = await llm.ainvoke([
    HumanMessage(content="Hello")
])
```

---

### Example 2: WebSocket HITL Integration

```python
from adapters.claude_cli_simple import ClaudeCLISimple
import asyncio

class HITLWebSocketHandler:
    def __init__(self, websocket):
        self.websocket = websocket

    async def send_debug_info(self, info: dict):
        """Send debug info to frontend via WebSocket."""
        try:
            await self.websocket.send_json({
                "type": "hitl_debug",
                "data": info
            })
        except Exception as e:
            logger.error(f"Failed to send HITL debug: {e}")

# In your workflow
class WorkflowV6:
    def __init__(self, websocket):
        self.hitl = HITLWebSocketHandler(websocket)

        # Create LLM with HITL callback
        self.llm = ClaudeCLISimple(
            agent_name="codesmith",
            hitl_callback=self.hitl.send_debug_info
        )

    async def generate_code(self, design):
        # Execute - debug info automatically sent to frontend!
        response = await self.llm.ainvoke([
            SystemMessage(content="You are a code generator..."),
            HumanMessage(content=f"Generate: {design}")
        ])

        return response
```

---

### Example 3: HITL Manager Integration

```python
from workflow.hitl_manager_v6 import HITLManagerV6, HITLMode
from adapters.claude_cli_simple import ClaudeCLISimple

# Create HITL manager
hitl = HITLManagerV6(
    websocket_callback=my_websocket_send,
    default_mode=HITLMode.INTERACTIVE
)

# Detect mode from user message
user_msg = "Ich bin erstmal nicht da, mach alles was geht"
mode = hitl.detect_mode(user_msg)  # → AUTONOMOUS
hitl.set_mode(mode)

# Create LLM with HITL callback
llm = ClaudeCLISimple(
    agent_name="codesmith",
    hitl_callback=lambda info: hitl.websocket_callback({
        "type": "claude_debug",
        **info
    })
)

# Add tasks
hitl.add_task("Research", research_fn)
hitl.add_task("Generate code", lambda: llm.ainvoke([...]))
hitl.add_task("Review code", review_fn)

# Execute (skip_on_error automatic based on mode)
report = await hitl.execute_tasks()

# Generate report
print(hitl.format_report_markdown(report))
```

---

## 🔄 INTEGRATION WORKFLOW

```
User Request
     ↓
HITL Manager detects mode (INTERACTIVE/AUTONOMOUS/DEBUG)
     ↓
Create ClaudeCLISimple with hitl_callback
     ↓
───────────────────────────────────────────
Execute Agent Task:
───────────────────────────────────────────
     ↓
llm.ainvoke([messages])
     ↓
   [BEFORE EXECUTION]
   hitl_callback({
     type: "claude_cli_start",
     command: [...],
     prompts: {...},
     timestamp: ...
   })
     ↓
   Send to WebSocket → Frontend shows:
   "🚀 Starting Codesmith Agent..."
   "📋 Command: claude --model claude-sonnet..."
   "📝 System: 473 chars | User: 2272 chars"
     ↓
───────────────────────────────────────────
   Execute CLI Command
   (duration: 20-30s)
───────────────────────────────────────────
     ↓
   [AFTER EXECUTION]
   hitl_callback({
     type: "claude_cli_complete",
     duration_ms: 25430,
     raw_output: "...",
     events: [...],
     result_preview: "..."
   })
     ↓
   Send to WebSocket → Frontend shows:
   "✅ Codesmith Complete (25.4s)"
   "📦 Output: 11,067 chars"
   "📊 Events: 3 (system, assistant, result)"
   "📄 Files: 1 (calculator.py - 4139 bytes)"
───────────────────────────────────────────
     ↓
Parse Response & Continue Workflow
     ↓
HITL Manager tracks progress
     ↓
Generate Session Report
     ↓
User sees complete transparency!
```

---

## 💡 KEY TAKEAWAYS

### 1. **v6.1 is the Way**
- ✅ Keep direct `ainvoke()` approach
- ✅ Delete v6.0 files when ready
- ✅ Better for HITL, async, debugging

### 2. **HITL Debug Info: Complete**
- ✅ All info captured (command, prompts, output, events)
- ✅ Callbacks before/after/error
- ✅ Ready for WebSocket integration
- ✅ User has full transparency

### 3. **Plugin System: Opportunity**
- 🎯 Start with MCP servers (Phase 2)
- 🎯 Gradual migration to full plugin
- 🎯 Don't break existing system
- 🎯 Vision: One-command install from marketplace

---

## 📚 NEXT SESSION PRIORITIES

### HIGH PRIORITY:
1. **Test HITL Callbacks**
   - Create test with WebSocket mock
   - Verify all debug info transmitted correctly
   - Test error scenarios

2. **Update Subgraphs with HITL**
   - Research: Add hitl_callback
   - Codesmith: Add hitl_callback
   - ReviewFix: Add hitl_callback
   - Architect: Add hitl_callback (if needed)

3. **Frontend Integration**
   - Update BackendClient to handle `hitl_debug` messages
   - Create UI components to show debug info
   - Test end-to-end flow

### MEDIUM PRIORITY:
4. **MCP Server Prototype**
   - Research MCP protocol
   - Create Perplexity MCP server
   - Test with Claude Code

5. **Delete v6.0 Files**
   - After full v6.1 validation
   - Keep backups
   - Update imports

### LOW PRIORITY:
6. **Plugin API Research**
   - Find official documentation
   - Study example plugins
   - Plan full plugin structure

---

## ✨ SUMMARY

**Achieved Today:**
- ✅ v6/v6_1 analysis complete → **Decision: Keep v6.1**
- ✅ HITL debug info **fully implemented** in ClaudeCLISimple
- ✅ HITL Manager v6 created (15-chapter rules + code)
- ✅ Plugin System analyzed → **Roadmap created**
- ✅ 4 new documentation files (2000+ lines)

**Ready for:**
- ✅ User to see ALL debug info (command + outputs)
- ✅ Full HITL transparency
- ✅ WebSocket integration (callback ready)
- ✅ Plugin system when official docs available

**Next:**
- Test HITL callbacks with real workflow
- Update all subgraphs with hitl_callback
- Frontend UI for debug info display

---

**All documentation in:**
- `REACT_AGENT_ANALYSIS.md` - Why v6.1 is better
- `HITL_WORKFLOW_RULES.md` - Complete HITL patterns
- `CLAUDE_CODE_PLUGIN_ANALYSIS.md` - Plugin system roadmap
- `HITL_AND_PLUGIN_SUMMARY_2025-10-10.md` - This summary

**Code changes in:**
- `backend/adapters/claude_cli_simple.py` - HITL integration
- `backend/workflow/hitl_manager_v6.py` - HITL manager

**Testing:**
- All existing tests still pass
- HITL callbacks ready for integration
- No breaking changes
