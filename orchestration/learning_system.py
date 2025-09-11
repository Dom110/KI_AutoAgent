"""
Learning System - Lernt aus vergangenen Ausführungen
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import statistics

class LearningSystem:
    """
    Adaptives System das aus Erfahrung lernt
    Speichert Erfolgsmetriken und optimiert zukünftige Ausführungen
    """
    
    def __init__(self):
        # Create memory directory
        self.memory_dir = Path("/Users/dominikfoert/git/KI_AutoAgent/memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.history_file = self.memory_dir / "execution_history.json"
        self.patterns_file = self.memory_dir / "success_patterns.json"
        self.metrics_file = self.memory_dir / "performance_metrics.json"
        
        # Load existing data
        self.execution_history = self._load_history()
        self.success_patterns = self._load_patterns()
        self.performance_metrics = self._load_metrics()
        
        print(f"📚 Learning System initialisiert mit {len(self.execution_history)} historischen Ausführungen")
    
    async def record_execution(
        self,
        request: str,
        intent: Dict,
        workflow: Dict,
        result: Dict
    ):
        """
        Zeichnet eine Ausführung auf und lernt daraus
        """
        # Calculate metrics
        metrics = self._calculate_metrics(result)
        
        # Create execution record
        execution_record = {
            "id": len(self.execution_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "request": request[:500],  # Limit length
            "intent": intent,
            "workflow_name": workflow.get("name"),
            "workflow_steps": len(workflow.get("steps", [])),
            "result_status": result.get("status"),
            "metrics": metrics,
            "agents_used": self._extract_agents_used(workflow)
        }
        
        # Save to history
        self.execution_history.append(execution_record)
        
        # Analyze for patterns
        if self._was_successful(result):
            self._record_success_pattern(execution_record)
        
        # Update performance metrics
        self._update_performance_metrics(execution_record)
        
        # Persist to disk
        self._save_all()
        
        print(f"📝 Ausführung aufgezeichnet (Success Score: {metrics.get('success_score', 0):.2%})")
    
    def suggest_workflow(self, intent: Dict) -> Optional[Dict]:
        """
        Schlägt basierend auf Historie einen Workflow vor
        """
        # Find similar successful executions
        similar_executions = self._find_similar_executions(intent)
        
        if not similar_executions:
            return None
        
        # Select best performing workflow
        best_execution = max(
            similar_executions,
            key=lambda x: x["metrics"]["success_score"]
        )
        
        suggested_workflow = {
            "suggested": True,
            "based_on": best_execution["id"],
            "confidence": best_execution["metrics"]["success_score"],
            "workflow_name": best_execution["workflow_name"],
            "agents": best_execution["agents_used"]
        }
        
        print(f"💡 Workflow-Vorschlag basierend auf Ausführung #{best_execution['id']} "
              f"(Erfolgsrate: {suggested_workflow['confidence']:.2%})")
        
        return suggested_workflow
    
    async def get_agent_performance(self) -> Dict:
        """
        Gibt Performance-Metriken für alle Agenten zurück
        """
        if not self.performance_metrics:
            return {}
        
        agent_stats = {}
        
        for agent_name, metrics in self.performance_metrics.get("agents", {}).items():
            total_exec = metrics.get("total_executions", 0)
            if total_exec > 0:
                success_rate = metrics.get("successful", 0) / total_exec
                avg_time = metrics.get("total_time", 0) / total_exec
                
                agent_stats[agent_name] = {
                    "total_executions": total_exec,
                    "success_rate": success_rate,
                    "avg_execution_time": avg_time,
                    "last_used": metrics.get("last_used"),
                    "rating": self._calculate_agent_rating(metrics)
                }
        
        return agent_stats
    
    def get_intent_statistics(self) -> Dict:
        """
        Gibt Statistiken über Intent-Typen zurück
        """
        intent_stats = {}
        
        for execution in self.execution_history:
            intent_type = execution.get("intent", {}).get("type", "unknown")
            
            if intent_type not in intent_stats:
                intent_stats[intent_type] = {
                    "count": 0,
                    "success_count": 0,
                    "avg_success_score": [],
                    "avg_execution_time": []
                }
            
            stats = intent_stats[intent_type]
            stats["count"] += 1
            
            if execution.get("result_status") == "success":
                stats["success_count"] += 1
            
            metrics = execution.get("metrics", {})
            if metrics.get("success_score"):
                stats["avg_success_score"].append(metrics["success_score"])
            if metrics.get("execution_time"):
                stats["avg_execution_time"].append(metrics["execution_time"])
        
        # Calculate averages
        for intent_type, stats in intent_stats.items():
            if stats["avg_success_score"]:
                stats["avg_success_score"] = statistics.mean(stats["avg_success_score"])
            else:
                stats["avg_success_score"] = 0
                
            if stats["avg_execution_time"]:
                stats["avg_execution_time"] = statistics.mean(stats["avg_execution_time"])
            else:
                stats["avg_execution_time"] = 0
            
            stats["success_rate"] = stats["success_count"] / stats["count"] if stats["count"] > 0 else 0
        
        return intent_stats
    
    # Private methods
    
    def _load_history(self) -> List[Dict]:
        """Lädt Ausführungshistorie von Disk"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Historie: {e}")
        return []
    
    def _load_patterns(self) -> Dict:
        """Lädt Erfolgsmuster von Disk"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Muster: {e}")
        return {}
    
    def _load_metrics(self) -> Dict:
        """Lädt Performance-Metriken von Disk"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Metriken: {e}")
        return {"agents": {}, "intents": {}}
    
    def _save_all(self):
        """Speichert alle Daten auf Disk"""
        try:
            # Save history
            with open(self.history_file, 'w') as f:
                json.dump(self.execution_history[-100:], f, indent=2)  # Keep last 100
            
            # Save patterns
            with open(self.patterns_file, 'w') as f:
                json.dump(self.success_patterns, f, indent=2)
            
            # Save metrics
            with open(self.metrics_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern: {e}")
    
    def _calculate_metrics(self, result: Dict) -> Dict:
        """Berechnet Erfolgsmetriken für eine Ausführung"""
        metrics = {}
        
        # Success score calculation
        total_steps = len(result.get("completed_steps", [])) + len(result.get("failed_steps", []))
        if total_steps > 0:
            success_ratio = len(result.get("completed_steps", [])) / total_steps
        else:
            success_ratio = 0
        
        # Adjust based on status
        if result.get("status") == "success":
            success_score = 1.0
        elif result.get("status") == "partial_success":
            success_score = success_ratio * 0.8
        else:
            success_score = success_ratio * 0.5
        
        metrics["success_score"] = success_score
        metrics["execution_time"] = result.get("execution_time", 0)
        metrics["error_count"] = len(result.get("errors", []))
        metrics["completed_steps"] = len(result.get("completed_steps", []))
        metrics["failed_steps"] = len(result.get("failed_steps", []))
        
        return metrics
    
    def _was_successful(self, result: Dict) -> bool:
        """Prüft ob eine Ausführung erfolgreich war"""
        return result.get("status") in ["success", "partial_success"]
    
    def _record_success_pattern(self, execution_record: Dict):
        """Zeichnet ein erfolgreiches Muster auf"""
        intent_type = execution_record.get("intent", {}).get("type", "unknown")
        
        if intent_type not in self.success_patterns:
            self.success_patterns[intent_type] = []
        
        pattern = {
            "execution_id": execution_record["id"],
            "workflow_name": execution_record.get("workflow_name"),
            "agents_used": execution_record.get("agents_used", []),
            "success_score": execution_record.get("metrics", {}).get("success_score", 0),
            "timestamp": execution_record.get("timestamp")
        }
        
        self.success_patterns[intent_type].append(pattern)
        
        # Keep only top 10 patterns per intent
        self.success_patterns[intent_type] = sorted(
            self.success_patterns[intent_type],
            key=lambda x: x["success_score"],
            reverse=True
        )[:10]
    
    def _update_performance_metrics(self, execution_record: Dict):
        """Aktualisiert Performance-Metriken"""
        # Update agent metrics
        for agent in execution_record.get("agents_used", []):
            if agent not in self.performance_metrics["agents"]:
                self.performance_metrics["agents"][agent] = {
                    "total_executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "last_used": None
                }
            
            agent_metrics = self.performance_metrics["agents"][agent]
            agent_metrics["total_executions"] += 1
            
            if execution_record.get("result_status") == "success":
                agent_metrics["successful"] += 1
            elif execution_record.get("result_status") == "error":
                agent_metrics["failed"] += 1
            
            agent_metrics["total_time"] += execution_record.get("metrics", {}).get("execution_time", 0)
            agent_metrics["last_used"] = execution_record.get("timestamp")
    
    def _find_similar_executions(self, intent: Dict) -> List[Dict]:
        """Findet ähnliche vergangene Ausführungen"""
        intent_type = intent.get("type")
        similar = []
        
        for execution in self.execution_history:
            if execution.get("intent", {}).get("type") == intent_type:
                # Check if successful
                if execution.get("metrics", {}).get("success_score", 0) > 0.7:
                    similar.append(execution)
        
        # Sort by success score
        similar.sort(key=lambda x: x.get("metrics", {}).get("success_score", 0), reverse=True)
        
        return similar[:5]  # Return top 5
    
    def _extract_agents_used(self, workflow: Dict) -> List[str]:
        """Extrahiert Liste der verwendeten Agenten aus Workflow"""
        agents = []
        for step in workflow.get("steps", []):
            agent = step.get("agent")
            if agent and agent not in agents:
                agents.append(agent)
        return agents
    
    def _calculate_agent_rating(self, metrics: Dict) -> float:
        """Berechnet eine Bewertung für einen Agenten"""
        total = metrics.get("total_executions", 0)
        if total == 0:
            return 0.0
        
        success_rate = metrics.get("successful", 0) / total
        
        # Adjust for execution count (more executions = more reliable)
        reliability_factor = min(total / 10, 1.0)  # Max at 10 executions
        
        return success_rate * reliability_factor