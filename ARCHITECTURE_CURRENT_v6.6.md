# Aktuelle Architektur - v6.6 (Stand: 2025-10-20)

## Übersicht

**Version:** v6.6.0-alpha
**Status:** Funktionsfähig, aber mit kritischen Design-Schwächen
**Problem:** Überkomplexe Multi-Agent-Architektur mit verteilter Intelligenz

---

## 🏗️ Architektur-Komponenten

### 1. Multi-Agent Orchestrator (Zentral)
**Datei:** `backend/core/multi_agent_orchestrator.py`

```python
class MultiAgentOrchestrator:
    """
    LLM-basierte Routing-Entscheidung mit GPT-4o-mini.
    Problem: Fragt jeden Agent einzeln "Kannst du helfen?"
    """

    async def route_request(user_query, workspace_path, context) -> RoutingDecision:
        # Sammelt Proposals von ALLEN Agents (parallel)
        proposals = await self._collect_proposals()

        # Jeder Agent evaluiert mit eigenem LLM-Call
        # 4 Agents = 4 LLM-Calls parallel

        # Bestimmt beste Strategie
        return RoutingDecision(
            strategy="single|parallel|sequential",
            agents=[("agent", "mode"), ...],
            confidence=0.9
        )
```

**Probleme:**
- Jeder Agent trifft eigene Entscheidungen (`evaluate_task()`)
- Modi sind hardcoded pro Agent definiert
- Kein Agent kann sich selbst nochmal aufrufen
- Research wird als User-facing Agent missverstanden

### 2. Agent-Definitionen mit Modi

**AGENT_CAPABILITIES:**
```python
{
    "research": {
        "modes": {
            "research": "Web search",
            "explain": "Analyze existing code",
            "analyze": "Deep analysis",
            "index": "Index workspace"
        }
    },
    "architect": {
        "modes": {
            "scan": "Load existing architecture",
            "design": "Design new architecture",
            "post_build_scan": "Document after generation",
            "re_scan": "Update architecture"
        }
    },
    # ... weitere Agents
}
```

**Problem:** Modi sind statisch, LLM kann nur EINEN Mode pro Agent-Aufruf wählen!

### 3. Workflow-Routing mit LangGraph

**Datei:** `backend/workflow_v6_integrated.py`

```python
# Statische Edges definiert
graph.add_edge("research", "research_decide_next")
graph.add_edge("architect", "architect_decide_next")
graph.add_edge("codesmith", "codesmith_decide_next")
graph.add_edge("reviewfix", "reviewfix_decide_next")

# Jeder Agent entscheidet selbst was als nächstes
def architect_decide_next(state) -> str:
    # Hardcoded logic
    if state.get("architecture_design"):
        return "codesmith"
    else:
        return "hitl"
```

**Probleme:**
- Hardcoded routing edges
- Verteilte Entscheidungslogik
- Keine Selbstaufrufe möglich
- Inflexibel bei neuen Workflows

### 4. Agent-Implementierungen

**Research Agent:** `backend/subgraphs/research_subgraph_v6_1.py`
```python
async def evaluate_task(user_query: str, context: dict) -> AgentProposal:
    """
    Entscheidet selbst ob er helfen kann.
    Problem: Research denkt er ist User-facing!
    """
    # Keyword-basierte Analyse
    if "untersuche" in query:
        return AgentProposal(can_help=True, mode="explain")
```

**Architect Agent:** `backend/subgraphs/architect_subgraph_v6_3.py`
```python
async def evaluate_task(user_query: str, context: dict) -> AgentProposal:
    """
    Hat Anti-Indicators um andere Agents zu vermeiden.
    Problem: Kann sich nicht selbst mehrfach aufrufen!
    """
    if "untersuche" in query:
        return AgentProposal(can_help=False)  # Research soll das machen
```

---

## 🔄 Workflow-Ablauf (Aktuell)

### Beispiel: "Create a task manager API"

```
1. User Query → routing_node
   ↓
2. MultiAgentOrchestrator.route_request()
   ↓
3. Parallel LLM-Calls an alle Agents:
   - research.evaluate_task() → "can_help=False"
   - architect.evaluate_task() → "can_help=True, mode=design"
   - codesmith.evaluate_task() → "can_help=False"
   - reviewfix.evaluate_task() → "can_help=False"
   ↓
4. RoutingDecision: single, architect(design)
   ↓
5. architect_node(mode="design")
   ↓
6. architect_decide_next() → "codesmith"
   ↓
7. codesmith_node()
   ↓
8. codesmith_decide_next() → "reviewfix"
   ↓
9. reviewfix_node()
   ↓
10. END
```

### Kritische Fehler im Ablauf:

1. **Kein Workspace-Scan:** Architect designt ohne Kontext
2. **Kein Research:** Keine Informationssammlung vorab
3. **Nur ein Mode pro Agent:** Architect kann nicht scan → design → post_build_scan
4. **Statisches Routing:** Kann nicht adaptiv reagieren

---

## 📊 Probleme der aktuellen Architektur

### 1. Verteilte Intelligenz
- Jeder Agent entscheidet selbst (evaluate_task)
- Jeder Agent hat eigene Routing-Logik (decide_next)
- Keine zentrale Orchestrierung

### 2. Modi-Limitierung
```python
# LLM kann nur wählen:
architect(scan) ODER architect(design) ODER architect(post_build_scan)
# Aber NICHT die Sequenz:
architect(scan) → architect(design) → architect(post_build_scan)
```

### 3. Research-Missverständnis
- Research wird als User-facing Agent behandelt
- Macht Web-Search für User-Antworten
- SOLLTE: Kontext für andere Agents sammeln

### 4. Keine Selbstaufrufe
```python
# Unmöglich in aktueller Architektur:
architect(design) → architect(design)  # Verfeinerung
research(analyze) → research(analyze)  # Tiefere Analyse
```

### 5. Hardcoded Workflows
```python
# Fix in workflow_v6_integrated.py:
if workflow_type == "CREATE":
    path = ["architect", "codesmith", "reviewfix"]
elif workflow_type == "FIX":
    path = ["research", "codesmith", "reviewfix"]
```

---

## 🗂️ Dateistruktur

```
backend/
├── core/
│   └── multi_agent_orchestrator.py    # LLM-based routing (v6.6)
├── workflow_v6_integrated.py          # LangGraph workflow
├── subgraphs/
│   ├── research_subgraph_v6_1.py     # Research agent + evaluate_task
│   ├── architect_subgraph_v6_3.py    # Architect + evaluate_task
│   ├── codesmith_subgraph_v6_1.py    # Codesmith + evaluate_task
│   └── reviewfix_subgraph_v6_1.py    # ReviewFix + evaluate_task
└── cognitive/
    ├── workflow_aware_router.py       # OBSOLETE (v6.5)
    └── asimov_rules.py               # Constraints (noch aktiv)
```

---

## 💔 Warum diese Architektur scheitert

### 1. **Zu viele Entscheidungsträger**
- 4 Agents + 1 Orchestrator = 5 Entitäten die Entscheidungen treffen
- Koordination wird exponentiell komplexer

### 2. **Statische Modi statt dynamische Instructions**
- Modi müssen vorab definiert werden
- Keine Flexibilität für neue Aufgaben
- Agent kann nicht adaptiv reagieren

### 3. **Falsche Abstraktion**
- Agents sind zu "intelligent" (eigene Entscheidungen)
- Orchestrator ist zu "dumm" (sammelt nur Proposals)
- Research ist falsch positioniert (User-facing statt Support)

### 4. **LangGraph wird falsch genutzt**
- Hardcoded edges statt Command-based routing
- Conditional edges mit statischer Logik
- Kein Supervisor-Pattern implementiert

---

## 📈 Metriken der Komplexität

| Metrik | Wert | Problem |
|--------|------|---------|
| LLM-Calls pro Request | 4-8 | Zu viele parallele Evaluierungen |
| Entscheidungspunkte | 9+ | Jeder Agent + jede decide_next Funktion |
| Modi-Kombinationen | 15+ | Zu viele Möglichkeiten |
| Code-Duplikation | Hoch | Jeder Agent hat evaluate_task |
| Wartbarkeit | Niedrig | Verteilte Logik schwer zu debuggen |

---

## 🎯 Fazit

Die v6.6 Architektur ist funktional, aber fundamental fehlerhaft:

1. **Verteilte Intelligenz** macht System unkontrollierbar
2. **Modi-System** ist zu starr für dynamische Aufgaben
3. **Research-Agent** ist falsch konzipiert
4. **Routing** ist hardcoded statt dynamisch
5. **Komplexität** explodiert mit jedem neuen Feature

**Lösung:** Migration zu Supervisor-Pattern (v7.0) mit zentraler Orchestrierung.

---

**Dokumentiert von:** Claude (Opus 4.1)
**Datum:** 2025-10-20
**Status:** Zur Ablösung vorgesehen durch v7.0