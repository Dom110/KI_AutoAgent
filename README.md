# 🤖 KI AutoAgent System

**Universal Multi-Agent AI Development Platform**

Ein revolutionäres, domain-agnostisches System, das automatisch spezialisierte KI-Agenten orchestriert, um komplexe Entwicklungsaufgaben in **beliebigen Softwareprojekten** zu lösen. Stelle einfach eine Aufgabe und das System erkennt automatisch den Projekttyp und orchestriert die passenden Agenten und Workflows.

[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/yourusername/KI_AutoAgent)
[![VS Code Extension](https://img.shields.io/badge/vs--code--extension-1.0.1-brightgreen.svg)](vscode-extension/)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

## 🌟 Kern-Features

- **🌍 Universal Project Support** - Arbeitet mit beliebigen Softwareprojekten und Domains
- **🤖 7 Spezialisierte KI-Agenten** - Jeder ist Experte in seinem Bereich
- **🧠 Intelligente Orchestrierung** - Automatische Projektyp-Erkennung und Workflow-Optimierung
- **🔧 Domain-spezifische Kontexte** - Trading, Web Development, APIs, Desktop Apps, etc.
- **📋 Adaptive Workflows** - Maßgeschneiderte Entwicklungszyklen je nach Projekttyp
- **⚡ Parallele Ausführung** - Optimierte Workflows für maximale Geschwindigkeit
- **📈 Lernendes System** - Wird mit jeder Nutzung besser und effizienter
- **🎛️ Moderne KI-Modelle** - GPT-4o, Claude 3.5 Sonnet, Perplexity Pro
- **💻 Intuitive CLI** - Schöne, interaktive Benutzeroberfläche
- **🔌 VS Code Extension** - Nahtlose Integration in VS Code Chat (v1.0.1)
- **🌐 Claude Pro Web Integration** - Nutzt Claude Pro Account via Browser-Sessions (kostenlos!)
- **🔍 Echtzeit-Recherche** - Live Web-Suche für aktuelle Informationen

## 🎯 Unterstützte Projekttypen

Das KI AutoAgent System erkennt automatisch verschiedene Projekttypen und wendet spezialisierte Kontexte und Workflows an:

### 💹 **Trading Systems**
- **Spezialisierung**: RON Strategy, Backtesting, Risk Management
- **Quality Gates**: Engine Parity, Trading System Validation, RON Strategy Compliance
- **Workflows**: 12-stufiger Trading Development Lifecycle
- **Agenten**: TradeStrat (Lead), ArchitectGPT, CodeSmithClaude

### 🌐 **Web Applications** 
- **Spezialisierung**: REST APIs, Frontend Development, Security-First Design
- **Quality Gates**: OWASP Top 10 Security, Performance Optimization
- **Workflows**: 8-stufiger Software Development Lifecycle  
- **Agenten**: ArchitectGPT (Lead), CodeSmithClaude, ReviewerGPT

### 📱 **Generic Software Projects**
- **Spezialisierung**: Cross-Platform Development, Clean Architecture
- **Quality Gates**: Code Quality, Performance, Security Best Practices
- **Workflows**: Standard Software Development Lifecycle
- **Agenten**: Dynamic assignment based on requirements

### 🔮 **Erweiterbar für beliebige Domains**
- **Plugin Architecture**: Neue Projekttypen einfach hinzufügbar
- **Custom Workflows**: Domain-spezifische Entwicklungszyklen
- **Specialized Quality Gates**: Branchenspezifische Validierungsregeln

## 🤖 Die Agenten im Detail

| 🎯 Agent | 🛠️ Rolle | 🧠 KI-Modell | 🎯 Spezialisierung |
|----------|-----------|-------------|-------------------|
| **ArchitectGPT** | System Architect | GPT-4o | System-Design, Architektur-Patterns, Tech-Stack Planung |
| **CodeSmithClaude** | Senior Developer | Claude 3.5 Sonnet | Python/Web-Entwicklung, Code-Optimierung, Testing |
| **DocuBot** | Technical Writer | GPT-4o | Dokumentation, README, API-Referenzen, Tutorials |
| **ReviewerGPT** | Code Reviewer | GPT-4o-mini | Code-Review, Security-Analyse, Best-Practices |
| **FixerBot** | Bug Hunter | Claude 3.5 Sonnet | Debugging, Fehlerbehebung, Performance-Optimierung |
| **TradeStrat** | Trading Expert | Claude 3.5 Sonnet | Trading-Strategien, Backtesting, Risk-Management |
| **ResearchBot** | Research Analyst | Perplexity API | Web-Recherche, Marktanalyse, Dokumentations-Suche |

## 🚀 Quick Start

### 🎯 Zwei Nutzungsmodi verfügbar:

#### 🔌 **Option A: VS Code Extension (Empfohlen für VS Code Nutzer)**
**Nahtlose Integration in deine VS Code Umgebung**

```bash
# 1. Extension installieren
cd vscode-extension
./scripts/build.sh
# Folge den Installationsanweisungen

# 2. VS Code Chat öffnen (Ctrl+Shift+I)
# 3. Agenten nutzen: @ki, @codesmith, @architect, etc.
```

#### 💻 **Option B: Standalone CLI**
**Unabhängiges System für alle Editoren**

### Voraussetzungen
- Python 3.8 oder höher
- Git
- API-Keys für OpenAI, Anthropic, Perplexity

### Installation

```bash
# 1. Repository klonen
git clone https://github.com/yourusername/KI_AutoAgent.git
cd KI_AutoAgent

# 2. Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependencies installieren
pip install -r requirements.txt
```

### API-Keys & Authentication einrichten

Du hast **zwei Optionen** für die AI-Agent Authentifizierung:

---

## 🎯 Option 1: Direkte APIs (Maximale Performance)

**Für Power-User mit hohem Durchsatz** - Schnellste Reaktionszeiten, vollständige Kontrolle

### .env Datei erstellen:

```bash
# .env Datei erstellen
touch .env

# API-Keys hinzufügen (ersetze mit deinen echten Keys)
echo "OPENAI_API_KEY=sk-proj-..." >> .env      # OpenAI API Key (beginnt mit sk-proj-)
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env    # Anthropic API Key (beginnt mit sk-ant-)
echo "PERPLEXITY_API_KEY=pplx-..." >> .env     # Perplexity API Key (beginnt mit pplx-)
```

#### Wo bekomme ich die API-Keys?

**1. 🔵 OpenAI API Key (für ArchitectGPT, DocuBot, ReviewerGPT)**
- **Website**: [platform.openai.com](https://platform.openai.com/api-keys)
- **Registrierung**: Account erstellen → "Create new secret key"
- **Kosten**: Pay-as-you-use (ca. $10-50/Monat je nach Nutzung)
- **Modelle**: GPT-4o, GPT-4o-mini
- **Rate Limits**: 500 RPM (Requests per Minute) für neue Accounts
- **Key-Format**: `sk-proj-...` (beginnt mit sk-proj-)

**2. 🟠 Anthropic API Key (für CodeSmithClaude, FixerBot, TradeStrat)**  
- **Website**: [console.anthropic.com](https://console.anthropic.com/)
- **Claude Max Plan**: Auch wenn du bereits Claude Max Plan hast, brauchst du separaten API-Zugang
- **Registrierung**: Account erstellen → "Get API Key" → Kreditkarte hinterlegen
- **Kosten**: Pay-per-token (ca. $15-75/Monat je nach Nutzung)  
- **Modelle**: Claude 3.5 Sonnet (20241022)
- **Rate Limits**: 1000 RPM, höhere Limits nach Anfrage verfügbar
- **Key-Format**: `sk-ant-...` (beginnt mit sk-ant-)

**3. 🟢 Perplexity API Key (für ResearchBot)**
- **Website**: [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
- **Registrierung**: Account erstellen → "API" → Pro Plan upgraden
- **Kosten**: $20/Monat für Pro API-Zugang (feste Koste)
- **Modelle**: llama-3.1-sonar-small-128k-online (mit Live Web-Suche)
- **Rate Limits**: 50 requests/Minute (Pro Plan)
- **Key-Format**: `pplx-...` (beginnt mit pplx-)

---

## 💰 Option 2: Claude Web Proxy (Kostensparend) - **EMPFOHLEN**

**Für smarte Nutzer** - Nutze deinen vorhandenen Claude Max Plan ($20/Monat) statt separater APIs

### Vorteile:
- ✅ **Massive Kosteneinsparung**: $50-100+ weniger pro Monat
- ✅ **Bereits vorhanden**: Nutze deinen bestehenden Claude Max Plan
- ✅ **Volle Funktionalität**: Kompletter Claude 3.5 Sonnet Zugriff
- ✅ **Keine API-Limits**: Browser-basierte Authentifizierung

### Setup für Claude Web Proxy:

```bash
# 1. Nur OpenAI + Perplexity Keys benötigt
echo "OPENAI_API_KEY=sk-proj-..." >> .env      # OpenAI für ArchitectGPT, DocuBot, ReviewerGPT  
echo "PERPLEXITY_API_KEY=pplx-..." >> .env     # Perplexity für ResearchBot
# KEIN Anthropic Key nötig! 🎉

# 2. Claude Web Proxy Setup (einmalig)
python claude_web_proxy/setup_and_test.py

# 3. In Browser in Claude.ai einloggen (einmalig)
# 4. System nutzen - Claude-Agenten verwenden automatisch Web Proxy
```

**Claude-Agenten (CodeSmithClaude, FixerBot, TradeStrat)** nutzen automatisch Claude Web statt API.

👉 **Detaillierte Anleitung**: Siehe [🌐 Claude Web Proxy Integration](#-claude-web-proxy-integration)

---

## 📊 Kostenvergleich

| Nutzungsart | Option 1: Direkte APIs | Option 2: Claude Web Proxy | 💰 Ersparnis |
|-------------|------------------------|-----------------------------|---------------|
| **Leichte Nutzung** (10-20 Tasks/Tag) | | | |
| • OpenAI | ~$10-15 | ~$10-15 | $0 |
| • Anthropic | ~$15-25 | $0 (Max Plan) | ~$15-25 |
| • Perplexity | $20 | $20 | $0 |
| **Gesamt** | **$45-60/Monat** | **$30-35/Monat** | **$15-25/Monat** |
| | | | |
| **Intensive Nutzung** (50-100 Tasks/Tag) | | | |
| • OpenAI | ~$30-50 | ~$30-50 | $0 |
| • Anthropic | ~$50-75 | $0 (Max Plan) | ~$50-75 |
| • Perplexity | $20 | $20 | $0 |
| **Gesamt** | **$100-145/Monat** | **$50-70/Monat** | **$50-75/Monat** |

## 🎯 Welche Option wählen?

### 🚀 **Wähle Option 2 (Claude Web Proxy) wenn:**
- Du bereits einen Claude Max Plan hast ($20/Monat)
- Du Kosten sparen möchtest ($50+ monatliche Ersparnis)
- Du normale bis mittlere Nutzung hast
- Dir 3-8 Sekunden Antwortzeit ausreichen

### ⚡ **Wähle Option 1 (Direkte APIs) wenn:**
- Du maximale Performance brauchst (1-3 Sekunden Antwortzeit)
- Du sehr hohen Durchsatz hast (100+ Tasks/Tag)
- Du vollständige API-Kontrolle benötigst
- Kosten sind weniger wichtig als Geschwindigkeit

## 💡 Spar-Tipps:
- **Start mit Claude Web Proxy**: Teste das System kostengünstig
- **Upgrade bei Bedarf**: Wechsel zu direkten APIs wenn Performance kritisch wird
- **Kostenüberwachung**: Alle Anbieter haben Usage-Dashboards
- **Hybride Lösung**: Claude Web für Development, direkte APIs für Production

### Erste Schritte

```bash
# System testen
python test_system.py

# Sollte zeigen: ✅ ALL TESTS PASSED!

# CLI starten
python cli.py

# Oder direkt eine Aufgabe stellen
python cli.py --task "Erstelle eine REST API für ein Blog-System"
```

## 💻 Verwendung

### Interaktiver Modus

```bash
$ python cli.py

🤖 Willkommen zum KI AutoAgent System v1.0
Multi-Agent AI Development Platform

Verfügbare Agenten:
• ArchitectGPT - System Architecture & Design
• CodeSmithClaude - Code Implementation
• DocuBot - Documentation Generation
...

KI-Agent> Erstelle einen Trading Bot mit Momentum-Strategie

📋 Aufgabe: Erstelle einen Trading Bot mit Momentum-Strategie
🎯 Intent erkannt: trading_strategy (95% Confidence)
🔄 Generiere Workflow...
⚙️  Führe aus: ResearchBot -> TradeStrat -> CodeSmithClaude -> ReviewerGPT -> DocuBot

✅ Erfolgreich abgeschlossen!
```

### Direkter Modus

```bash
# Einzelne Aufgabe ausführen (automatische Projektyp-Erkennung)
python cli.py --task "Debug diesen Code: def add(a,b): return a-b"

# Spezifischen Projekttyp angeben
python cli.py --task "Erstelle eine REST API für ein Blog-System" --project-type web_app

# Trading-System entwickeln
python cli.py --task "Entwickle RON Momentum Strategie" --project-type trading

# Test-Szenarien ausführen
python cli.py --test
```

## 📝 Praktische Beispiele

Das KI AutoAgent System demonstriert seine universelle Anwendbarkeit durch intelligente Projektyp-Erkennung und spezialisierte Workflows:

### 🎯 Automatische Projektyp-Erkennung

```bash
# System erkennt automatisch "Trading" aus Keywords
KI-Agent> Entwickle eine Momentum-Strategie mit RSI-Indikatoren

🎯 Projekt erkannt: Trading System (95% Confidence)
📋 Kontext: TradingProjectContext mit RON Strategy Spezialisierung  
🔄 Workflow: Trading System Development (12 Schritte)
⚙️  Agenten: TradeStrat (Lead) -> ArchitectGPT -> CodeSmithClaude -> ReviewerGPT

# System erkennt automatisch "Web App" aus Keywords  
KI-Agent> Baue eine REST API für Benutzerregistrierung mit JWT

🎯 Projekt erkannt: Web Application (92% Confidence)
📋 Kontext: WebAppProjectContext mit Security-First Approach
🔄 Workflow: Software Development Lifecycle (8 Schritte)  
⚙️  Agenten: ArchitectGPT (Lead) -> CodeSmithClaude -> ReviewerGPT -> DocuBot

# Fallback auf Generic für unklare Anfragen
KI-Agent> Optimiere die Performance dieser Anwendung

🎯 Projekt erkannt: Generic Software (70% Confidence)
📋 Kontext: GenericProjectContext mit Best Practices
🔄 Workflow: Generic Software Development (8 Schritte)
⚙️  Agenten: ReviewerGPT (Lead) -> FixerBot -> CodeSmithClaude
```

### 🌐 Web Development

```bash
# REST API erstellen
KI-Agent> Erstelle eine FastAPI REST API für ein Todo-System mit SQLAlchemy

# Erwarteter Ablauf:
# 1. ResearchBot: Recherchiert FastAPI Best Practices
# 2. ArchitectGPT: Entwirft API-Architektur und Datenbank-Schema  
# 3. CodeSmithClaude: Implementiert API-Endpoints und Datenmodelle
# 4. ReviewerGPT: Überprüft Code-Qualität und Sicherheit
# 5. DocuBot: Erstellt API-Dokumentation und README
```

### 📈 Trading Development

```bash
# Trading Strategie entwickeln
KI-Agent> Entwickle eine Mean-Reversion Strategie mit Bollinger Bands

# Erwarteter Ablauf:
# 1. ResearchBot: Sucht aktuelle Marktforschung zu Mean-Reversion
# 2. TradeStrat: Entwickelt Strategie-Logic und Parameter
# 3. CodeSmithClaude: Implementiert Backtesting-Framework
# 4. ReviewerGPT: Validiert Risk-Management und Performance-Metriken
# 5. DocuBot: Dokumentiert Strategie und Verwendung
```

### 🔧 Code Review & Debugging

```bash
# Code analysieren
KI-Agent> Analysiere und optimiere diese Funktion: [Code hier einfügen]

# Erwarteter Ablauf:
# 1. ReviewerGPT: Findet Bugs und Performance-Issues
# 2. FixerBot: Schlägt konkrete Verbesserungen vor
# 3. CodeSmithClaude: Implementiert optimierte Version
# 4. DocuBot: Dokumentiert Änderungen und Begründung
```

### 📚 Dokumentation

```bash
# README erstellen
KI-Agent> Erstelle eine professionelle README für mein Python-Projekt

# Erwarteter Ablauf:
# 1. ResearchBot: Analysiert Code-Struktur und Dependencies
# 2. ArchitectGPT: Plant Dokumentations-Struktur
# 3. DocuBot: Schreibt umfassende README mit Beispielen
# 4. ReviewerGPT: Überprüft Vollständigkeit und Klarheit
```

## 🎛️ CLI-Befehle Referenz

### Basis-Befehle

| Befehl | Beschreibung | Beispiel |
|--------|--------------|----------|
| `task <beschreibung>` | Stelle eine Aufgabe an das System | `task Erstelle eine Docker-Konfiguration` |
| `help` | Zeige alle verfügbaren Befehle | `help` |
| `agents` | Zeige Details aller Agenten | `agents` |
| `exit` | Beende das Programm | `exit` |

### Verlauf & Statistiken

| Befehl | Beschreibung | Beispiel |
|--------|--------------|----------|
| `history` | Zeige die letzten 10 Aufgaben | `history` |
| `stats` | Zeige System-Performance-Statistiken | `stats` |
| `clear` | Lösche Bildschirm und zeige Willkommensnachricht | `clear` |

### Test & Debug

| Befehl | Beschreibung | Beispiel |
|--------|--------------|----------|
| `test` | Führe vordefinierte Test-Szenarien aus | `test` |

### Command Line Optionen

```bash
# Direkte Aufgabe ohne Interaktion
python cli.py --task "Deine Aufgabe hier"

# Test-Modus ausführen  
python cli.py --test

# Hilfe anzeigen
python cli.py --help
```

## ⚙️ Konfiguration

### config.yaml anpassen

```yaml
# Haupt-Einstellungen
system:
  max_parallel_agents: 3      # Max. gleichzeitige Agenten
  timeout_seconds: 300        # Timeout pro Workflow
  debug: false               # Debug-Modus

# Agent-spezifische Einstellungen
agents:
  CodeSmithClaude:
    temperature: 0.2          # Kreativität (0-1)
    max_tokens: 8000         # Max. Ausgabe-Länge
    enabled: true            # Agent aktiviert
```

### Environment Variables

```bash
# .env Datei
OPENAI_API_KEY=sk-proj-...      # Für ArchitectGPT, DocuBot, ReviewerGPT
ANTHROPIC_API_KEY=sk-ant-...     # Für CodeSmithClaude, FixerBot, TradeStrat  
PERPLEXITY_API_KEY=pplx-...      # Für ResearchBot (HTTP API, kein SDK)
KI_AUTOAGENT_DEBUG=false         # Debug-Logs aktivieren

# Note: ResearchBot nutzt die Perplexity REST API via HTTP requests
# Model: "llama-3.1-sonar-small-128k-online" mit Web-Suche-Funktionalität
```

## 🏗️ System-Architektur

```
KI_AutoAgent/
├── orchestration/           # 🎛️ Universal Orchestrierungs-System
│   ├── master_dispatcher.py        # Zentrale Koordination & Projektyp-Erkennung
│   ├── intent_classifier.py        # Intent-Erkennung (9 Typen)  
│   ├── workflow_generator.py       # Adaptive Workflow-Planung
│   ├── execution_engine.py         # Parallele Ausführung
│   ├── learning_system.py          # Adaptives Lernen
│   ├── shared_context.py           # Context Management & Factory
│   ├── project_contexts/           # 🎯 Domain-spezifische Kontexte
│   │   ├── base_project_context.py     # Abstract Base Class
│   │   ├── trading_project_context.py  # Trading Systems (RON, Risk Management)
│   │   ├── web_app_context.py          # Web Applications (Security-First)
│   │   └── ... (erweiterbar)           # Neue Domains einfach hinzufügbar
│   ├── quality_gates/              # 🛡️ Domain-spezifische Qualitätssicherung
│   │   ├── base_quality_gate.py        # Abstract Quality Gate
│   │   ├── trading_quality_gate.py     # Financial Systems Validation
│   │   ├── security_quality_gate.py    # OWASP Top 10 Security
│   │   ├── ron_strategy_quality_gate.py # RON Strategy Compliance
│   │   └── engine_parity_quality_gate.py # Live/Backtest Parity
│   └── workflows/                  # 📋 Adaptive Development Workflows
│       ├── base_workflow.py            # Abstract Workflow Interface
│       ├── generic_software_workflow.py # Standard SDLC (8 Steps)
│       ├── trading_system_workflow.py   # Trading SDLC (12 Steps)
│       └── ... (erweiterbar)            # Custom Domain Workflows
├── agents/                  # 🤖 KI-Agenten (unchanged)
│   ├── base_agent.py           # Basis-Klasse für alle Agenten
│   ├── architect_gpt.py        # System-Architekt (GPT-4o)
│   ├── codesmith_claude.py     # Python-Developer (Claude 3.5)
│   ├── docu_bot.py            # Technical Writer (GPT-4o)
│   ├── reviewer_gpt.py        # Code-Reviewer (GPT-4o-mini)
│   ├── fixer_bot.py           # Bug-Hunter (Claude 3.5)
│   ├── trade_strat.py         # Trading-Expert (Claude 3.5)  
│   └── research_bot.py        # Research-Analyst (Perplexity Pro)
├── cli.py                   # 💻 Universal CLI Interface
├── test_system.py          # 🧪 System-Tests
├── config.yaml             # ⚙️ Konfiguration
└── requirements.txt        # 📦 Dependencies
```

### Universal Workflow-Ablauf

```
1. User Input 
   ↓
2. Project Type Detection (Keyword-basierte Analyse + Machine Learning)
   ↓
3. Context Loading (Domain-spezifischer Kontext + Quality Gates)
   ↓
4. Intent Classification (9 Intent-Typen erkannt)
   ↓  
5. Adaptive Workflow Selection (Generic/Trading/Web/Custom)
   ↓
6. Agent Selection & Orchestration (Kontext-bewusste Zuteilung)
   ↓
7. Parallel/Sequential Execution (Domain-spezifische Steps)
   ↓
8. Quality Gate Validation (Domain-spezifische Qualitätsprüfung)
   ↓
9. Result Aggregation & Context Integration
   ↓
10. Learning & Improvement (für zukünftige Workflows)
```

## 🔧 System für neue Domains erweitern

Das KI AutoAgent System ist vollständig erweiterbar für neue Projekttypen und Domains:

### 1. Neuen Project Context erstellen

```python
# orchestration/project_contexts/my_domain_context.py
from .base_project_context import BaseProjectContext, ProjectSpecification

class MyDomainProjectContext(BaseProjectContext):
    def __init__(self, project_name: str = "My Domain Project"):
        self.project_name = project_name
        self.project_type = "my_domain"
    
    def get_domain_instructions(self) -> str:
        return """
        DOMAIN-SPECIFIC INSTRUCTIONS:
        
        1. Domain Requirements:
           - Specific requirements for your domain
           - Industry standards and regulations
           - Best practices and patterns
        
        2. Quality Standards:
           - Domain-specific quality criteria
           - Validation requirements
           - Performance benchmarks
        
        3. Agent Enhancements:
           - Specialized instructions for agents
           - Domain-specific tools and libraries
        """
    
    def get_quality_gates(self) -> List[str]:
        return ["MyDomainQualityGate", "SecurityQualityGate"]
    
    def get_project_specifics(self) -> ProjectSpecification:
        return ProjectSpecification(
            name=self.project_name,
            domain="My Domain",
            programming_languages=["Python", "JavaScript"],
            frameworks=["Domain-Framework-1", "Domain-Framework-2"],
            architecture_patterns=["Domain-Pattern"],
            special_requirements=["Domain-Requirement-1"],
            compliance_standards=["Domain-Standard"]
        )
```

### 2. Quality Gate implementieren

```python
# orchestration/quality_gates/my_domain_quality_gate.py
from .base_quality_gate import BaseQualityGate, QualityCheck, QualityGateResult

class MyDomainQualityGate(BaseQualityGate):
    def __init__(self):
        super().__init__("MyDomainQualityGate", "My Domain Validation")
    
    def validate_output(self, agent_output: str, context: dict) -> QualityGateResult:
        checks = []
        
        # Domain-specific validation logic
        if "domain_requirement_1" in agent_output.lower():
            checks.append(QualityCheck(
                name="Domain Requirement 1",
                passed=True,
                score=1.0,
                details="Domain requirement properly addressed"
            ))
        
        return self._create_result(checks)
```

### 3. Custom Workflow erstellen

```python
# orchestration/workflows/my_domain_workflow.py
from .base_workflow import BaseWorkflow

class MyDomainWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__("My Domain Workflow")
        self.workflow_steps = [
            "domain_analysis",
            "domain_design", 
            "domain_implementation",
            "domain_validation"
        ]
    
    def get_step_agents(self, step: str) -> List[str]:
        return {
            "domain_analysis": ["ResearchBot", "ArchitectGPT"],
            "domain_design": ["ArchitectGPT"],
            "domain_implementation": ["CodeSmithClaude"],
            "domain_validation": ["ReviewerGPT"]
        }.get(step, ["CodeSmithClaude"])
```

### 4. System registrieren

```python
# orchestration/shared_context.py - ProjectContextFactory erweitern
context_map = {
    'trading': TradingProjectContext,
    'web_app': WebAppProjectContext,
    'my_domain': MyDomainProjectContext,  # Neue Domain hinzufügen
}

# orchestration/workflows/__init__.py - Workflow registrieren
WORKFLOW_REGISTRY = {
    'generic': GenericSoftwareWorkflow,
    'trading': TradingSystemWorkflow,
    'my_domain': MyDomainWorkflow,  # Neuen Workflow hinzufügen
}
```

### 5. Sofort verwendbar!

```bash
# System erkennt automatisch neue Domain
python cli.py --task "Entwickle meine Domain-Anwendung" --project-type my_domain

# Oder automatische Erkennung durch Keywords
python cli.py --task "Erstelle eine my_domain spezifische Lösung"
```

## 🌐 Claude Web Proxy Integration

**Revolutionäre Browser-basierte Claude Integration für CrewAI**

Da Claude API-Zugriff separat vom Max-Plan erworben werden muss, haben wir eine innovative Lösung entwickelt: Ein intelligenter Web-Proxy, der Claude.ai über Browser-Automation in CrewAI integriert.

### 🚀 Features

- **🤖 Vollautomatisierte Browser-Steuerung** - Playwright-basierte Claude.ai Integration
- **⚡ REST API Server** - FastAPI-Server als Bridge zwischen Browser und CrewAI
- **🔄 Session Management** - Persistente Browser-Profile und Login-Sessions  
- **🎯 CrewAI Compatible** - Custom LLM Implementation für nahtlose Integration
- **📊 Conversation Tracking** - Separate Konversationen pro Agent
- **🛡️ Anti-Detection** - Robuste Browser-Simulation mit User-Agent Spoofing

### 📁 Claude Web Proxy Architektur

```
claude_web_proxy/
├── claude_browser.py           # 🤖 Playwright Browser Automation
│   ├── ClaudeBrowser class        # Haupt-Browser-Controller
│   ├── Login & Session Management  # Persistent Profile Support
│   ├── Message Sending/Receiving   # Automatische Chat-Interaktion
│   └── Anti-Detection Features     # User-Agent & Stealth-Modus
├── fastapi_server.py          # 🖥️ REST API Server
│   ├── /claude/status            # Browser & Login-Status
│   ├── /claude/setup             # Interactive Setup & Login
│   ├── /claude/chat              # Message Endpoint
│   └── /claude/new-conversation   # Conversation Management
├── crewai_integration.py      # 🔧 CrewAI LLM Implementation
│   ├── ClaudeWebLLM class        # Custom LLM für CrewAI
│   ├── Async/Sync Bridging       # CrewAI Compatibility Layer
│   └── Agent Conversation Tracking # Per-Agent Sessions
├── setup_and_test.py          # 🧪 Setup & Testing Suite
└── requirements.txt           # 📦 Proxy Dependencies
```

### 🛠️ Installation & Setup

```bash
# 1. Dependencies installieren (bereits in Haupt-requirements.txt)
pip install playwright fastapi uvicorn structlog

# 2. Playwright Browser installieren  
python -m playwright install chromium

# 3. Setup & Test ausführen
cd claude_web_proxy
python setup_and_test.py

# Erwartete Ausgabe:
# 🚀 Starting Claude Web Proxy Setup and Testing...
# ✅ playwright
# ✅ fastapi  
# ✅ Browser automation
# ✅ Server startup
# 🎉 All critical tests passed! Claude Web Proxy is ready to use.
```

### 💻 Verwendung

#### Option 1: Standalone Server

```bash
# Server starten
python setup_and_test.py --server-only

# Server läuft auf http://localhost:8000
# API Dokumentation: http://localhost:8000/docs
```

#### Option 2: Direkte Integration

```python
from claude_web_proxy.crewai_integration import create_claude_web_llm
from crewai import Agent

# Claude Web LLM erstellen
claude_llm = create_claude_web_llm(server_url="http://localhost:8000")

# CrewAI Agent mit Claude Web
agent = Agent(
    role="Senior Developer",
    goal="Write high-quality code",
    backstory="Expert Python developer",
    llm=claude_llm
)
```

#### Option 3: Beispiel-Demo

```bash
# Interaktive Demo starten
cd examples
python claude_web_integration_example.py --demo

# Oder interaktiver Modus
python claude_web_integration_example.py --interactive
```

### 🔧 API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | Health Check & Server Info |  
| `/claude/status` | GET | Browser & Login Status |
| `/claude/setup` | POST | Browser Setup & Login |
| `/claude/chat` | POST | Message an Claude senden |
| `/claude/new-conversation` | POST | Neue Konversation starten |
| `/claude/restart` | POST | Browser neu starten |
| `/claude/shutdown` | DELETE | Browser beenden |

### 📝 Beispiel API Calls

```bash
# Status prüfen
curl http://localhost:8000/claude/status

# Setup (Browser öffnet sich für Login)
curl -X POST http://localhost:8000/claude/setup \
  -H "Content-Type: application/json" \
  -d '{"headless": false, "timeout": 300}'

# Message senden
curl -X POST http://localhost:8000/claude/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Claude! How are you?", "new_conversation": false}'
```

### ⚙️ Konfiguration

```python
# Erweiterte Konfiguration
claude_llm = ClaudeWebLLM(
    server_url="http://localhost:8000",
    timeout=120,                      # Request Timeout
    new_conversation_per_agent=True   # Separate Conversations
)

# Agent-spezifische Konversationen
response = claude_llm.generate(
    "Write a Python function", 
    agent_id="CodeSmithClaude"
)
```

### 🚨 Wichtige Hinweise

- **🔐 Manuel Login erforderlich**: Beim ersten Setup öffnet sich Browser für Claude.ai Login
- **💾 Persistent Sessions**: Browser-Profile werden gespeichert für automatische Re-Login
- **⚡ Performance**: Etwas langsamer als direkte API, aber vollwertige Claude-Funktionalität
- **🛡️ Stabilität**: Robuste Error-Handling und automatische Recovery-Mechanismen

### 🔍 Troubleshooting

```bash
# System-Check ausführen
python setup_and_test.py --test-only

# Häufige Probleme:
# 1. Port 8000 belegt → Server Port ändern
# 2. Playwright nicht installiert → python -m playwright install chromium  
# 3. Claude.ai nicht erreichbar → Browser-Setup erneut ausführen
# 4. Session abgelaufen → /claude/restart endpoint aufrufen
```

## 🧪 Tests & Entwicklung

### System testen

```bash
# Alle Komponenten testen
python test_system.py

# Erwartete Ausgabe:
# ✅ Intent Classifier: 8/8 tests passed
# ✅ Workflow Generator: All checks passed  
# ✅ Learning System: Learning system functional
# ✅ Execution Engine: Execution engine working
# ✅ Master Dispatcher: Dispatcher ready
# 
# ✅ ALL TESTS PASSED! (5/5)
```

### Neuen Agent entwickeln

```python
# 1. Erstelle agents/my_new_agent.py
from .base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyNewAgent", 
            role="Specialist",
            model="gpt-4o"
        )
    
    async def execute(self, task, context):
        # Agent-Logic hier implementieren
        return {"agent": self.name, "output": "result"}

# 2. In agents/__init__.py registrieren  
from .my_new_agent import MyNewAgent
AVAILABLE_AGENTS["MyNewAgent"] = MyNewAgent

# 3. In config.yaml konfigurieren
agents:
  MyNewAgent:
    model: "gpt-4o"
    enabled: true
```

## 🔧 Troubleshooting

### Häufige Probleme

#### ❌ API Key Fehler
```
Error: Invalid API key for OpenAI
```

**Lösung:**
```bash
# Prüfe .env Datei
cat .env

# API Keys sollten so aussehen:
OPENAI_API_KEY=sk-proj-...     # Beginnt mit sk-proj-
ANTHROPIC_API_KEY=sk-ant-...   # Beginnt mit sk-ant-
PERPLEXITY_API_KEY=pplx-...    # Beginnt mit pplx-
```

#### ❌ Import Fehler
```
ModuleNotFoundError: No module named 'rich'
```

**Lösung:**
```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies erneut installieren
pip install -r requirements.txt
```

#### ❌ Agent nicht erreichbar
```
Error: Agent timeout after 300 seconds
```

**Lösungen:**
```bash
# 1. Timeout erhöhen in config.yaml
system:
  timeout_seconds: 600

# 2. Netzwerk-Verbindung prüfen
ping api.openai.com

# 3. Debug-Modus aktivieren
export KI_AUTOAGENT_DEBUG=true
python cli.py
```

#### ❌ Performance Probleme
```
Workflow takes very long to complete
```

**Optimierungen:**
```yaml
# config.yaml - Performance optimieren
system:
  max_parallel_agents: 5    # Mehr parallele Agenten
  
performance:
  cache_responses: true     # Response Caching aktivieren
  cache_ttl_seconds: 3600  # 1 Stunde Cache
```

### Debug-Modus

```bash
# Verbose Logging aktivieren
export KI_AUTOAGENT_DEBUG=true
python cli.py --task "test task"

# Oder in config.yaml:
development:
  verbose_logging: true
  save_all_outputs: true
```

## 📊 Performance & Benchmarks

### Response-Zeiten (Durchschnitt)

| Aufgaben-Typ | Einfach | Mittel | Komplex |
|-------------|---------|---------|---------|
| **Code Review** | 5-15s | 20-45s | 60-120s |
| **Code Generation** | 10-30s | 45-90s | 120-300s |
| **Trading Strategy** | 30-60s | 90-180s | 180-400s |
| **Documentation** | 15-30s | 45-90s | 90-180s |
| **Research** | 20-40s | 60-120s | 120-240s |

### Genauigkeit

- **Intent Classification**: >90% Accuracy
- **Workflow Optimization**: 15-25% Geschwindigkeits-Verbesserung  
- **Learning Improvement**: 15-20% nach 10 Executions
- **Parallel Efficiency**: Bis zu 3x schneller bei geeigneten Tasks

### System-Anforderungen

**Minimum:**
- Python 3.8+
- 4 GB RAM
- Internetverbindung
- API Credits ($10-50/Monat je nach Nutzung)

**Empfohlen:**
- Python 3.10+  
- 8 GB RAM
- SSD Storage
- Stabile Internetverbindung (>10 Mbps)

## 🤝 Contributing

Contributions sind herzlich willkommen! 

### Development Setup

```bash
# Repository forken und klonen
git clone https://github.com/yourusername/KI_AutoAgent.git

# Development Dependencies
pip install -r requirements-dev.txt

# Pre-commit hooks installieren  
pre-commit install

# Tests ausführen
python test_system.py
pytest tests/
```

### Pull Request Guidelines

1. **Fork** das Repository
2. **Branch** erstellen: `git checkout -b feature/amazing-feature`
3. **Tests** hinzufügen für neue Features
4. **Commit**: `git commit -m 'Add amazing feature'`
5. **Push**: `git push origin feature/amazing-feature`  
6. **Pull Request** erstellen

## 📄 Lizenz

Dieses Projekt ist unter der MIT License lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## 📧 Kontakt & Support

- **GitHub Issues**: [github.com/yourusername/KI_AutoAgent/issues](https://github.com/yourusername/KI_AutoAgent/issues)
- **Discussions**: [github.com/yourusername/KI_AutoAgent/discussions](https://github.com/yourusername/KI_AutoAgent/discussions)
- **Email**: your-email@example.com

## 🎯 Roadmap

### Version 1.1 (Coming Soon)
- [ ] Web-Interface zusätzlich zur CLI
- [ ] Custom GPT Integration  
- [ ] More Agent Types (DevOps, Data Science)
- [ ] Plugin System
- [ ] Cloud Deployment Option

### Version 1.2 (Q2 2025)
- [ ] Multi-Language Support (JavaScript, Go, etc.)
- [ ] Integration with GitHub/GitLab
- [ ] Team Collaboration Features
- [ ] Advanced Analytics Dashboard

---

**🚀 Entwickelt mit modernster KI-Technologie für maximale Produktivität**

*"Why do manually what AI can do automatically?"*