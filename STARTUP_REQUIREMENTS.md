# 🔧 Startup Requirements - Detaillierte Anforderungen

**Version:** v7.0 Pure MCP  
**Date:** 2025-11-10  
**Author:** Code Analysis & Documentation Update

---

## 📋 Übersicht: 5 Kritische Startup-Checks

Der Server führt **5 Sicherheitschecks** aus, bevor er startet. Diese Checks sind **MANDATORY** und können nicht übersprungen werden.

```
┌─────────────────────────────────────────┐
│   STARTUP PROCESS (start_server.py)     │
├─────────────────────────────────────────┤
│ 1. Python Version Check                 │
│    ✅ PASSED: 3.13.8+                   │
├─────────────────────────────────────────┤
│ 2. Virtual Environment Check            │
│    ✅ PASSED: /venv/bin/activate        │
├─────────────────────────────────────────┤
│ 3. Project Root Check                   │
│    ✅ PASSED: /KI_AutoAgent             │
├─────────────────────────────────────────┤
│ 4. Startup Script Guard                 │
│    ✅ PASSED: start_server.py           │
├─────────────────────────────────────────┤
│ 5. Port Management & Cleanup            │
│    ✅ PASSED: Port 8002 available       │
├─────────────────────────────────────────┤
│ ✅ ALL CHECKS PASSED - STARTING SERVER  │
└─────────────────────────────────────────┘
```

---

## ✅ CHECK 1: Python Version (3.13.8+)

### Requirement
**Python 3.13.8 oder höher ist MANDATORY**

### Location in Code
`backend/api/server_v7_mcp.py:38-85`

### Why 3.13.8+?
Das Projekt nutzt moderne Python 3.13 Features:

1. **Native Type Unions mit `|`**
   ```python
   # Python 3.13+ syntax
   def func() -> str | int | None:
       pass
   
   # Alte syntax (Python < 3.13)
   from typing import Union
   def func() -> Union[str, int, None]:
       pass
   ```

2. **Pattern Matching (match/case)**
   ```python
   match command:
       case "research":
           return "research_agent"
       case "architect":
           return "architect_agent"
   ```

3. **Enhanced Error Messages**
   - Bessere Fehlermeldungen mit Context
   - Bessere Stack Traces

4. **Modern Asyncio Features**
   - Improved async/await
   - Better concurrent execution

### Check durchführen
```bash
# Prüfe aktuelle Python Version
python --version
# Output: Python 3.13.8

# Oder detailliert:
python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
# Output: 3.13.8
```

### Fehlerbehandlung
Wenn Python < 3.13.8:

```
❌ CRITICAL ERROR: PYTHON VERSION INCOMPATIBLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Current Python: 3.11.0
📍 Required: Python 3.13.8 or higher

⚠️  This project uses Python 3.13+ features:
   • Native type unions with | (not Union[])
   • Pattern matching (match/case)
   • Enhanced error messages
   • Modern asyncio features

✅ HOW TO FIX - Run from Virtual Environment:
   # Step 1: Go to project root
   cd /Users/dominikfoert/git/KI_AutoAgent
   
   # Step 2: Create new venv with Python 3.13+
   python3.13 -m venv venv_new
   
   # Step 3: Activate new venv
   source venv_new/bin/activate
   
   # Step 4: Install dependencies
   pip install -r backend/requirements.txt
   
   # Step 5: Start the server
   python start_server.py
```

---

## ✅ CHECK 2: Virtual Environment (MANDATORY)

### Requirement
**Venv MUSS aktiviert sein, bevor Server startet**

### Location in Code
`backend/utils/startup_guard.py` (if exists) oder `start_server.py`

### Why Virtual Environment?
Ein Virtual Environment isoliert:
- ✅ Python Version (3.13.8 wird erzwungen)
- ✅ Abhängigkeiten (keine Konflikte mit System-Packages)
- ✅ Projekt-spezifische Pakete (FastAPI, LangChain, etc.)

### Check durchführen
```bash
# Venv ist aktiviert wenn du (venv) in der Shell siehst:
(venv) user@host KI_AutoAgent %

# Oder prüfe:
echo $VIRTUAL_ENV
# Output: /Users/dominikfoert/git/KI_AutoAgent/venv

# Oder:
which python | grep venv
# Output: /Users/dominikfoert/git/KI_AutoAgent/venv/bin/python
```

### Fehlerbehandlung
Wenn Venv nicht aktiviert:

```bash
# Aktiviere Venv
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
# Jetzt solltest du (venv) prompt sehen

# Dann:
python start_server.py
```

---

## ✅ CHECK 3: Project Root (/KI_AutoAgent)

### Requirement
**Server MUSS von /Users/dominikfoert/git/KI_AutoAgent laufen**

### Location in Code
`backend/utils/startup_guard.py` oder `start_server.py`

### Why Project Root?
Der Server braucht diese relativen Pfade:
- `backend/` - Quellcode
- `mcp_servers/` - MCP Server
- `venv/` - Virtual Environment
- `config/` - Konfiguration
- `.ki_autoagent/` - Global Config

### Check durchführen
```bash
# Prüfe aktuelles Verzeichnis
pwd
# Output: /Users/dominikfoert/git/KI_AutoAgent

# Prüfe ob richtige Files existieren
ls backend/api/server_v7_mcp.py
ls mcp_servers/research_agent_server.py
# Wenn beide existieren → richtig!
```

### Fehlerbehandlung
Wenn falsch platziert:

```bash
# Geh zum richtigen Verzeichnis
cd /Users/dominikfoert/git/KI_AutoAgent

# Starte von hier
python start_server.py
```

---

## ✅ CHECK 4: Startup Script Guard

### Requirement
**start_server.py MUSS verwendet werden (nicht direkt python backend/api/server_v7_mcp.py)**

### Location in Code
`backend/api/server_v7_mcp.py:88`

```python
if os.environ.get('KI_AUTOAGENT_STARTUP_SCRIPT') != 'true':
    print("❌ CRITICAL ERROR: DIRECT STARTUP NOT ALLOWED")
    print("🚫 Server cannot be started directly")
    print("✅ HOW TO FIX: Start the server using the provided script:")
    print("   python start_server.py")
    sys.exit(1)
```

### Why This Guard?
Wenn Server direkt startet, werden übersprungen:
- ❌ Port Cleanup (alter Prozess auf 8002 bleibt)
- ❌ Port Konflikt Check (keine Auto-Fallback auf 8003)
- ❌ System Diagnostics (Health Checks nicht durchgeführt)
- ❌ Dependencies Validation (Pakete nicht geprüft)
- ❌ Environment Setup (Env Vars nicht validiert)

### Check durchführen
```bash
# ❌ FALSCH - weigert sich zu starten:
python backend/api/server_v7_mcp.py
# Error: DIRECT STARTUP NOT ALLOWED

# ✅ RICHTIG - läuft alle Checks:
python start_server.py
# ✅ All checks passed
```

### Fehlerbehandlung
Wenn Error "DIRECT STARTUP NOT ALLOWED":

```bash
# FALSCH:
python backend/api/server_v7_mcp.py

# RICHTIG:
python start_server.py
```

---

## ✅ CHECK 5: Port Management & Cleanup

### Requirement
**Port 8002 muss verfügbar sein (oder Auto-Fallback auf 8003+)**

### Location in Code
`start_server.py` (~50 Zeilen Code für Port Management)

### What start_server.py tut
```python
def find_and_cleanup_port(port: int = 8002):
    """
    1. Prüft ob Port 8002 besetzt ist
    2. Wenn ja: Findet PID des Prozesses
    3. Killed alten Prozess sauber (SIGTERM)
    4. Wartet kurz (cleanup)
    5. Startet Server auf Port 8002
    
    Falls Port immer noch besetzt:
    6. Fallback auf Port 8003, 8004, 8005, etc.
    """
```

### Flags
```bash
# Normaler Start (Auto-Fallback auf 8003+ wenn 8002 besetzt)
python start_server.py

# Mit spezifischem Port
python start_server.py --port 8003

# Nur Checks durchführen (nicht starten)
python start_server.py --check-only

# Force-Kill alten Prozess auf Port 8002
python start_server.py --force-kill-port

# Verbose Logging
python start_server.py --verbose
```

### Check durchführen
```bash
# Prüfe ob Port 8002 frei ist
lsof -i :8002
# Wenn keine Output → Port ist frei

# Oder:
netstat -tulpn | grep :8002
# Wenn keine Output → Port ist frei
```

### Fehlerbehandlung
Wenn Port 8002 besetzt:

```bash
# start_server.py killed automatisch alten Prozess
# Falls nicht, manuell:

# Finde PID auf Port 8002
lsof -i :8002
# Output: PID 12345

# Kill den Prozess
kill -9 12345

# Starte Server neu
python start_server.py
```

---

## 🎯 Vollständige Startup-Sequenz

```
1. user@host ~/KI_AutoAgent % cd /Users/dominikfoert/git/KI_AutoAgent
   ✅ CHECK 3: Project root correct

2. user@host ~/KI_AutoAgent % source venv/bin/activate
   (venv) user@host ~/KI_AutoAgent %
   ✅ CHECK 2: Virtual environment active

3. (venv) user@host ~/KI_AutoAgent % python start_server.py
   ✅ CHECK 1: Python 3.13.8+ detected
   ✅ CHECK 4: Running via start_server.py
   ✅ CHECK 5: Port 8002 available
   
   🚀 Starting MCP Servers...
   ✅ openai_server.py initialized
   ✅ research_agent_server.py initialized
   ✅ architect_agent_server.py initialized
   ✅ codesmith_agent_server.py initialized
   ✅ reviewfix_agent_server.py initialized
   ✅ responder_agent_server.py initialized
   ✅ perplexity_server.py initialized
   ✅ memory_server.py initialized
   ✅ build_validation_server.py initialized
   ✅ file_tools_server.py initialized
   ✅ tree_sitter_server.py initialized
   
   🎉 KI AutoAgent v7.0 Ready!
   📡 WebSocket: ws://localhost:8002/ws/chat
```

---

## 🚨 Troubleshooting

### Problem: "Python version incompatible"
**Solution:** Activate venv with Python 3.13+
```bash
source venv/bin/activate
python --version  # Should show 3.13.8+
```

### Problem: "Not running in virtual environment"
**Solution:** Activate venv
```bash
cd /Users/dominikfoert/git/KI_AutoAgent
source venv/bin/activate
```

### Problem: "DIRECT STARTUP NOT ALLOWED"
**Solution:** Use start_server.py
```bash
python start_server.py  # ✅ Correct
# NOT: python backend/api/server_v7_mcp.py ❌
```

### Problem: "Project root error"
**Solution:** Start from project root
```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python start_server.py
```

### Problem: "Port 8002 already in use"
**Solution:** start_server.py handles this automatically!
```bash
python start_server.py
# Falls 8002 besetzt: Fallback zu 8003
# Falls 8003 besetzt: Fallback zu 8004
# etc.
```

---

## ✅ Verifikation

Alle Checks erfolgreich wenn:

```
✅ Python version: 3.13.8 or higher
✅ Virtual environment: Active (/venv/bin/activate)
✅ Project root: /Users/dominikfoert/git/KI_AutoAgent
✅ Startup method: python start_server.py
✅ Port: 8002 available (or fallback to 8003+)
✅ MCP Servers: All 11 initialized
✅ WebSocket: ws://localhost:8002/ws/chat
✅ API Keys: OPENAI_API_KEY and PERPLEXITY_API_KEY set
```

Server läuft dann in production-ready Mode!

---

**Updated:** 2025-11-10  
**Status:** ✅ Complete  
**Related:** START_HERE.md, README.md, MCP_MIGRATION_FINAL_SUMMARY.md
