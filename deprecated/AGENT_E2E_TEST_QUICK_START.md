# 🤖 KI Agent E2E WebSocket Test - QUICK START

**Wie man den KI Agent korrekt testet**

---

## 🎯 Kurz & Knapp

Der Agent wird über **WebSocket** getestet. Es gibt 2 Optionen:

| Option | Für | Kommando |
|--------|-----|----------|
| **Manual Interactive** | Entwicklung & Debugging | `python test_agent_manual_interactive.py` |
| **Automated E2E Test** | CI/CD & Validierung | `python test_agent_websocket_real_e2e.py` |

---

## 🚀 SCHNELLSTART (5 Minuten)

### Schritt 1: Terminal 1 - Backend starten

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python start_server.py --port=8002
```

**Erwartet:** Backend läuft auf `ws://localhost:8002/ws/chat` ✅

```
✓ WebSocket server started on port 8002
✓ Ready for connections
```

### Schritt 2: Terminal 2 - Agent interaktiv testen

```bash
cd /Users/dominikfoert/git/KI_AutoAgent
python test_agent_manual_interactive.py
```

**Was passiert:**
1. ✅ Workspace wird erstellt (`~/TestApps/manual_interactive_test/...`)
2. ✅ WebSocket Verbindung zum Backend
3. ✅ Interaktive Menü mit Test-Szenarien
4. ✅ Du wählst Szenario → Agent generiert App
5. ✅ Echtzeit-Monitoring der Agent-Ausgaben
6. ✅ Generierte Dateien werden angezeigt

**Output:**
```
🔗 Connecting to agent at ws://localhost:8002/ws/chat...
✅ Connected and initialized!

═══ Test Scenarios ═══
1. Simple React Todo App
2. React Dashboard
3. Contact Form
4. Custom Request

Select scenario (1-4) or 'q' to quit: 
```

### Schritt 3: Szenario wählen & beobachten

```
Select scenario (1-4) or 'q' to quit: 1

📤 Sending request #1...

📨 Monitoring agent responses...
(Press Ctrl+C to stop)

ℹ️  Processing request...
⏳ Supervisor analyzing requirements...
⏳ Codesmith creating project structure...
✓ Created: package.json
⏳ ComponentWriter generating components...
✓ Generated: TodoList.jsx, TodoItem.jsx
✓ Generated: AddTodoForm.jsx
⏳ E2E Test Generator creating tests...
✓ Generated: App.test.js
⏳ ReviewFix validating code...
✅ COMPLETE: App generated successfully!

📁 Generated Files:
Total: 47 files
  .js                :  12 files
  .json              :   3 files
  .jsx               :   8 files
  .css               :   5 files
  .md                :   1 files

Test another scenario? (y/n): 
```

---

## 🔍 Was wird während des Tests überprüft?

### ✅ PHASE 1: SETUP
- [ ] Workspace ist sauber (außerhalb Dev Repo)
- [ ] Backend läuft auf richtigem Port
- [ ] Keine alten Test-Artefakte

### ✅ PHASE 2: VERBINDUNG
- [ ] WebSocket Connection hergestellt
- [ ] Init-Nachricht mit `workspace_path` gesendet
- [ ] Backend bestätigt Init mit `success=true`

### ✅ PHASE 3: REQUEST
- [ ] Request wird an Agent gesendet
- [ ] Message-ID ist korrekt
- [ ] Agent empfängt Request (im Log zu sehen)

### ✅ PHASE 4: EXECUTION
- [ ] Agent antwortet mit Status-Messages
- [ ] Mehrere Agents werden nacheinander aufgerufen:
  - Supervisor (parst Request)
  - Codesmith (erstellt Struktur)
  - ComponentWriter (generiert Code)
  - E2E Generator (erstellt Tests)
  - ReviewFix (validiert Code)
- [ ] Keine ERROR-Messages

### ✅ PHASE 5: RESULTS
- [ ] Workflow completed Message
- [ ] Dateien wurden generiert
- [ ] App-Struktur ist korrekt
  - `package.json` vorhanden
  - `src/` Verzeichnis
  - README.md

---

## 🏃 AUTOMATED E2E TEST (CI/CD)

Für automatisierte Tests in CI/CD Pipeline:

```bash
# Führe automatisierten Test aus
python test_agent_websocket_real_e2e.py

# Exit-Code:
# 0 = SUCCESS ✅
# 1 = FAILURE ❌
```

**Validierungen:**
- ✅ Workspace initial clean
- ✅ Agent connection works
- ✅ Messages received
- ✅ No errors in responses
- ✅ Workflow completed
- ✅ Files generated
- ✅ App structure valid

**Output:**
```
======================================================================
🤖 STARTING KI AGENT E2E WEBSOCKET TEST
======================================================================

📋 PHASE 1: SETUP
✅ Workspace isolation verified

📋 PHASE 2: CONNECT TO AGENT
✅ Agent connection successful

📋 PHASE 3: REQUEST APP GENERATION
📤 Sending request #1: Create a React Todo Application...

📋 PHASE 4: MONITOR AGENT EXECUTION
📨 Received: status - Processing request...
📨 Received: progress - Supervisor analyzing...
...

📋 PHASE 5: VALIDATE RESULTS
✅ Received 42 messages from agent
✅ No critical errors found
✅ Workflow completed successfully

📋 PHASE 6: VERIFY GENERATED FILES
✅ 47 files generated
✅ App structure looks correct

📋 PHASE 7: TEST SUMMARY
⏱️  Test duration: 85.3 seconds
📨 Messages received: 42
📁 Workspace: /Users/.../TestApps/e2e_websocket_test/20250215_143022
   File types: {'.jsx': 8, '.js': 12, '.json': 3, '.css': 5, '.md': 1}

======================================================================
✅ E2E TEST PASSED!
======================================================================
```

---

## 🐛 DEBUGGING - Wenn etwas schiefgeht

### Problem 1: Connection refused

```
❌ Connection failed: [Errno 111] Connection refused
Is the backend running?
Start it with: python start_server.py --port=8002
```

**Lösung:**
```bash
# Terminal 1 - Backend starten
python start_server.py --port=8002

# Warte bis:
# ✓ Server started on port 8002
# ✓ Ready for connections
```

### Problem 2: Init failed

```
❌ Init failed: {'success': false, 'error': 'Invalid workspace'}
```

**Lösung:**
- Workspace muss außerhalb des Dev Repos sein ✅
- Workspace muss existieren und schreibbar sein ✅
- Pfad muss absolut sein (nicht relativ) ✅

### Problem 3: No messages received

```
❌ No messages received!
```

**Debugging:**
```bash
# 1. Check Backend-Logs
tail -f /tmp/v7_server.log

# 2. Check WebSocket connection
wscat -c ws://localhost:8002/ws/chat

# 3. Check request format
python -c "
import json
msg = {'type': 'message', 'content': 'test'}
print(json.dumps(msg))
"
```

### Problem 4: Agent errors

```
✗ ERROR: Claude API rate limit exceeded
✗ ERROR: Invalid workspace path
✗ ERROR: Codesmith crashed
```

**Lösung:**
- Check API Credits/Rate Limits
- Check `workspace_path` ist korrekt
- Check Backend Logs für vollständigen Error

---

## 📊 MONITORING IN REAL-TIME

### Terminal 2 - Live Backend Logs

```bash
tail -f /tmp/v7_server.log

# Schau nach:
# ✓ ws_client_connected
# ✓ workspace_path: /Users/.../TestApps/...
# ✓ supervisor_started
# ✓ codesmith_started
# ✓ component_writer_started
# ✓ e2e_generator_started
# ✓ reviewfix_started
# ✓ workflow_completed
```

### Terminal 3 - File Generation beobachten

```bash
# Watch workspace during test
watch -n 1 'ls -la ~/TestApps/manual_interactive_test/*/

# Oder mit tree
tree ~/TestApps/manual_interactive_test/ --dirsfirst
```

---

## ✅ ERFOLGS-KRITERIEN

Ein Agent E2E Test ist **ERFOLGREICH** wenn:

| Kriterium | Beschreibung | Check |
|-----------|-------------|-------|
| **Connection** | Agent antwortet auf WebSocket | ✅ Messages received > 0 |
| **Execution** | Alle Workflow-Phasen durchlaufen | ✅ Completion message |
| **Code Generation** | Quellcode wurde generiert | ✅ .js/.jsx/.json Dateien |
| **Structure** | App-Struktur ist valide | ✅ package.json + src/ |
| **No Errors** | Keine kritischen Fehler | ✅ Kein ERROR in Messages |
| **Tests** | E2E Tests wurden generiert | ✅ .test.js Dateien |
| **Artifact Location** | Dateien im richtigen Workspace | ✅ ~/TestApps/... ✅ |

---

## 🚨 FAILURE DETECTION

Ein Test **SCHLÄGT FEHL** wenn:

| Fehler | Bedeutung | Lösung |
|--------|-----------|--------|
| Connection timeout | Agent antwortet nicht | Backend neustarten |
| 0 messages received | Agent sent nothing | Check Logs |
| ERROR in response | Agent encountered problem | Fix Agent Issue |
| No files generated | App creation failed | Check Request |
| Files in Dev Repo | Workspace isolation failed | Fix workspace_path |
| Test timeout (>120s) | Agent hängt | Kill + restart |

**RULE: Jeder Fehler = Test FAILED. Keine Exceptions!**

---

## 📈 PERFORMANCE EXPECTATIONS

| Metrik | Expected | Max |
|--------|----------|-----|
| Connection | < 1s | 5s |
| First response | < 5s | 10s |
| Total execution | 60-120s | 300s |
| Message count | 20-50 | 100+ |
| Files generated | 30-100 | ∞ |

---

## 🔄 ZYKLUS: Entwicklung → Test → Fix

### 1. **Entwicklung**: Agent Code ändern

```python
# backend/agents/supervisor_agent.py
# ... make changes ...
```

### 2. **Test**: Agent testen

```bash
# Terminal 1: Backend mit neuem Code
python start_server.py --port=8002

# Terminal 2: Test ausführen
python test_agent_manual_interactive.py

# Oder automatisiert:
python test_agent_websocket_real_e2e.py
```

### 3. **Validation**: Ergebnisse prüfen

```
✅ PASSED: Agent works correctly
❌ FAILED: Fix the issue
```

### 4. **Repeat**: Zurück zu Schritt 1

---

## 🎓 BEISPIELE

### Beispiel 1: Request Processing

```
USER: "Create a React Todo App"
↓
🔗 WebSocket Message gesendet
↓
📨 Agent empfängt
↓
ℹ️  Status: Processing request...
ℹ️  Status: Supervisor analyzing...
ℹ️  Status: Codesmith creating structure...
ℹ️  Status: ComponentWriter generating components...
ℹ️  Status: E2E Generator creating tests...
ℹ️  Status: ReviewFix validating...
↓
✅ COMPLETE: App generated!
↓
📁 Files created in workspace
```

### Beispiel 2: Error Handling

```
USER: "Create a [WEIRD REQUEST]"
↓
🔗 WebSocket Message gesendet
↓
📨 Agent empfängt
↓
ℹ️  Status: Processing...
✗ ERROR: Invalid request format
↓
❌ TEST FAILED (Error detected!)
```

---

## 🔗 Related Documentation

- **E2E Testing Guide**: `E2E_TESTING_GUIDE.md`
- **Critical Failure Instructions**: `CRITICAL_FAILURE_INSTRUCTIONS.md`
- **System Architecture**: `CURRENT_SYSTEM_STATUS_v7.0.md`
- **WebSocket Integration**: See backend `/ws/chat` endpoint

---

## ❓ FAQ

**Q: Kann ich im Development Repo testen?**  
A: NEIN! ❌ Workspace muss in `~/TestApps/` sein. Siehe Testing Guide.

**Q: Wie lange dauert ein Test?**  
A: 60-120 Sekunden normalerweise. Max 300 Sekunden.

**Q: Was wenn der Agent hängt?**  
A: Test timeout nach 120s. Ctrl+C zum Abbrechen. Backend neustarten.

**Q: Kann ich mehrere Tests gleichzeitig laufen lassen?**  
A: Ja, aber auf verschiedenen Ports. Z.B. 8002, 8003, 8004...

**Q: Wo sehe ich die generierten Dateien?**  
A: In `~/TestApps/manual_interactive_test/TIMESTAMP/APPNAME/`

**Q: Kann ich den Test automatisieren?**  
A: Ja! Nutze `test_agent_websocket_real_e2e.py` für CI/CD.

---

**Version**: 1.0  
**Last Updated**: 2025-02-15  
**Status**: READY FOR TESTING ✅