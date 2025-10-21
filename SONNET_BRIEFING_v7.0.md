# Briefing für Sonnet: v7.0 Supervisor Pattern Migration

## 🎯 Deine Aufgabe

Migriere das KI_AutoAgent System von v6.6 (verteilte Intelligenz) zu v7.0 (Supervisor Pattern).

---

## 📋 Kontext

### Aktuelles Problem (v6.6)
- **Zu komplex:** 5 Entscheidungsträger (alle Agents + Orchestrator)
- **Modi-System:** Starr, nur EIN Mode pro Agent-Aufruf möglich
- **Research falsch:** Als User-facing Agent statt Support-Agent
- **Keine Selbstaufrufe:** Agent kann sich nicht selbst nochmal aufrufen

### Lösung (v7.0)
- **Supervisor Pattern:** EIN LLM (GPT-4o) orchestriert ALLES
- **Command-based Routing:** Nutzt LangGraph's Command(goto=...)
- **Research als Support:** Sammelt Kontext für andere Agents
- **Instructions statt Modi:** Dynamische Anweisungen vom Supervisor

---

## 📚 Wichtige Dokumente

**MUST READ (in dieser Reihenfolge):**

1. **ARCHITECTURE_CURRENT_v6.6.md** - Verstehe was jetzt da ist
2. **ARCHITECTURE_TARGET_v7.0.md** - Verstehe das Ziel
3. **MIGRATION_GUIDE_v7.0.md** - Schritt-für-Schritt Anleitung

**Referenz (bei Bedarf):**
- PYTHON_BEST_PRACTICES.md - Python 3.13 Standards
- CLAUDE_CLI_INTEGRATION.md - Claude Tool Integration
- BUILD_VALIDATION_GUIDE.md - Test/Validation
- E2E_TESTING_GUIDE.md - End-to-End Tests

---

## 🔧 Konkrete Schritte

### 1. Supervisor implementieren
```python
# Neue Datei: backend/core/supervisor.py
class Supervisor:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")

    async def decide_next(state) -> Command:
        # Analysiert State
        # Entscheidet nächsten Agent
        # Gibt Command(goto=...) zurück
```

### 2. Agents vereinfachen
```python
# ENTFERNEN aus allen Agents:
- evaluate_task()  # Agents entscheiden nicht mehr!
- decide_next()    # Routing macht Supervisor!

# BEHALTEN:
- execute(state)   # Agents führen nur aus
```

### 3. LangGraph umbauen
```python
# ENTFERNEN:
- Alle conditional edges
- Alle hardcoded edges (außer START → supervisor)

# NEU:
- Supervisor nutzt Command(goto="agent_name")
- Agents returnen Command(goto="supervisor")
```

### 4. Research repositionieren
```python
class ResearchAgent:
    """Support-Agent, NICHT User-facing!"""

    async def execute(state):
        # Sammelt Kontext für ANDERE Agents
        # Gibt NIE direkte User-Antworten
```

### 5. Responder Agent NEU
```python
class ResponderAgent:
    """EINZIGER User-facing Agent!"""

    async def execute(state):
        # Sammelt alle Ergebnisse
        # Formatiert User-Antwort
```

---

## ⚠️ Kritische Punkte

### Was MUSS funktionieren:

1. **Selbstaufrufe:**
   ```
   architect → architect → architect (Verfeinerung)
   ```

2. **Research VOR wichtigen Entscheidungen:**
   ```
   research (workspace scan) → architect (design)
   ```

3. **Command-based routing:**
   ```python
   return Command(goto="architect", update={"instructions": "..."})
   ```

4. **Keine Modi mehr:**
   ```python
   # ALT: architect(mode="scan")
   # NEU: architect(instructions="Scan workspace for patterns")
   ```

---

## 🧪 Test-Szenarien

### Must-Pass Tests:

1. **CREATE:** "Create a task manager API"
   - Research scannt Workspace
   - Architect designt mit Kontext
   - Codesmith generiert
   - ReviewFix validiert
   - Responder antwortet User

2. **EXPLAIN:** "Untersuche die App"
   - Research analysiert Code
   - Responder formuliert Erklärung
   - (KEIN Architect/Codesmith!)

3. **SELF-CALL:** Architect verfeinert Design
   - Architect (initial design)
   - Architect (add database)
   - Architect (add auth)

---

## 💡 Tipps

### DO:
- ✅ Supervisor trifft ALLE Entscheidungen
- ✅ Agents sind "dumme" Werkzeuge
- ✅ Research läuft VOR wichtigen Tasks
- ✅ Command(goto=...) für routing
- ✅ Responder für User-Antworten

### DON'T:
- ❌ Keine evaluate_task() mehr
- ❌ Keine hardcoded edges
- ❌ Keine Modi (nur Instructions)
- ❌ Research NIE direkt an User
- ❌ Keine verteilte Intelligenz

---

## 🎯 Definition of Done

Migration ist erfolgreich wenn:

1. ✅ Supervisor orchestriert alles
2. ✅ Keine Agent-Intelligenz mehr
3. ✅ Research = Support-Agent
4. ✅ Selbstaufrufe funktionieren
5. ✅ E2E Tests bestehen
6. ✅ Code ist EINFACHER als vorher

---

## 🚀 Los geht's!

1. Checkout branch: `git checkout -b v7.0-supervisor`
2. Starte mit `backend/core/supervisor.py`
3. Folge MIGRATION_GUIDE_v7.0.md
4. Teste früh und oft!

**Viel Erfolg!** 🎉

---

*P.S. von Opus: Ich habe das System gründlich analysiert. Der Supervisor-Pattern ist die richtige Lösung. Die aktuelle v6.6 ist zu komplex und wird nur schlimmer. Trust the process!*