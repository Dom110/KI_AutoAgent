# 🤖 Development AI Assistant Strategy für KI AutoAgent

**Erstellt:** 2025-11-12  
**Version:** 1.0.0  
**Zielgruppe:** AI Developer (Claude) für KI AutoAgent Entwicklung  

---

## 📋 Workflow beim Entwickeln neuer Features

### Phase 1: **ANALYSE & DOKUMENTATION LESEN**

```
1. Dokumentation studieren
   ├─ PYTHON_BEST_PRACTICES.md (Python 3.13+ Standards)
   ├─ backend/CLAUDE.md (Architektur-Regeln)
   ├─ E2E_TESTING_GUIDE.md (Test-Prozess)
   ├─ PHASE_3C3_CONTEXT_SUMMARY_20251112.md (Aktuelle Phase)
   └─ Phase-spezifische Dokumentation

2. Quellcode analysieren
   ├─ Existierende Pattern studieren
   ├─ Test-Struktur verstehen
   ├─ Import-Dependencies checken
   └─ Code-Conventions identifizieren

3. Anforderungen klären (HITL)
   ├─ Was genau soll implementiert werden?
   ├─ Welche Dateien sind betroffen?
   ├─ Welche Dependencies existieren?
   └─ Wie sollen Tests aussehen?
```

### Phase 2: **IMPLEMENTIERUNG**

```
1. Kleine, isolierte Funktion schreiben
   ├─ Nicht alles auf einmal
   ├─ Jede Funktion <100 Zeilen
   ├─ Massives Logging (stdout/stderr)
   └─ Python 3.13+ Features nutzen

2. Syntax & Best Practices checken
   ├─ Type hints vollständig
   ├─ Error handling spezifisch
   ├─ Docstrings aussagekräftig
   └─ Keine Comments (nur für komplexe Logik)

3. Automatisch ausführen & testen
   ├─ pytest für Unit Tests
   ├─ mypy für Type Checking
   ├─ ruff für Linting
   └─ Logs analysieren

4. Log-Auswertung
   ├─ Stdout vollständig prüfen
   ├─ Fehler interpretieren
   ├─ Debug-Output analysieren
   └─ Fehler beheben
```

### Phase 3: **E2E TESTS (Layer 3b)**

**Diese Phase ist für WebSocket-Tests des AGENTEN selbst!**

```
1. Test-Workspace vorbereiten
   ├─ ~/TestApps/e2e_test_run/
   ├─ Alte Artefakte löschen
   ├─ Neuer Workspace erstellen
   └─ Isolation verifizieren

2. Backend starten (Layer 3a)
   ├─ python backend/workflow_v7_mcp.py
   ├─ Mit cwd=TEST_WORKSPACE (KRITISCH!)
   ├─ WebSocket auf Port 8002
   └─ Warten bis ready (3 sec)

3. WebSocket Test (Layer 3b)
   ├─ WebSocket Client verbinden
   ├─ Task senden
   ├─ Fortschritt monitoren
   └─ Validierungen durchführen

4. Auto-Validierung (Layer 4)
   ├─ Agent testet generierte App AUTO
   ├─ Nutzt Playwright Framework
   ├─ Berichtet Test-Ergebnisse
   └─ Ich sehe nur Ergebnis (nicht manuell)

5. Cleanup
   ├─ Bei Erfolg: Workspace behalten (für Inspektion)
   ├─ Bei Fehler: Logs archivieren, Workspace löschen
   └─ Debug-Info dokumentieren
```

### Phase 4: **DOKUMENTATION AKTUALISIEREN**

```
1. Code-Dokumentation
   ├─ Docstrings vervollständigen
   ├─ Komplexe Logik erklären
   └─ Type hints dokumentieren

2. Projekt-Dokumentation
   ├─ PHASE_3Cx_*.md aktualisieren
   ├─ Test-Resultate dokumentieren
   ├─ Neue Patterns erklären
   └─ Probleme & Lösungen festhalten

3. backend/CLAUDE.md
   ├─ Neue Features erklären
   ├─ Verwendungsbeispiele geben
   ├─ Konfigurationen dokumentieren
   └─ Known Issues notieren

4. Context-Zusammenfassung
   ├─ Wenn Chat-Länge > 80% → Neue Summary
   ├─ Alle Entscheidungen dokumentieren
   ├─ Next Steps klären
   └─ Wichtige Dateien referenzieren
```

---

## 🧪 E2E TEST ARCHITEKTUR (4 Layer)

**Wichtig:** Es gibt 4 Test-Ebenen - nicht nur eine!

### **Layer 2: Backend Tests** (Meine Entwicklung)
- `backend/tests/` - Unit Tests für Features
- `pytest` Framework
- **Wann:** Während Entwicklung
- **Beispiel:** `pytest backend/tests/test_error_recovery.py -v`

### **Layer 3b: E2E WebSocket Tests** (Agent-Tests)
- `test_e2e_*.py` im Root
- Verbinden sich via WebSocket zum Backend
- **Wann:** Nach Feature-Implementation
- **Beispiel:** `python3 test_e2e_app_creation.py`

### **Layer 4: E2E Testing Framework** (Automatisch im Agent)
- `backend/e2e_testing/` - Playwright Framework
- Agent nutzt automatisch
- **Wann:** Agent testet generierte App
- **Beispiel:** Agent startet automatisch (kein Manual Trigger)

**📖 Vollständig dokumentiert in: `TEST_ARCHITECTURE_LAYERS.md`**

---

## 🧪 E2E TEST PROZESS (Detailliert)

### 1. **Workspace Vorbereitung**

```python
import shutil
from pathlib import Path

TEST_WORKSPACE = Path.home() / "TestApps" / "e2e_test_run"

print(f"🧹 [E2E] Workspace wird vorbereitet...")
print(f"📍 Location: {TEST_WORKSPACE}")

# Alte Artefakte löschen
if TEST_WORKSPACE.exists():
    print(f"🧹 [E2E] Alte Workspace wird gelöscht...")
    shutil.rmtree(TEST_WORKSPACE)

# Neuer Workspace
TEST_WORKSPACE.mkdir(parents=True, exist_ok=True)
print(f"✅ [E2E] Workspace ist sauber und bereit")

# Isolation prüfen
assert not (TEST_WORKSPACE / "task-manager-app").exists()
print(f"✅ [E2E] Workspace ist isoliert")
```

### 2. **Backend Starten**

```python
import subprocess
import asyncio

print(f"🚀 [E2E] Backend wird gestartet...")

# Backend starten (mit workspace_path!)
process = await asyncio.create_subprocess_exec(
    "python", "backend/workflow_v7_mcp.py",
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd=str(TEST_WORKSPACE),  # 🎯 KRITISCH!
)

print(f"✅ [E2E] Backend PID: {process.pid}")

# Auf Ready warten
await asyncio.sleep(3)
print(f"✅ [E2E] Backend ist bereit")
```

### 3. **WebSocket Client**

```python
import websockets
import json

print(f"📡 [E2E] WebSocket Client wird verbunden...")

async def run_e2e():
    async with websockets.connect("ws://localhost:8002/ws/chat") as ws:
        print(f"✅ [E2E] WebSocket verbunden")
        
        # Task senden
        task = {
            "type": "task",
            "content": "Create a simple task manager app",
            "workspace_path": str(TEST_WORKSPACE)
        }
        
        print(f"📤 [E2E] Task wird gesendet...")
        await ws.send(json.dumps(task))
        
        # Fortschritt monitoren
        print(f"⏳ [E2E] Warte auf Response...")
        
        while True:
            message = await ws.recv()
            data = json.loads(message)
            
            # Fortschritt anzeigen
            if data.get("type") == "progress":
                progress = data.get("progress", 0)
                print(f"⏳ [E2E] Progress: {progress}%")
            
            # Fertig?
            if data.get("type") == "complete":
                print(f"✅ [E2E] Task erfolgreich")
                return data
            
            # Fehler?
            if data.get("type") == "error":
                print(f"❌ [E2E] Fehler: {data.get('error')}")
                raise Exception(data.get("error"))
```

### 4. **Validierungen**

```python
print(f"🔍 [E2E] Validierungen werden durchgeführt...")

# 1. Dateien im richtigen Workspace?
expected_files = ["README.md", "package.json", "src/"]
for file in expected_files:
    path = TEST_WORKSPACE / file
    if path.exists():
        print(f"✅ [E2E] Datei vorhanden: {file}")
    else:
        print(f"❌ [E2E] Datei FEHLT: {file}")
        raise AssertionError(f"Missing file: {file}")

# 2. Keine alten Artefakte?
old_app = TEST_WORKSPACE / "old-app"
if not old_app.exists():
    print(f"✅ [E2E] Keine alten Artefakte gefunden")
else:
    print(f"❌ [E2E] ALTE ARTEFAKTE GEFUNDEN: {old_app}")
    raise AssertionError("Old artifacts found!")

# 3. Korrekte Struktur?
assert (TEST_WORKSPACE / "README.md").is_file()
assert (TEST_WORKSPACE / "src").is_dir()
print(f"✅ [E2E] Struktur ist korrekt")

print(f"✅ [E2E] ALLE VALIDIERUNGEN BESTANDEN!")
```

### 5. **Cleanup**

```python
print(f"🧹 [E2E] Cleanup wird durchgeführt...")

# Bei Erfolg: Optional behalten
if test_passed:
    print(f"📦 [E2E] Workspace behalten für Inspektion: {TEST_WORKSPACE}")
    # Optional: Backup mit Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TEST_WORKSPACE.parent / f"test_success_{timestamp}"
    shutil.copytree(TEST_WORKSPACE, backup)
    print(f"📦 [E2E] Backup erstellt: {backup}")
else:
    # Bei Fehler: Löschen
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)
    print(f"✅ [E2E] Workspace gelöscht")

print(f"✅ [E2E] Cleanup abgeschlossen")
```

---

## 🔍 DEBUG STRATEGIE

### Log-Auswertung

```bash
# 1. Workspace Isolation prüfen
ls -la ~/TestApps/e2e_test_run/
# Sollte NUR neue Dateien enthalten!

# 2. Claude CLI CWD prüfen
grep "cwd" /tmp/debug.log
# Sollte zeigen: /Users/.../TestApps/e2e_test_run

# 3. Backend Logs prüfen
grep "workspace_path" /tmp/backend.log
# Sollte zeigen: workspace_path: /Users/.../TestApps/...

# 4. Fehler analysieren
grep -i "error\|exception\|failed" /tmp/backend.log
# Probleme identifizieren

# 5. Subprocess Output
ps aux | grep "claude"
# Claude CLI Prozesse checken
```

### Häufige Fehler

| ❌ Problem | 🔍 Debug | ✅ Fix |
|-----------|---------|-------|
| App schon vorhanden | CWD prüfen | `cwd=workspace_path` setzen |
| Dateien im dev repo | Alte Artefakte suchen | Workspace aufräumen |
| Claude findet alte Files | Backend Logs checken | workspace_path richtig? |
| Subprocess crasht | Raw Output lesen | CWD Parameter prüfen |
| Test hängt | Fortschritt monitoren | Timeout erhöhen |

---

## 📊 STDOUT LOGGING Standard

```python
# Format für alle Ausgaben:
# [PHASE] [STATUS] Message

# Beispiele:
print(f"🚀 [INIT] Konfiguration wird geladen...")
print(f"📡 [CONN] WebSocket verbindet...")
print(f"📤 [REQ]  Task wird gesendet...")
print(f"⏳ [WAIT] Response wird erwartet...")
print(f"✅ [OK]   Validierung bestanden")
print(f"❌ [ERR]  Fehler aufgetreten: {error}")
print(f"📊 [LOG]  Debug Info: {info}")
```

---

## 🎯 Integration-Checklist

### Code-Integration
- [ ] Imports sind richtig (MCP, nicht direkt)
- [ ] workspace_path wird gepassed
- [ ] subprocess cwd ist gesetzt
- [ ] Logging ist vollständig

### Test-Integration
- [ ] Unit Tests (backend/tests/)
- [ ] E2E Tests (isolierter Workspace)
- [ ] Alle Tests ✅ passing

### Dokumentation
- [ ] Code Docstrings
- [ ] backend/CLAUDE.md aktualisiert
- [ ] Phase-Dokumentation aktualisiert
- [ ] Entscheidungen dokumentiert

### Deployment
- [ ] Zero Regressions
- [ ] Alle Tests passing
- [ ] Logs analysiert
- [ ] Performance OK

---

## 📚 Wichtige Dateien

```
/Users/dominikfoert/git/KI_AutoAgent/
├── PYTHON_BEST_PRACTICES.md          ← Coding Standards
├── backend/CLAUDE.md                 ← Architektur Regeln
├── E2E_TESTING_GUIDE.md              ← E2E Test Prozess
├── PHASE_3C3_CONTEXT_SUMMARY_20251112.md ← Aktuelle Phase
├── PHASE_3C_QUICK_REFERENCE.md       ← Quick Lookup
├── backend/
│   ├── e2e_testing/                  ← E2E Framework
│   ├── tests/                        ← Unit Tests
│   ├── agents/integration/           ← Error Recovery Pattern
│   ├── core/error_recovery.py        ← Framework
│   └── workflow_v7_mcp.py            ← Main Entry
└── mcp_servers/                      ← Agent MCP Servers
```

---

## ✅ Checkliste für neues Feature

### Vor der Implementierung:
- [ ] Dokumentation gelesen
- [ ] Existierende Pattern verstanden
- [ ] Test-Strategie geklärt
- [ ] E2E Workspace vorbereitet

### Nach der Implementierung:
- [ ] Unit Tests ✅
- [ ] Linting ✅
- [ ] Type Checking ✅
- [ ] E2E Tests ✅
- [ ] Logs analysiert ✅
- [ ] Dokumentation aktualisiert ✅
- [ ] Keine Regressions ✅

---

**Nächste Schritte:**
1. Feature anfordern (was soll implementiert werden?)
2. Dokumentation analysieren
3. Tests schreiben (simulate zuerst)
4. Code implementieren
5. E2E Tests durchführen
6. Dokumentation aktualisieren

**Fragen?** Fragen Sie immer bei Unklarheiten! (HITL)
