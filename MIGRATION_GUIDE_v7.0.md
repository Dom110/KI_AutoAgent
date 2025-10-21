# Migration Guide: v6.6 → v7.0 Supervisor Pattern

## Übersicht

**Von:** v6.6 Multi-Agent mit verteilter Intelligenz
**Nach:** v7.0 Supervisor Pattern mit zentraler Orchestrierung
**Geschätzte Zeit:** 2-3 Wochen
**Breaking Changes:** Ja (Backend-Architektur komplett neu)

---

## 📋 Pre-Migration Checklist

- [ ] Backup der v6.6 Installation erstellen
- [ ] E2E Tests dokumentieren für Vergleich
- [ ] ARCHITECTURE_CURRENT_v6.6.md gelesen
- [ ] ARCHITECTURE_TARGET_v7.0.md verstanden
- [ ] Development Branch erstellen: `git checkout -b v7.0-supervisor-pattern`

---

## 🔄 Migration Steps

### Phase 1: Supervisor implementieren (Tag 1-3)

#### 1.1 Neue Datei erstellen
```bash
touch backend/core/supervisor.py
```

#### 1.2 Supervisor-Klasse implementieren
```python
# backend/core/supervisor.py

from langchain_openai import ChatOpenAI
from langgraph.types import Command
from typing import Literal
from pydantic import BaseModel

class SupervisorDecision(BaseModel):
    """Structured output for supervisor decisions."""
    action: Literal["CONTINUE", "PARALLEL", "FINISH"]
    next_agent: str | None
    parallel_agents: list[str] | None
    instructions: str
    reasoning: str
    confidence: float

class Supervisor:
    """Central orchestrator using GPT-4o."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1000
        )

    async def decide_next(self, state: dict) -> Command:
        """
        Main decision function.
        Analyzes state and decides next action.
        """
        prompt = self._build_prompt(state)
        decision = await self.llm.with_structured_output(
            SupervisorDecision
        ).ainvoke(prompt)

        if decision.action == "FINISH":
            return Command(goto=END)
        elif decision.action == "PARALLEL":
            return Command(
                goto=decision.parallel_agents,
                update={"instructions": decision.instructions}
            )
        else:  # CONTINUE
            return Command(
                goto=decision.next_agent,
                update={
                    "instructions": decision.instructions,
                    "last_agent": decision.next_agent,
                    "iteration": state.get("iteration", 0) + 1
                }
            )

    def _build_prompt(self, state: dict) -> str:
        """Build decision prompt from state."""
        return f"""
        You are orchestrating a multi-agent system.

        Current Goal: {state.get('goal', '')}
        Last Agent: {state.get('last_agent', 'none')}
        Iteration: {state.get('iteration', 0)}

        Context collected: {bool(state.get('research_context'))}
        Architecture ready: {bool(state.get('architecture'))}
        Code generated: {bool(state.get('generated_files'))}

        Available agents:
        - research: Collect context and information
        - architect: Design system architecture
        - codesmith: Generate code
        - reviewfix: Validate and fix
        - responder: Format user response

        Decide next action. Consider:
        - Does research need to run first to collect context?
        - Should the same agent run again with refined instructions?
        - Are we ready to finish?
        """
```

---

### Phase 2: Agents vereinfachen (Tag 4-6)

#### 2.1 Research Agent refactoren
```python
# backend/agents/research_agent.py

class ResearchAgent:
    """
    Support agent for context collection.
    NO user-facing functionality!
    """

    async def execute(self, state: dict) -> dict:
        """Execute supervisor instructions."""
        instructions = state.get("instructions", "")
        workspace_path = state.get("workspace_path", "")

        results = {}

        if "analyze workspace" in instructions.lower():
            results["workspace_analysis"] = await self._analyze_workspace(
                workspace_path
            )

        if "search web" in instructions.lower():
            # Extract search query from instructions
            query = self._extract_search_query(instructions)
            results["web_results"] = await self._search_web(query)

        if "index code" in instructions.lower():
            results["code_index"] = await self._index_codebase(
                workspace_path
            )

        return {
            "research_context": results,
            "research_complete": True
        }
```

#### 2.2 Architect Agent vereinfachen
```python
# backend/agents/architect_agent.py

class ArchitectAgent:
    """Design agent using research context."""

    async def execute(self, state: dict) -> dict:
        """Execute supervisor instructions."""
        instructions = state.get("instructions", "")
        context = state.get("research_context", {})

        # ALWAYS use research context
        if not context:
            return {
                "error": "No research context available",
                "needs_research": True
            }

        # Design based on instructions and context
        architecture = await self._design_architecture(
            instructions,
            context
        )

        return {
            "architecture": architecture,
            "architecture_complete": True
        }
```

#### 2.3 ENTFERNEN aus allen Agents:
```python
# Diese Funktionen LÖSCHEN:
- async def evaluate_task()
- def decide_next()
- def get_capability_score()
- class AgentProposal
```

---

### Phase 3: LangGraph umbauen (Tag 7-9)

#### 3.1 Neuer Workflow Graph
```python
# backend/workflow_v7_supervisor.py

from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class SupervisorState(TypedDict):
    messages: list[dict]
    goal: str
    workspace_path: str
    research_context: dict
    architecture: dict
    generated_files: list
    validation_results: dict
    user_response: str
    instructions: str
    last_agent: str
    iteration: int

# Build graph
def build_supervisor_workflow():
    graph = StateGraph(SupervisorState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)
    graph.add_node("architect", architect_node)
    graph.add_node("codesmith", codesmith_node)
    graph.add_node("reviewfix", reviewfix_node)
    graph.add_node("responder", responder_node)

    # ONLY ONE EDGE!
    graph.add_edge(START, "supervisor")

    # Supervisor uses Command(goto=...) for everything else
    # NO MORE EDGES!

    return graph.compile(config={"recursion_limit": 25})

async def supervisor_node(state: SupervisorState):
    """Supervisor decision node."""
    supervisor = Supervisor()
    command = await supervisor.decide_next(state)
    return command

async def research_node(state: SupervisorState):
    """Research execution node."""
    agent = ResearchAgent()
    result = await agent.execute(state)
    # After execution, go back to supervisor
    return Command(
        goto="supervisor",
        update=result
    )
```

#### 3.2 ENTFERNEN aus workflow_v6_integrated.py:
```python
# Diese Teile LÖSCHEN:
- multi_agent_orchestrator imports
- routing_node()
- conditional edges
- decide_next functions
- workflow_aware_router
```

---

### Phase 4: Responder Agent hinzufügen (Tag 10-11)

#### 4.1 Neuer User-facing Agent
```python
# backend/agents/responder_agent.py

class ResponderAgent:
    """
    The ONLY agent that talks to users.
    Formats final responses from all results.
    """

    async def execute(self, state: dict) -> dict:
        """Create user response from accumulated results."""
        instructions = state.get("instructions", "")

        # Gather all results
        response_parts = []

        if state.get("research_context"):
            response_parts.append(
                self._format_research(state["research_context"])
            )

        if state.get("architecture"):
            response_parts.append(
                self._format_architecture(state["architecture"])
            )

        if state.get("generated_files"):
            response_parts.append(
                self._format_code(state["generated_files"])
            )

        if state.get("validation_results"):
            response_parts.append(
                self._format_validation(state["validation_results"])
            )

        # Combine into final response
        user_response = "\n\n".join(response_parts)

        return {
            "user_response": user_response,
            "response_ready": True
        }
```

---

### Phase 5: Testing & Validation (Tag 12-14)

#### 5.1 E2E Test Suite anpassen
```python
# tests/e2e/test_supervisor_workflows.py

async def test_create_workflow():
    """Test CREATE workflow with supervisor."""
    state = {
        "messages": [{"role": "user", "content": "Create a task manager API"}],
        "goal": "Create task manager API",
        "workspace_path": "/test/workspace"
    }

    app = build_supervisor_workflow()
    result = await app.ainvoke(state)

    # Verify workflow steps
    assert result.get("research_context") is not None
    assert result.get("architecture") is not None
    assert result.get("generated_files") is not None
    assert result.get("user_response") is not None

async def test_self_invocation():
    """Test that agents can be called multiple times."""
    # Verify architect can be called twice
    # Check iteration counter increases
    pass
```

#### 5.2 Migration Validation
```bash
# Run all tests
pytest tests/e2e/ -v

# Compare with v6.6 baselines
python scripts/compare_test_results.py
```

---

## 🗑️ Was entfernt wird

### Dateien zum Löschen:
```bash
rm backend/core/multi_agent_orchestrator.py
rm backend/cognitive/workflow_aware_router.py
rm backend/cognitive/workflow_estimator_v6.py
```

### Code zum Entfernen:
- Alle `evaluate_task()` Funktionen
- Alle `decide_next()` Funktionen
- AGENT_CAPABILITIES Dictionary
- Modi-System
- Conditional edges in LangGraph

---

## 🎯 Erfolgs-Kriterien

### Migration ist erfolgreich wenn:

1. ✅ Supervisor trifft alle Routing-Entscheidungen
2. ✅ Keine evaluate_task() mehr in Agents
3. ✅ Research läuft VOR Architect/Codesmith
4. ✅ Selbstaufrufe funktionieren (gleicher Agent mehrfach)
5. ✅ Responder formatiert alle User-Antworten
6. ✅ E2E Tests bestehen
7. ✅ Komplexität reduziert (weniger Code)

---

## ⚠️ Rollback Plan

Falls Migration fehlschlägt:

```bash
# 1. Zu v6.6 zurückkehren
git checkout 6.4-beta

# 2. v7.0 Branch löschen
git branch -D v7.0-supervisor-pattern

# 3. Backend neu starten
cd backend
python main.py
```

---

## 📚 Referenz-Dokumentation

### Must-Read:
- ARCHITECTURE_CURRENT_v6.6.md - Verstehe was geändert wird
- ARCHITECTURE_TARGET_v7.0.md - Verstehe das Ziel
- PYTHON_BEST_PRACTICES.md - Code-Standards
- CLAUDE_BEST_PRACTICES.md - AI-Integration

### LangGraph Docs:
- [Supervisor Pattern](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/)
- [Command API](https://blog.langchain.com/command-a-new-tool-for-multi-agent-architectures-in-langgraph/)
- [Multi-Agent Systems](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

---

## 🚀 Post-Migration

### Nach erfolgreicher Migration:

1. **Performance messen:**
   - LLM-Calls pro Request (sollte sinken)
   - Response-Zeit (sollte gleich bleiben)
   - Token-Verbrauch (sollte sinken)

2. **Dokumentation aktualisieren:**
   - README.md
   - API-Dokumentation
   - Entwickler-Guide

3. **Team-Schulung:**
   - Supervisor-Pattern erklären
   - Neue Debug-Workflows
   - Erweiterungs-Möglichkeiten

---

**Erstellt von:** Claude (Opus 4.1)
**Datum:** 2025-10-20
**Version:** 1.0.0
**Support:** Fragen an KI_AutoAgent Team