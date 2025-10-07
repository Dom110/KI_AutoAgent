from __future__ import annotations

"""
Development Query Handler - v5.5.2
Spezialisierte Handler für Entwicklungs-Anfragen
Alle Antworten auf Deutsch
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DevelopmentContext:
    """Kontext für Entwicklungs-Anfragen"""

    has_code_context: bool
    has_specific_files: bool
    has_error_details: bool
    has_performance_metrics: bool
    has_test_requirements: bool
    suggested_agents: list[str]
    required_information: list[str]
    confidence: float


class DevelopmentQueryHandler:
    """
    Spezialisierte Handler für 10 Entwicklungs-Query-Typen
    Alle Antworten sind auf Deutsch und bieten konkrete Hilfestellung
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_context(self, query: str, state: dict[str, Any]) -> DevelopmentContext:
        """Analysiert den Kontext einer Entwicklungs-Anfrage"""

        # Check for code context
        has_code = any(
            indicator in query.lower()
            for indicator in ["code:", "class ", "function ", "def ", "import ", "```"]
        )

        # Check for specific files
        has_files = bool(re.search(r"\.[py|js|ts|java|cpp|go|rs]\b", query))

        # Check for error details
        has_errors = any(
            indicator in query.lower()
            for indicator in [
                "error:",
                "exception",
                "traceback",
                "stack trace",
                "fehler:",
            ]
        )

        # Check for performance metrics
        has_metrics = any(
            indicator in query.lower()
            for indicator in [
                "ms",
                "sekunden",
                "seconds",
                "mb",
                "cpu",
                "memory",
                "latenz",
            ]
        )

        # Check for test requirements
        has_tests = any(
            indicator in query.lower()
            for indicator in ["test", "pytest", "unittest", "jest", "coverage"]
        )

        # Calculate confidence
        confidence = (
            sum([has_code, has_files, has_errors, has_metrics, has_tests]) / 5.0
        )

        return DevelopmentContext(
            has_code_context=has_code,
            has_specific_files=has_files,
            has_error_details=has_errors,
            has_performance_metrics=has_metrics,
            has_test_requirements=has_tests,
            suggested_agents=[],
            required_information=[],
            confidence=confidence,
        )

    # 11. Performance Optimization ohne Metriken
    def handle_performance_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Performance-Anfragen ohne konkrete Metriken"""
        context = self.analyze_context(query, state)

        if context.has_performance_metrics:
            agents = ["performance", "codesmith"]
            return (
                "Performance-Analyse mit konkreten Metriken wird gestartet.",
                agents,
            )

        response = """🎯 **Performance-Optimierung benötigt konkrete Daten**

Um Ihre Anwendung zu optimieren, benötige ich folgende Informationen:

1. **Aktuelle Metriken:**
   - Ladezeiten (in ms/s)
   - CPU-Auslastung (%)
   - Speicherverbrauch (MB/GB)
   - Anzahl der Anfragen pro Sekunde

2. **Problembereiche:**
   - Welche Funktionen sind langsam?
   - Wann treten die Probleme auf?
   - Gibt es bestimmte Eingabegrößen?

3. **Zielwerte:**
   - Wie schnell soll es werden?
   - Welche Ressourcen stehen zur Verfügung?

**Beispiel für eine vollständige Anfrage:**
"Die Funktion calculate_report() braucht 5 Sekunden für 1000 Einträge.
Ziel: unter 1 Sekunde. Datei: backend/reports.py"

Möchten Sie mit einer Profiling-Analyse beginnen?"""

        return (response, [])

    # 12. Bug Report ohne Details
    def handle_bug_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Bug-Reports ohne ausreichende Details"""
        context = self.analyze_context(query, state)

        if context.has_error_details and context.has_code_context:
            agents = ["reviewer", "fixer"]
            return ("Bug-Analyse mit Fehlerdetails wird durchgeführt.", agents)

        response = """🐛 **Bug-Report: Mehr Details für effektive Hilfe**

Um den Fehler zu beheben, benötige ich:

1. **Fehlerbeschreibung:**
   - Was sollte passieren?
   - Was passiert stattdessen?
   - Wann tritt der Fehler auf?

2. **Technische Details:**
   ```python
   # Fehlermeldung (vollständig):
   Traceback (most recent call last):
   ...

   # Betroffener Code:
   def problematic_function():
       ...
   ```

3. **Reproduktion:**
   - Schritte zum Nachstellen
   - Eingabedaten
   - Erwartete vs. tatsächliche Ausgabe

**Quick-Check Befehle:**
- `python -m pytest tests/ -v`  # Tests ausführen
- `python script.py --debug`     # Mit Debug-Modus
- `tail -n 100 error.log`       # Letzte Fehler ansehen

Haben Sie eine Fehlermeldung oder können Sie den Fehler genauer beschreiben?"""

        return (response, [])

    # 13. Refactoring ohne Code-Kontext
    def handle_refactoring_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Refactoring-Anfragen ohne Code"""
        context = self.analyze_context(query, state)

        if context.has_code_context or context.has_specific_files:
            agents = ["architect", "codesmith", "reviewer"]
            return ("Refactoring-Analyse mit Code-Kontext wird gestartet.", agents)

        response = """♻️ **Refactoring: Code-Kontext erforderlich**

Für effektives Refactoring benötige ich:

1. **Zu refactorierender Code:**
   - Dateipfad(e): z.B. `backend/services/auth.py`
   - Oder Code-Snippet direkt einfügen

2. **Refactoring-Ziele:**
   - □ Code-Duplikation reduzieren
   - □ Lesbarkeit verbessern
   - □ Performance optimieren
   - □ Design Patterns anwenden
   - □ Testbarkeit erhöhen
   - □ Abhängigkeiten reduzieren

3. **Kontext:**
   - Welche Probleme gibt es aktuell?
   - Welche Standards sollen befolgt werden?

**Häufige Refactoring-Patterns:**
- **Extract Method**: Lange Funktionen aufteilen
- **Extract Class**: Große Klassen aufteilen
- **Replace Magic Numbers**: Konstanten einführen
- **Introduce Parameter Object**: Parameter gruppieren

Welche Datei oder welchen Code möchten Sie refactoren?"""

        return (response, [])

    # 14. Test-Anfrage ohne Spezifikation
    def handle_testing_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Test-Anfragen ohne klare Spezifikation"""
        context = self.analyze_context(query, state)

        if context.has_test_requirements and context.has_code_context:
            agents = ["codesmith", "reviewer"]
            return ("Test-Erstellung mit Spezifikation wird durchgeführt.", agents)

        response = """🧪 **Testing: Spezifikation für effektive Tests**

Welche Art von Tests benötigen Sie?

**1. Test-Typen:**
- **Unit Tests**: Einzelne Funktionen/Methoden
- **Integration Tests**: Komponenten-Interaktion
- **End-to-End Tests**: Komplette Workflows
- **Performance Tests**: Geschwindigkeit/Last
- **Security Tests**: Sicherheitslücken

**2. Für Tests benötige ich:**
```python
# Zu testende Funktion/Klasse:
def function_to_test(param1, param2):
    # Implementierung
    pass

# Erwartetes Verhalten:
# - Bei Input X → Output Y
# - Edge Cases: ...
# - Error Cases: ...
```

**3. Test-Framework:**
- Python: `pytest`, `unittest`
- JavaScript: `jest`, `mocha`
- TypeScript: `jest`, `vitest`

**Quick-Start Beispiel:**
"Erstelle Unit Tests für die Klasse UserAuthentication in backend/auth.py
mit pytest. Teste erfolgreiche Logins, fehlgeschlagene Logins und Token-Validierung."

Was möchten Sie testen?"""

        return (response, [])

    # 15. Vage Implementation Request
    def handle_implementation_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für vage Implementierungs-Anfragen"""

        # Check for specific features mentioned
        has_specifics = any(
            word in query.lower()
            for word in [
                "api",
                "database",
                "frontend",
                "backend",
                "ui",
                "login",
                "auth",
                "payment",
                "search",
                "upload",
                "download",
            ]
        )

        if has_specifics:
            agents = ["architect", "codesmith"]
            return (
                "Feature-Implementierung mit Architektur-Planung wird gestartet.",
                agents,
            )

        response = """🚀 **Feature-Implementierung: Anforderungen definieren**

Um Ihr Feature zu implementieren, benötige ich:

**1. Feature-Beschreibung:**
- Was soll das Feature tun?
- Wer sind die Nutzer?
- Welches Problem löst es?

**2. Technische Anforderungen:**
```yaml
Feature-Name: [Name]
Typ: [API/UI/Backend/Service]
Technologien: [Python/TypeScript/etc.]
Abhängigkeiten: [Externe Services/Libraries]
```

**3. Akzeptanzkriterien:**
- [ ] Kriterium 1
- [ ] Kriterium 2
- [ ] Kriterium 3

**Beispiel-Anfragen:**
- "Implementiere eine REST API für Benutzerverwaltung mit FastAPI"
- "Erstelle ein Login-System mit JWT-Authentication"
- "Baue eine Datei-Upload-Funktion mit Progress-Bar"

**Standard-Features (wählen Sie eines):**
1. 🔐 Authentication System
2. 📊 Dashboard/Analytics
3. 🔍 Such-Funktionalität
4. 📧 Email-Integration
5. 💳 Payment Processing
6. 📁 File Management
7. 👥 User Management
8. 🔔 Notification System

Welches Feature möchten Sie implementieren?"""

        return (response, [])

    # 16. Technology/Framework Auswahl
    def handle_technology_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Technologie-Auswahl-Fragen"""

        response = """🛠️ **Technologie-Auswahl: Kontext-basierte Empfehlung**

Für eine fundierte Empfehlung benötige ich:

**1. Projekt-Kontext:**
- Projekttyp: Web/Mobile/Desktop/API/CLI
- Teamgröße und Erfahrung
- Timeline und Budget
- Bestehende Technologien

**2. Anforderungen:**
- Performance: Geschwindigkeit kritisch?
- Skalierung: Wie viele Nutzer?
- Wartbarkeit: Langzeit-Projekt?
- Integration: Welche Systeme?

**3. Aktuelle Tech-Stack-Empfehlungen (2024):**

**Backend:**
- 🚀 **FastAPI** (Python): Modern, schnell, async
- 🟢 **Node.js/Express**: JavaScript everywhere
- ⚡ **Go**: Performance-kritisch
- 🦀 **Rust**: System-Level, Sicherheit

**Frontend:**
- ⚛️ **React**: Große Community, flexibel
- 🎯 **Vue 3**: Einfacher Einstieg
- 🅰️ **Angular**: Enterprise, vollständig
- 🔥 **Svelte**: Compiler-basiert, schnell

**Datenbank:**
- 🐘 **PostgreSQL**: Relational, robust
- 🍃 **MongoDB**: NoSQL, flexibel
- 🔥 **Redis**: Cache, Sessions
- 📊 **ClickHouse**: Analytics

Beschreiben Sie Ihr Projekt für eine spezifische Empfehlung!"""

        return (response, ["research"])

    # 17. Database Query ohne Schema
    def handle_database_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Datenbank-Anfragen ohne Schema-Kontext"""

        has_schema = any(
            word in query.lower()
            for word in ["table", "schema", "model", "migration", "create table"]
        )

        if has_schema:
            agents = ["architect", "codesmith"]
            return ("Datenbank-Design mit Schema-Analyse wird durchgeführt.", agents)

        response = """🗄️ **Datenbank-Optimierung: Schema-Analyse erforderlich**

Für Datenbank-Hilfe benötige ich:

**1. Aktuelles Schema:**
```sql
-- Tabellen-Struktur
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    ...
);

-- Oder ORM Models:
class User(Base):
    __tablename__ = 'users'
    ...
```

**2. Problem-Beschreibung:**
- [ ] Langsame Queries (welche?)
- [ ] Schema-Design-Fragen
- [ ] Migration erforderlich
- [ ] Index-Optimierung
- [ ] Datenbank-Wahl

**3. Query-Analyse Tools:**
```sql
-- PostgreSQL
EXPLAIN ANALYZE SELECT ...;

-- MySQL
SHOW PROFILE FOR QUERY 1;

-- MongoDB
db.collection.explain("executionStats").find({...})
```

**Häufige Optimierungen:**
- 🔍 **Indices**: Für WHERE, JOIN, ORDER BY
- 📊 **Partitionierung**: Für große Tabellen
- 🔄 **Denormalisierung**: Für Read-Heavy
- 💾 **Caching**: Redis/Memcached Layer

Was ist Ihr konkretes Datenbank-Problem?"""

        return (response, [])

    # 18. AI/ML Integration ohne Details
    def handle_ai_integration_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für AI/ML-Integrations-Anfragen"""

        response = """🤖 **AI/ML Integration: Use-Case Definition**

Für AI-Integration benötige ich Details:

**1. Anwendungsfall:**
- **NLP/Text**: Sentiment, Übersetzung, Zusammenfassung
- **Computer Vision**: Objekterkennung, OCR
- **Predictive**: Vorhersagen, Klassifikation
- **Generative**: Text/Bild-Generierung
- **RAG**: Retrieval-Augmented Generation

**2. Integration-Optionen:**

**Cloud APIs (schnell, einfach):**
- OpenAI API (GPT-4, DALL-E)
- Claude API (Anthropic)
- Google Cloud AI
- AWS Bedrock

**Self-Hosted (Kontrolle, Privatsphäre):**
- Ollama (local LLMs)
- Hugging Face Models
- LangChain/LlamaIndex

**3. Beispiel-Implementierung:**
```python
# OpenAI Integration
from openai import OpenAI
client = OpenAI()

# Claude Integration
import anthropic
client = anthropic.Client()

# Local mit Ollama
import ollama
response = ollama.chat(model='llama2')
```

**Konkrete Use-Cases:**
- "Chatbot für Kundensupport"
- "Dokumenten-Zusammenfassung"
- "Code-Review-Assistent"
- "Bilderkennung für Qualitätskontrolle"

Was möchten Sie mit AI/ML erreichen?"""

        return (response, ["research"])

    # 19. Fehler-Diagnose ohne Logs
    def handle_error_diagnosis_query(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für Fehler-Diagnose ohne Logs"""

        has_logs = any(
            word in query.lower()
            for word in ["log", "error", "traceback", "exception", "stack"]
        )

        if has_logs:
            agents = ["reviewer", "fixer"]
            return ("Fehler-Analyse mit Logs wird durchgeführt.", agents)

        response = """🔍 **Fehler-Diagnose: Logs und Kontext benötigt**

Für effektive Fehler-Diagnose brauche ich:

**1. Error Logs sammeln:**
```bash
# Python
tail -n 100 app.log
python script.py 2>&1 | tee error.log

# Node.js
npm run dev 2>&1 | tee error.log

# Docker
docker logs container_name --tail 100

# System
journalctl -u service_name -n 100
```

**2. Debug-Informationen:**
```python
# Python Debug
import logging
logging.basicConfig(level=logging.DEBUG)

# Environment
import sys
print(f"Python: {sys.version}")
print(f"Pfad: {sys.path}")

# Traceback
import traceback
try:
    # Fehlerhafte Funktion
except Exception as e:
    traceback.print_exc()
```

**3. Fehler-Kategorien:**
- **Syntax Error**: Code-Struktur prüfen
- **Runtime Error**: Daten/Input prüfen
- **Logic Error**: Algorithmus debuggen
- **Performance**: Profiling nötig
- **Integration**: API/Service-Status

**Quick Debug Commands:**
```bash
# Syntax Check
python -m py_compile script.py
pylint script.py

# Dependencies
pip list | grep package_name
npm ls package_name
```

Können Sie die Fehlermeldung oder Logs teilen?"""

        return (response, [])

    # 20. Scope/Requirements Klarstellung
    def handle_scope_clarification(
        self, query: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Handler für unklare Anforderungen"""

        response = """📋 **Anforderungs-Klärung: Strukturierte Planung**

Lassen Sie uns Ihr Projekt strukturiert angehen:

**1. Projekt-Definition (User Story Format):**
```
Als [Nutzer-Rolle]
möchte ich [Funktionalität]
damit [Nutzen/Ziel]
```

**2. Anforderungs-Template:**

**Funktionale Anforderungen:**
- Must-Have (kritisch):
  - [ ] Feature 1
  - [ ] Feature 2

- Should-Have (wichtig):
  - [ ] Feature 3

- Nice-to-Have (optional):
  - [ ] Feature 4

**Nicht-Funktionale Anforderungen:**
- Performance: < 2s Ladezeit
- Sicherheit: OAuth2, HTTPS
- Skalierung: 1000 User gleichzeitig
- Browser: Chrome, Firefox, Safari

**3. Projekt-Umfang:**
```yaml
Phase 1 (MVP):
  - Core Features
  - Basic UI
  - Zeitrahmen: 2 Wochen

Phase 2:
  - Erweiterte Features
  - Optimierung
  - Zeitrahmen: 4 Wochen
```

**4. Success Metrics:**
- Wie messen wir Erfolg?
- Welche KPIs sind relevant?

**Beispiel-Scope:**
"MVP für Todo-App: Nutzer können Tasks erstellen, bearbeiten, löschen und als
erledigt markieren. Daten lokal speichern. Einfache Web-UI. Fertig in 3 Tagen."

Beschreiben Sie Ihr Projekt - ich helfe bei der Strukturierung!"""

        return (response, ["architect"])

    def get_handler_for_type(self, dev_type: str) -> callable | None:
        """Gibt den passenden Handler für einen Entwicklungs-Typ zurück"""

        handlers = {
            "performance": self.handle_performance_query,
            "bug": self.handle_bug_query,
            "refactoring": self.handle_refactoring_query,
            "testing": self.handle_testing_query,
            "implementation": self.handle_implementation_query,
            "technology": self.handle_technology_query,
            "database": self.handle_database_query,
            "ai_integration": self.handle_ai_integration_query,
            "error_diagnosis": self.handle_error_diagnosis_query,
            "scope": self.handle_scope_clarification,
        }

        return handlers.get(dev_type)

    def handle_development_query(
        self, query: str, dev_type: str, state: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """
        Hauptmethode zur Behandlung von Entwicklungs-Anfragen

        Returns:
            Tuple[str, List[str]]: (Response text, List of agents to route to)
        """

        handler = self.get_handler_for_type(dev_type)

        if handler:
            return handler(query, state)

        # Fallback für unbekannte Typen
        return (
            "Ich verstehe Ihre Entwicklungs-Anfrage. Könnten Sie bitte mehr Details "
            "angeben, damit ich Ihnen gezielt helfen kann?",
            [],
        )

    def suggest_next_steps(self, query_type: str) -> str:
        """Schlägt nächste Schritte basierend auf Query-Typ vor"""

        next_steps = {
            "performance": "Führen Sie ein Profiling durch: `python -m cProfile script.py`",
            "bug": "Sammeln Sie vollständige Error-Logs: `python script.py 2>&1 | tee error.log`",
            "refactoring": "Identifizieren Sie Code-Smells mit: `pylint --load-plugins=pylint.extensions.code_style`",
            "testing": "Prüfen Sie Test-Coverage: `pytest --cov=. --cov-report=html`",
            "implementation": "Erstellen Sie ein Design-Dokument mit Architektur-Diagramm",
            "technology": "Recherchieren Sie aktuelle Benchmarks und Community-Größe",
            "database": "Analysieren Sie Query-Performance: `EXPLAIN ANALYZE SELECT ...`",
            "ai_integration": "Evaluieren Sie Kosten vs. Self-Hosting für Ihren Use-Case",
            "error_diagnosis": "Aktivieren Sie Debug-Logging: `logging.basicConfig(level=logging.DEBUG)`",
            "scope": "Verwenden Sie User Stories und definieren Sie MVP-Features",
        }

        return next_steps.get(
            query_type, "Sammeln Sie mehr Informationen über Ihre Anforderungen."
        )
