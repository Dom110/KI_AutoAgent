# 🧠 CLAUDE'S SYSTEM MEMORY - KI AutoAgent

## 📌 QUICK CONTEXT (für mich wenn ich zurückkomme)
- **Wer**: Du (Dominik) und ich (Claude) - wir arbeiten zu zweit
- **Version**: 4.0.0 (22.9.2025) - MAJOR Update mit System-Verständnis
- **Zweck**: Multi-Agent AI System für VS Code Development
- **Meine Rolle**: System verstehen, verbessern, debuggen, Infrastructure analysieren

## 🏗️ WAS IST WO - Die wichtigsten Orte

### Python Backend (hier passiert ALLES Wichtige)
```
📁 backend/
├── agents/specialized/           ← DIE AGENTS (9 Stück, alle in Python!)
│   ├── architect_agent.py       ← NEU: understand_system(), analyze_infrastructure_improvements()
│   ├── codesmith_agent.py       ← NEU: analyze_codebase(), implement_with_patterns()
│   ├── orchestrator_agent_v2.py ← Routing & Task Decomposition
│   ├── opus_arbitrator_agent.py ← Konfliktlösung mit Claude Opus 4.1
│   ├── docubot_agent.py
│   ├── fixerbot_agent.py
│   ├── reviewer_gpt_agent.py
│   ├── research_agent.py
│   └── tradestrat_agent.py
├── core/                         ← NEU in v4.0: Analyse-Engine!
│   ├── indexing/                ← Tree-sitter AST (ich habe das heute gebaut!)
│   │   ├── tree_sitter_indexer.py (766 Zeilen)
│   │   └── code_indexer.py (524 Zeilen)
│   ├── analysis/                ← Security & Quality Tools
│   │   ├── semgrep_analyzer.py (440 Zeilen)
│   │   ├── vulture_analyzer.py (Dead Code)
│   │   └── radon_metrics.py (Complexity)
│   ├── memory/                  ← Vector Storage, Pattern Recognition
│   └── workflow/                ← Task Execution Engine
├── services/
│   └── diagram_service.py       ← NEU: Mermaid Visualisierung (600+ Zeilen)
├── api/
│   └── server.py                ← FastAPI, Port 8000, WebSocket
└── utils/
    ├── openai_service.py        ← GPT-5 Integration
    ├── claude_code_service.py   ← Claude 4.1 via CLI
    └── perplexity_service.py    ← Web Search
```

### VS Code Extension (nur UI - KEINE Logic!)
```
📁 vscode-extension/
├── src/
│   ├── extension.ts             ← Entry Point
│   ├── ui/
│   │   └── MultiAgentChatPanel.ts ← Chat Interface
│   └── api/
│       └── BackendClient.ts    ← WebSocket zu Python Backend
├── package.json                 ← Version 4.0.0 (war 3.81.3)
└── [DEPRECATED]/                ← Alte TypeScript Agents - IGNORIEREN!
```

## 🔧 WAS ICH HEUTE GEBAUT HABE (22.9.2025)

### v4.0.0 - Die große Transformation

**VORHER (v3.x)**: Agents konnten nur Code generieren
**JETZT (v4.0)**: Agents VERSTEHEN das System inheränt!

### Konkrete neue Features:

1. **ArchitectAgent kann jetzt:**
   ```python
   # System komplett verstehen
   await architect.understand_system()

   # DIE Hauptfrage beantworten
   await architect.analyze_infrastructure_improvements()
   # → Gibt konkrete Verbesserungen mit Code-Beispielen!

   # Architektur visualisieren
   await architect.generate_architecture_flowchart()
   # → Mermaid Diagrams!
   ```

2. **CodeSmithAgent kann jetzt:**
   ```python
   # Codebase analysieren und Patterns lernen
   await codesmith.analyze_codebase()

   # Mit gelernten Patterns implementieren
   await codesmith.implement_with_patterns(spec)

   # Dead Code finden und aufräumen
   await codesmith.cleanup_dead_code()
   ```

### Dateien die ich heute erstellt habe:
- ✅ 7 neue Core-Module (indexing, analysis)
- ✅ 600+ Zeilen Diagram Service
- ✅ 25+ neue Dependencies in requirements.txt
- ✅ Test Script (test_system_understanding.py)
- ✅ Migration Guide für v4.0

## ❓ DIE WICHTIGSTE FRAGE: Infrastructure Improvements

**Frage**: "Was kann an der Infrastruktur verbessert werden?"

**Was passiert**:
1. 🔍 **Scan**: Tree-sitter AST indexiert ALLE Files
2. 🔎 **Analyse**: Sucht nach Cache, Redis, Pool, Indexes, etc.
3. 📊 **Metrics**: Radon berechnet Complexity & Maintainability
4. 🔒 **Security**: Semgrep scannt nach Vulnerabilities
5. 🎨 **Visualize**: Mermaid generiert Architektur-Diagramme
6. 💡 **Suggest**: Konkrete Verbesserungen mit Code!

**Typische Antwort**:
```markdown
### 🚀 Konkrete Verbesserungen (Priorisiert)

1. **Add Redis Caching** [QUICK WIN]
   - Problem: No caching detected
   - Solution: Redis für Session & API Response Caching
   - Code: [Funktionierender Redis Decorator]
   - Impact: 70% weniger API Calls

2. **Connection Pooling** [QUICK WIN]
   - Problem: Neue Connection für jeden Call
   - Solution: httpx.AsyncClient mit Pool
   - Impact: 40% schnellere Requests
```

## 🐛 BEKANNTE PROBLEME & WORKAROUNDS

1. **Import Errors bei neuen Modulen**
   - Problem: `ModuleNotFoundError: tree_sitter`
   - Fix: `pip install -r backend/requirements.txt`

2. **Claude CLI nicht installiert**
   - Problem: CodeSmithAgent braucht Claude Code CLI
   - Fix: `npm install -g @anthropic-ai/claude-code` oder anderen Agent nutzen

3. **Performance bei großen Repos**
   - Problem: Indexing dauert lange
   - Fix: Nur Subdirectory scannen: `understand_system('./src')`

4. **Version History Gap**
   - v3.60.0 - v3.81.3 sind undokumentiert
   - Nicht kritisch, einfach ignorieren

## 💡 PRAKTISCHE COMMANDS & TRICKS

```bash
# Quick Test ob alles läuft
cd backend && python test_system_understanding.py

# NUR Infrastructure-Analyse (ohne Test)
python -c "
from agents.specialized.architect_agent import ArchitectAgent
import asyncio
agent = ArchitectAgent()
result = asyncio.run(agent.analyze_infrastructure_improvements())
print(result)
"

# Dependencies Problem debuggen
pip list | grep -E "tree-sitter|semgrep|radon|vulture|mermaid"

# Backend Server starten
cd backend && uvicorn api.server:app --reload --port 8000

# VS Code Extension testen
cd vscode-extension && npm run compile && code --extensionDevelopmentPath=.
```

## 🔴 KRITISCHE REGELN (nie vergessen!)

1. **ALLE Agents** → Python Backend (`backend/agents/`)
2. **KEINE Business Logic** → VS Code Frontend
3. **ALLE AI Calls** → Nur aus Python Backend
4. **WebSocket** → Einzige Verbindung Frontend ↔ Backend
5. **Version 4.0.0** → Breaking Changes wegen neuer Agent APIs

## 📝 WORKING NOTES (für unsere Zusammenarbeit)

### Unsere Arbeitsweise:
- **Pragmatisch**: Quick Wins > Perfekte Lösungen
- **Direkt**: Keine Corporate-Sprache, klare Ansagen
- **Fokussiert**: Infrastructure-Verbesserungen sind Priorität
- **Iterativ**: Erst funktionieren, dann optimieren

### Was der User (Dominik) typischerweise will:
- Konkrete Verbesserungen, keine Theorie
- Funktionierende Code-Beispiele
- Performance & Security Improvements
- Das System soll sich selbst verstehen

### Was ich (Claude) beachten soll:
- Immer Tree-sitter für Code-Analyse nutzen
- Mermaid für Visualisierungen
- Konkrete Beispiele mit Impact-Schätzung
- Python Backend hat ALLE Intelligenz

## 🔄 CHANGELOG (was wir gemacht haben)

### 22.9.2025 - v4.0.0 - Cognitive Architecture
- Komplett neues System-Verständnis implementiert
- Tree-sitter AST Indexing für alle Sprachen
- Mermaid Diagram Generation
- Infrastructure Analysis ("Was kann verbessert werden?")
- 25+ neue Dependencies
- Breaking Changes in Agent APIs

### 21.9.2025 - v3.59.0 - Project-Agnostic
- System arbeitet mit jedem Projekt-Typ
- Dynamische Projekt-Erkennung

### [v3.60-v3.81.3] - Undokumentiert
- Verschiedene Fixes (Details unbekannt)

## 🎯 NÄCHSTE SCHRITTE

1. [ ] **Testen**: Backend wirklich mit allen neuen Features starten
2. [ ] **Performance**: Bei großen Codebases optimieren (Caching?)
3. [ ] **Error Handling**: Bessere Fehler wenn Tools fehlen
4. [ ] **UI Integration**: Infrastructure-Analyse im Chat anzeigen

## 🔮 ZUKUNFTS-IDEEN

- **Auto-Fix**: Gefundene Probleme automatisch beheben
- **CI/CD Integration**: Infrastructure-Check in Pipeline
- **Real-time Monitoring**: Live Code-Quality Dashboard
- **Learning**: System lernt aus gemachten Verbesserungen

---

## 📌 QUICK REFERENCE

**Version**: 4.0.0
**Backend Port**: 8000
**Main Files**:
- `backend/agents/specialized/architect_agent.py` - System Understanding
- `backend/agents/specialized/codesmith_agent.py` - Pattern Learning
- `backend/test_system_understanding.py` - Test Script

**Die wichtigste Methode**:
```python
architect.analyze_infrastructure_improvements()
```

**Bei Problemen**: Erst requirements installieren, dann testen!

---

*Letzte Aktualisierung: 22.9.2025 - v4.0.0 Implementation*