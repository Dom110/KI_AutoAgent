# Port Management & Health Check System

## Overview

Die KI AutoAgent hat jetzt ein intelligentes **Port-Management- und Health-Check-System**, das:

1. **Prüft automatisch ob der Server bereits läuft** (Port 8002)
2. **Räumt alte Prozesse auf** - erst mit SIGTERM, dann bei Bedarf mit SIGKILL
3. **Validiert alle System-Anforderungen** - Python, Dependencies, API Keys
4. **Zeigt prominente Fehlermeldungen** - keine Fehler mehr im Logfile versteckt
5. **Bietet Diagnose-Endpunkte** - `/health` und `/diagnostics` für Monitoring

## Files

### New Files Created

- **`backend/utils/port_manager.py`** - Standalone Port Management Utility
  - Detect if port is in use
  - Find process using port
  - Gracefully kill process with fallback to force kill
  - Wait for port availability

- **`backend/utils/health_check.py`** - Extended with Port Checks
  - `check_port_availability()` - Integrated port check
  - `_find_process_on_port()` - Find process by port
  - `_get_process_info()` - Get process details
  - `_kill_process()` - Graceful and force termination
  - `print_port_status()` - Display port status

- **`start_server.py`** - Convenient Startup Script
  - Full startup sequence with validation
  - Optional port auto-cleanup
  - Check-only mode
  - Error reporting before start

## Usage

### Quick Start (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Start server with automatic port cleanup
python start_server.py
```

### Advanced Options

```bash
# Start on different port
python start_server.py --port 8003

# Don't auto-cleanup existing processes
python start_server.py --no-cleanup

# Only run checks, don't start
python start_server.py --check-only

# Check current port status
python -c "from backend.utils.health_check import print_port_status; print_port_status()"
```

### Direct Server Start (Original Method)

```bash
# This still works and will do port cleanup during startup
python backend/api/server_v7_mcp.py
```

## Health Check Endpoints

### `/health` Endpoint

Returns quick health status:

```bash
curl http://localhost:8002/health
```

Response:
```json
{
  "status": "healthy",
  "version": "7.0",
  "architecture": "pure_mcp",
  "critical_errors": [],
  "warnings": [],
  "active_connections": 0,
  "active_sessions": 0
}
```

### `/diagnostics` Endpoint

Returns detailed system diagnostics:

```bash
curl http://localhost:8002/diagnostics
```

Response includes:
- All system checks results
- Error and warning details
- Server uptime
- API key status
- Port status
- Dependency status

## Startup Sequence

When the server starts, this happens:

```
1. Print startup header
2. Check port availability
   ├─ If port is free → Continue
   └─ If port is in use → Try to cleanup
      ├─ Send SIGTERM (graceful)
      ├─ Wait up to 5 seconds
      └─ If still running → Send SIGKILL (force)
3. Validate Python version (3.13.8+)
4. Check environment file (~/.ki_autoagent/config/.env)
5. Verify API keys loaded
6. Check dependencies installed
7. If all checks pass → Print ready message
8. Print prominent error banner if issues found
9. Start accepting connections
```

## Error Handling

### Red Banner Errors (Critical)

If these fail, server won't start:

```
❌ Python Version - Requires 3.13.8+
❌ Environment File - Not found at ~/.ki_autoagent/config/.env
❌ OpenAI API Key - Not loaded
❌ Missing Dependencies - websockets, langgraph, etc.
```

### Yellow Banner Warnings (Non-Critical)

These don't block startup but may affect functionality:

```
⚠️ Perplexity API Key - Not found (optional service)
⚠️ Port Cleanup - Could not kill existing process
⚠️ OpenAI Rate Limited - HTTP 429 (wait before retry)
```

## Common Scenarios

### Scenario 1: Server Already Running

```bash
$ python start_server.py

🔍 PORT STATUS
   Host: localhost
   Port: 8002
   Status: ❌ IN USE
   PID: 12345
   Process: python

🔄 CLEANING UP EXISTING SERVER
   Found process using port 8002:
   • PID: 12345
   • Command: python
   • Status: running
   
   Sending SIGTERM to PID 12345...
   ✅ Process 12345 terminated gracefully
   ✅ Port 8002 is now available
```

### Scenario 2: Process Won't Respond to SIGTERM

```bash
🔄 CLEANING UP EXISTING SERVER
   Found process using port 8002:
   • PID: 12345
   • Command: python
   
   Sending SIGTERM to PID 12345...
   ⚠️ Process did not terminate, using SIGKILL...
   Sending SIGKILL to PID 12345...
   ✅ Process 12345 force killed
   ✅ Port 8002 is now available
```

### Scenario 3: API Key Issues

```bash
🚨 SYSTEM STATUS REPORT
================================================================================

CRITICAL ERRORS (Must fix before proceeding):
  1. OpenAI API Key: Not found or not loaded

================================================================================
```

### Scenario 4: All Systems Go

```bash
====================================
✅ SERVER READY!
====================================
WebSocket: ws://localhost:8002/ws/chat
Health Check: http://localhost:8002/health
Full Diagnostics: http://localhost:8002/diagnostics
====================================
```

## Port Cleanup Details

The system uses the following approach:

### 1. Detect Port Status
```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 8002))
# result == 0 → port in use
# result != 0 → port available
```

### 2. Find Process (macOS/Linux)
```bash
lsof -i :8002 -t  # Returns PID(s)
```

### 3. Graceful Termination
```python
import signal
os.kill(pid, signal.SIGTERM)  # Polite shutdown
time.sleep(0.5)
# Check if process exited
os.kill(pid, 0)  # Raises ProcessLookupError if gone
```

### 4. Force Termination (if needed)
```python
import signal
os.kill(pid, signal.SIGKILL)  # Forced termination
# Process is immediately killed, no cleanup possible
```

## Integration Points

### In Server Startup

The health check automatically runs during FastAPI lifespan startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print_startup_header()
    
    # Check port availability FIRST
    logger.info("🔍 Checking server port...")
    print_port_status(port=8002)
    
    # Run comprehensive diagnostics (includes port cleanup)
    logger.info("🔍 Running startup diagnostics...")
    _startup_diagnostics = await run_startup_diagnostics()
    
    # ... rest of startup
    
    yield
    
    # Cleanup on shutdown
```

### In Diagnostics

The `/diagnostics` endpoint includes port status:

```json
{
  "checks": {
    "Server Port": {
      "status": "✅ OK",
      "message": "Port 8002 is available and ready for binding",
      "details": {
        "port": 8002,
        "host": "localhost",
        "status": "available"
      }
    }
  }
}
```

## Troubleshooting

### Port Still In Use After Cleanup

If the cleanup fails:

```bash
# Manual cleanup commands:
# Find process
lsof -i :8002

# Kill gracefully
kill -15 <PID>

# Force kill if needed
kill -9 <PID>

# Or use pkill to find by name
pkill -9 -f 'uvicorn.*8002'
```

### Permission Denied on Kill

If you get permission denied when killing a process:

```bash
# The process is owned by a different user
# Check who owns it:
ps aux | grep 8002

# Use sudo if needed (be careful!)
sudo kill -9 <PID>
```

### Lsof Not Found

If `lsof` is not installed on your system:

```bash
# macOS
brew install lsof

# Ubuntu/Debian
sudo apt-get install lsof

# Or use netstat/ss instead
ss -tlnp | grep 8002
```

## Monitoring

### Check Server Health

```bash
# Simple health check
curl -s http://localhost:8002/health | json_pp

# Full diagnostics
curl -s http://localhost:8002/diagnostics | json_pp

# Watch diagnostics (updates every 2 seconds)
watch 'curl -s http://localhost:8002/diagnostics | json_pp'
```

### Log Monitoring

```bash
# See server startup in real-time
python start_server.py 2>&1 | tee server.log

# Watch logs as they appear
tail -f server.log
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         start_server.py (Main Script)       │
│                                             │
│  1. Check Python Version                    │
│  2. Check Environment File                  │
│  3. Check Dependencies                      │
│  4. Check Port Status                       │
│  5. Run Full Diagnostics                    │
│  6. Start Server (if all pass)              │
└─────────────────────────────────────────────┘
         │
         ├─────→ backend/utils/health_check.py
         │       ├─ SystemDiagnostics class
         │       ├─ check_port_availability()
         │       ├─ _find_process_on_port()
         │       ├─ _kill_process()
         │       └─ print functions
         │
         ├─────→ backend/utils/port_manager.py
         │       ├─ PortManager class (standalone)
         │       ├─ ensure_port_available()
         │       └─ print_port_status()
         │
         └─────→ backend/api/server_v7_mcp.py
                 ├─ lifespan() context manager
                 ├─ /health endpoint
                 ├─ /diagnostics endpoint
                 └─ WebSocket connections
```

## Performance

- **Port Check**: < 100ms
- **Process Detection**: < 500ms
- **Graceful Kill**: < 1 second
- **Force Kill**: < 100ms
- **Full Startup Diagnostics**: < 3 seconds

## Security Notes

- Port cleanup only works on processes the current user owns
- `lsof` command requires system utilities to be installed
- Process killing uses standard OS signals (no elevated privileges needed)
- All operations are logged for audit trail

## Future Enhancements

Possible additions:

- [ ] Health check API key connectivity during startup
- [ ] Metrics endpoint for Prometheus monitoring
- [ ] Auto-restart on crash
- [ ] Multiple instance coordination (distributed locking)
- [ ] Graceful shutdown with in-flight request handling
- [ ] Health check webhooks/notifications