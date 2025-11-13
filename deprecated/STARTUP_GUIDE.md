# 🚀 Quick Startup Guide

## The Right Way to Start the Server

```bash
python start_server.py
```

That's it! 🎉

## Why Not Direct Startup?

❌ **Don't do this:**
```bash
python backend/api/server_v7_mcp.py  # ❌ BLOCKED!
```

✅ **Do this instead:**
```bash
python start_server.py  # ✅ ALLOWED!
```

## What the Script Does

When you run `python start_server.py`, it automatically:

1. ✅ Checks Python version (3.13.8+)
2. ✅ Verifies environment configuration
3. ✅ Validates all dependencies
4. ✅ Checks if port 8002 is available
5. ✅ Cleans up any stale processes
6. ✅ Runs full system diagnostics
7. ✅ Starts the FastAPI server

## Options

```bash
# Check everything without starting
python start_server.py --check-only

# Use a different port
python start_server.py --port 8003

# Don't auto-cleanup existing processes
python start_server.py --no-cleanup

# Combine options
python start_server.py --port 8003 --no-cleanup
```

## Accessing the Server

```
WebSocket: ws://localhost:8002/ws/chat
Health Check: http://localhost:8002/health
Diagnostics: http://localhost:8002/diagnostics
```

## If You Get an Error

### "Direct Startup Not Allowed"
Use the startup script:
```bash
python start_server.py
```

### Port Already in Use
The script auto-cleans this up. Or use a different port:
```bash
python start_server.py --port 8003
```

### Dependencies Missing
Run with `--check-only` to see what's missing:
```bash
python start_server.py --check-only
```

### Environment Not Found
Create or verify: `~/.ki_autoagent/config/.env`

## For E2E Tests

Don't start the server in your test code. Instead:

1. Start server separately:
   ```bash
   python start_server.py
   ```

2. Connect via WebSocket in your tests:
   ```python
   async with websockets.connect("ws://localhost:8002/ws/chat") as ws:
       await ws.send(json.dumps({"type": "init", "workspace": "..."}))
       # ...
   ```

3. Server keeps running for all tests

## What's Being Enforced?

The server now **requires** startup via `start_server.py`. This ensures:

- 🔒 No accidental direct execution
- 📋 All checks always run
- 🛡️ Port conflicts prevented
- ✅ Dependencies validated
- 📊 System diagnostics captured

## Further Reading

- [Detailed Startup Enforcement Documentation](./STARTUP_ENFORCEMENT.md)
- [Port Management System](./PORT_MANAGEMENT.md)

## Quick Reference

| Task | Command |
|------|---------|
| Normal startup | `python start_server.py` |
| Check config only | `python start_server.py --check-only` |
| Use port 8003 | `python start_server.py --port 8003` |
| Skip port cleanup | `python start_server.py --no-cleanup` |
| Stop server | `Ctrl+C` |

## Need Help?

1. Check the startup output for error messages
2. Run `python start_server.py --check-only` to diagnose
3. Read [STARTUP_ENFORCEMENT.md](./STARTUP_ENFORCEMENT.md) for detailed info
4. Check [PORT_MANAGEMENT.md](./PORT_MANAGEMENT.md) for port issues

---

**Remember: Always use `python start_server.py` to start the server!**