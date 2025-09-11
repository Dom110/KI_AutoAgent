"""
Workflow Generator - Erstellt optimale Ausführungspläne
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
from datetime import datetime

@dataclass
class WorkflowStep:
    """Einzelner Schritt in einem Workflow"""
    id: int
    agent: str
    task: str
    description: str
    dependencies: List[int] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""
    parallel_group: Optional[int] = None
    can_parallel: bool = False
    estimated_time: int = 60  # seconds

class WorkflowGenerator:
    """
    Generiert optimierte Workflows basierend auf Intent und Kontext
    """
    
    def __init__(self):
        # Workflow Templates für verschiedene Intent-Typen
        self.templates = self._load_templates()
        
    async def generate(
        self, 
        intent: Dict,
        user_input: str,
        context: Dict,
        agent_capabilities: Dict
    ) -> Dict:
        """
        Generiert einen optimierten Workflow
        """
        print(f"📋 Generiere Workflow für Intent: {intent['type']}")
        
        # 1. Select base template
        template = self._select_template(intent["type"])
        
        # 2. Customize based on entities and context
        workflow = self._customize_workflow(template, intent, context, user_input)
        
        # 3. Optimize for parallel execution
        workflow = self._optimize_parallel_execution(workflow)
        
        # 4. Validate agent availability
        workflow = self._validate_agents(workflow, agent_capabilities)
        
        # 5. Add metadata
        workflow["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "intent": intent["type"],
            "complexity": intent.get("complexity", "medium"),
            "estimated_total_time": self._estimate_total_time(workflow)
        }
        
        return workflow
    
    def _load_templates(self) -> Dict:
        """Lädt vordefinierte Workflow-Templates"""
        return {
            "create_system": {
                "name": "Full System Development",
                "description": "Vollständige Entwicklung eines neuen Systems",
                "steps": [
                    {
                        "agent": "ResearchBot",
                        "task": "research_requirements",
                        "description": "Recherchiere Anforderungen und Best Practices",
                        "estimated_time": 120
                    },
                    {
                        "agent": "ArchitectGPT",
                        "task": "design_architecture",
                        "description": "Entwerfe System-Architektur",
                        "dependencies": [0],
                        "estimated_time": 180
                    },
                    {
                        "agent": "CodeSmithClaude",
                        "task": "implement_system",
                        "description": "Implementiere das System",
                        "dependencies": [1],
                        "estimated_time": 300
                    },
                    {
                        "agent": "ReviewerGPT",
                        "task": "review_code",
                        "description": "Review Code-Qualität",
                        "dependencies": [2],
                        "estimated_time": 120
                    },
                    {
                        "agent": "FixerBot",
                        "task": "fix_issues",
                        "description": "Behebe gefundene Probleme",
                        "dependencies": [3],
                        "estimated_time": 180
                    },
                    {
                        "agent": "DocuBot",
                        "task": "generate_documentation",
                        "description": "Erstelle Dokumentation",
                        "dependencies": [4],
                        "estimated_time": 90
                    }
                ]
            },
            
            "debug_code": {
                "name": "Debug and Fix",
                "description": "Fehlersuche und Behebung",
                "steps": [
                    {
                        "agent": "ReviewerGPT",
                        "task": "analyze_error",
                        "description": "Analysiere Fehler und finde Ursache",
                        "estimated_time": 60
                    },
                    {
                        "agent": "FixerBot",
                        "task": "fix_bug",
                        "description": "Behebe den Fehler",
                        "dependencies": [0],
                        "estimated_time": 90
                    }
                ]
            },
            
            "trading_strategy": {
                "name": "Trading Strategy Development",
                "description": "Entwicklung einer Trading-Strategie",
                "steps": [
                    {
                        "agent": "ResearchBot",
                        "task": "research_market_data",
                        "description": "Recherchiere Marktdaten und Strategien",
                        "estimated_time": 150
                    },
                    {
                        "agent": "TradeStrat",
                        "task": "design_strategy",
                        "description": "Entwerfe Trading-Strategie",
                        "dependencies": [0],
                        "estimated_time": 180
                    },
                    {
                        "agent": "CodeSmithClaude",
                        "task": "implement_strategy",
                        "description": "Implementiere Strategie",
                        "dependencies": [1],
                        "estimated_time": 240
                    },
                    {
                        "agent": "ReviewerGPT",
                        "task": "backtest_review",
                        "description": "Review Backtest-Ergebnisse",
                        "dependencies": [2],
                        "estimated_time": 120
                    },
                    {
                        "agent": "DocuBot",
                        "task": "document_strategy",
                        "description": "Dokumentiere Strategie",
                        "dependencies": [3],
                        "estimated_time": 60
                    }
                ]
            },
            
            "explain_concept": {
                "name": "Concept Explanation",
                "description": "Erklärung eines Konzepts",
                "steps": [
                    {
                        "agent": "ResearchBot",
                        "task": "research_topic",
                        "description": "Recherchiere zum Thema",
                        "estimated_time": 90
                    },
                    {
                        "agent": "DocuBot",
                        "task": "create_explanation",
                        "description": "Erstelle verständliche Erklärung",
                        "dependencies": [0],
                        "estimated_time": 60
                    }
                ]
            },
            
            "optimize_code": {
                "name": "Code Optimization",
                "description": "Code-Optimierung",
                "steps": [
                    {
                        "agent": "ReviewerGPT",
                        "task": "analyze_performance",
                        "description": "Analysiere Performance-Probleme",
                        "estimated_time": 90
                    },
                    {
                        "agent": "CodeSmithClaude",
                        "task": "optimize_implementation",
                        "description": "Optimiere Implementation",
                        "dependencies": [0],
                        "estimated_time": 180
                    },
                    {
                        "agent": "ReviewerGPT",
                        "task": "verify_optimization",
                        "description": "Verifiziere Optimierungen",
                        "dependencies": [1],
                        "estimated_time": 60
                    }
                ]
            },
            
            "test_code": {
                "name": "Test Generation",
                "description": "Test-Erstellung",
                "steps": [
                    {
                        "agent": "CodeSmithClaude",
                        "task": "generate_tests",
                        "description": "Generiere Tests",
                        "estimated_time": 120
                    },
                    {
                        "agent": "ReviewerGPT",
                        "task": "review_tests",
                        "description": "Review Test-Coverage",
                        "dependencies": [0],
                        "estimated_time": 60
                    }
                ]
            },
            
            "documentation": {
                "name": "Documentation Creation",
                "description": "Dokumentations-Erstellung",
                "steps": [
                    {
                        "agent": "DocuBot",
                        "task": "generate_docs",
                        "description": "Erstelle Dokumentation",
                        "estimated_time": 90
                    }
                ]
            },
            
            "research_topic": {
                "name": "Topic Research",
                "description": "Themen-Recherche",
                "steps": [
                    {
                        "agent": "ResearchBot",
                        "task": "deep_research",
                        "description": "Führe umfassende Recherche durch",
                        "estimated_time": 120
                    },
                    {
                        "agent": "DocuBot",
                        "task": "summarize_findings",
                        "description": "Fasse Ergebnisse zusammen",
                        "dependencies": [0],
                        "estimated_time": 60
                    }
                ]
            },
            
            "unknown": {
                "name": "General Assistance",
                "description": "Allgemeine Unterstützung",
                "steps": [
                    {
                        "agent": "ResearchBot",
                        "task": "understand_request",
                        "description": "Verstehe Anfrage besser",
                        "estimated_time": 60
                    },
                    {
                        "agent": "ArchitectGPT",
                        "task": "provide_guidance",
                        "description": "Biete Anleitung",
                        "dependencies": [0],
                        "estimated_time": 90
                    }
                ]
            }
        }
    
    def _select_template(self, intent_type: str) -> Dict:
        """Wählt das passende Template basierend auf Intent"""
        template = self.templates.get(intent_type)
        if not template:
            print(f"⚠️ Kein Template für Intent '{intent_type}', verwende 'unknown'")
            template = self.templates["unknown"]
        
        return template.copy()
    
    def _customize_workflow(self, template: Dict, intent: Dict, context: Dict, user_input: str) -> Dict:
        """Passt Template an spezifische Anforderungen an"""
        workflow = {
            "name": template["name"],
            "description": template["description"],
            "steps": []
        }
        
        # Convert template steps to WorkflowStep objects
        for i, step_data in enumerate(template["steps"]):
            step = WorkflowStep(
                id=i,
                agent=step_data["agent"],
                task=step_data["task"],
                description=step_data.get("description", ""),
                dependencies=step_data.get("dependencies", []),
                estimated_time=step_data.get("estimated_time", 60)
            )
            
            # Add specific context based on entities
            if intent.get("entities"):
                step.inputs["entities"] = intent["entities"]
            
            # Add user input for context
            if i == 0:  # First step gets full user input
                step.inputs["user_request"] = user_input
            
            workflow["steps"].append(step.__dict__)
        
        # Add ML-specific steps if ML entities detected
        if "ml_model" in intent.get("entities", {}):
            ml_step = {
                "id": len(workflow["steps"]),
                "agent": "ResearchBot",
                "task": "research_ml_approaches",
                "description": "Recherchiere ML-Ansätze",
                "dependencies": [],
                "inputs": {"models": intent["entities"]["ml_model"]},
                "estimated_time": 90
            }
            workflow["steps"].insert(1, ml_step)
            
            # Update dependencies
            for step in workflow["steps"][2:]:
                if step["dependencies"]:
                    step["dependencies"] = [d + 1 for d in step["dependencies"]]
        
        return workflow
    
    def _optimize_parallel_execution(self, workflow: Dict) -> Dict:
        """Identifiziert und gruppiert parallel ausführbare Steps"""
        if not workflow.get("steps"):
            return workflow
        
        # Group steps by dependency level
        dependency_levels = {}
        max_level = 0
        
        for step in workflow["steps"]:
            if not step.get("dependencies"):
                level = 0
            else:
                # Find maximum dependency level
                level = max(dependency_levels.get(dep, 0) for dep in step["dependencies"]) + 1
            
            dependency_levels[step["id"]] = level
            step["parallel_group"] = level
            max_level = max(max_level, level)
        
        # Mark steps that can run in parallel
        for level in range(max_level + 1):
            parallel_steps = [s for s in workflow["steps"] if s.get("parallel_group") == level]
            if len(parallel_steps) > 1:
                for step in parallel_steps:
                    step["can_parallel"] = True
        
        workflow["execution_plan"] = {
            "parallel_groups": max_level + 1,
            "total_steps": len(workflow["steps"]),
            "can_parallelize": any(s.get("can_parallel") for s in workflow["steps"])
        }
        
        return workflow
    
    def _validate_agents(self, workflow: Dict, agent_capabilities: Dict) -> Dict:
        """Validiert, dass alle benötigten Agenten verfügbar sind"""
        unavailable_agents = []
        
        for step in workflow.get("steps", []):
            agent_name = step["agent"]
            if agent_name not in agent_capabilities:
                unavailable_agents.append(agent_name)
                step["status"] = "agent_unavailable"
            else:
                step["status"] = "ready"
        
        if unavailable_agents:
            workflow["warnings"] = [
                f"Folgende Agenten sind nicht verfügbar: {', '.join(unavailable_agents)}"
            ]
        
        return workflow
    
    def _estimate_total_time(self, workflow: Dict) -> int:
        """Schätzt die Gesamtausführungszeit in Sekunden"""
        if not workflow.get("steps"):
            return 0
        
        # If we can parallelize, calculate based on parallel groups
        if workflow.get("execution_plan", {}).get("can_parallelize"):
            time_by_group = {}
            for step in workflow["steps"]:
                group = step.get("parallel_group", 0)
                if group not in time_by_group:
                    time_by_group[group] = 0
                time_by_group[group] = max(time_by_group[group], step.get("estimated_time", 60))
            
            return sum(time_by_group.values())
        else:
            # Sequential execution
            return sum(step.get("estimated_time", 60) for step in workflow["steps"])
    
    def get_workflow_summary(self, workflow: Dict) -> str:
        """Erstellt eine Zusammenfassung des Workflows"""
        summary = f"Workflow: {workflow.get('name', 'Unnamed')}\n"
        summary += f"Beschreibung: {workflow.get('description', 'Keine Beschreibung')}\n"
        summary += f"Schritte: {len(workflow.get('steps', []))}\n"
        
        if workflow.get("execution_plan"):
            plan = workflow["execution_plan"]
            summary += f"Parallele Gruppen: {plan.get('parallel_groups', 0)}\n"
            summary += f"Kann parallelisiert werden: {'Ja' if plan.get('can_parallelize') else 'Nein'}\n"
        
        estimated_time = workflow.get("metadata", {}).get("estimated_total_time", 0)
        summary += f"Geschätzte Zeit: {estimated_time // 60} Minuten\n"
        
        return summary