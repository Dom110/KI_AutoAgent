# KI AutoAgent - Claude Instructions

## 📋 Dokumentations-Index

Die vollständige Dokumentation wurde in separate Dateien ausgelagert für bessere Wartbarkeit:

### 🔴 Grundlegende Regeln
- **[ASIMOV-REGELN](.kiautoagent/docs/ASIMOV_RULES.md)** - Absolute und unveränderliche Gesetze
  - Keine Fallbacks ohne dokumentierten Grund
  - Vollständige Implementierung
  - Globale Fehlersuche

### 🏗️ Architektur & Struktur
- **[ARCHITECTURE](.kiautoagent/docs/ARCHITECTURE.md)** - System-Architektur und Ordnerstruktur
  - Python Backend vs. TypeScript Frontend
  - Standardisierte Projekt-Ordner
  - Kommunikations-Protokolle

### 🤖 KI-Modelle
- **[MODEL_VERSIONS](.kiautoagent/docs/MODEL_VERSIONS.md)** - Claude & GPT Model Versionen
  - Aktuelle Model IDs
  - OpusArbitrator Konfliktlösung
  - Performance-Vergleiche

### 🤝 Agent Collaboration System (NEW v5.1)
- **[AGENT_COLLABORATION](.kiautoagent/docs/AGENT_COLLABORATION.md)** - Agenten-Zusammenarbeit
  - Reviewer → Fixer → Reviewer Zyklus
  - CodeSmith → Research Kollaboration
  - Dynamische Workflow-Modifikation
- **[ORCHESTRATOR_LOOPBACK](.kiautoagent/docs/ORCHESTRATOR_LOOPBACK.md)** - Loop-Back Pattern
  - Re-Planning Mechanismus
  - State Flag Management
  - Routing Priority System
- **[LANGGRAPH_WORKFLOW](.kiautoagent/docs/LANGGRAPH_WORKFLOW.md)** - LangGraph Integration
  - State Management Deep Dive
  - Conditional Routing Patterns
  - Dynamic Step Addition
- **[FIXES_SESSION_2025_10_02](.kiautoagent/docs/FIXES_SESSION_2025_10_02.md)** - Session Fixes
  - Settings → .env Auto-Sync
  - Workflow Completion Bug Fix
  - Complete Collaboration System

---

## 🚀 Quick Start für Claude

### Aktuelle Version
**v5.0.0-unstable** - LangGraph Integration & Agent-to-Agent Communication

### Wichtigste Punkte:

1. **ASIMOV-REGELN befolgen** (siehe [ASIMOV_RULES.md](.kiautoagent/docs/ASIMOV_RULES.md))
   - Keine Fallbacks ohne Grund
   - Vollständige Implementierung
   - Globale Fehlersuche

2. **Python Backend Architektur** (siehe [ARCHITECTURE.md](.kiautoagent/docs/ARCHITECTURE.md))
   - ALLE Agents in `backend/agents/`
   - TypeScript NUR für UI
   - WebSocket auf Port 8001

3. **venv immer nutzen**
   ```bash
   source /Users/dominikfoert/git/KI_AutoAgent/venv/bin/activate
   ```

4. **Standardisierter Ordner**
   - Verwende `.kiautoagent` (lowercase mit k)
   - NICHT `.ki_autoagent` oder andere Varianten

---

## 🎯 Aktuelle System-Konfiguration

### Server
- **Backend**: FastAPI auf Port 8001
- **Frontend**: VS Code Extension
- **WebSocket**: ws://localhost:8001/ws/chat

### ⚠️ Server Management - WICHTIG!

**NIEMALS `kill -9` verwenden!** Der Server muss graceful beendet werden!

#### ✅ RICHTIGE Methode (Graceful Shutdown):
```bash
# Methode 1: Über API (EMPFOHLEN)
curl -X POST http://localhost:8001/shutdown

# Methode 2: Python Script
python -c "import requests; requests.post('http://localhost:8001/shutdown')"

# Methode 3: SIGTERM (graceful)
kill $(lsof -ti :8001)
```

#### ❌ FALSCHE Methode:
```bash
# NIEMALS verwenden - unterbricht Workflows und korruptiert State!
kill -9 $(lsof -ti :8001)  # ❌ FALSCH!
lsof -ti :8001 | xargs kill -9  # ❌ FALSCH!
pkill -9 -f "server_langgraph"  # ❌ FALSCH!
```

#### Warum Graceful Shutdown wichtig ist:
- **Workflow State**: Aktive Workflows werden sauber beendet
- **WebSocket Verbindungen**: Clients werden ordnungsgemäß benachrichtigt
- **Checkpoints**: Workflow-State wird korrekt gespeichert
- **Ressourcen**: Datenbankverbindungen, File Handles werden freigegeben
- **Logs**: Finale Logs werden geschrieben

### Agenten (10 total)
1. **Orchestrator** (GPT-5) - Task Decomposition
2. **Architect** (GPT-4o) - System Design
3. **CodeSmith** (Claude 4.1 Sonnet) - Code Generation
4. **Reviewer** (GPT-5-mini) - Code Review
5. **Fixer** (Claude 4.1 Sonnet) - Bug Fixing
6. **DocBot** (GPT-4o) - Documentation
7. **Research** (Perplexity) - Web Research
8. **TradeStrat** (Claude 4.1 Sonnet) - Trading Strategies
9. **OpusArbitrator** (Claude Opus 4.1) - Conflict Resolution
10. **Performance** (GPT-4o) - Performance Optimization

---

## 📁 TEST-REGELN: Alle Tests im agent_projects Ordner

### Grundprinzip
**ALLE Test-Dateien und generierten Apps MÜSSEN im `agent_projects/` Ordner erstellt werden!**

### ✅ RICHTIGE Orte:
- `/Users/dominikfoert/git/KI_AutoAgent/agent_projects/test_*.py` - Test-Skripte
- `/Users/dominikfoert/git/KI_AutoAgent/agent_projects/*/` - Generierte Apps
- `/Users/dominikfoert/git/KI_AutoAgent/agent_projects/*.log` - Test-Logs

### ❌ FALSCHE Orte:
- `/Users/dominikfoert/git/KI_AutoAgent/*.html` - KEINE HTML-Dateien im Hauptordner
- `/Users/dominikfoert/git/KI_AutoAgent/test_*.py` - KEINE Tests im Hauptordner
- `/Users/dominikfoert/git/KI_AutoAgent/generate.html` - KEINE generierten Dateien im Hauptordner

### 🧹 Cleanup-Regel:
Vor jedem neuen Test:
```bash
rm -rf /Users/dominikfoert/git/KI_AutoAgent/agent_projects/[test_dir]
```

### 📝 KI Agent Output:
Wenn der KI Agent eine App generiert, IMMER mit Pfad-Angabe:
```
"Create app in agent_projects/my_app/ directory"
```

---

## 🚨 DEBUGGING-REGELN: "Es funktioniert" ist KEIN Beweis

### Grundprinzip
**Symptome ignorieren = schlechtes Engineering**

Wenn etwas "merkwürdig" ist aber das System "trotzdem funktioniert", ist das ein **RED FLAG**, kein Grund zum Weitermachen!

### ❌ FALSCHE Denkweise:
- "Test X funktioniert nicht, aber Test Y funktioniert, also ist alles okay"
- "Die Logs erscheinen nicht, aber der Server läuft, also egal"
- "Das ist nur ein Edge Case, der normale Weg funktioniert"
- "Ich verstehe nicht warum es funktioniert, aber es tut es"

### ✅ RICHTIGE Denkweise:
- "Test X funktioniert nicht. Ich muss herausfinden WARUM, auch wenn Test Y funktioniert!"
- "Die Logs erscheinen nicht. Das ist ein BUG im Logging-System, den ich JETZT fixen muss!"
- "Edge Cases sind echte Use Cases - ich debug das vollständig"
- "Ich verstehe nicht warum - dann verstehe ich das System nicht gut genug!"

### 🔍 Debug-Protokoll:

1. **Symptom beobachtet?** → Nicht weitermachen bis Root Cause gefunden!
2. **"Es funktioniert trotzdem"?** → Nein! Es funktioniert FALSCH, nur End-to-End geht
3. **Root Cause unklar?** → Tests schreiben die das spezifische Problem isolieren
4. **Fix angewendet?** → Verifizieren dass SYMPTOM weg ist, nicht nur End-to-End

### 📊 Beispiel aus diesem Projekt:

**Symptom:** `logger.info()` Logs erscheinen nicht
**Falsche Reaktion:** "Server funktioniert, also okay"
**Richtige Reaktion:** Root Cause finden (Uvicorn überschreibt basicConfig)
**Fix:** `log_config=None` + `force=True` in basicConfig
**Verifikation:** Logs erscheinen jetzt ✅

### 🎯 Für FixerBot Agent:
Siehe detaillierte Instruktionen in [FIXER_INSTRUCTIONS.md](.kiautoagent/docs/FIXER_INSTRUCTIONS.md)

---

**Zuletzt aktualisiert**: 2025-10-01
**Version**: v5.0.0-unstable
