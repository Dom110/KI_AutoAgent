# Ziel-Architektur - v7.0 Supervisor Pattern

## Executive Summary

**Version:** v7.0.0-alpha (Target)
**Paradigma:** Supervisor-Pattern mit Command-based Routing
**Kern-Prinzip:** EIN intelligenter Supervisor orchestriert "dumme" Tool-Agents

---

## 🎯 Design-Prinzipien

### 1. Zentrale Orchestrierung
- **EIN** Supervisor (LLM) trifft ALLE Entscheidungen
- Agents sind reine Werkzeuge ohne eigene Intelligenz
- Keine verteilte Entscheidungslogik mehr

### 2. Command-Based Routing
- Nutzt LangGraph's `Command` mit `goto`
- Keine hardcoded edges
- Dynamische, adaptive Workflows

### 3. Research als Support-Agent
- Research sammelt Kontext für andere Agents
- NIE direkte User-Antworten
- Immer vor wichtigen Entscheidungen

### 4. Instructions statt Modi
- Supervisor gibt spezifische Instructions
- Keine vordefinierten Modi
- Maximale Flexibilität

---

## 🏗️ Architektur-Komponenten

### 1. Supervisor (Der einzige Entscheider)

```python
class Supervisor:
    """
    Zentrale Orchestrierung mit GPT-4o.
    Einziger Entscheidungsträger im System.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    async def decide_next(self, state: SupervisorState) -> Command:
        """
        Analysiert State und entscheidet:
        - Welcher Agent als nächstes?
        - Mit welchen Instructions?
        - Selbstaufruf? (gleicher Agent nochmal)
        - Parallelisierung möglich?
        - Fertig? (END)
        """

        prompt = self._build_decision_prompt(state)
        decision = await self.llm.with_structured_output(SupervisorDecision).ainvoke(prompt)

        # Command mit goto (KEINE conditional edges!)
        if decision.action == "CONTINUE":
            return Command(
                goto=decision.next_agent,
                update={
                    "instructions": decision.instructions,
                    "iteration": state.iteration + 1
                }
            )
        elif decision.action == "PARALLEL":
            return Command(
                goto=decision.parallel_agents,  # Liste von Agents
                update={"instructions": decision.instructions}
            )
        else:  # FINISH
            return Command(goto=END)
```

### 2. Research Agent (Kontext-Sammler)

```python
class ResearchAgent:
    """
    Sammelt Informationen für andere Agents.
    KEIN User-facing Agent!
    """

    async def execute(self, state: AgentState) -> dict:
        """
        Führt Supervisor-Instructions aus:
        - Workspace-Analyse
        - Code-Indexierung
        - Web-Search für Best Practices
        - Bug-Analyse
        """
        instructions = state["instructions"]

        # Parse Instructions vom Supervisor
        if "analyze workspace" in instructions:
            return await self._analyze_workspace(state["workspace_path"])
        elif "search web" in instructions:
            return await self._search_web(instructions)
        elif "analyze bugs" in instructions:
            return await self._analyze_bugs(state["code_files"])

        return {"context": collected_info}
```

### 3. Architect Agent (Designer)

```python
class ArchitectAgent:
    """
    Nutzt Research-Kontext für Design-Entscheidungen.
    Keine eigene Intelligenz!
    """

    async def execute(self, state: AgentState) -> dict:
        """
        Führt Supervisor-Instructions aus:
        - Design neue Architektur
        - Update existierende Architektur
        - Dokumentiere System
        """
        instructions = state["instructions"]
        context = state["research_context"]  # Von Research Agent!

        # Nutzt IMMER Research-Context
        architecture = await self._design_with_context(instructions, context)

        return {"architecture": architecture}
```

### 4. Codesmith Agent (Implementierer)

```python
class CodesmithAgent:
    """
    Generiert Code basierend auf Architecture + Context.
    """

    async def execute(self, state: AgentState) -> dict:
        """
        Führt Supervisor-Instructions aus:
        - Generate Code
        - Fix Bugs
        - Refactor
        """
        instructions = state["instructions"]
        architecture = state["architecture"]  # Von Architect!
        context = state["research_context"]  # Von Research!

        code = await self._generate_code(instructions, architecture, context)

        return {"generated_files": code}
```

### 5. Responder Agent (NEU! User-Interface)

```python
class ResponderAgent:
    """
    Der EINZIGE Agent der mit dem User kommuniziert!
    Formuliert finale Antworten aus allen Ergebnissen.
    """

    async def execute(self, state: AgentState) -> dict:
        """
        Sammelt alle Ergebnisse und formuliert User-Antwort.
        """
        instructions = state["instructions"]
        all_results = state["accumulated_results"]

        # Erstellt lesbare Antwort für User
        response = await self._format_response(all_results, instructions)

        return {"user_response": response}
```

---

## 🔄 Workflow mit LangGraph

### Graph-Definition (OHNE hardcoded edges!)

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# State Definition
class SupervisorState(TypedDict):
    messages: list[dict]
    goal: str
    research_context: dict
    architecture: dict
    generated_files: list
    instructions: str
    iteration: int
    last_agent: str

# Graph Setup
graph = StateGraph(SupervisorState)

# Nodes (Agents)
graph.add_node("supervisor", supervisor_node)
graph.add_node("research", research_node)
graph.add_node("architect", architect_node)
graph.add_node("codesmith", codesmith_node)
graph.add_node("reviewfix", reviewfix_node)
graph.add_node("responder", responder_node)

# EINZIGER Edge: Start → Supervisor
graph.add_edge(START, "supervisor")

# Supervisor nutzt Command(goto=...) für ALLES andere!
# KEINE weiteren Edges definiert!

app = graph.compile(config={"recursion_limit": 20})
```

### Beispiel-Flow: "Create a task manager API"

```python
# 1. User Input
state = {
    "messages": [{"role": "user", "content": "Create a task manager API with FastAPI"}],
    "goal": "Create task manager API",
    "iteration": 0
}

# 2. Supervisor entscheidet
supervisor: "Ich brauche erst Workspace-Kontext"
→ Command(goto="research", instructions="Analyze workspace for existing patterns")

# 3. Research sammelt Kontext
research: Analysiert Workspace, findet FastAPI-Patterns
→ Returns: {"context": workspace_analysis}

# 4. Supervisor (automatisch wieder aufgerufen)
supervisor: "Jetzt habe ich Kontext, Architect kann designen"
→ Command(goto="architect", instructions="Design API using context")

# 5. Architect nutzt Context
architect: Designt mit Research-Context
→ Returns: {"architecture": api_design}

# 6. Supervisor
supervisor: "Design gut, aber DB-Schema fehlt. Architect nochmal!"
→ Command(goto="architect", instructions="Add database schema")  # SELBSTAUFRUF!

# 7. Architect erweitert
architect: Fügt DB-Schema hinzu
→ Returns: {"architecture": complete_design}

# 8. Supervisor
supervisor: "Jetzt kann Code generiert werden"
→ Command(goto="codesmith", instructions="Generate FastAPI code")

# 9. Codesmith implementiert
codesmith: Generiert Code mit Architecture + Context
→ Returns: {"generated_files": [...]}

# 10. Supervisor
supervisor: "Code review nötig"
→ Command(goto="reviewfix", instructions="Validate and test")

# 11. ReviewFix validiert
reviewfix: Tests, Linting, Fixes
→ Returns: {"validation": "passed"}

# 12. Supervisor
supervisor: "Fertig! Responder soll Antwort formulieren"
→ Command(goto="responder", instructions="Summarize for user")

# 13. Responder
responder: "✅ Task Manager API created successfully..."
→ Returns: {"user_response": formatted_message}

# 14. Supervisor
supervisor: "Task complete"
→ Command(goto=END)
```

---

## 🚀 Vorteile der neuen Architektur

### 1. Zentrale Kontrolle
- EIN Entscheidungsträger (Supervisor)
- Vollständige Transparenz
- Einfaches Debugging

### 2. Maximale Flexibilität
- Keine hardcoded Modi
- Dynamische Instructions
- Adaptive Workflows

### 3. Selbstaufrufe möglich
```python
# Supervisor kann entscheiden:
architect → architect → architect  # Iterative Verfeinerung
research → research  # Tiefere Analyse
```

### 4. Research richtig positioniert
- Sammelt Kontext VOR Entscheidungen
- Unterstützt andere Agents
- Kein direkter User-Kontakt

### 5. Skalierbarkeit
- Neue Agents einfach hinzufügen
- Keine Änderungen an Routing nötig
- Supervisor lernt automatisch

---

## 📊 Vergleich: v6.6 vs v7.0

| Aspekt | v6.6 (Alt) | v7.0 (Neu) |
|--------|------------|------------|
| **Entscheidungsträger** | 5 (alle Agents + Orchestrator) | 1 (nur Supervisor) |
| **Routing** | Hardcoded edges + conditional | Command(goto=...) |
| **Agent-Intelligenz** | Jeder Agent mit evaluate_task() | Agents sind "dumm" |
| **Modi** | Statisch vordefiniert | Dynamische Instructions |
| **Selbstaufrufe** | Unmöglich | Jederzeit möglich |
| **Research-Rolle** | User-facing | Support-Agent |
| **LLM-Calls** | 4-8 parallel | 1 pro Entscheidung |
| **Komplexität** | Exponentiell | Linear |
| **Wartbarkeit** | Niedrig | Hoch |
| **Erweiterbarkeit** | Schwierig | Einfach |

---

## 🔧 Implementierungs-Roadmap

### Phase 1: Supervisor implementieren
- [ ] Supervisor-Klasse mit GPT-4o
- [ ] Command-based routing
- [ ] Decision-Prompts optimieren

### Phase 2: Agents vereinfachen
- [ ] Remove evaluate_task() von allen Agents
- [ ] Remove decide_next() Funktionen
- [ ] Agents zu reinen Execute-Tools machen

### Phase 3: Research repositionieren
- [ ] Research als Support-Agent
- [ ] Workspace-Analyse-Tools
- [ ] Context-Sammlung optimieren

### Phase 4: Responder hinzufügen
- [ ] Neuer User-facing Agent
- [ ] Response-Formatierung
- [ ] Markdown-Ausgabe

### Phase 5: LangGraph-Migration
- [ ] Entfernen aller hardcoded edges
- [ ] Command-Pattern implementieren
- [ ] Recursion-Limits setzen

---

## 🎯 Erfolgs-Kriterien

### System gilt als erfolgreich wenn:

1. ✅ Supervisor trifft ALLE Routing-Entscheidungen
2. ✅ Keine hardcoded edges mehr
3. ✅ Research läuft VOR wichtigen Entscheidungen
4. ✅ Agents können sich selbst aufrufen
5. ✅ Komplexität bleibt linear bei neuen Features
6. ✅ E2E-Tests bestehen alle Szenarien
7. ✅ User bekommt strukturierte Antworten vom Responder

---

## 📝 Migrations-Notizen

### Was bleibt erhalten:
- WebSocket-Interface (keine UI-Änderungen)
- Agent-Tools (Claude CLI, etc.)
- Workspace-Handling
- Session-Management

### Was wird entfernt:
- multi_agent_orchestrator.py (komplett neu)
- evaluate_task() Funktionen
- decide_next() Funktionen
- Conditional edges
- AGENT_CAPABILITIES Dictionary
- Modi-System

### Was wird neu:
- Supervisor-Klasse
- Command-based routing
- Responder-Agent
- Instructions-System
- Zentrale Orchestrierung

---

## 🔮 Zukunfts-Erweiterungen

### v7.1: Lernender Supervisor
- Speichert erfolgreiche Patterns
- Optimiert Instructions basierend auf Feedback
- Adaptive Komplexität

### v7.2: Multi-Model Support
- Verschiedene LLMs für verschiedene Agents
- Cost-Optimierung
- Parallel-Execution

### v7.3: Plugin-System
- Externe Agents als Plugins
- Community-Agents
- Marketplace

---

**Architekt:** Claude (Opus 4.1)
**Datum:** 2025-10-20
**Status:** Bereit zur Implementierung
**Geschätzte Entwicklungszeit:** 2-3 Wochen