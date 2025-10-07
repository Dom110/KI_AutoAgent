"""
Enhanced Query Classifier v5.5.2
Erkennt und klassifiziert 20 problematische Query-Typen
Alle Antworten auf Deutsch
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DetailedClassification:
    """Detaillierte Klassifikation einer Query"""

    # Basis-Klassifikation
    query: str
    query_hash: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Query-Typ Erkennung
    is_greeting: bool = False
    is_nonsense: bool = False
    is_personal: bool = False
    is_temporal: bool = False
    is_comparison: bool = False
    is_philosophical: bool = False
    is_control_command: bool = False
    is_meta_question: bool = False
    has_context_reference: bool = False

    # Development-spezifisch
    is_development_query: bool = False
    dev_type: str | None = None  # performance, bug, refactoring, etc.
    has_sufficient_context: bool = False

    # Analyse-Ergebnisse
    confidence_score: float = 0.0
    coherence_score: float = 0.0
    execution_safety_score: float = 0.0

    # Aktions-Empfehlung
    safe_to_execute: bool = False
    needs_clarification: bool = False
    suggested_action: str = (
        "fallback"  # direct_response, clarification, safe_execution, route_agent
    )
    suggested_agent: str | None = None

    # Response-Vorschläge
    prefilled_response: str | None = None
    clarification_text: str | None = None

    def summary(self) -> str:
        """Zusammenfassung für Logging"""
        return (
            f"Query: {self.query[:50]}... | "
            f"Safe: {self.safe_to_execute} | "
            f"Action: {self.suggested_action} | "
            f"Agent: {self.suggested_agent or 'none'}"
        )


class EnhancedQueryClassifier:
    """
    Umfassender Klassifikator für 20 Query-Typen
    Arbeitet primär auf Deutsch
    """

    def __init__(self):
        # General Patterns (Queries 1-10)
        self.greeting_patterns = [
            "hi",
            "hallo",
            "hey",
            "guten tag",
            "guten morgen",
            "guten abend",
            "servus",
            "moin",
            "grüß",
            "hello",
            "greetings",
        ]

        self.personal_patterns = [
            "wie geht",
            "wie gehts",
            "how are",
            "bist du",
            "kannst du",
            "wer bist",
            "was bist",
        ]

        self.temporal_patterns = [
            "gestern",
            "heute",
            "morgen",
            "yesterday",
            "today",
            "tomorrow",
            "letzte woche",
            "nächste woche",
            "vorhin",
            "später",
        ]

        self.comparison_patterns = [
            "besser als",
            "schlechter als",
            "better than",
            "worse than",
            "versus",
            " vs ",
            "vergleich",
            "unterschied",
        ]

        self.philosophical_patterns = [
            "sinn des lebens",
            "meaning of life",
            "warum existier",
            "was ist realität",
            "bewusstsein",
            "consciousness",
        ]

        self.control_patterns = [
            "stop",
            "halt",
            "cancel",
            "abbrech",
            "beende",
            "exit",
            "quit",
            "pause",
            "anhalten",
        ]

        self.meta_patterns = [
            "welcher agent",
            "welche agents",
            "beste agent",
            "which agent",
            "agent list",
            "agenten liste",
            "was kannst du",
            "was machst du",
            "deine fähigkeiten",
            "your capabilities",
        ]

        # Development Patterns (Queries 11-20)
        self.performance_patterns = [
            "schneller",
            "langsam",
            "faster",
            "slower",
            "optimier",
            "optimize",
            "performance",
            "geschwindigkeit",
            "speed",
        ]

        self.bug_patterns = [
            "bug",
            "fehler",
            "error",
            "kaputt",
            "broken",
            "funktioniert nicht",
            "doesn't work",
            "geht nicht",
            "problem",
            "issue",
        ]

        self.refactoring_patterns = [
            "refactor",
            "umschreiben",
            "rewrite",
            "clean",
            "aufräumen",
            "verbessern",
            "improve",
            "überarbeiten",
        ]

        self.testing_patterns = [
            "test",
            "tests",
            "unit test",
            "integration",
            "prüf",
            "testen",
            "überprüf",
            "validier",
        ]

        self.implementation_patterns = [
            "implement",
            "erstell",
            "create",
            "build",
            "bau",
            "entwickl",
            "develop",
            "programmier",
            "code",
            "schreib",
        ]

        self.technology_patterns = [
            "technologie",
            "technology",
            "framework",
            "library",
            "tool",
            "werkzeug",
            "beste",
            "empfehl",
            "recommend",
        ]

        self.database_patterns = [
            "database",
            "datenbank",
            "sql",
            "query",
            "tabelle",
            "table",
            "schema",
            "index",
            "optimier",
        ]

        self.ai_patterns = [
            " ai ",
            " ki ",
            "künstliche intelligenz",
            "artificial intelligence",
            "machine learning",
            "neural",
            "llm",
            "gpt",
            "claude",
        ]

        # Context indicators
        self.context_references = [
            "das",
            "dies",
            "es",
            "this",
            "that",
            "it",
            "der code",
            "the code",
            "davon",
            "damit",
        ]

        self.vague_scope_indicators = [
            "alles",
            "everything",
            "all",
            "komplett",
            "gesamt",
            "entire",
            "whole",
            "vollständig",
        ]

    def classify_query(
        self, query: str, state: dict[str, Any] = None
    ) -> DetailedClassification:
        """
        Hauptmethode: Klassifiziert eine Query umfassend
        """
        if state is None:
            state = {}

        query_lower = query.lower().strip()

        # Basis-Klassifikation erstellen
        classification = DetailedClassification(
            query=query, query_hash=hashlib.md5(query.encode()).hexdigest()
        )

        # Schritt 1: Basis-Checks
        classification.is_greeting = self._is_greeting(query_lower)
        classification.is_nonsense = self._is_nonsense(query_lower)
        classification.has_context_reference = self._has_context_reference(query_lower)

        # Schritt 2: General Query Types (1-10)
        classification.is_personal = self._check_pattern(
            query_lower, self.personal_patterns
        )
        classification.is_temporal = self._check_pattern(
            query_lower, self.temporal_patterns
        )
        classification.is_comparison = self._check_pattern(
            query_lower, self.comparison_patterns
        )
        classification.is_philosophical = self._check_pattern(
            query_lower, self.philosophical_patterns
        )
        classification.is_control_command = self._check_pattern(
            query_lower, self.control_patterns
        )
        classification.is_meta_question = self._check_pattern(
            query_lower, self.meta_patterns
        )

        # Schritt 3: Development Query Types (11-20)
        dev_checks = self._check_development_patterns(query_lower)
        classification.is_development_query = dev_checks["is_dev"]
        classification.dev_type = dev_checks["type"]
        classification.has_sufficient_context = dev_checks["has_context"]

        # Schritt 4: Scores berechnen
        classification.coherence_score = self._calculate_coherence(query_lower)
        classification.confidence_score = self._calculate_confidence(classification)
        classification.execution_safety_score = self._calculate_safety(
            classification, state
        )

        # Schritt 5: Action bestimmen
        self._determine_action(classification, state)

        # Schritt 6: Responses vorbereiten
        self._prepare_responses(classification)

        return classification

    def _is_greeting(self, query: str) -> bool:
        """Prüft ob Query eine Begrüßung ist"""
        # Exakte Matches für kurze Grüße
        if query in ["hi", "hallo", "hey", "moin", "servus"]:
            return True

        # Pattern-Check für längere Grüße mit Wortgrenzen
        # Nicht "erstelle" als "hello" erkennen!
        words = query.split()
        for word in words:
            if word.lower() in self.greeting_patterns:
                return True

        # Check for greeting at start of query
        for pattern in self.greeting_patterns:
            if query.startswith(pattern + " ") or query.startswith(pattern + ","):
                return True

        return False

    def _is_nonsense(self, query: str) -> bool:
        """Prüft ob Query Nonsense ist"""
        # Check 1: Zu kurz
        if len(query) < 2:
            return True

        # Check 2: Keine echten Wörter (nur Zeichen/Zahlen)
        words = query.split()
        real_words = [w for w in words if re.search(r"[a-zäöüß]{2,}", w, re.I)]
        if len(real_words) == 0:
            return True

        # Check 3: Zufällige Zeichenketten
        if re.match(r"^[a-z]{5,}$", query) and query not in ["hallo", "servus"]:
            # Könnte keyboard smash sein
            unique_chars = len(set(query))
            if unique_chars > len(query) * 0.7:  # Zu viele verschiedene Zeichen
                return True

        return False

    def _has_context_reference(self, query: str) -> bool:
        """Prüft ob Query Kontext-Referenzen enthält"""
        # Prüfe auf Pronomen/Referenzen ohne klaren Bezug
        for ref in self.context_references:
            if ref in query:
                # Prüfe ob es am Anfang steht (stark indikativ)
                if query.startswith(ref) or query.startswith(f"{ref} "):
                    return True
        return False

    def _check_pattern(self, query: str, patterns: list[str]) -> bool:
        """Generischer Pattern-Check"""
        return any(pattern in query for pattern in patterns)

    def _check_development_patterns(self, query: str) -> dict[str, Any]:
        """Prüft Development-spezifische Patterns"""
        result = {"is_dev": False, "type": None, "has_context": False}

        # Check each development pattern
        if self._check_pattern(query, self.performance_patterns):
            result["is_dev"] = True
            result["type"] = "performance"
            result["has_context"] = not self._has_context_reference(query)

        elif self._check_pattern(query, self.bug_patterns):
            result["is_dev"] = True
            result["type"] = "bug_report"
            # Bug reports often lack context
            result["has_context"] = len(query.split()) > 3

        elif self._check_pattern(query, self.refactoring_patterns):
            result["is_dev"] = True
            result["type"] = "refactoring"
            result["has_context"] = not self._has_context_reference(query)

        elif self._check_pattern(query, self.testing_patterns):
            result["is_dev"] = True
            result["type"] = "testing"
            result["has_context"] = len(query.split()) > 2

        elif self._check_pattern(query, self.implementation_patterns):
            result["is_dev"] = True
            result["type"] = "implementation"
            # Check for vague scope
            if self._check_pattern(query, self.vague_scope_indicators):
                result["has_context"] = False
            else:
                result["has_context"] = len(query.split()) > 3

        elif self._check_pattern(query, self.technology_patterns):
            result["is_dev"] = True
            result["type"] = "technology"
            result["has_context"] = len(query.split()) > 2

        elif self._check_pattern(query, self.database_patterns):
            result["is_dev"] = True
            result["type"] = "database"
            result["has_context"] = "schema" in query or "table" in query

        elif self._check_pattern(query, self.ai_patterns):
            result["is_dev"] = True
            result["type"] = "ai_integration"
            result["has_context"] = len(query.split()) > 3

        return result

    def _calculate_coherence(self, query: str) -> float:
        """Berechnet Kohärenz-Score (0.0-1.0)"""
        score = 1.0

        # Reduce for very short
        if len(query) < 3:
            score *= 0.3
        elif len(query) < 10:
            score *= 0.7

        # Reduce for no real words
        words = query.split()
        if len(words) == 0:
            score *= 0.1
        elif len(words) == 1:
            score *= 0.5

        # Reduce for random characters
        if re.match(r"^[a-z]+$", query) and len(set(query)) > len(query) * 0.7:
            score *= 0.2

        return max(0.0, min(1.0, score))

    def _calculate_confidence(self, classification: DetailedClassification) -> float:
        """Berechnet Konfidenz-Score"""
        score = 0.5  # Basis

        # Erhöhe für klare Patterns
        if classification.is_greeting:
            score += 0.4
        if (
            classification.is_development_query
            and classification.has_sufficient_context
        ):
            score += 0.3
        if classification.is_meta_question:
            score += 0.3

        # Reduziere für Probleme
        if classification.is_nonsense:
            score -= 0.4
        if (
            classification.has_context_reference
            and not classification.has_sufficient_context
        ):
            score -= 0.2
        if classification.is_philosophical:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _calculate_safety(
        self, classification: DetailedClassification, state: dict
    ) -> float:
        """Berechnet Safety-Score für Ausführung"""
        score = 0.5

        # Positive Faktoren
        if classification.coherence_score > 0.7:
            score += 0.2
        if classification.confidence_score > 0.6:
            score += 0.2
        if not classification.has_context_reference:
            score += 0.1

        # Negative Faktoren
        if classification.is_nonsense:
            score -= 0.5
        if state.get("orchestration_depth", 0) > 2:
            score -= 0.3
        if classification.is_philosophical:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def _determine_action(self, classification: DetailedClassification, state: dict):
        """Bestimmt die empfohlene Aktion"""

        # Grüße → Direkte Antwort
        if classification.is_greeting:
            classification.suggested_action = "direct_response"
            classification.safe_to_execute = False
            return

        # Nonsense → Klärung
        if classification.is_nonsense:
            classification.suggested_action = "clarification"
            classification.needs_clarification = True
            classification.safe_to_execute = False
            return

        # Kontext-Referenz ohne Kontext → Klärung
        if (
            classification.has_context_reference
            and not classification.has_sufficient_context
        ):
            classification.suggested_action = "clarification"
            classification.needs_clarification = True
            classification.safe_to_execute = False
            return

        # Development mit genug Kontext → Spezifischer Agent
        if (
            classification.is_development_query
            and classification.has_sufficient_context
        ):
            classification.suggested_action = "route_agent"
            classification.suggested_agent = self._get_dev_agent(
                classification.dev_type
            )
            classification.safe_to_execute = False
            return

        # Meta-Fragen → Direkte Antwort
        if classification.is_meta_question:
            classification.suggested_action = "direct_response"
            classification.safe_to_execute = False
            return

        # Philosophisch → Direkte Antwort
        if classification.is_philosophical:
            classification.suggested_action = "direct_response"
            classification.safe_to_execute = False
            return

        # Safety-Check für Orchestrator-Ausführung
        if classification.execution_safety_score > 0.5:
            classification.suggested_action = "safe_execution"
            classification.safe_to_execute = True
        else:
            classification.suggested_action = "fallback"
            classification.safe_to_execute = False

    def _get_dev_agent(self, dev_type: str) -> str:
        """Mapping von Dev-Type zu Agent"""
        mapping = {
            "performance": "performance",
            "bug_report": "fixer",
            "refactoring": "codesmith",
            "testing": "reviewer",
            "implementation": "codesmith",
            "technology": "architect",
            "database": "architect",
            "ai_integration": "research",
        }
        return mapping.get(dev_type, "codesmith")

    def _prepare_responses(self, classification: DetailedClassification):
        """Bereitet Response-Texte vor (auf Deutsch)"""

        if classification.is_greeting:
            classification.prefilled_response = """Hallo! 👋 Ich bin das KI AutoAgent System.

Ich kann Ihnen bei der Softwareentwicklung helfen:
• Code erstellen und analysieren
• Bugs finden und beheben
• Architekturen entwerfen
• Tests schreiben
• Performance optimieren

Womit kann ich Ihnen heute helfen?"""

        elif classification.is_nonsense:
            classification.clarification_text = """Entschuldigung, ich habe Ihre Anfrage nicht verstanden.

Könnten Sie bitte präzisieren, was Sie möchten?

Beispiele gültiger Anfragen:
• "Erstelle eine Python-Funktion für..."
• "Analysiere diesen Code..."
• "Hilf mir bei einem Bug..."
• "Optimiere die Performance von..."

Was möchten Sie tun?"""

        elif (
            classification.has_context_reference
            and not classification.has_sufficient_context
        ):
            classification.clarification_text = f"""Ich sehe, dass Sie sich auf etwas beziehen ("{classification.query}"), aber mir fehlt der Kontext.

Könnten Sie bitte spezifizieren:
• Worauf bezieht sich "{classification.query.split()[0]}"?
• Was genau möchten Sie damit tun?
• Gibt es Code oder Dateien, die ich mir ansehen soll?"""

        elif classification.is_philosophical:
            classification.prefilled_response = """Das ist eine interessante philosophische Frage!

Allerdings bin ich auf Softwareentwicklung spezialisiert. Ich kann Ihnen am besten bei folgenden Themen helfen:
• Programmierung und Code-Erstellung
• Software-Architektur und Design
• Debugging und Fehlerbehebung
• Performance-Optimierung
• Testing und Qualitätssicherung

Haben Sie eine konkrete Entwicklungsaufgabe, bei der ich helfen kann?"""

        elif classification.is_meta_question:
            classification.prefilled_response = """Das KI AutoAgent System verfügt über 10 spezialisierte Agenten:

🤖 **Verfügbare Agenten:**
1. **Orchestrator** - Plant und verteilt Aufgaben
2. **Architect** - System-Design und Architektur
3. **CodeSmith** - Code-Implementierung
4. **Reviewer** - Code-Review und Analyse
5. **Fixer** - Fehlerbehebung
6. **Research** - Web-Recherche und Information
7. **DocBot** - Dokumentation
8. **Performance** - Performance-Optimierung
9. **TradeStrat** - Trading-Strategien (spezialisiert)
10. **OpusArbitrator** - Konfliktlösung

Jeder Agent hat spezielle Fähigkeiten. Die Aufgaben werden automatisch an den passenden Agenten weitergeleitet.

Was möchten Sie entwickeln oder verbessern?"""


class ExecutionGuard:
    """
    Sicherheitsprüfungen gegen unsichere Ausführungen
    """

    MAX_DEPTH = 3
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 30

    def __init__(self):
        self.execution_history = []

    def is_safe(
        self, classification: DetailedClassification, state: dict[str, Any]
    ) -> bool:
        """
        Prüft ob Ausführung sicher ist
        """

        # Check 1: Depth limit
        if state.get("orchestration_depth", 0) >= self.MAX_DEPTH:
            logger.warning(
                f"⚠️ Max orchestration depth reached: {state.get('orchestration_depth')}"
            )
            return False

        # Check 2: Recent duplicate
        if self._is_duplicate(classification.query_hash):
            logger.warning(f"⚠️ Duplicate query detected: {classification.query[:50]}")
            return False

        # Check 3: Safety score threshold
        if classification.execution_safety_score < 0.3:
            logger.warning(
                f"⚠️ Safety score too low: {classification.execution_safety_score}"
            )
            return False

        # Check 4: Infinite loop pattern
        if self._detect_loop_pattern(state):
            logger.warning("⚠️ Loop pattern detected")
            return False

        # Check 5: Resource limits
        if self._check_resource_exhaustion(state):
            logger.warning("⚠️ Resource exhaustion detected")
            return False

        return True

    def _is_duplicate(self, query_hash: str) -> bool:
        """Prüft auf kürzliche Duplikate"""
        # Check last 10 executions
        recent_hashes = [h for h, _ in self.execution_history[-10:]]
        return query_hash in recent_hashes

    def _detect_loop_pattern(self, state: dict) -> bool:
        """Erkennt Loop-Patterns"""
        history = state.get("query_history", [])
        if len(history) >= 3:
            # A→B→A Pattern
            if history[-1] == history[-3]:
                return True
        return False

    def _check_resource_exhaustion(self, state: dict) -> bool:
        """Prüft Ressourcen-Limits"""
        messages = state.get("messages", [])
        if len(messages) > 1000:
            return True

        execution_plan = state.get("execution_plan", [])
        if len(execution_plan) > 50:
            return True

        return False

    def record_execution(self, query_hash: str):
        """Zeichnet Ausführung auf"""
        self.execution_history.append((query_hash, datetime.now()))
        # Keep only last 100
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
