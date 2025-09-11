"""
Master Dispatcher - Der zentrale Orchestrator
Analysiert User Input und koordiniert alle Agenten
"""
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import yaml
import json
from datetime import datetime

from .intent_classifier import IntentClassifier
from .workflow_generator import WorkflowGenerator
from .execution_engine import ExecutionEngine
from .learning_system import LearningSystem

@dataclass
class UserRequest:
    text: str
    context: Dict[str, Any]
    preferences: Optional[Dict] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class MasterDispatcher:
    """
    Zentrale Orchestrierungs-Komponente
    Entscheidet automatisch welche Agenten für welche Aufgabe
    """
    
    def __init__(self):
        print("🧠 Initialisiere Master Dispatcher...")
        
        # Core Components
        self.intent_classifier = IntentClassifier()
        self.workflow_generator = WorkflowGenerator()
        self.execution_engine = ExecutionEngine()
        self.learning_system = LearningSystem()
        
        # Agent Registry (wird später von agents module geladen)
        self.agents = {}
        self._initialize_agents()
        
        # System Prompt für Meta-Reasoning
        self.system_prompt = """
        You are the Master Orchestrator for a multi-agent AI system.
        Your responsibilities:
        1. Understand user intentions precisely
        2. Break complex tasks into manageable subtasks
        3. Select the most appropriate agents for each subtask
        4. Create optimal execution workflows
        5. Handle dependencies and parallel execution
        6. Learn from past executions to improve
        
        Available Agents:
        - ArchitectGPT: System design and architecture
        - CodeSmithClaude: Python implementation
        - DocuBot: Documentation generation
        - ReviewerGPT: Code review and quality checks
        - FixerBot: Bug fixes and improvements
        - TradeStrat: Trading strategy development
        - ResearchBot: Internet research and data gathering
        
        Return structured workflow plans with clear dependencies.
        """
        
        print("✅ Master Dispatcher bereit!")
    
    async def process_request(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        """
        Haupteinstiegspunkt - Verarbeitet User-Anfragen vollautomatisch
        """
        print(f"\n🧠 Master Dispatcher: Analysiere Anfrage...")
        print(f"📝 User Input: {user_input[:100]}...")
        
        # Create request object
        request = UserRequest(
            text=user_input,
            context=context or {}
        )
        
        try:
            # 1. Intent Classification
            print("🎯 Klassifiziere Intent...")
            intent = await self.intent_classifier.classify(user_input)
            print(f"📊 Erkannter Intent: {intent['type']} (Confidence: {intent['confidence']:.2%})")
            
            # 2. Workflow Generation
            print("🔄 Generiere Workflow...")
            workflow = await self.workflow_generator.generate(
                intent=intent,
                user_input=user_input,
                context=context or {},
                agent_capabilities=self._get_agent_capabilities()
            )
            print(f"📋 Generierter Workflow: {len(workflow.get('steps', []))} Schritte")
            
            # 3. Validate & Optimize
            workflow = self._optimize_workflow(workflow)
            
            # 4. Execute Workflow
            print("🚀 Starte Ausführung...")
            result = await self.execution_engine.execute(
                workflow=workflow,
                agents=self.agents
            )
            
            # 5. Learn from Execution
            await self.learning_system.record_execution(
                request=user_input,
                intent=intent,
                workflow=workflow,
                result=result
            )
            
            # 6. Format response
            response = self._format_response(result, workflow, intent)
            
            return response
            
        except Exception as e:
            print(f"❌ Fehler im Master Dispatcher: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "request": user_input
            }
    
    def _initialize_agents(self):
        """Initialisiert alle verfügbaren Agenten"""
        try:
            from agents import (
                ArchitectGPT, CodeSmithClaude, DocuBot,
                ReviewerGPT, FixerBot, TradeStrat, ResearchBot
            )
            
            self.agents = {
                "ArchitectGPT": ArchitectGPT(),
                "CodeSmithClaude": CodeSmithClaude(),
                "DocuBot": DocuBot(),
                "ReviewerGPT": ReviewerGPT(),
                "FixerBot": FixerBot(),
                "TradeStrat": TradeStrat(),
                "ResearchBot": ResearchBot()
            }
            print(f"✅ {len(self.agents)} Agenten initialisiert")
            
        except ImportError as e:
            print(f"⚠️ Agenten noch nicht implementiert: {e}")
            # Placeholder für Testing
            self.agents = {}
    
    def _get_agent_capabilities(self) -> Dict:
        """Sammelt Fähigkeiten aller Agenten"""
        capabilities = {}
        for name, agent in self.agents.items():
            if hasattr(agent, 'get_capabilities'):
                capabilities[name] = agent.get_capabilities()
            else:
                capabilities[name] = {
                    "skills": ["general"],
                    "available": True
                }
        return capabilities
    
    def _optimize_workflow(self, workflow: Dict) -> Dict:
        """Optimiert Workflow für parallele Ausführung"""
        # Identifiziere unabhängige Steps
        # Gruppiere für parallele Ausführung
        # Minimiere Wartezeiten
        
        if not workflow.get('steps'):
            return workflow
            
        # Einfache Optimierung: Markiere unabhängige Steps
        for i, step in enumerate(workflow['steps']):
            if 'dependencies' not in step or not step['dependencies']:
                step['can_parallel'] = True
            else:
                step['can_parallel'] = False
                
        return workflow
    
    def _format_response(self, result: Dict, workflow: Dict, intent: Dict) -> Dict:
        """Formatiert die Antwort für den User"""
        response = {
            "status": "success",
            "intent": intent,
            "workflow_summary": {
                "total_steps": len(workflow.get('steps', [])),
                "completed_steps": len(result.get('completed_steps', [])),
                "execution_time": result.get('execution_time', 0)
            },
            "results": result.get('outputs', {}),
            "final_output": result.get('final_output', ''),
            "artifacts": result.get('artifacts', {})
        }
        
        # Add errors if any
        if result.get('errors'):
            response['errors'] = result['errors']
            response['status'] = 'partial_success'
            
        return response
    
    async def get_agent_stats(self) -> Dict:
        """Gibt Statistiken über Agent-Performance zurück"""
        return await self.learning_system.get_agent_performance()
    
    async def suggest_workflow(self, user_input: str) -> Optional[Dict]:
        """Schlägt basierend auf Historie einen Workflow vor"""
        intent = await self.intent_classifier.classify(user_input)
        return self.learning_system.suggest_workflow(intent)