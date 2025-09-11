"""
Base Project Context for KI_AutoAgent

This module provides the abstract base class for project-specific contexts.
All domain-specific contexts (trading, web apps, APIs, etc.) should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ProjectSpecification:
    """Project specifications and requirements"""
    name: str
    domain: str
    programming_languages: List[str]
    frameworks: List[str]
    architecture_patterns: List[str]
    special_requirements: List[str]
    compliance_standards: List[str]


class BaseProjectContext(ABC):
    """
    Abstract base class for project-specific contexts.
    
    Each domain (trading, web apps, APIs, etc.) should create a concrete
    implementation that provides domain-specific instructions, quality gates,
    and project specifications.
    """
    
    def __init__(self, project_name: Optional[str] = None):
        self.project_name = project_name or "Unknown Project"
    
    @abstractmethod
    def get_domain_instructions(self) -> str:
        """
        Return domain-specific instructions for agents.
        
        This should include:
        - Domain knowledge and terminology
        - Best practices for the domain
        - Common patterns and architectures
        - Specific requirements and constraints
        
        Returns:
            str: Formatted instructions for agents
        """
        pass
    
    @abstractmethod
    def get_quality_gates(self) -> List[str]:
        """
        Return list of quality gate class names for this domain.
        
        Quality gates are domain-specific validation classes that check
        code quality, compliance, and domain-specific requirements.
        
        Returns:
            List[str]: List of quality gate class names to apply
        """
        pass
    
    @abstractmethod
    def get_project_specifics(self) -> ProjectSpecification:
        """
        Return project-specific details and requirements.
        
        Returns:
            ProjectSpecification: Detailed project specifications
        """
        pass
    
    def get_agent_enhancement_instructions(self) -> Dict[str, str]:
        """
        Return agent-specific enhancements for this domain.
        
        Override this method to provide specialized instructions for
        specific agents (e.g., enhanced research patterns for trading).
        
        Returns:
            Dict[str, str]: Agent name -> additional instructions
        """
        return {}
    
    def get_iteration_limits(self) -> Dict[str, int]:
        """
        Return domain-specific iteration limits.
        
        Some domains may need different iteration limits due to complexity.
        
        Returns:
            Dict[str, int]: Limit configurations
        """
        return {
            "max_iterations": 10,
            "complexity_boost_threshold": 7,  # Add more iterations for complex projects
            "quality_gate_failures_limit": 3
        }
    
    def get_conflict_resolution_priorities(self) -> Dict[str, int]:
        """
        Return agent priority order for conflict resolution.
        
        Higher number = higher priority when agents disagree.
        
        Returns:
            Dict[str, int]: Agent name -> priority level
        """
        return {
            "claude": 100,  # Claude always wins conflicts
            "architect": 90,
            "reviewer": 80,
            "codesmith": 70,
            "research": 60,
            "docubot": 50,
            "fixer": 40
        }
    
    def validate_context(self) -> bool:
        """
        Validate that this context is properly configured.
        
        Returns:
            bool: True if context is valid
        """
        try:
            instructions = self.get_domain_instructions()
            quality_gates = self.get_quality_gates()
            specs = self.get_project_specifics()
            
            if not instructions or len(instructions.strip()) == 0:
                return False
            if not isinstance(quality_gates, list):
                return False
            if not specs or not specs.name:
                return False
                
            return True
        except Exception:
            return False