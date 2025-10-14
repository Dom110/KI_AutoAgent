# ❌ OBSOLETE: file_tools.py

**Status:** DEPRECATED - Replaced by MCP Server
**Date:** 2025-10-14
**Migration:** v6.1 → v6.2 Pure MCP Architecture

---

## Replacement

This file (`file_tools.py`) has been **REPLACED** by:

```
mcp_servers/file_tools_server.py
```

## Migration Path

**OLD (v6.1):**
```python
from tools.file_tools import read_file, write_file

result = await read_file.ainvoke({
    "file_path": "src/app.py",
    "workspace_path": workspace_path
})

await write_file.ainvoke({
    "file_path": "src/app.py",
    "content": code,
    "workspace_path": workspace_path
})
```

**NEW (v6.2):**
```python
# NO IMPORT!

result = await mcp.call(
    server="file_tools",
    tool="read_file",
    arguments={
        "file_path": "src/app.py",
        "workspace_path": workspace_path
    }
)

await mcp.call(
    server="file_tools",
    tool="write_file",
    arguments={
        "file_path": "src/app.py",
        "content": code,
        "workspace_path": workspace_path
    }
)
```

## Benefits of MCP Version

1. **Streaming Support:** Large files streamed in chunks
2. **Progress Updates:** Real-time progress for writes
3. **Standardized Protocol:** JSON-RPC 2.0 MCP protocol
4. **Better Security:** Workspace-scoped, no path traversal
5. **Centralized:** One server for all file operations

---

## Action Required

**DO NOT USE** `backend/tools/file_tools.py` anymore!

File can be safely deleted after confirming no other code imports it.

---

**Verification Command:**
```bash
grep -r "from tools.file_tools import" backend/ --include="*.py"
```

If output is empty, file can be deleted.