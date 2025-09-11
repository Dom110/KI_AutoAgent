"""
Intent Classifier - Versteht was der User will
"""
import re
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

class IntentType(Enum):
    CREATE_SYSTEM = "create_system"
    DEBUG_CODE = "debug_code"
    EXPLAIN_CONCEPT = "explain_concept"
    OPTIMIZE_CODE = "optimize_code"
    TEST_CODE = "test_code"
    ANALYZE_CODE = "analyze_code"
    RESEARCH_TOPIC = "research_topic"
    TRADING_STRATEGY = "trading_strategy"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    type: IntentType
    confidence: float
    entities: Dict[str, List[str]]
    complexity: str
    original_input: str
    suggested_agents: List[str]

class IntentClassifier:
    """
    Klassifiziert User-Input in Intents
    Versteht was der User erreichen möchte
    """
    
    def __init__(self):
        # Intent Patterns
        self.patterns = {
            IntentType.CREATE_SYSTEM: {
                "keywords": ["baue", "erstelle", "create", "entwickle", "implementiere", "programmiere", "build", "make"],
                "regex": [
                    r"(baue|erstelle|entwickle|build|create).*(bot|system|modul|app|tool|application)",
                    r"ich (brauche|benötige|will|möchte|need|want) ein",
                    r"kannst du.*(bauen|erstellen|entwickeln|implementieren)"
                ],
                "examples": [
                    "Baue mir einen Trading Bot",
                    "Erstelle ein Portfolio Management System",
                    "Entwickle eine Backtesting Engine"
                ],
                "typical_agents": ["ResearchBot", "ArchitectGPT", "CodeSmithClaude", "ReviewerGPT", "DocuBot"]
            },
            
            IntentType.DEBUG_CODE: {
                "keywords": ["debug", "fehler", "error", "fix", "repariere", "funktioniert nicht", "problem", "bug", "kaputt"],
                "regex": [
                    r"(fehler|error|exception|bug|problem)",
                    r"funktioniert nicht",
                    r"(debug|fix|repariere|repair)",
                    r"(wirft|throws|raises).*(error|exception)"
                ],
                "examples": [
                    "Mein Code wirft einen IndexError",
                    "Debug diese Funktion",
                    "Das funktioniert nicht richtig"
                ],
                "typical_agents": ["ReviewerGPT", "FixerBot"]
            },
            
            IntentType.TRADING_STRATEGY: {
                "keywords": ["entwickle", "implementiere", "baue", "optimiere", "backtest", "strategie", "strategy"],
                "regex": [
                    r"(entwickle|implementiere|baue|create|build).*(trading|handel|trade).*(strategie|strategy|system)",
                    r"(optimiere|verbessere|optimize).*(strategie|strategy)",
                    r"backtest.*(strategie|strategy)",
                    r"(ron|ma|rsi|macd).*(strategie|strategy).*(entwickl|implemen|bau|optim)",
                    r"(erstelle|create).*(trading|momentum|arbitrage).*(system|bot|strategie)"
                ],
                "examples": [
                    "Entwickle eine Momentum Strategie",
                    "Backtest dieser Trading Idee", 
                    "Optimiere meine RON Strategie"
                ],
                "typical_agents": ["ResearchBot", "TradeStrat", "CodeSmithClaude", "ReviewerGPT"]
            },
            
            IntentType.EXPLAIN_CONCEPT: {
                "keywords": ["erkläre", "was ist", "wie funktioniert", "verstehe", "explain", "what is", "how does", "bedeutet"],
                "regex": [
                    r"(erkläre|explain).*(mir|me)?",
                    r"was (ist|sind|bedeutet)",
                    r"wie funktioniert",
                    r"verstehe.*(nicht|nicht ganz)",
                    r"(erkläre|explain).*(trading|momentum|arbitrage|strategie|backtesting)",
                    r"was.*(ist|bedeutet).*(trading|momentum|arbitrage|rsi|macd|vwap)",
                    r"(definiere|definition).*(von|of)?",
                    r"(beschreibe|describe).*(concept|konzept)"
                ],
                "examples": [
                    "Erkläre mir Momentum Trading",
                    "Was ist eine RON Strategie?",
                    "Wie funktioniert Backtesting?"
                ],
                "typical_agents": ["ResearchBot", "DocuBot"]
            },
            
            IntentType.OPTIMIZE_CODE: {
                "keywords": ["optimiere", "verbessere", "performance", "schneller", "effizienter", "optimize", "improve"],
                "regex": [
                    r"(optimiere|verbessere|optimize|improve)",
                    r"(schneller|faster|langsam|slow)",
                    r"performance",
                    r"effizienter"
                ],
                "examples": [
                    "Optimiere diese Funktion",
                    "Mach den Code schneller",
                    "Verbessere die Performance"
                ],
                "typical_agents": ["ReviewerGPT", "CodeSmithClaude", "FixerBot"]
            },
            
            IntentType.TEST_CODE: {
                "keywords": ["test", "teste", "unit test", "testing", "pytest", "coverage"],
                "regex": [
                    r"(schreibe|write|erstelle|create).*(test|tests)",
                    r"teste",
                    r"unit.?test",
                    r"test coverage"
                ],
                "examples": [
                    "Schreibe Tests für diese Funktion",
                    "Erstelle Unit Tests",
                    "Teste mein Trading Modul"
                ],
                "typical_agents": ["CodeSmithClaude", "ReviewerGPT"]
            },
            
            IntentType.ANALYZE_CODE: {
                "keywords": ["analysiere", "überprüfe", "validiere", "review", "analyze", "check", "validate", "untersuche", "prüfe"],
                "regex": [
                    r"(analysiere|analyze|überprüfe|check|validiere|validate|untersuche|prüfe).*(code|implementierung|implementation|datei|file)",
                    r"(code.?review|review.?code)",
                    r"(schaue?|look|guck).*(in|at|into).*(datei|file|verzeichnis|directory)",
                    r"(ist|are).*(korrekt|correct|richtig|right)",
                    r"(überprüfe|check|validiere|validate).*(auf|for).*(korrektheit|correctness|fehler|errors)",
                    r"(analysiere|analyze).*(bestehend|existing|vorhanden|current).*(system|code|implementation)",
                    r"\/Users\/.*\.(py|js|ts|java|cpp)"  # File paths
                ],
                "examples": [
                    "Analysiere die RON Strategy Implementierung",
                    "Überprüfe strategies/ron_strategy.py auf Korrektheit", 
                    "Code-Review für /path/to/file.py",
                    "Validiere die VWAP Fibonacci Logik"
                ],
                "typical_agents": ["CodeSmithClaude", "ReviewerGPT", "FixerBot"]
            },
            
            IntentType.DOCUMENTATION: {
                "keywords": ["dokumentiere", "dokumentation", "readme", "docstring", "kommentare", "document"],
                "regex": [
                    r"(dokumentiere|document)",
                    r"(schreibe|write).*(dokumentation|documentation|readme)",
                    r"(füge|add).*(kommentare|comments|docstrings)"
                ],
                "examples": [
                    "Dokumentiere diesen Code",
                    "Schreibe eine README",
                    "Füge Docstrings hinzu"
                ],
                "typical_agents": ["DocuBot"]
            },
            
            IntentType.RESEARCH_TOPIC: {
                "keywords": ["recherche", "recherchiere", "research", "suche", "finde", "information", "daten", "sammle", "collect"],
                "regex": [
                    r"(recherche|recherchiere|research|suche|search)",
                    r"(finde|find).*(information|daten|data)",
                    r"was.*(sagt|zeigt).*(literatur|research|studien)",
                    r"(recherche|recherchiere|research).*(trading|ml|machine learning|strategie|algorithmic)",
                    r"(sammle|collect).*(information|daten|data)",
                    r"(studiere|study|analysiere|analyze).*(literatur|literature|papers|studien)",
                    r"(suche|search).*(nach|for).*(information|papers|studies)"
                ],
                "examples": [
                    "Recherchiere ML Trading Strategien",
                    "Finde Informationen über Arbitrage",
                    "Was sagt die Literatur zu Momentum?"
                ],
                "typical_agents": ["ResearchBot", "DocuBot"]
            }
        }
        
        # Entity Extraction Patterns
        self.entity_patterns = {
            "programming_language": r"(python|javascript|typescript|java|c\+\+|rust|go)",
            "framework": r"(fastapi|django|flask|react|vue|angular|streamlit)",
            "trading_term": r"(momentum|arbitrage|mean reversion|breakout|scalping|swing|day trading)",
            "ml_model": r"(lstm|transformer|random forest|xgboost|neural network|deep learning)",
            "broker": r"(interactive brokers|ib|ibkr|alpaca|binance|kraken)",
            "indicator": r"(rsi|macd|ema|sma|vwap|bollinger|fibonacci)"
        }
    
    async def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Klassifiziert User Input
        Returns: Intent mit Confidence und Entities
        """
        user_input_lower = user_input.lower()
        
        # Score each intent
        intent_scores = {}
        suggested_agents_map = {}
        
        for intent_type, config in self.patterns.items():
            score = self._calculate_enhanced_intent_score(user_input_lower, config, intent_type)
            intent_scores[intent_type] = score
            if score > 0:
                suggested_agents_map[intent_type] = config.get("typical_agents", [])
        
        # Select best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
        else:
            best_intent = IntentType.UNKNOWN
            confidence = 0.0
        
        # If confidence too low, mark as unknown
        if confidence < 0.4:
            best_intent = IntentType.UNKNOWN
            suggested_agents = ["ResearchBot", "ArchitectGPT"]  # Fallback agents
        else:
            suggested_agents = suggested_agents_map.get(best_intent, [])
        
        # Extract entities
        entities = self._extract_entities(user_input)
        
        # Determine complexity
        complexity = self._assess_complexity(user_input, best_intent)
        
        return {
            "type": best_intent.value,
            "confidence": confidence,
            "entities": entities,
            "complexity": complexity,
            "original_input": user_input,
            "suggested_agents": suggested_agents
        }
    
    def _calculate_intent_score(self, text: str, config: Dict) -> float:
        """Berechnet Score für einen Intent"""
        score = 0.0
        matches = 0
        total_patterns = len(config["keywords"]) + len(config["regex"])
        
        # Keyword matching
        for keyword in config["keywords"]:
            if keyword in text:
                score += 0.3
                matches += 1
        
        # Regex matching
        for pattern in config["regex"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.5
                matches += 1
        
        # Calculate confidence based on pattern coverage
        if total_patterns > 0:
            confidence = matches / total_patterns
        else:
            confidence = 0
        
        # Boost score if multiple patterns match
        if matches > 1:
            score *= 1.2
        
        # Normalize score
        return min(score, 1.0)
    
    def _calculate_enhanced_intent_score(self, text: str, config: Dict, intent_type: IntentType) -> float:
        """Enhanced scoring with action priority and domain dampening"""
        
        # Base score calculation (existing logic)
        base_score = self._calculate_intent_score(text, config)
        
        # Action verb priority mapping
        action_verbs = {
            IntentType.EXPLAIN_CONCEPT: ["erkläre", "explain", "was ist", "wie funktioniert", "definiere", "beschreibe"],
            IntentType.RESEARCH_TOPIC: ["recherche", "recherchiere", "research", "suche", "finde", "sammle", "studiere", "analysiere"],
            IntentType.CREATE_SYSTEM: ["baue", "erstelle", "entwickle", "implementiere", "create", "build"],
            IntentType.DEBUG_CODE: ["debug", "fix", "repariere", "fehler", "error"],
            IntentType.OPTIMIZE_CODE: ["optimiere", "verbessere", "optimize", "improve"],
            IntentType.TEST_CODE: ["teste", "test", "schreibe test", "testing"],
            IntentType.DOCUMENTATION: ["dokumentiere", "document", "schreibe dokumentation"]
        }
        
        # Apply action priority boost
        if intent_type in action_verbs:
            text_lower = text.lower()
            for verb in action_verbs[intent_type]:
                if verb in text_lower:
                    base_score *= 1.4  # 40% boost for strong action priority
                    break
        
        # Apply domain dampening for trading_strategy when action verbs present
        if intent_type == IntentType.TRADING_STRATEGY:
            text_lower = text.lower()
            explanation_indicators = ["erkläre", "explain", "was ist", "wie funktioniert"]
            research_indicators = ["recherche", "recherchiere", "research", "finde", "sammle"]
            
            # If explanation or research verbs are present, reduce trading_strategy confidence
            if any(indicator in text_lower for indicator in explanation_indicators + research_indicators):
                base_score *= 0.6  # Reduce confidence by 40% when action verbs conflict
        
        return min(base_score, 1.0)
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrahiert Entities aus dem Text"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                # Remove duplicates while preserving order
                entities[entity_type] = list(dict.fromkeys(matches))
        
        return entities
    
    def _assess_complexity(self, text: str, intent: IntentType) -> str:
        """Bewertet Komplexität der Anfrage"""
        word_count = len(text.split())
        
        # High complexity intents
        high_complexity_intents = [
            IntentType.CREATE_SYSTEM,
            IntentType.TRADING_STRATEGY,
            IntentType.OPTIMIZE_CODE
        ]
        
        # Assess based on intent and text length
        if intent in high_complexity_intents:
            return "high"
        elif intent == IntentType.UNKNOWN:
            return "unknown"
        elif word_count > 50:
            return "high"
        elif word_count > 20:
            return "medium"
        else:
            return "low"
    
    def get_intent_description(self, intent_type: str) -> str:
        """Gibt eine Beschreibung für einen Intent zurück"""
        descriptions = {
            "create_system": "Entwicklung eines neuen Systems oder Moduls",
            "debug_code": "Fehlersuche und Debugging",
            "explain_concept": "Erklärung eines Konzepts oder einer Technologie",
            "optimize_code": "Code-Optimierung und Performance-Verbesserung",
            "test_code": "Erstellung von Tests",
            "analyze_code": "Code-Analyse und Review",
            "research_topic": "Recherche und Informationssammlung",
            "trading_strategy": "Entwicklung von Trading-Strategien",
            "documentation": "Dokumentation erstellen",
            "unknown": "Unklare Anfrage - weitere Klärung benötigt"
        }
        return descriptions.get(intent_type, "Keine Beschreibung verfügbar")