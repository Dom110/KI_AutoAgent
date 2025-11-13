# 🚀 KI AutoAgent v7.0 - SERVER STARTUP GUIDE

## ⚡ Quick Start (30 seconds)

```bash
# 1. Go to project directory
cd /Users/dominikfoert/git/KI_AutoAgent

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start the server
python start_server.py
```

**That's it!** Server will be running on `http://0.0.0.0:8002` ✅

---

## ✅ Startup Verification

The startup process automatically checks:

```
Step 1: Checking Python Version...
   ✅ Python 3.13.9

Step 2: Checking Environment...
   ✅ Environment file: /Users/dominikfoert/.ki_autoagent/config/.env

Step 3: Checking Dependencies...
   ✅ fastapi
   ✅ uvicorn
   ✅ websockets
   ✅ langgraph
   ✅ langchain_openai
   ✅ pydantic

Step 4: Checking Port 8002...
   ✅ AVAILABLE

Step 5: Cleaning up port if needed...
   ✅ Port 8002 is available

Step 6: Running Full Diagnostics...
   ✅ OPENAI_API_KEY: Valid
   ⚠️ PERPLEXITY_API_KEY: Connectivity uncertain (HTTP 405) - Will attempt anyway

✅ ALL CHECKS PASSED - READY TO START SERVER
```

---

## 📋 STARTUP OPTIONS

### Option 1: Standard Start
```bash
python start_server.py
```
- Checks everything
- Auto-cleans port if needed
- Starts server on port 8002
- Logs everything to console

### Option 2: Custom Port
```bash
python start_server.py --port 8003
```
- Useful if port 8002 is locked
- Server will run on 8003 instead

### Option 3: Diagnostics Only (No Server)
```bash
python start_server.py --check-only
```
- Runs all checks but doesn't start server
- Perfect for debugging startup issues
- Exit code 0 = all good, 1 = problem found

### Option 4: No Auto-Cleanup
```bash
python start_server.py --no-cleanup
```
- Doesn't kill existing processes on port
- Useful if port is already in use and you want to keep it

---

## ⚠️ REQUIRED: Virtual Environment

**The server REQUIRES a virtual environment!**

### If You Get This Error:
```
❌ CRITICAL ERROR: NOT RUNNING IN VIRTUAL ENVIRONMENT
```

### Fix It:
```bash
# 1. Make sure you're in the right directory
cd /Users/dominikfoert/git/KI_AutoAgent

# 2. Activate venv
source venv/bin/activate

# 3. Verify (you should see (venv) at prompt)
(venv) $ python start_server.py
```

---

## 🔑 REQUIRED: Environment Configuration

**You need:** `/Users/dominikfoert/.ki_autoagent/config/.env`

```ini
# .env file format
OPENAI_API_KEY=sk-proj-...
PERPLEXITY_API_KEY=pplx-...
```

### If You Get This Error:
```
❌ Environment file not found: /Users/dominikfoert/.ki_autoagent/config/.env
```

### Fix It:
```bash
# 1. Create directory
mkdir -p ~/.ki_autoagent/config

# 2. Create .env file with your keys
cat > ~/.ki_autoagent/config/.env << 'EOF'
OPENAI_API_KEY=your-key-here
PERPLEXITY_API_KEY=your-key-here
EOF

# 3. Verify permissions
chmod 600 ~/.ki_autoagent/config/.env
```

---

## 🔗 API Keys

### OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy and paste into `.env`

**⚠️ Rate Limit Note:** If you get `429 - insufficient_quota` error, your account is out of credits.  
→ Add credits at: https://platform.openai.com/account/billing/overview

### Perplexity API Key
1. Go to: https://www.perplexity.ai/
2. Get API key from settings
3. Copy and paste into `.env`

---

## 📊 REAL-TIME MONITORING

### In One Terminal - Start Server:
```bash
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
python start_server.py
```

### In Another Terminal - Monitor Logs:
```bash
# Watch for OpenAI calls
tail -f server_startup.log | grep -i "openai\|call\|error"

# Watch for all activity
tail -f server_startup.log

# Watch only errors
tail -f server_startup.log | grep -i "error\|failed\|404\|429"
```

---

## 🧪 TEST SERVER AFTER STARTUP

### Using WebSocket (CLI):
```bash
# First install websocat if needed
brew install websocat

# Connect to server
websocat ws://localhost:8002/ws/chat

# Send init message
{"type": "init", "workspace": "/Users/dominikfoert/TestApps/test"}

# Should see: {"type": "initialized", "message": "..."}
```

### Using Python:
```python
import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8002/ws/chat") as ws:
        # Initialize
        await ws.send(json.dumps({
            "type": "init",
            "workspace": "/Users/dominikfoert/TestApps/test"
        }))
        
        # Get response
        response = await ws.recv()
        print(response)

asyncio.run(test())
```

### Using cURL (HTTP):
```bash
# Health check
curl http://localhost:8002/health

# Should return: {"status": "ok"}
```

---

## 🐛 TROUBLESHOOTING

### Problem: "Port 8002 already in use"

```bash
# Find what's using the port
lsof -i :8002

# Kill it
kill -9 $(lsof -t -i:8002)

# Or use --no-cleanup flag to skip auto-cleanup
python start_server.py --port 8003
```

### Problem: "ImportError: No module named..."

```bash
# Update pip and reinstall requirements
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Problem: "OPENAI_API_KEY not found"

```bash
# Verify .env file exists
ls -la ~/.ki_autoagent/config/.env

# Check contents (should have key)
cat ~/.ki_autoagent/config/.env

# Verify server loaded it
grep "Loaded API keys" server_startup.log
```

### Problem: "429 - insufficient_quota"

```bash
# 1. Check your OpenAI account
# https://platform.openai.com/account/billing/overview

# 2. Add credits via payment method

# 3. Check usage
# https://platform.openai.com/account/usage/overview

# 4. Try with a cheaper model temporarily
# Edit: backend/core/supervisor_mcp.py
# Change: model="gpt-3.5-turbo" (line 168)
```

---

## 🎯 STARTUP MARKERS

The server sets these environment variables after successful startup:

```python
# Set by start_server.py
os.environ['KI_AUTOAGENT_STARTUP_SCRIPT'] = 'true'
os.environ['KI_AUTOAGENT_SERVER_ROOT'] = '/Users/dominikfoert/git/KI_AutoAgent'
```

These are verified by:
- `backend/utils/startup_guard.py`
- `backend/core/supervisor_mcp.py`
- `backend/api/server_v7_mcp.py`

---

## 📡 ENDPOINTS AFTER STARTUP

```
WebSocket Chat:
  ws://localhost:8002/ws/chat

Health Check:
  GET http://localhost:8002/health

Diagnostics:
  GET http://localhost:8002/diagnostics

OpenAPI Docs:
  http://localhost:8002/docs

ReDoc:
  http://localhost:8002/redoc
```

---

## 🔒 VIRTUAL ENVIRONMENT CHECK

The server verifies virtual environment at STARTUP, checking:

1. **VIRTUAL_ENV environment variable** is set
   ```bash
   echo $VIRTUAL_ENV
   # Should show: /Users/dominikfoert/git/KI_AutoAgent/venv
   ```

2. **Activation required BEFORE script execution**
   ```bash
   # ✅ CORRECT
   source venv/bin/activate
   python start_server.py

   # ❌ WRONG
   python start_server.py  # Without activating venv first
   ```

3. **Startup Guard Module enforces this**
   ```python
   # At module import time, checks:
   from backend.utils.startup_guard import check_startup_method
   check_virtual_environment()  # Fails if VIRTUAL_ENV not set
   ```

---

## 💡 PRO TIPS

### 1. Use Screen/tmux for Long-Running Server
```bash
# Start in background
tmux new-session -d -s autoagent "cd /Users/dominikfoert/git/KI_AutoAgent && source venv/bin/activate && python start_server.py"

# Re-attach
tmux attach-session -t autoagent

# Detach
Ctrl+B then D
```

### 2. Log Everything
```bash
# All logs to file
python start_server.py > server.log 2>&1 &
tail -f server.log
```

### 3. Monitor Real-Time OpenAI Calls
```bash
# Show only OpenAI API calls
grep -E "OPENAI API CALL|Error Type|Total OpenAI calls" server_startup.log

# Count calls per minute
grep "OPENAI API CALL" server_startup.log | wc -l
```

### 4. Test Rate Limiting
```bash
# See how server handles rapid requests
for i in {1..5}; do curl http://localhost:8002/health & done

# Watch logs for rate limit handling
grep -i "rate\|wait\|quota" server_startup.log
```

---

## ✨ SUCCESS INDICATORS

When server starts successfully, you'll see:

```
✅ Loaded API keys from: /Users/dominikfoert/.ki_autoagent/config/.env
✅ OPENAI_API_KEY: Valid
⚠️ PERPLEXITY_API_KEY: Connectivity uncertain - Will attempt anyway
✅ ALL CHECKS PASSED - READY TO START SERVER

🚀 KI AutoAgent v7.0 - STARTUP
🎯 Architecture: Supervisor Pattern + Pure MCP Protocol
📡 WebSocket endpoint: ws://localhost:8002/ws/chat
✅ MCP Servers (will start on first request):
   - openai_server.py
   - research_agent_server.py
   - architect_agent_server.py
   - codesmith_agent_server.py
   - reviewfix_agent_server.py
   - responder_agent_server.py
   + utility servers

INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

---

## 🎓 UNDERSTANDING THE PURE MCP ARCHITECTURE

- **Agents are MCP servers** - Separate processes communicating via JSON-RPC
- **Supervisor makes all decisions** - Central orchestrator via LLM
- **Communication is async** - WebSockets for client, stdio for MCP
- **Lazy startup** - MCP servers start on first workflow execution
- **Comprehensive logging** - Every API call tracked with details

---

## 📞 SUPPORT

For issues, check:
1. `/PRODUCTION_STATUS.md` - Full system status report
2. `server_startup.log` - Startup logs with all details
3. Grep for "ERROR" or "429" in logs to find specific issues

---

*Last Updated: 2025-11-04*  
*Version: KI AutoAgent v7.0*