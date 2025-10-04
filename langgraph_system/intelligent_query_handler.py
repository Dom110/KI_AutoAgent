"""
Intelligent Query Handler v5.5.2
Ensures EVERY query gets a meaningful response
Enhanced integration with Safe Orchestrator Executor
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

from .state import ExecutionStep

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Analysis result of a user query"""
    query_type: str  # question, command, request, statement
    domain: str  # technical, business, general, project
    intent: str  # get_info, create, modify, analyze, explain
    confidence: float
    suggested_agent: str
    reasoning: str
    keywords: List[str]
    language: str  # en, de, etc.


class IntelligentQueryHandler:
    """
    Ensures EVERY query gets handled appropriately
    No more generic "Task completed but no results" messages!
    """

    def __init__(self):
        self.fallback_responses = self._init_fallback_responses()
        self.query_patterns = self._init_query_patterns()

    def _init_fallback_responses(self) -> Dict[str, str]:
        """Initialize intelligent fallback responses for different query types"""
        return {
            "project_info": """KI AutoAgent v5.5.1 - Intelligentes Multi-Agent Development System

📋 PROJEKT ÜBERSICHT:
Das KI AutoAgent System ist eine fortschrittliche Entwicklungsplattform, die mehrere spezialisierte KI-Agenten orchestriert, um komplexe Softwareentwicklungsaufgaben zu automatisieren.

🎯 KERNFUNKTIONEN:
• Automatische Code-Generierung und -Optimierung
• Intelligente Code-Reviews und Fehlerbehebung
• Selbstdiagnose und Fehlerprävention (v5.5.0)
• Multi-Agent Kollaboration für komplexe Aufgaben
• Echtzeit-Workflow-Überwachung und -Anpassung

🤖 VERFÜGBARE AGENTEN:
1. Orchestrator - Aufgabenplanung und -verteilung
2. Architect - System-Design und Architektur
3. CodeSmith - Code-Implementierung
4. Reviewer - Code-Qualitätssicherung
5. Fixer - Fehlerbehebung
6. Research - Web-Recherche und Informationsbeschaffung
7. DocBot - Dokumentationserstellung
8. Performance - Performance-Optimierung
9. TradeStrat - Trading-Strategien (spezialisiert)
10. OpusArbitrator - Konfliktlösung bei widersprüchlichen Empfehlungen

💡 Stellen Sie gerne spezifische Fragen oder geben Sie mir eine Aufgabe!""",

            "capabilities": """🚀 WAS KANN ICH FÜR SIE TUN?

✅ ENTWICKLUNGSAUFGABEN:
• Vollständige Anwendungen entwickeln (Web, Desktop, Mobile)
• Code in verschiedenen Sprachen generieren (Python, JavaScript, TypeScript, etc.)
• Bestehenden Code analysieren und verbessern
• Bugs finden und beheben
• Performance optimieren

📚 ANALYSE & RECHERCHE:
• Code-Reviews durchführen
• Sicherheitslücken identifizieren
• Best Practices vorschlagen
• Technologie-Recherche durchführen
• Dokumentation erstellen

🛠️ SYSTEM-FUNKTIONEN:
• Multi-Agent-Workflows orchestrieren
• Komplexe Aufgaben in Teilschritte zerlegen
• Selbstdiagnose und Fehlerprävention
• Echtzeit-Fortschrittsverfolgung

Wie kann ich Ihnen heute helfen?""",

            "greeting": """Hallo! 👋

Ich bin das KI AutoAgent System v5.5.1 - Ihr intelligenter Entwicklungsassistent.

Ich kann Ihnen bei verschiedenen Aufgaben helfen:
• Software entwickeln und Code schreiben
• Bestehenden Code analysieren und verbessern
• Bugs finden und beheben
• Architekturen entwerfen
• Dokumentation erstellen
• Und vieles mehr!

Was möchten Sie heute entwickeln oder verbessern?""",

            "unknown": """Ich verstehe Ihre Anfrage und werde mein Bestes geben, um zu helfen!

Ihre Anfrage wird analysiert und an den geeignetsten Agenten weitergeleitet.

Falls Sie spezifische Hilfe benötigen, können Sie gerne präzisieren:
• Möchten Sie Code entwickeln?
• Brauchen Sie eine Analyse oder Review?
• Suchen Sie nach Informationen?
• Haben Sie ein Problem, das gelöst werden muss?

Ich bin hier, um zu helfen! 🤝"""
        }

    def _init_query_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for query understanding"""
        return [
            # Greetings
            {
                "patterns": ["hallo", "hi", "hey", "guten tag", "servus", "moin", "hello", "greetings"],
                "type": "greeting",
                "response_key": "greeting"
            },
            # Project info
            {
                "patterns": ["projekt", "project", "system", "was ist", "what is", "erkläre", "explain"],
                "type": "info_request",
                "response_key": "project_info"
            },
            # Capabilities
            {
                "patterns": ["kannst du", "can you", "fähigkeiten", "capabilities", "was machst", "what do you do"],
                "type": "capability_question",
                "response_key": "capabilities"
            },
            # Help requests
            {
                "patterns": ["hilfe", "help", "unterstützung", "support", "wie", "how"],
                "type": "help_request",
                "response_key": "capabilities"
            }
        ]

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Comprehensively analyze a query to understand intent and context
        """
        query_lower = query.lower()

        # Detect language
        language = "de" if any(word in query_lower for word in ["der", "die", "das", "ich", "du", "wir"]) else "en"

        # Detect query type
        if "?" in query:
            query_type = "question"
        elif any(word in query_lower for word in ["mach", "make", "erstelle", "create", "build", "baue"]):
            query_type = "command"
        elif any(word in query_lower for word in ["möchte", "want", "need", "brauche"]):
            query_type = "request"
        else:
            query_type = "statement"

        # Detect domain
        if any(word in query_lower for word in ["code", "function", "class", "bug", "error"]):
            domain = "technical"
        elif any(word in query_lower for word in ["projekt", "project", "system", "agent"]):
            domain = "project"
        elif any(word in query_lower for word in ["strategy", "trading", "business"]):
            domain = "business"
        else:
            domain = "general"

        # Detect intent
        if any(word in query_lower for word in ["was", "what", "wie", "how", "warum", "why"]):
            intent = "get_info"
        elif any(word in query_lower for word in ["erstelle", "create", "build", "mach", "make"]):
            intent = "create"
        elif any(word in query_lower for word in ["ändere", "modify", "change", "update"]):
            intent = "modify"
        elif any(word in query_lower for word in ["analysiere", "analyze", "review", "prüfe"]):
            intent = "analyze"
        else:
            intent = "explain"

        # Extract keywords (simple approach)
        stopwords = {"ich", "du", "der", "die", "das", "und", "oder", "aber", "the", "a", "an", "and", "or", "but"}
        keywords = [word for word in query_lower.split() if word not in stopwords and len(word) > 2]

        # Determine best agent based on analysis
        agent_map = {
            ("technical", "create"): "codesmith",
            ("technical", "analyze"): "reviewer",
            ("technical", "modify"): "fixer",
            ("project", "get_info"): "architect",
            ("business", "create"): "tradestrat",
            ("general", "get_info"): "research"
        }

        suggested_agent = agent_map.get((domain, intent), "research")

        # Calculate confidence
        confidence = 0.8 if domain != "general" else 0.6

        return QueryAnalysis(
            query_type=query_type,
            domain=domain,
            intent=intent,
            confidence=confidence,
            suggested_agent=suggested_agent,
            reasoning=f"Query appears to be a {query_type} about {domain} with intent to {intent}",
            keywords=keywords,
            language=language
        )

    def get_intelligent_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Generate an intelligent response for ANY query
        Never returns empty or generic responses
        """
        query_lower = query.lower()

        # Check predefined patterns first
        for pattern_group in self.query_patterns:
            if any(pattern in query_lower for pattern in pattern_group["patterns"]):
                return self.fallback_responses[pattern_group["response_key"]]

        # Analyze query for intelligent response
        analysis = self.analyze_query(query)

        # Generate contextual response based on analysis
        if analysis.domain == "project":
            return self.fallback_responses["project_info"]
        elif analysis.intent == "get_info" and analysis.domain == "general":
            return self.fallback_responses["capabilities"]
        elif analysis.query_type == "greeting":
            return self.fallback_responses["greeting"]
        else:
            # Build a custom response
            response = f"""Ich habe Ihre Anfrage analysiert:

📋 Query-Typ: {analysis.query_type}
🎯 Bereich: {analysis.domain}
💡 Absicht: {analysis.intent}
🤖 Empfohlener Agent: {analysis.suggested_agent}

{analysis.reasoning}

Der {analysis.suggested_agent} Agent wird sich um Ihre Anfrage kümmern.
"""
            return response

    def create_intelligent_execution_plan(
        self,
        query: str,
        fallback_agent: str = None
    ) -> List[ExecutionStep]:
        """
        Create an execution plan that ALWAYS produces meaningful results
        """
        analysis = self.analyze_query(query)

        # If high confidence in a specific agent, use it
        if analysis.confidence > 0.7 and analysis.suggested_agent != "orchestrator":
            return [
                ExecutionStep(
                    id="step1",
                    agent=analysis.suggested_agent,
                    task=query,
                    expected_output=f"{analysis.suggested_agent} will handle this {analysis.intent} request",
                    dependencies=[],
                    status="pending",
                    result=None
                )
            ]

        # For general queries, use research agent as fallback
        if analysis.domain == "general" or analysis.confidence < 0.5:
            intelligent_response = self.get_intelligent_response(query)

            return [
                ExecutionStep(
                    id="step1",
                    agent="research",
                    task=f"Provide comprehensive information about: {query}",
                    expected_output="Detailed information and analysis",
                    dependencies=[],
                    status="pending",
                    result=None,
                    # Store fallback response in case research fails
                    error=None,
                    attempts=[{
                        "fallback_response": intelligent_response
                    }]
                )
            ]

        # For complex queries, create multi-step plan
        if analysis.intent == "create" and analysis.domain == "technical":
            return [
                ExecutionStep(
                    id="step1",
                    agent="architect",
                    task=f"Design architecture for: {query}",
                    expected_output="Architecture design",
                    dependencies=[],
                    status="pending"
                ),
                ExecutionStep(
                    id="step2",
                    agent="codesmith",
                    task=f"Implement: {query}",
                    expected_output="Working implementation",
                    dependencies=["step1"],
                    status="pending"
                ),
                ExecutionStep(
                    id="step3",
                    agent="reviewer",
                    task="Review implementation",
                    expected_output="Quality assessment",
                    dependencies=["step2"],
                    status="pending"
                )
            ]

        # Default: Use specified fallback agent or research
        fallback_agent = fallback_agent or "research"
        return [
            ExecutionStep(
                id="step1",
                agent=fallback_agent,
                task=query,
                expected_output=f"Comprehensive response from {fallback_agent}",
                dependencies=[],
                status="pending",
                result=None
            )
        ]

    def enhance_orchestrator_step(self, step: ExecutionStep, query: str) -> ExecutionStep:
        """
        Enhance an orchestrator step with intelligent response
        Never returns empty results
        """
        if step.agent == "orchestrator" and step.status == "completed" and not step.result:
            # Generate intelligent response
            intelligent_response = self.get_intelligent_response(query)
            step.result = intelligent_response

            # Log enhancement
            logger.info(f"✨ Enhanced orchestrator step with intelligent response ({len(intelligent_response)} chars)")

        return step

    def integrate_with_classification(self, classification: Dict[str, Any]) -> str:
        """
        v5.5.2: Integrate with Safe Executor's classification system
        Returns appropriate response based on classification
        """
        # Check for prefilled response
        if classification.get("prefilled_response"):
            return classification["prefilled_response"]

        # Map classification to appropriate response
        if classification.get("is_greeting"):
            return self.fallback_responses["greeting"]

        if classification.get("is_nonsense"):
            return self.fallback_responses["unclear"]

        if classification.get("is_development_query"):
            dev_type = classification.get("dev_type")
            if dev_type:
                # Return specific development guidance
                return self._get_development_guidance(dev_type)

        # Default to intelligent response
        suggested_action = classification.get("suggested_action", "")
        if suggested_action == "direct_response":
            return self.fallback_responses["capabilities"]

        # Fallback
        return self.fallback_responses["general_help"]

    def _get_development_guidance(self, dev_type: str) -> str:
        """
        v5.5.2: Get specific guidance for development query types
        """
        dev_responses = {
            "performance": """🎯 Performance-Optimierung

Für Performance-Verbesserungen benötige ich:
• Aktuelle Performance-Metriken
• Identifizierte Engpässe
• Ziel-Performance

Führen Sie ein Profiling durch oder teilen Sie mir spezifische langsame Bereiche mit.""",

            "bug": """🐛 Bug-Analyse

Bitte teilen Sie mir mit:
• Fehlermeldung oder Symptome
• Schritte zur Reproduktion
• Erwartetes vs. tatsächliches Verhalten

Mit diesen Details kann ich effektiv helfen.""",

            "refactoring": """♻️ Code Refactoring

Für Refactoring benötige ich:
• Den zu refaktorierenden Code oder Dateipfad
• Gewünschte Verbesserungen
• Qualitätsziele

Zeigen Sie mir den Code, den ich verbessern soll.""",

            "testing": """🧪 Test-Erstellung

Für Tests benötige ich:
• Zu testende Komponente/Funktion
• Test-Art (Unit, Integration, E2E)
• Spezielle Test-Szenarien

Welche Funktionalität soll getestet werden?"""
        }

        return dev_responses.get(dev_type, self.fallback_responses["general_help"])