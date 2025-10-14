# ❌ OBSOLETE: claude_cli_simple.py

**Status:** DEPRECATED - Replaced by MCP Server
**Date:** 2025-10-14
**Migration:** v6.1 → v6.2 Pure MCP Architecture

---

## Replacement

This file (`claude_cli_simple.py`) has been **REPLACED** by:

```
mcp_servers/claude_cli_server.py
```

## Migration Path

**OLD (v6.1):**
```python
from adapters.claude_cli_simple import ClaudeCLISimple

llm = ClaudeCLISimple(
    workspace_path=workspace_path,
    agent_name="architect",
    temperature=0.3
)

response = await llm.ainvoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_prompt)
])
```

**NEW (v6.2):**
```python
# NO IMPORT!

result = await mcp.call(
    server="claude",
    tool="claude_generate",
    arguments={
        "prompt": user_prompt,
        "system_prompt": system_prompt,
        "workspace_path": workspace_path,
        "agent_name": "architect",
        "temperature": 0.3,
        "max_tokens": 8192,
        "tools": ["Read", "Edit", "Bash"]
    }
)
```

## Benefits of MCP Version

1. **Streaming Support:** Real-time token streaming
2. **HITL Events:** Human-in-the-loop event callbacks
3. **Tool Support:** Full Claude tools (Read, Edit, Bash)
4. **Standardized:** JSON-RPC 2.0 MCP protocol
5. **Better Error Handling:** Structured error responses
6. **Model Flexibility:** Easy to change models

---

## Action Required

**DO NOT USE** `backend/adapters/claude_cli_simple.py` anymore!

File can be safely deleted after confirming no other code imports it.

---

**Verification Command:**
```bash
grep -r "from adapters.claude_cli_simple import\|ClaudeCLISimple" backend/ --include="*.py" | grep -v "__pycache__" | grep -v "OBSOLETE"
```

If output only shows test files (checking for obsolescence), file can be deleted.