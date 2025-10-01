"""
Base Workflow Abstract Class
Defines the interface for all workflow implementations in the KI_AutoAgent system
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseWorkflow(ABC):
    """
    Abstract base class for all workflow implementations
    
    Workflows define the sequence of steps and agent interactions
    needed to complete different types of projects
    """
    
    def __init__(self, name: str):
        self.name = name
        self.created_at = datetime.now()
        self.execution_history = []
    
    @abstractmethod
    def get_workflow_steps(self) -> List[str]:
        """
        Return ordered list of workflow steps
        
        Returns:
            List of step names in execution order
        """
        pass
    
    @abstractmethod
    def get_step_agents(self, step: str) -> List[str]:
        """
        Return list of agents suitable for executing a specific step
        
        Args:
            step: The workflow step name
            
        Returns:
            List of agent names that can handle this step
        """
        pass
    
    @abstractmethod
    def get_step_instructions(self, step: str, context: Any) -> str:
        """
        Generate specific instructions for a workflow step
        
        Args:
            step: The workflow step name
            context: Shared context containing project information
            
        Returns:
            Detailed instructions for the step
        """
        pass
    
    @abstractmethod
    def validate_step_completion(self, step: str, step_output: Dict[str, Any]) -> bool:
        """
        Validate that a workflow step has been completed successfully
        
        Args:
            step: The workflow step name
            step_output: The output from step execution
            
        Returns:
            True if step completed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_workflow_description(self) -> str:
        """
        Return a human-readable description of the workflow
        
        Returns:
            Workflow description string
        """
        pass
    
    @abstractmethod
    def get_success_criteria(self) -> Dict[str, List[str]]:
        """
        Define success criteria for each workflow step
        
        Returns:
            Dictionary mapping step names to lists of success criteria
        """
        pass
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get comprehensive workflow information
        
        Returns:
            Dictionary with workflow metadata and configuration
        """
        return {
            "name": self.name,
            "description": self.get_workflow_description(),
            "steps": self.get_workflow_steps(),
            "success_criteria": self.get_success_criteria(),
            "created_at": self.created_at.isoformat(),
            "execution_count": len(self.execution_history)
        }
    
    def log_execution(self, step: str, agent: str, result: Dict[str, Any]):
        """
        Log workflow step execution for tracking and analysis
        
        Args:
            step: The workflow step that was executed
            agent: The agent that executed the step
            result: The execution result
        """
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "agent": agent,
            "success": result.get("success", False),
            "duration": result.get("duration", 0),
            "output_length": len(str(result.get("content", "")))
        }
        
        self.execution_history.append(execution_record)
        
        logger.info(f"Workflow step logged: {step} by {agent} - Success: {execution_record['success']}")
    
    def get_next_step(self, current_step: Optional[str] = None) -> Optional[str]:
        """
        Get the next step in the workflow sequence
        
        Args:
            current_step: The current step, or None to get first step
            
        Returns:
            Next step name, or None if workflow is complete
        """
        steps = self.get_workflow_steps()
        
        if not current_step:
            return steps[0] if steps else None
        
        try:
            current_index = steps.index(current_step)
            if current_index + 1 < len(steps):
                return steps[current_index + 1]
        except ValueError:
            logger.warning(f"Current step '{current_step}' not found in workflow steps")
        
        return None
    
    def get_step_position(self, step: str) -> tuple:
        """
        Get the position of a step in the workflow
        
        Args:
            step: The step name
            
        Returns:
            Tuple of (current_position, total_steps)
        """
        steps = self.get_workflow_steps()
        try:
            position = steps.index(step) + 1
            return (position, len(steps))
        except ValueError:
            return (0, len(steps))
    
    def is_workflow_complete(self, current_step: str) -> bool:
        """
        Check if the workflow is complete
        
        Args:
            current_step: The current step
            
        Returns:
            True if this is the last step in the workflow
        """
        steps = self.get_workflow_steps()
        return steps and current_step == steps[-1]
    
    def get_workflow_progress(self, current_step: str) -> float:
        """
        Calculate workflow completion progress
        
        Args:
            current_step: The current step
            
        Returns:
            Progress as a float between 0.0 and 1.0
        """
        position, total = self.get_step_position(current_step)
        return position / total if total > 0 else 0.0
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about workflow executions
        
        Returns:
            Dictionary with execution statistics
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "steps_executed": {},
                "agents_used": {}
            }
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for exec in self.execution_history if exec.get("success", False))
        success_rate = successful_executions / total_executions
        
        durations = [exec.get("duration", 0) for exec in self.execution_history]
        average_duration = sum(durations) / len(durations) if durations else 0
        
        # Count step executions
        steps_executed = {}
        agents_used = {}
        
        for exec in self.execution_history:
            step = exec.get("step", "unknown")
            agent = exec.get("agent", "unknown")
            
            steps_executed[step] = steps_executed.get(step, 0) + 1
            agents_used[agent] = agents_used.get(agent, 0) + 1
        
        return {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "average_duration": average_duration,
            "steps_executed": steps_executed,
            "agents_used": agents_used,
            "most_used_agent": max(agents_used, key=agents_used.get) if agents_used else None,
            "most_executed_step": max(steps_executed, key=steps_executed.get) if steps_executed else None
        }