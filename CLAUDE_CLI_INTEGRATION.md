# Claude CLI Integration Guide

**Extracted from:** CLAUDE.md
**Date:** 2025-10-13
**Version:** v6.2+

---

## 🤖 CLAUDE CLI INTEGRATION (v6.0+)

### **CRITICAL: Correct Claude CLI Syntax**

**Model:** `claude-sonnet-4-20250514` (Sonnet 4.5) - Default for all agents

**Valid Tools:** ONLY `["Read", "Edit", "Bash"]`
- ❌ **"Write" does NOT exist!** Use "Edit" instead
- ✅ Read - Read files
- ✅ Edit - Create/modify files
- ✅ Bash - Execute shell commands

### **Complete CLI Command Template**

```bash
claude \
  --model claude-sonnet-4-20250514 \
  --permission-mode acceptEdits \
  --allowedTools Read Edit Bash \
  --agents '{
    "agent_name": {
      "description": "Brief description of agent role",
      "prompt": "System prompt defining agent behavior and instructions",
      "tools": ["Read","Edit","Bash"]
    }
  }' \
  --output-format stream-json \
  --verbose \
  -p "User task/prompt here"
```

### **Key Parameters**

1. **--permission-mode acceptEdits**
   - Auto-approves file edits (no manual confirmation needed)
   - Required for automated code generation

2. **--allowedTools Read Edit Bash**
   - Global tool whitelist
   - Space-separated list

3. **--agents '{...}'**
   - **OBJECT syntax**, not array: `{"name": {...}}`
   - NOT: `[{"name": "...", ...}]` ❌
   - Contains: description, prompt, tools

4. **--output-format stream-json**
   - Returns JSONL (JSON Lines)
   - Avoids truncation bug in regular JSON (Issue #2904)
   - Each line is a complete JSON event

5. **--verbose**
   - **REQUIRED** for stream-json to work properly
   - Without this, stream-json may timeout

6. **-p "..."**
   - User prompt/task (separate from agent.prompt)
   - Agent.prompt = system instructions
   - -p = user task

### **Python Integration Example**

```python
from adapters.use_claude_cli import use_claude_cli
use_claude_cli()

from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.2,
    max_tokens=8192,
    agent_name="codesmith",
    agent_description="Expert code generator following best practices",
    agent_tools=["Read", "Edit", "Bash"],  # NO Write!
    permission_mode="acceptEdits"
)

response = await llm.ainvoke([
    SystemMessage(content="Agent instructions..."),
    HumanMessage(content="User task...")
])
```

### **JSONL Response Format**

Claude CLI returns JSON Lines (one JSON object per line):

```jsonl
{"type":"system","subtype":"init",...}
{"type":"assistant","message":{...}}
{"type":"user","message":{...}}
{"type":"result","subtype":"success","result":"...",duration_ms:1234,...}
```

**Last line** contains the final result in `result` field.

### **Common Mistakes**

❌ **Using Write tool**
```python
agent_tools=["Read", "Write", "Edit"]  # WRONG! Write doesn't exist
```

✅ **Correct**
```python
agent_tools=["Read", "Edit", "Bash"]  # RIGHT!
```

❌ **Array syntax for --agents**
```bash
--agents '[{"name":"agent",...}]'  # WRONG!
```

✅ **Object syntax**
```bash
--agents '{"agent": {...}}'  # RIGHT!
```

❌ **Missing --verbose with stream-json**
```bash
--output-format stream-json  # WRONG! May timeout
```

✅ **Include --verbose**
```bash
--output-format stream-json --verbose  # RIGHT!
```

### **File Generation Best Practices**

When generating code, specify exact file paths in prompt:

```bash
-p "Generate Task Manager app.
Write files to:
  src/task.py
  src/manager.py
  main.py
  tests/test_manager.py"
```

This ensures Claude creates files at exact locations without asking.

### **Subprocess Integration**

**CRITICAL:** Always set `cwd` parameter when running Claude CLI:

```python
# File: backend/adapters/claude_cli_simple.py

# ✅ CORRECT: Explicit CWD to workspace
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=self.workspace_path  # 🎯 Use target workspace!
)
```

**Why:** Without `cwd`, Claude CLI runs from wherever Python started, causing workspace pollution and context confusion.

### **Timeout Configuration**

**Default:** 120 seconds (2 minutes)
**Extended (v6.1+):** 15 minutes for complex operations

```python
# backend/adapters/claude_cli_simple.py
timeout_seconds = 900  # 15 minutes (900 seconds)

try:
    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=timeout_seconds
    )
except asyncio.TimeoutError:
    logger.error(f"Claude CLI timeout after {timeout_seconds}s")
    process.kill()
    raise
```

### **Event Extraction**

Parse JSONL output to extract tool events:

```python
async def extract_file_events(raw_output: str) -> list[dict]:
    """Extract Write/Edit tool events from Claude CLI JSONL output."""

    file_events = []

    for line in raw_output.strip().split('\n'):
        try:
            event = json.loads(line)

            # Look for tool use events
            if event.get('type') == 'tool_use':
                tool_name = event.get('tool_name')

                if tool_name in ['Edit', 'Bash']:
                    file_path = event.get('parameters', {}).get('file_path')
                    if file_path:
                        file_events.append({
                            'tool': tool_name,
                            'path': file_path,
                            'content': event.get('parameters', {}).get('new_string')
                        })
        except json.JSONDecodeError:
            continue  # Skip invalid JSON lines

    return file_events
```

### **Debugging**

#### Check CLI execution:
```bash
# View raw CLI commands
grep "claude --model" /tmp/v6_server.log

# Check CLI output
cat /var/folders/.../tmp*_claude_raw.jsonl
```

#### Common issues:

**Issue:** "Tool not found: Write"
**Solution:** Change to "Edit" tool

**Issue:** "Agent configuration invalid"
**Solution:** Check JSON syntax - use object not array

**Issue:** "Timeout after 2 minutes"
**Solution:** Increase timeout or use extended timeout (15 min)

**Issue:** "Working directory wrong"
**Solution:** Set `cwd` parameter in subprocess call

---

## 📚 Reference Links

- **Claude Best Practices:** `/CLAUDE_BEST_PRACTICES.md`
- **Claude 4 Official Docs:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
- **Command Pipelining:** https://www.anthropic.com/engineering/claude-code-best-practices
- **Prompt Caching:** https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- **Streaming:** https://docs.claude.com/en/docs/build-with-claude/streaming

---

**Last Updated:** 2025-10-13
**See Also:** BUILD_VALIDATION_GUIDE.md, E2E_TESTING_GUIDE.md
