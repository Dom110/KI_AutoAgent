"""
Base Component Analyzer - Framework-agnostic interface

All framework-specific analyzers inherit from this class and provide
a unified output structure (UniversalAppStructure) regardless of framework.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ComponentType(str, Enum):
    """Component types"""
    PAGE = "page"
    COMPONENT = "component"
    SERVICE = "service"
    UTILITY = "utility"


@dataclass
class Property:
    """Component property/prop"""
    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None


@dataclass
class StateVariable:
    """State variable"""
    name: str
    type: str
    initial_value: Optional[Any] = None
    description: Optional[str] = None


@dataclass
class EventHandler:
    """Event handler"""
    name: str
    event_type: str  # 'onClick', 'onChange', 'onSubmit', etc.
    action: str  # Description of what it does
    triggers: List[str] = field(default_factory=list)  # Related state/props


@dataclass
class APICall:
    """API call within component"""
    endpoint: str
    method: str  # 'GET', 'POST', 'PUT', 'DELETE'
    description: Optional[str] = None
    params: List[str] = field(default_factory=list)
    response_type: Optional[str] = None
    error_handling: bool = False


@dataclass
class Component:
    """Unified component structure"""
    name: str
    file_path: str
    type: ComponentType
    language: str  # 'typescript', 'javascript', 'python'
    
    # Component structure
    properties: List[Property] = field(default_factory=list)
    state_variables: List[StateVariable] = field(default_factory=list)
    event_handlers: List[EventHandler] = field(default_factory=list)
    api_calls: List[APICall] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Testing
    test_ids: List[str] = field(default_factory=list)
    form_fields: List[str] = field(default_factory=list)
    conditional_renders: List[str] = field(default_factory=list)
    
    # Metadata
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class Route:
    """Application route"""
    path: str
    component: str
    method: Optional[str] = None  # For API routes
    protected: bool = False
    parameters: List[str] = field(default_factory=list)


@dataclass
class Service:
    """Service/utility module"""
    name: str
    file_path: str
    methods: List[str] = field(default_factory=list)
    purpose: Optional[str] = None


@dataclass
class UniversalAppStructure:
    """Universal app structure - framework-agnostic representation"""
    
    framework: str  # 'react', 'vue', 'angular', 'fastapi', etc.
    language: str  # 'javascript', 'typescript', 'python'
    app_type: str  # 'frontend', 'backend', 'fullstack'
    
    components: List[Component] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    
    # Additional metadata
    entry_point: Optional[str] = None
    build_command: Optional[str] = None
    test_command: Optional[str] = None
    description: Optional[str] = None


class BaseComponentAnalyzer(ABC):
    """
    Abstract base class for all framework-specific component analyzers
    
    Each framework adapter (React, Vue, Angular, FastAPI, etc.) must implement
    this interface and return a unified UniversalAppStructure.
    """

    def __init__(self, app_path: str):
        """
        Initialize analyzer
        
        Args:
            app_path: Path to application root
        """
        self.app_path = app_path

    @abstractmethod
    def analyze_app(self) -> UniversalAppStructure:
        """
        Analyze application and return unified structure
        
        Must be implemented by each framework adapter
        
        Returns:
            UniversalAppStructure with app analysis
        """
        pass

    @abstractmethod
    def extract_components(self) -> List[Component]:
        """Extract components from app"""
        pass

    @abstractmethod
    def extract_routes(self) -> List[Route]:
        """Extract routes from app"""
        pass

    @abstractmethod
    def extract_services(self) -> List[Service]:
        """Extract services/utilities from app"""
        pass

    @abstractmethod
    def extract_api_calls(self) -> List[APICall]:
        """Extract API calls from components"""
        pass

    def identify_test_scenarios(self) -> Dict[str, List[str]]:
        """
        Identify test scenarios based on app structure
        
        Returns: {
            'happy_path': [...],
            'error_cases': [...],
            'edge_cases': [...],
            'integration': [...]
        }
        """
        # This could be framework-specific if needed
        return {
            'happy_path': [],
            'error_cases': [],
            'edge_cases': [],
            'integration': []
        }