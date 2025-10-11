"""
Safe Orchestrator Executor - v5.5.2
Sicheres Ausführen des Orchestrators mit Loop-Prevention
"""

import logging
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

from .query_classifier import EnhancedQueryClassifier, ExecutionGuard, DetailedClassification
from .development_query_handler import DevelopmentQueryHandler
from .state import ExecutionStep, WorkflowState

logger = logging.getLogger(__name__)

@dataclass
class ExecutionAttempt:
    """Einzelner Ausführungsversuch"""
    query: str
    query_hash: str
    timestamp: datetime
    depth: int
    result: Optional[str] = None
    error: Optional[str] = None
    was_blocked: bool = False
    block_reason: Optional[str] = None

@dataclass
class ExecutionHistory:
    """Historie aller Ausführungsversuche"""
    attempts: List[ExecutionAttempt] = field(default_factory=list)
    query_hashes: Dict[str, int] = field(default_factory=dict)  # hash -> count
    depth_stack: List[str] = field(default_factory=list)  # Stack of query hashes
    max_depth_reached: int = 0
    total_blocked: int = 0

    def add_attempt(self, attempt: ExecutionAttempt):
        """Fügt einen Versuch zur Historie hinzu"""
        self.attempts.append(attempt)
        if attempt.query_hash not in self.query_hashes:
            self.query_hashes[attempt.query_hash] = 0
        self.query_hashes[attempt.query_hash] += 1
        if attempt.was_blocked:
            self.total_blocked += 1
        if attempt.depth > self.max_depth_reached:
            self.max_depth_reached = attempt.depth


class SafeOrchestratorExecutor:
    """
    Sichere Ausführung des Orchestrators mit mehreren Sicherheitsebenen:
    1. Query-Klassifikation und Filterung
    2. Execution Guards (Depth, Duplicates, Loops)
    3. Timeout-Mechanismen
    4. Fallback-Strategien
    """

    # Sicherheits-Konstanten
    MAX_ORCHESTRATOR_DEPTH = 3
    MAX_RETRIES_PER_QUERY = 2
    TIMEOUT_SECONDS = 30
    LOOP_DETECTION_WINDOW = 5  # Letzte N Queries für Loop-Erkennung

    def __init__(self):
        self.classifier = EnhancedQueryClassifier()
        self.dev_handler = DevelopmentQueryHandler()
        self.guard = ExecutionGuard()
        self.history = ExecutionHistory()
        self.logger = logging.getLogger(__name__)

    def _generate_query_hash(self, query: str) -> str:
        """Generiert einen Hash für eine Query"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:8]

    def _detect_loop_pattern(self, recent_hashes: List[str]) -> bool:
        """
        Erkennt Loop-Patterns in den letzten Queries
        Z.B. A->B->A oder A->B->C->A
        """
        if len(recent_hashes) < 2:
            return False

        # Check für direkte Wiederholung
        if len(recent_hashes) >= 2 and recent_hashes[-1] == recent_hashes[-2]:
            return True

        # Check für zyklische Patterns
        for i in range(1, min(4, len(recent_hashes) // 2 + 1)):
            pattern = recent_hashes[-i:]
            previous = recent_hashes[-2*i:-i] if 2*i <= len(recent_hashes) else []
            if pattern == previous:
                self.logger.warning(f"Loop pattern detected: {pattern}")
                return True

        return False

    def _get_safe_fallback_response(self, query: str, classification: DetailedClassification) -> str:
        """Generiert eine sichere Fallback-Antwort"""

        if classification.prefilled_response:
            return classification.prefilled_response

        if classification.is_greeting:
            return "Hallo! Ich bin der KI AutoAgent. Wie kann ich Ihnen bei der Entwicklung helfen?"

        if classification.is_nonsense:
            return "Entschuldigung, ich konnte Ihre Anfrage nicht verstehen. Könnten Sie sie bitte umformulieren?"

        if classification.is_development_query and classification.dev_type:
            response, _ = self.dev_handler.handle_development_query(
                query, classification.dev_type, {}
            )
            return response

        # Generische aber hilfreiche Antwort
        return f"""Ich habe Ihre Anfrage erhalten: "{query[:100]}..."

Ich kann Ihnen bei folgenden Aufgaben helfen:
- Code-Entwicklung und -Generierung
- Bug-Fixing und Debugging
- Performance-Optimierung
- Architektur-Design
- Test-Erstellung
- Dokumentation

Bitte geben Sie mehr Details an, damit ich Ihnen gezielt helfen kann."""

    async def _execute_with_timeout(
        self,
        func: callable,
        *args,
        timeout: int = None,
        **kwargs
    ) -> Tuple[bool, Any]:
        """Führt eine Funktion mit Timeout aus"""

        timeout = timeout or self.TIMEOUT_SECONDS

        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout
            )
            return True, result
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout after {timeout}s executing {func.__name__}")
            return False, None
        except Exception as e:
            self.logger.error(f"Error executing {func.__name__}: {e}")
            return False, None

    async def execute_safely(
        self,
        query: str,
        state,
        orchestrator_func: Optional[callable] = None,
        timeout: Optional[int] = None
    ) -> Tuple[bool, Any, str]:
        """
        Hauptmethode für sichere Orchestrator-Ausführung

        Returns:
            Tuple[bool, Any, str]: (success, result, message)
        """

        # Handle both dict and WorkflowState objects
        if isinstance(state, dict):
            state_dict = state
        else:
            state_dict = state.dict() if hasattr(state, "dict") else state.__dict__

        # 1. Query klassifizieren
        classification = self.classifier.classify_query(query, state_dict)

        # 2. Query-Hash generieren
        query_hash = self._generate_query_hash(query)
        current_depth = len(self.history.depth_stack)

        # 3. Erstelle Ausführungsversuch
        attempt = ExecutionAttempt(
            query=query,
            query_hash=query_hash,
            timestamp=datetime.now(),
            depth=current_depth
        )

        # 4. Sicherheitschecks
        # 4a. Depth Check
        if current_depth >= self.MAX_ORCHESTRATOR_DEPTH:
            attempt.was_blocked = True
            attempt.block_reason = f"Max depth {self.MAX_ORCHESTRATOR_DEPTH} erreicht"
            self.history.add_attempt(attempt)

            return False, None, self._get_safe_fallback_response(query, classification)

        # 4b. Duplicate Check (gleiche Query zu oft)
        if query_hash in self.history.query_hashes:
            if self.history.query_hashes[query_hash] >= self.MAX_RETRIES_PER_QUERY:
                attempt.was_blocked = True
                attempt.block_reason = f"Query bereits {self.MAX_RETRIES_PER_QUERY}x versucht"
                self.history.add_attempt(attempt)

                return False, None, self._get_safe_fallback_response(query, classification)

        # 4c. Loop Detection
        recent_hashes = self.history.depth_stack[-self.LOOP_DETECTION_WINDOW:]
        if self._detect_loop_pattern(recent_hashes + [query_hash]):
            attempt.was_blocked = True
            attempt.block_reason = "Loop-Pattern erkannt"
            self.history.add_attempt(attempt)

            return False, None, self._get_safe_fallback_response(query, classification)

        # 4d. Classification-based Safety Check
        if not classification.safe_to_execute:
            attempt.was_blocked = True
            attempt.block_reason = f"Unsichere Query (Safety Score: {classification.execution_safety_score:.2f})"
            self.history.add_attempt(attempt)

            return False, None, self._get_safe_fallback_response(query, classification)

        # 5. Query ist sicher - zur Ausführung vorbereiten
        self.history.depth_stack.append(query_hash)

        try:
            # 6. Entscheide basierend auf Klassifikation
            if classification.suggested_action == "direct_response":
                # Direkte Antwort ohne Orchestrator
                result = self._get_safe_fallback_response(query, classification)
                attempt.result = result
                self.history.add_attempt(attempt)
                return True, result, "Direkte Antwort generiert"

            elif classification.suggested_action == "clarification":
                # Klärung erforderlich
                result = classification.prefilled_response or self._get_safe_fallback_response(query, classification)
                attempt.result = result
                self.history.add_attempt(attempt)
                return True, result, "Klärung angefordert"

            elif classification.suggested_action == "route_agent":
                # An spezifischen Agenten weiterleiten
                if classification.is_development_query and classification.dev_type:
                    response, agents = self.dev_handler.handle_development_query(
                        query, classification.dev_type, state_dict
                    )

                    if agents:
                        # Erstelle Execution Steps für die Agenten
                        steps = []
                        for agent in agents:
                            step = ExecutionStep(
                                step_id=f"safe_exec_{agent}_{datetime.now().timestamp()}",
                                agent=agent,
                                task=query,
                                status="pending",
                                dependencies=[],
                                can_run_parallel=False
                            )
                            steps.append(step)

                        attempt.result = f"Routing zu Agenten: {', '.join(agents)}"
                        self.history.add_attempt(attempt)
                        return True, {"steps": steps, "response": response}, "An Agenten weitergeleitet"
                    else:
                        attempt.result = response
                        self.history.add_attempt(attempt)
                        return True, response, "Entwicklungs-Hilfe bereitgestellt"

            elif classification.suggested_action == "safe_execution" and orchestrator_func:
                # Sichere Orchestrator-Ausführung mit Timeout
                self.logger.info(f"Safe execution for query: {query[:50]}...")

                success, result = await self._execute_with_timeout(
                    orchestrator_func,
                    query,
                    state,
                    timeout=timeout or self.TIMEOUT_SECONDS
                )

                if success:
                    attempt.result = str(result)[:200]  # Kurze Zusammenfassung
                    self.history.add_attempt(attempt)
                    return True, result, "Orchestrator erfolgreich ausgeführt"
                else:
                    # Timeout oder Fehler
                    attempt.error = "Timeout or execution error"
                    self.history.add_attempt(attempt)
                    return False, None, self._get_safe_fallback_response(query, classification)

            else:
                # Fallback für unbekannte Actions
                result = self._get_safe_fallback_response(query, classification)
                attempt.result = result
                self.history.add_attempt(attempt)
                return True, result, "Fallback-Antwort generiert"

        except Exception as e:
            self.logger.error(f"Error in safe execution: {e}")
            attempt.error = str(e)
            self.history.add_attempt(attempt)
            return False, None, self._get_safe_fallback_response(query, classification)

        finally:
            # Stack bereinigen
            if self.history.depth_stack and self.history.depth_stack[-1] == query_hash:
                self.history.depth_stack.pop()

    def get_execution_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Ausführungen zurück"""

        total_attempts = len(self.history.attempts)
        blocked_attempts = self.history.total_blocked
        unique_queries = len(self.history.query_hashes)

        # Berechne durchschnittliche Tiefe
        avg_depth = 0
        if total_attempts > 0:
            avg_depth = sum(a.depth for a in self.history.attempts) / total_attempts

        # Finde häufigste Queries
        most_common_queries = sorted(
            self.history.query_hashes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Blockierungsgründe sammeln
        block_reasons = {}
        for attempt in self.history.attempts:
            if attempt.was_blocked and attempt.block_reason:
                reason = attempt.block_reason.split(':')[0]  # Nur den Hauptgrund
                block_reasons[reason] = block_reasons.get(reason, 0) + 1

        return {
            "total_attempts": total_attempts,
            "blocked_attempts": blocked_attempts,
            "block_percentage": (blocked_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            "unique_queries": unique_queries,
            "max_depth_reached": self.history.max_depth_reached,
            "average_depth": avg_depth,
            "most_common_queries": most_common_queries,
            "block_reasons": block_reasons
        }

    def should_use_safe_execution(self, query: str, state) -> bool:
        """
        Entscheidet ob Safe Execution verwendet werden soll
        Basiert auf Query-Klassifikation und aktuellem State
        """

        # Handle both dict and WorkflowState objects
        if isinstance(state, dict):
            execution_plan = state.get("execution_plan", [])
            state_dict = state
        else:
            execution_plan = state.execution_plan if hasattr(state, "execution_plan") else []
            state_dict = state.dict() if hasattr(state, "dict") else state.__dict__

        # Immer Safe Execution verwenden wenn:
        # 1. Orchestrator bereits aktiv war (Depth > 0)
        if execution_plan and any(
            step.agent == "orchestrator" and step.status == "completed"
            if hasattr(step, "agent") else
            step.get("agent") == "orchestrator" and step.get("status") == "completed"
            for step in execution_plan
        ):
            return True

        # 2. Query wurde klassifiziert als potentiell problematisch
        classification = self.classifier.classify_query(query, state_dict)
        if classification.execution_safety_score < 0.7:
            return True

        # 3. Es gibt bereits viele Steps im Plan (Komplexität)
        if len(execution_plan) > 10:
            return True

        # 4. Loop-Verdacht basierend auf bisherigen Steps
        if len(execution_plan) >= 5:
            agent_sequence = []
            for step in execution_plan[-5:]:
                if hasattr(step, "agent"):
                    agent_sequence.append(step.agent)
                elif isinstance(step, dict):
                    agent_sequence.append(step.get("agent", ""))

            if len(agent_sequence) >= 3 and len(set(agent_sequence)) == 1:
                # Gleicher Agent 3x hintereinander
                return True

        return False

    def reset_history(self):
        """Setzt die Ausführungs-Historie zurück"""
        self.history = ExecutionHistory()
        self.logger.info("Execution history reset")

    async def create_safe_execution_plan(
        self,
        query: str,
        state
    ) -> List[ExecutionStep]:
        """
        Erstellt einen sicheren Execution Plan ohne tatsächliche Orchestrator-Ausführung
        Nutzt Klassifikation und vordefinierte Patterns
        """

        # Handle both dict and WorkflowState objects
        if isinstance(state, dict):
            state_dict = state
        else:
            state_dict = state.dict() if hasattr(state, "dict") else state.__dict__

        classification = self.classifier.classify_query(query, state_dict)
        steps = []
        timestamp = datetime.now().timestamp()

        # Basierend auf Klassifikation einen Plan erstellen
        if classification.is_development_query and classification.dev_type:
            # Entwicklungs-spezifischer Plan
            response, agents = self.dev_handler.handle_development_query(
                query, classification.dev_type, state_dict
            )

            for i, agent in enumerate(agents):
                step = ExecutionStep(
                    step_id=f"safe_plan_{agent}_{timestamp}_{i}",
                    agent=agent,
                    task=query if i == 0 else f"Continue with {classification.dev_type} task",
                    status="pending",
                    dependencies=[] if i == 0 else [steps[i-1].step_id],
                    can_run_parallel=False
                )
                steps.append(step)

        elif classification.suggested_action == "route_agent":
            # Direkte Agent-Routing basierend auf Query-Typ
            if "architect" in query.lower() or "design" in query.lower():
                agents = ["architect"]
            elif "code" in query.lower() or "implement" in query.lower():
                agents = ["codesmith", "reviewer"]
            elif "test" in query.lower():
                agents = ["codesmith", "reviewer"]
            elif "doc" in query.lower():
                agents = ["docbot"]
            else:
                agents = ["codesmith"]  # Default

            for i, agent in enumerate(agents):
                step = ExecutionStep(
                    step_id=f"safe_plan_{agent}_{timestamp}_{i}",
                    agent=agent,
                    task=query if i == 0 else f"Review and improve",
                    status="pending",
                    dependencies=[] if i == 0 else [steps[i-1].step_id],
                    can_run_parallel=False
                )
                steps.append(step)

        else:
            # Fallback: Einzelner CodeSmith Step
            step = ExecutionStep(
                step_id=f"safe_plan_fallback_{timestamp}",
                agent="codesmith",
                task=query,
                status="pending",
                dependencies=[],
                can_run_parallel=False
            )
            steps.append(step)

        self.logger.info(f"Created safe execution plan with {len(steps)} steps")
        return steps