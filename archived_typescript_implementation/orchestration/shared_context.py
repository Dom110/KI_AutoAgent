"""
Shared Context System for Multi-Agent Workflows
Base classes and utilities for cross-agent communication
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class SharedContext(ABC):
    """
    Abstract base class for shared context across agents
    """
    user_request: str
    max_iterations: int = 5
    
    def __post_init__(self):
        self.agent_outputs = {}
        self.iteration_history = []
        self.current_iteration = 0
        self.created_at = datetime.now().isoformat()
    
    @abstractmethod
    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Return context specific to an agent"""
        pass
    
    @abstractmethod
    def get_agent_instruction_summary(self, agent_name: str) -> str:
        """Get formatted instructions for specific agent"""
        pass
    
    def add_agent_output(self, agent_name: str, step_id: int, output: Dict):
        """Store agent output with iteration tracking"""
        if self.current_iteration not in self.agent_outputs:
            self.agent_outputs[self.current_iteration] = {}
            
        self.agent_outputs[self.current_iteration][step_id] = {
            "agent": agent_name,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_iteration_summary(self) -> Dict:
        """Get summary of all iterations"""
        return {
            "total_iterations": self.current_iteration,
            "max_iterations": self.max_iterations,
            "iteration_history": self.iteration_history,
            "current_outputs": self.agent_outputs.get(self.current_iteration, {}),
            "limit_reached": self.current_iteration >= self.max_iterations
        }
    
    def start_new_iteration(self, reason: str = ""):
        """Start a new iteration cycle"""
        self.iteration_history.append({
            "iteration": self.current_iteration,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        self.current_iteration += 1
    
    def get_relevant_outputs(self, agent_name: str) -> Dict:
        """Get outputs relevant to specific agent"""
        relevant_outputs = {}
        
        # Get outputs from all previous iterations
        for iteration in range(self.current_iteration):
            if iteration in self.agent_outputs:
                for step_id, step_data in self.agent_outputs[iteration].items():
                    relevant_outputs[f"iteration_{iteration}_step_{step_id}"] = step_data
                    
        return relevant_outputs

class ProjectContextFactory:
    """
    Factory for creating appropriate project contexts based on project type
    """
    
    @staticmethod
    def create_project_context(project_type: str, project_name: Optional[str] = None):
        """
        Create project-specific context based on project type
        
        Args:
            project_type: Type of project ('trading', 'web_app', 'api', 'desktop', etc.)
            project_name: Optional specific project name
            
        Returns:
            BaseProjectContext: Project-specific context instance
        """
        from .project_contexts import (
            TradingProjectContext, 
            WebAppProjectContext,
            BaseProjectContext
        )
        
        project_name = project_name or f"{project_type}_project"
        
        context_map = {
            'trading': TradingProjectContext,
            'stock_analyser': TradingProjectContext,  # Alias for trading
            'web_app': WebAppProjectContext,
            'webapp': WebAppProjectContext,  # Alias
            'api': WebAppProjectContext,  # Use web app context for APIs
            'rest_api': WebAppProjectContext,  # Alias
        }
        
        context_class = context_map.get(project_type.lower())
        if context_class:
            return context_class(project_name)
        else:
            # Create a generic context for unknown types
            return GenericProjectContext(project_name, project_type)
    
    @staticmethod
    def get_available_project_types() -> List[str]:
        """Get list of available project types"""
        return [
            'trading',
            'stock_analyser',
            'web_app',
            'webapp', 
            'api',
            'rest_api',
            'desktop',
            'mobile',
            'data_science',
            'ml',
            'generic'
        ]
    
    @staticmethod
    def create_shared_context(
        project_type: str, 
        user_request: str, 
        project_name: Optional[str] = None,
        **kwargs
    ) -> 'ProjectSharedContext':
        """
        Create shared context with project-specific context embedded
        
        Args:
            project_type: Type of project
            user_request: User's request
            project_name: Optional project name
            **kwargs: Additional context parameters
            
        Returns:
            ProjectSharedContext: Complete shared context for workflow
        """
        project_context = ProjectContextFactory.create_project_context(project_type, project_name)
        return ProjectSharedContext(
            user_request=user_request,
            project_context=project_context,
            **kwargs
        )


class GenericProjectContext:
    """Generic project context for unknown project types"""
    
    def __init__(self, project_name: str, project_type: str = "generic"):
        self.project_name = project_name
        self.project_type = project_type
    
    def get_domain_instructions(self) -> str:
        return f"""
GENERIC PROJECT INSTRUCTIONS:

PROJECT: {self.project_name}
TYPE: {self.project_type}

GENERAL DEVELOPMENT GUIDELINES:
- Write clean, readable, maintainable code
- Follow best practices for the chosen programming language
- Implement proper error handling
- Add comprehensive documentation
- Include unit tests where appropriate
- Follow security best practices
- Optimize for performance where necessary

QUALITY REQUIREMENTS:
- Code should be well-structured and modular
- Functions should be focused and single-purpose
- Variable and function names should be descriptive
- Error messages should be clear and actionable
- Code should handle edge cases gracefully
"""
    
    def get_quality_gates(self) -> List[str]:
        return ["SecurityQualityGate", "PerformanceQualityGate"]
    
    def get_project_specifics(self):
        from .project_contexts.base_project_context import ProjectSpecification
        return ProjectSpecification(
            name=self.project_name,
            domain="Generic Software Development",
            programming_languages=["Python", "JavaScript", "Java", "C++"],
            frameworks=["To be determined"],
            architecture_patterns=["MVC", "Clean Architecture", "Hexagonal Architecture"],
            special_requirements=["Cross-platform compatibility", "Maintainable codebase"],
            compliance_standards=["Industry best practices"]
        )


class ContextFactory:
    """
    Legacy factory for backward compatibility - redirects to ProjectContextFactory
    """
    
    @staticmethod
    def create_context(project_type: str, user_request: str, **kwargs) -> SharedContext:
        """Create shared context based on project type - Legacy method"""
        # For backward compatibility, create ProjectSharedContext
        project_context = ProjectContextFactory.create_shared_context(
            project_type, user_request, **kwargs
        )
        return project_context

@dataclass 
class GenericSharedContext(SharedContext):
    """
    Generic shared context for non-specialized projects
    """
    
    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Return generic context for agent"""
        return {
            "user_request": self.user_request,
            "previous_outputs": self.get_relevant_outputs(agent_name),
            "iteration": self.current_iteration,
            "project_type": "generic"
        }
    
    def get_agent_instruction_summary(self, agent_name: str) -> str:
        """Get generic instructions for agent"""
        return f"""
GENERIC PROJECT CONTEXT:

User Request: {self.user_request}
Iteration: {self.current_iteration + 1}/{self.max_iterations}

Previous Agent Outputs:
{json.dumps(self.get_relevant_outputs(agent_name), indent=2)}

Please complete your task according to your role and capabilities.
"""

class SharedContextManager:
    """
    Manages shared context throughout workflow execution
    """
    
    def __init__(self, context: SharedContext):
        self.context = context
        self.context_history = []
    
    def update_context(self, agent_name: str, step_id: int, output: Dict):
        """Update context with new agent output"""
        self.context.add_agent_output(agent_name, step_id, output)
        
        # Store context snapshot
        self.context_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "step_id": step_id,
            "iteration": self.context.current_iteration
        })
    
    def should_continue_iteration(self, quality_result: Dict) -> bool:
        """Determine if iteration should continue based on quality results"""
        if self.context.current_iteration >= self.context.max_iterations:
            return False
            
        return quality_result.get("requires_iteration", False)
    
    def prepare_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """Prepare complete context for agent execution"""
        base_context = self.context.get_context_for_agent(agent_name)
        base_context.update({
            "shared_context_manager": {
                "current_iteration": self.context.current_iteration,
                "max_iterations": self.context.max_iterations,
                "iteration_history": self.context.iteration_history,
                "context_updates": len(self.context_history)
            }
        })
        return base_context
    
    def get_context_statistics(self) -> Dict:
        """Get statistics about context usage"""
        total_outputs = sum(
            len(iteration_outputs) 
            for iteration_outputs in self.context.agent_outputs.values()
        )
        
        agent_activity = {}
        for iteration_outputs in self.context.agent_outputs.values():
            for step_data in iteration_outputs.values():
                agent_name = step_data["agent"]
                agent_activity[agent_name] = agent_activity.get(agent_name, 0) + 1
        
        return {
            "total_iterations": self.context.current_iteration,
            "total_agent_outputs": total_outputs,
            "agent_activity": agent_activity,
            "context_updates": len(self.context_history),
            "most_active_agent": max(agent_activity, key=agent_activity.get) if agent_activity else None
        }


@dataclass
class ProjectSharedContext(SharedContext):
    """
    Shared context that incorporates project-specific context
    """
    project_context: Any = None  # BaseProjectContext or compatible
    
    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Return project-specific context for agent"""
        base_context = {
            "user_request": self.user_request,
            "previous_outputs": self.get_relevant_outputs(agent_name),
            "iteration": self.current_iteration,
            "project_type": getattr(self.project_context, 'project_type', 'generic')
        }
        
        # Add project-specific details
        if self.project_context:
            base_context.update({
                "project_name": getattr(self.project_context, 'project_name', 'unknown'),
                "domain_instructions": self.project_context.get_domain_instructions(),
                "quality_gates": self.project_context.get_quality_gates(),
                "project_specifics": self.project_context.get_project_specifics()
            })
        
        return base_context
    
    def get_agent_instruction_summary(self, agent_name: str) -> str:
        """Get project-specific instructions for agent"""
        if not self.project_context:
            return f"""
GENERIC PROJECT CONTEXT:

User Request: {self.user_request}
Iteration: {self.current_iteration + 1}/{self.max_iterations}

Please complete your task according to your role and capabilities.
"""
        
        instructions = f"""
PROJECT CONTEXT:

User Request: {self.user_request}
Iteration: {self.current_iteration + 1}/{self.max_iterations}
Project: {getattr(self.project_context, 'project_name', 'Unknown')}

{self.project_context.get_domain_instructions()}

AGENT-SPECIFIC ENHANCEMENTS:
"""
        
        # Add agent-specific enhancements if available
        if hasattr(self.project_context, 'get_agent_enhancement_instructions'):
            agent_enhancements = self.project_context.get_agent_enhancement_instructions()
            if agent_name in agent_enhancements:
                instructions += agent_enhancements[agent_name]
        
        # Add previous outputs context
        relevant_outputs = self.get_relevant_outputs(agent_name)
        if relevant_outputs:
            instructions += f"""

PREVIOUS AGENT OUTPUTS:
{json.dumps(relevant_outputs, indent=2)}
"""
        
        return instructions