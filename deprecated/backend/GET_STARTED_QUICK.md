# 🚀 QUICK START - KI AutoAgent Backend v4.0

## 🎯 Du willst nur schnell testen ob alles läuft?

```bash
# 1. Dependencies installieren (einmalig)
pip install -r requirements.txt

# 2. Test ob System-Verständnis funktioniert
python test_system_understanding.py

# 3. Infrastructure-Analyse direkt ausführen
python -c "from agents.specialized.architect_agent import ArchitectAgent; import asyncio; print(asyncio.run(ArchitectAgent().analyze_infrastructure_improvements()))"
```

## 🔥 Die wichtigste Funktion

```python
from agents.specialized.architect_agent import ArchitectAgent

agent = ArchitectAgent()

# Das System verstehen lassen
await agent.understand_system()

# DIE Frage beantworten
result = await agent.analyze_infrastructure_improvements()
print(result)  # Konkrete Verbesserungen mit Code!
```

## 📁 Wo ist was?

```
backend/
├── agents/specialized/     ← ALLE 9 Agents
├── core/
│   ├── indexing/          ← NEU: AST Parser (Tree-sitter)
│   └── analysis/          ← NEU: Security & Metrics
├── services/
│   └── diagram_service.py ← NEU: Mermaid Diagrams
└── test_system_understanding.py ← START HIER!
```

## ⚠️ Häufige Probleme

**Problem**: `ModuleNotFoundError: tree_sitter`
```bash
pip install tree-sitter --no-cache-dir
```

**Problem**: `Claude Code CLI not found`
```bash
# Entweder installieren:
npm install -g @anthropic-ai/claude-code

# Oder anderen Agent nutzen (ArchitectAgent geht auch!)
```

**Problem**: Indexing dauert ewig
```python
# Nur einen Ordner scannen:
await agent.understand_system('./backend')  # statt '.'
```

## 💡 Was ist neu in v4.0?

- **Agents verstehen jetzt Code** (nicht nur generieren)
- **Infrastructure-Analyse** mit konkreten Vorschlägen
- **Mermaid Diagrams** automatisch generiert
- **Security Scanning** eingebaut
- **Dead Code Detection** inklusive

## 🎯 Nächster Schritt

```bash
python test_system_understanding.py
```

Das erstellt 3 Dateien:
- `infrastructure_report.md` - Was kann verbessert werden
- `architecture_flowchart.md` - System als Diagramm
- `dead_code_cleanup.md` - Unused Code zum entfernen

---

**Version**: 4.0.0 | **Port**: 8000 | **Agents**: 9 (alle in Python!)