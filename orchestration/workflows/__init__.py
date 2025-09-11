"""
Workflow Templates Package

This package contains workflow templates for different types of software projects.
Each workflow defines the sequence of steps, agent assignments, and validation
criteria for completing projects of a specific domain.

Available Workflows:
- GenericSoftwareWorkflow: Standard software development lifecycle
- TradingSystemWorkflow: Specialized workflow for financial trading systems

Usage:
    from orchestration.workflows import GenericSoftwareWorkflow, TradingSystemWorkflow
    
    # Create a generic workflow
    workflow = GenericSoftwareWorkflow()
    steps = workflow.get_workflow_steps()
    
    # Create a trading-specific workflow
    trading_workflow = TradingSystemWorkflow()
    agents = trading_workflow.get_step_agents("strategy_design")
"""

from .base_workflow import BaseWorkflow
from .generic_software_workflow import GenericSoftwareWorkflow
from .trading_system_workflow import TradingSystemWorkflow

__all__ = [
    'BaseWorkflow',
    'GenericSoftwareWorkflow', 
    'TradingSystemWorkflow'
]

# Workflow registry for dynamic loading
WORKFLOW_REGISTRY = {
    'generic': GenericSoftwareWorkflow,
    'software': GenericSoftwareWorkflow,
    'trading': TradingSystemWorkflow,
    'financial': TradingSystemWorkflow,
    'stock_analyser': TradingSystemWorkflow
}

def get_workflow_for_project_type(project_type: str) -> BaseWorkflow:
    """
    Get appropriate workflow for a project type
    
    Args:
        project_type: The type of project (generic, trading, etc.)
        
    Returns:
        Workflow instance appropriate for the project type
        
    Raises:
        ValueError: If project type is not supported
    """
    workflow_class = WORKFLOW_REGISTRY.get(project_type.lower())
    if not workflow_class:
        # Default to generic workflow for unknown types
        workflow_class = GenericSoftwareWorkflow
    
    return workflow_class()

def get_available_workflows() -> dict:
    """
    Get information about all available workflows
    
    Returns:
        Dictionary mapping workflow names to their descriptions
    """
    workflows = {}
    for name, workflow_class in WORKFLOW_REGISTRY.items():
        instance = workflow_class()
        workflows[name] = {
            'class': workflow_class.__name__,
            'description': instance.get_workflow_description(),
            'steps': instance.get_workflow_steps(),
            'step_count': len(instance.get_workflow_steps())
        }
    return workflows