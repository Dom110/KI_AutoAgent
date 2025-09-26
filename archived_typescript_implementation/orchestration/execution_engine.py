"""
Execution Engine - Führt Workflows aus
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import traceback

class ExecutionEngine:
    """
    Führt Workflows mit allen Agenten aus
    Unterstützt parallele und sequentielle Ausführung
    """
    
    def __init__(self):
        self.execution_history = []
        self.current_execution = None
        
    async def execute(self, workflow: Dict, agents: Dict) -> Dict:
        """
        Hauptausführungsmethode für Workflows
        """
        print(f"\n🚀 Starte Workflow-Ausführung: {workflow.get('name', 'Unnamed')}")
        start_time = time.time()
        
        # Initialize execution result
        result = {
            "workflow_name": workflow.get("name"),
            "started_at": datetime.now().isoformat(),
            "completed_steps": [],
            "failed_steps": [],
            "outputs": {},
            "artifacts": {},
            "errors": [],
            "status": "running"
        }
        
        self.current_execution = result
        
        try:
            # Group steps by parallel execution groups
            execution_groups = self._group_steps_for_execution(workflow)
            
            # Execute each group
            for group_id, steps in execution_groups.items():
                print(f"\n📋 Ausführung Gruppe {group_id + 1}/{len(execution_groups)}")
                
                if len(steps) > 1 and any(s.get("can_parallel") for s in steps):
                    # Parallel execution
                    print(f"   ⚡ Parallel: {len(steps)} Schritte")
                    group_results = await self._execute_parallel(steps, agents, result)
                else:
                    # Sequential execution
                    print(f"   📝 Sequentiell: {len(steps)} Schritte")
                    group_results = await self._execute_sequential(steps, agents, result)
                
                # Merge group results
                for step_id, step_result in group_results.items():
                    result["outputs"][step_id] = step_result
                    
                    # Check for errors
                    if step_result.get("status") == "error":
                        result["failed_steps"].append(step_id)
                        result["errors"].append({
                            "step": step_id,
                            "error": step_result.get("error")
                        })
            
            # Compile final output
            result["final_output"] = self._compile_final_output(result, workflow)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            # Determine final status
            if result["failed_steps"]:
                result["status"] = "partial_success"
                print(f"\n⚠️ Workflow teilweise erfolgreich ({len(result['failed_steps'])} Fehler)")
            else:
                result["status"] = "success"
                print(f"\n✅ Workflow erfolgreich abgeschlossen in {execution_time:.2f} Sekunden")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append({
                "type": "execution_error",
                "message": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"\n❌ Workflow fehlgeschlagen: {str(e)}")
        
        finally:
            result["completed_at"] = datetime.now().isoformat()
            self.execution_history.append(result)
            self.current_execution = None
        
        return result
    
    def _group_steps_for_execution(self, workflow: Dict) -> Dict[int, List[Dict]]:
        """Gruppiert Steps für Ausführung basierend auf Dependencies"""
        groups = {}
        
        for step in workflow.get("steps", []):
            group_id = step.get("parallel_group", 0)
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(step)
        
        # Sort groups by key to ensure correct execution order
        sorted_groups = dict(sorted(groups.items()))
        
        return sorted_groups
    
    async def _execute_parallel(self, steps: List[Dict], agents: Dict, result: Dict) -> Dict:
        """Führt mehrere Steps parallel aus"""
        tasks = []
        step_ids = []
        
        for step in steps:
            step_id = step["id"]
            step_ids.append(step_id)
            
            # Create async task for each step
            task = self._execute_single_step(step, agents, result)
            tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to step IDs
        step_results = {}
        for step_id, step_result in zip(step_ids, results):
            if isinstance(step_result, Exception):
                step_results[step_id] = {
                    "status": "error",
                    "error": str(step_result),
                    "traceback": traceback.format_exc()
                }
            else:
                step_results[step_id] = step_result
        
        return step_results
    
    async def _execute_sequential(self, steps: List[Dict], agents: Dict, result: Dict) -> Dict:
        """Führt Steps sequentiell aus"""
        step_results = {}
        
        for step in steps:
            step_id = step["id"]
            step_result = await self._execute_single_step(step, agents, result)
            step_results[step_id] = step_result
            
            # Stop if step failed and it's critical
            if step_result.get("status") == "error" and not step.get("allow_failure"):
                print(f"   ❌ Kritischer Fehler in Step {step_id}, stoppe Ausführung")
                break
        
        return step_results
    
    async def _execute_single_step(self, step: Dict, agents: Dict, result: Dict) -> Dict:
        """Führt einen einzelnen Step aus"""
        step_id = step["id"]
        agent_name = step["agent"]
        task = step["task"]
        
        print(f"   🤖 {agent_name}: {task}")
        
        try:
            # Get agent
            agent = agents.get(agent_name)
            if not agent:
                return {
                    "status": "error",
                    "error": f"Agent '{agent_name}' nicht verfügbar"
                }
            
            # Prepare context with outputs from dependencies
            context = step.get("inputs", {}).copy()
            
            # Add outputs from dependent steps
            for dep_id in step.get("dependencies", []):
                if dep_id in result["outputs"]:
                    context[f"step_{dep_id}_output"] = result["outputs"][dep_id].get("output")
            
            # Execute agent task
            if hasattr(agent, 'execute'):
                agent_result = await agent.execute(task, context)
            else:
                # Fallback for agents without execute method
                agent_result = {
                    "status": "success",
                    "output": f"Mock output from {agent_name} for task {task}",
                    "agent": agent_name,
                    "task": task
                }
            
            # Mark step as completed
            result["completed_steps"].append(step_id)
            
            print(f"      ✅ Abgeschlossen")
            
            return agent_result
            
        except Exception as e:
            print(f"      ❌ Fehler: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "agent": agent_name,
                "task": task
            }
    
    def _compile_final_output(self, result: Dict, workflow: Dict) -> str:
        """Kompiliert die finale Ausgabe aus allen Step-Outputs"""
        final_parts = []
        
        # Add workflow summary
        final_parts.append(f"# Workflow: {workflow.get('name', 'Unnamed')}\n")
        
        # Add successful outputs
        if result["completed_steps"]:
            final_parts.append(f"## Erfolgreich abgeschlossene Schritte ({len(result['completed_steps'])})\n")
            
            for step_id in result["completed_steps"]:
                if step_id in result["outputs"]:
                    output = result["outputs"][step_id]
                    agent = output.get("agent", "Unknown")
                    task = output.get("task", "Unknown")
                    
                    final_parts.append(f"### {agent}: {task}\n")
                    
                    if output.get("output"):
                        # Truncate very long outputs
                        output_text = str(output["output"])
                        if len(output_text) > 1000:
                            output_text = output_text[:1000] + "...[gekürzt]"
                        final_parts.append(f"{output_text}\n")
        
        # Add errors if any
        if result["errors"]:
            final_parts.append(f"\n## ⚠️ Fehler ({len(result['errors'])})\n")
            for error in result["errors"]:
                final_parts.append(f"- {error}\n")
        
        # Add execution summary
        final_parts.append(f"\n## Zusammenfassung\n")
        final_parts.append(f"- Status: {result['status']}\n")
        final_parts.append(f"- Ausführungszeit: {result.get('execution_time', 0):.2f} Sekunden\n")
        final_parts.append(f"- Abgeschlossene Schritte: {len(result['completed_steps'])}\n")
        final_parts.append(f"- Fehlgeschlagene Schritte: {len(result['failed_steps'])}\n")
        
        return "\n".join(final_parts)
    
    def get_current_status(self) -> Optional[Dict]:
        """Gibt den Status der aktuellen Ausführung zurück"""
        if self.current_execution:
            return {
                "running": True,
                "workflow": self.current_execution.get("workflow_name"),
                "completed_steps": len(self.current_execution.get("completed_steps", [])),
                "failed_steps": len(self.current_execution.get("failed_steps", [])),
                "started_at": self.current_execution.get("started_at")
            }
        return {"running": False}
    
    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """Gibt die Ausführungshistorie zurück"""
        return self.execution_history[-limit:] if self.execution_history else []