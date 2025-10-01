"""
Master Dispatcher - Der zentrale Orchestrator
Analysiert User Input und koordiniert alle Agenten
"""
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import yaml
import json
import re
from datetime import datetime

from .intent_classifier import IntentClassifier
from .workflow_generator import WorkflowGenerator
from .execution_engine import ExecutionEngine
from .learning_system import LearningSystem
from .shared_context import ProjectContextFactory

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
    
    async def process_request(self, user_input: str, context: Optional[Dict] = None, project_type: Optional[str] = None) -> Dict:
        """
        Haupteinstiegspunkt - Verarbeitet User-Anfragen vollautomatisch
        """
        print(f"\n🧠 Master Dispatcher: Analysiere Anfrage...")
        print(f"📝 User Input: {user_input[:100]}...")
        
        # Detect project type if not provided
        if not project_type:
            project_type = self._detect_project_type(user_input, context or {})
            print(f"🎯 Erkannter Project Type: {project_type}")
        
        # Create project-specific context
        project_context = None
        try:
            project_context = ProjectContextFactory.create_project_context(
                project_type, 
                context.get('project_name') if context else None
            )
            print(f"🔧 Project Context erstellt: {project_context.__class__.__name__}")
        except Exception as e:
            print(f"⚠️ Fallback zu Generic Context: {e}")
            project_context = ProjectContextFactory.create_project_context("generic")
        
        # Create request object with enhanced context
        enhanced_context = (context or {}).copy()
        enhanced_context.update({
            'project_type': project_type,
            'project_context': project_context,
            'domain_instructions': project_context.get_domain_instructions(),
            'quality_gates': project_context.get_quality_gates(),
            'project_specifics': project_context.get_project_specifics()
        })
        
        request = UserRequest(
            text=user_input,
            context=enhanced_context
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
    
    def _detect_project_type(self, user_input: str, context: Dict) -> str:
        """
        Automatically detect project type from user input and context
        """
        user_lower = user_input.lower()
        
        # Check context first for explicit project type
        if 'project_type' in context:
            return context['project_type']
        
        # Trading/Finance keywords
        trading_keywords = [
            'trading', 'trade', 'stock', 'aktien', 'börse', 'strategy', 'strategie',
            'backtest', 'backtesting', 'portfolio', 'investment', 'broker',
            'interactive brokers', 'ib', 'tws', 'market data', 'marktdaten',
            'vwap', 'ema', 'fibonacci', 'candlestick', 'chart', 'price',
            'ron strategy', 'live trading', 'after hours', 'engine parity',
            'stock_analyser', 'financial', 'finance', 'hedge fund',
            'algorithmic trading', 'algo trading', 'quant'
        ]
        
        # Web application keywords
        web_keywords = [
            'web app', 'webapp', 'website', 'api', 'rest', 'restful',
            'fastapi', 'flask', 'django', 'express', 'react', 'vue', 'angular',
            'frontend', 'backend', 'database', 'postgres', 'mysql', 'mongodb',
            'authentication', 'login', 'user management', 'crud', 'endpoint',
            'microservice', 'docker', 'kubernetes', 'cloud', 'aws', 'azure',
            'http', 'https', 'cors', 'jwt', 'oauth', 'session', 'cookie'
        ]
        
        # Desktop application keywords
        desktop_keywords = [
            'desktop app', 'desktop', 'gui', 'tkinter', 'pyqt', 'kivy',
            'electron', 'java swing', 'wpf', 'winforms', 'native app'
        ]
        
        # Mobile keywords
        mobile_keywords = [
            'mobile app', 'android', 'ios', 'react native', 'flutter',
            'xamarin', 'cordova', 'phonegap', 'ionic'
        ]
        
        # Data science/ML keywords
        ml_keywords = [
            'machine learning', 'ml', 'ai', 'artificial intelligence',
            'data science', 'data analysis', 'analytics', 'jupyter',
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
            'model', 'prediction', 'classification', 'regression', 'clustering'
        ]
        
        # Count matches for each category
        scores = {
            'trading': sum(1 for keyword in trading_keywords if keyword in user_lower),
            'web_app': sum(1 for keyword in web_keywords if keyword in user_lower),
            'desktop': sum(1 for keyword in desktop_keywords if keyword in user_lower),
            'mobile': sum(1 for keyword in mobile_keywords if keyword in user_lower),
            'ml': sum(1 for keyword in ml_keywords if keyword in user_lower)
        }
        
        # Special detection patterns
        if re.search(r'stock.*anal|trading.*system|backtest.*engine', user_lower):
            scores['trading'] += 3
        
        if re.search(r'build.*api|create.*endpoint|web.*service', user_lower):
            scores['web_app'] += 3
            
        if re.search(r'train.*model|predict|machine.*learning', user_lower):
            scores['ml'] += 3
        
        # Find the highest scoring type
        if max(scores.values()) > 0:
            detected_type = max(scores, key=scores.get)
            print(f"🔍 Project Type Detection Scores: {scores}")
            return detected_type
        
        # Default to generic if no clear match
        return 'generic'
    
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
    
    def _get_quality_gates_for_context(self, context: Dict) -> List[str]:
        """
        Get appropriate quality gates based on project context
        """
        quality_gates = []
        
        if 'project_context' in context:
            project_context = context['project_context']
            if hasattr(project_context, 'get_quality_gates'):
                quality_gates = project_context.get_quality_gates()
        
        # Fallback quality gates for different project types
        if not quality_gates:
            project_type = context.get('project_type', 'generic')
            if project_type in ['trading', 'stock_analyser']:
                quality_gates = ['TradingSystemQualityGate', 'RONStrategyQualityGate', 'EngineParityQualityGate']
            elif project_type in ['web_app', 'webapp', 'api']:
                quality_gates = ['SecurityQualityGate', 'PerformanceQualityGate']
            else:
                quality_gates = ['SecurityQualityGate']
        
        return quality_gates
    
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
        
        # Add project context information if available
        if 'project_context' in workflow.get('context', {}):
            project_context = workflow['context']['project_context']
            response['project_info'] = {
                'project_type': workflow['context'].get('project_type', 'unknown'),
                'project_name': getattr(project_context, 'project_name', 'Unknown'),
                'domain': getattr(project_context.get_project_specifics(), 'domain', 'Unknown') if hasattr(project_context, 'get_project_specifics') else 'Unknown',
                'quality_gates_applied': workflow['context'].get('quality_gates', [])
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