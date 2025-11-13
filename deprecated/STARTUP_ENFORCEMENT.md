# 🔒 Startup Enforcement System

## Overview

The KI AutoAgent MCP Server implements a **mandatory startup enforcement system** that requires all server instances to be started via the `start_server.py` script. This ensures all critical pre-flight checks are executed before the server becomes operational.

## Why Enforcement?

Direct server startup (`python backend/api/server_v7_mcp.py`) is **blocked** because it skips critical steps:

- ❌ No port management (port conflicts can occur)
- ❌ No dependency validation
- ❌ No system diagnostics
- ❌ No environment checks
- ❌ Potential race conditions during startup

## How It Works

### 1. Startup Marker (start_server.py)

When you run `python start_server.py`, the script:

1. Executes all pre-flight checks
2. Sets the environment variable: `KI_AUTOAGENT_STARTUP_SCRIPT=true`
3. Imports and starts the FastAPI app via uvicorn
4. The server reads this variable during startup

```python
# In start_server.py
os.environ['KI_AUTOAGENT_STARTUP_SCRIPT'] = 'true'
```

### 2. Startup Validation (server_v7_mcp.py)

At startup, the server checks for this marker:

```python
if os.environ.get('KI_AUTOAGENT_STARTUP_SCRIPT') != 'true':
    # BLOCK STARTUP WITH HELPFUL ERROR MESSAGE
    sys.exit(1)
```

If the marker is missing, the server displays a helpful error and exits immediately.

## Error Message

If you try to start the server directly:

```bash
$ python backend/api/server_v7_mcp.py

================================================================================
❌ CRITICAL ERROR: DIRECT STARTUP NOT ALLOWED
================================================================================

🚫 PROBLEM:
   • Server cannot be started directly
   • Critical port management checks are skipped
   • System diagnostics are not run
   • Dependencies are not validated
   • Port conflicts are not detected/resolved

✅ HOW TO FIX - Start the server using the provided script:

   cd /Users/dominikfoert/git/KI_AutoAgent
   python start_server.py

📋 Script options:
   python start_server.py --check-only         # Run checks without starting
   python start_server.py --port 8003          # Use different port
   python start_server.py --no-cleanup         # Don't kill existing processes

❌ STARTUP BLOCKED
   Direct execution is not supported. Please use start_server.py

================================================================================
Server startup cancelled.
================================================================================
```

## Correct Usage

### Standard Startup
```bash
python start_server.py
```

### Check System Without Starting
```bash
python start_server.py --check-only
```

### Use Different Port
```bash
python start_server.py --port 8003
```

### Disable Auto-Cleanup
```bash
python start_server.py --no-cleanup
```

## Startup Sequence

When using `python start_server.py`:

```
1. Python Version Check (3.13.8+ required)
2. Environment File Validation
3. Dependency Verification
4. Port Status Check
5. Port Cleanup (if needed)
6. Full System Diagnostics
7. Start FastAPI Server
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│       start_server.py (Entry Point)             │
│ - Sets: KI_AUTOAGENT_STARTUP_SCRIPT=true       │
│ - Runs: All pre-flight checks                   │
│ - Starts: uvicorn.run(app)                      │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│     server_v7_mcp.py (Main App)                 │
│ - CHECK: KI_AUTOAGENT_STARTUP_SCRIPT env var   │
│ - If missing: BLOCK STARTUP                     │
│ - If present: Continue initialization           │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  Rest of Server Initialization                  │
│ - Import backend modules                        │
│ - Setup MCP connections                         │
│ - Configure WebSocket handlers                  │
└─────────────────────────────────────────────────┘
```

## Integration with E2E Tests

E2E tests **do not** start the server. Instead:

1. Server is started separately: `python start_server.py`
2. Tests connect via WebSocket: `ws://localhost:8002/ws/chat`
3. Tests remain independent of server startup

This separation ensures:
- ✅ Tests can run while server is already running
- ✅ Multiple test instances can connect
- ✅ Server state is persistent across tests

## Security Benefits

1. **Controlled Startup**: All instances follow the same initialization path
2. **Audit Trail**: Script logs all startup checks
3. **Dependency Validation**: Ensures all required modules are available
4. **Port Conflict Prevention**: Auto-cleans up stale processes
5. **Diagnostic Logging**: Full system status before operation

## Disabling Enforcement (Not Recommended)

⚠️ **WARNING**: Only for advanced development scenarios!

To bypass enforcement temporarily (NOT RECOMMENDED):

```bash
# Set the marker BEFORE running the server directly
KI_AUTOAGENT_STARTUP_SCRIPT=true python backend/api/server_v7_mcp.py
```

However, this skips all the pre-flight checks that `start_server.py` provides:
- Port cleanup
- Dependency validation
- System diagnostics
- Environment validation

## Troubleshooting

### "Direct Startup Not Allowed" Error

**Solution**: Use the startup script instead
```bash
python start_server.py
```

### Still Getting Errors from start_server.py?

Check the startup sequence output for the specific error:
```bash
python start_server.py --check-only
```

Fix any reported issues, then start normally:
```bash
python start_server.py
```

### Need to Debug Server Startup?

Use check-only mode to validate everything without starting:
```bash
python start_server.py --check-only
```

Then examine the output to identify any problems.

## Key Checks Performed

### Python Version
- Requires: Python 3.13.8 or higher
- Reason: Project uses 3.13+ features (type unions, pattern matching, etc.)

### Environment File
- Checks: `~/.ki_autoagent/config/.env` exists
- Reason: Required for API keys and configuration

### Dependencies
- Validates: fastapi, uvicorn, websockets, langgraph, langchain_openai, pydantic
- Reason: Core functionality requires these packages

### Port Status
- Checks: Port 8002 (or specified port) is available
- Cleans up: Stale processes using the port
- Reason: Prevents "Address already in use" errors

### System Diagnostics
- API key validation
- Optional service availability (Perplexity, Claude CLI)
- MCP server configuration
- Workspace setup

## Files Modified

- **`start_server.py`**: Sets `KI_AUTOAGENT_STARTUP_SCRIPT` environment variable
- **`backend/api/server_v7_mcp.py`**: Added CHECK 1.5 to validate startup marker

## Related Documentation

- [`PORT_MANAGEMENT.md`](./PORT_MANAGEMENT.md) - Port management system
- [`backend/utils/port_manager.py`](./backend/utils/port_manager.py) - Port handling utilities
- [`backend/utils/health_check.py`](./backend/utils/health_check.py) - System diagnostics

## Summary

The startup enforcement system ensures:

✅ All servers follow the same controlled startup sequence
✅ No critical checks are accidentally skipped
✅ Users get clear guidance when startup fails
✅ Port conflicts are automatically resolved
✅ System state is validated before operation begins

**Use `python start_server.py` for all server startup scenarios.**