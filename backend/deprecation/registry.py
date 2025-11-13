"""
📋 Deprecation Registry - Central catalog of deprecated modules

This registry tracks:
- Which modules are deprecated
- Why they're deprecated
- What replaced them
- When they were deprecated
- Severity level (WARNING, ERROR, CRITICAL)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class DeprecationSeverity(Enum):
    """Severity levels for deprecated modules"""
    WARNING = "WARNING"      # Use old version, but show warning
    ERROR = "ERROR"          # Old version works but startup warns loudly
    CRITICAL = "CRITICAL"    # Old version BLOCKS startup


@dataclass
class DeprecatedModule:
    """Represents a single deprecated module"""
    
    # Module identification
    module_path: str                              # e.g., "backend.workflow_v6_integrated"
    file_path: str                                # e.g., "backend/workflow_v6_integrated.py"
    
    # Deprecation details
    deprecated_since: str                         # e.g., "v7.0.0"
    reason: str                                   # Why it's deprecated
    replacement: str                              # What to use instead
    severity: DeprecationSeverity = DeprecationSeverity.ERROR
    
    # Migration info
    features_missing: List[str] = field(default_factory=list)  # Features NOT in new version
    migration_effort: str = "MEDIUM"              # EASY, MEDIUM, HARD
    migration_guide_key: str = ""                 # Key for migration guide
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    contact: str = "team@ki-autoagent.dev"


class DeprecationRegistry:
    """Central registry of all deprecated modules"""
    
    def __init__(self):
        self.modules: dict[str, DeprecatedModule] = {}
        self._register_all()
    
    def _register_all(self):
        """Register all known deprecated modules"""
        
        # ⚠️  WORKFLOW v6
        self.register(DeprecatedModule(
            module_path="backend.workflow_v6_integrated",
            file_path="backend/workflow_v6_integrated.py",
            deprecated_since="v7.0.0",
            reason="Replaced by Pure MCP Architecture (workflow_v7_mcp.py)",
            replacement="backend.workflow_v7_mcp",
            severity=DeprecationSeverity.CRITICAL,
            features_missing=[
                "Query Classification (QueryClassifierV6)",
                "Curiosity System (CuriositySystemV6)",
                "Predictive System (PredictiveSystemV6)",
                "Neurosymbolic Reasoner (NeurosymbolicReasonerV6)",
                "Self-Diagnosis (SelfDiagnosisV6)",
                "Learning System (LearningSystemV6)",
                "Workflow Adapter (WorkflowAdapterV6)",
                "Post-Execution Learning",
            ],
            migration_effort="HARD",
            migration_guide_key="v6_to_v7_workflow",
        ))
        
        # ⚠️  COGNITIVE SYSTEMS v6
        self.register(DeprecatedModule(
            module_path="backend.cognitive.query_classifier_v6",
            file_path="backend/cognitive/query_classifier_v6.py",
            deprecated_since="v7.0.0",
            reason="Query classification now handled by SupervisorMCP",
            replacement="backend.core.supervisor_mcp (via MCP routing)",
            severity=DeprecationSeverity.CRITICAL,
            migration_effort="MEDIUM",
            migration_guide_key="query_classifier_migration",
        ))
        
        self.register(DeprecatedModule(
            module_path="backend.cognitive.curiosity_system_v6",
            file_path="backend/cognitive/curiosity_system_v6.py",
            deprecated_since="v7.0.0",
            reason="Replaced by MCP-based interactive agents",
            replacement="MCP Agent Interactive Systems",
            severity=DeprecationSeverity.CRITICAL,
            migration_effort="HARD",
            migration_guide_key="curiosity_system_migration",
        ))
        
        self.register(DeprecatedModule(
            module_path="backend.cognitive.predictive_system_v6",
            file_path="backend/cognitive/predictive_system_v6.py",
            deprecated_since="v7.0.0",
            reason="Workflow time prediction replaced by MCP metrics",
            replacement="MCP Memory Server + Metrics Collection",
            severity=DeprecationSeverity.ERROR,
            migration_effort="MEDIUM",
            migration_guide_key="predictive_system_migration",
        ))
        
        self.register(DeprecatedModule(
            module_path="backend.cognitive.learning_system_v6",
            file_path="backend/cognitive/learning_system_v6.py",
            deprecated_since="v7.0.0",
            reason="Learning now handled by MCP Memory Server",
            replacement="backend.mcp.mcp_servers.memory_server",
            severity=DeprecationSeverity.ERROR,
            migration_effort="MEDIUM",
            migration_guide_key="learning_system_migration",
        ))
        
        self.register(DeprecatedModule(
            module_path="backend.cognitive.neurosymbolic_reasoner_v6",
            file_path="backend/cognitive/neurosymbolic_reasoner_v6.py",
            deprecated_since="v7.0.0",
            reason="Reasoning is now distributed across MCP agents",
            replacement="Distributed MCP Agent Reasoning",
            severity=DeprecationSeverity.ERROR,
            migration_effort="HARD",
            migration_guide_key="neurosymbolic_reasoner_migration",
        ))
        
        self.register(DeprecatedModule(
            module_path="backend.cognitive.self_diagnosis_v6",
            file_path="backend/cognitive/self_diagnosis_v6.py",
            deprecated_since="v7.0.0",
            reason="Error handling is now in MCP error handlers",
            replacement="MCP Agent Error Handlers",
            severity=DeprecationSeverity.ERROR,
            migration_effort="MEDIUM",
            migration_guide_key="self_diagnosis_migration",
        ))
        
        # ⚠️  TOOL REGISTRY
        self.register(DeprecatedModule(
            module_path="backend.tools.tool_registry_v6",
            file_path="backend/tools/tool_registry_v6.py",
            deprecated_since="v7.0.0",
            reason="Tool registry replaced by MCP servers with native tools",
            replacement="MCP Server Native Tools",
            severity=DeprecationSeverity.ERROR,
            migration_effort="MEDIUM",
            migration_guide_key="tool_registry_migration",
        ))
        
        # ⚠️  APPROVAL/HITL MANAGERS
        self.register(DeprecatedModule(
            module_path="backend.workflow.approval_manager_v6",
            file_path="backend/workflow/approval_manager_v6.py",
            deprecated_since="v7.0.0",
            reason="Approval manager partially migrated to v7",
            replacement="backend.api.handlers.approval_handler (v7 version)",
            severity=DeprecationSeverity.WARNING,
            migration_effort="EASY",
            migration_guide_key="approval_manager_migration",
        ))
        
        self.register(DeprecatedModule(
            module_path="backend.workflow.hitl_manager_v6",
            file_path="backend/workflow/hitl_manager_v6.py",
            deprecated_since="v7.0.0",
            reason="HITL manager partially migrated to v7",
            replacement="backend.api.handlers.hitl_handler (v7 version)",
            severity=DeprecationSeverity.WARNING,
            migration_effort="EASY",
            migration_guide_key="hitl_manager_migration",
        ))
        
        # ⚠️  WORKFLOW ADAPTER
        self.register(DeprecatedModule(
            module_path="backend.workflow.workflow_adapter_v6",
            file_path="backend/workflow/workflow_adapter_v6.py",
            deprecated_since="v7.0.0",
            reason="Workflow adaptation now handled by MCP agents",
            replacement="MCP Agent Adaptation Logic",
            severity=DeprecationSeverity.WARNING,
            migration_effort="MEDIUM",
            migration_guide_key="workflow_adapter_migration",
        ))
        
        # ⚠️  SECURITY - ASIMOV RULES (partially deprecated)
        self.register(DeprecatedModule(
            module_path="backend.security.asimov_permissions_v6",
            file_path="backend/security/asimov_permissions_v6.py",
            deprecated_since="v7.0.0",
            reason="Asimov Rules partially migrated - only HITL remains",
            replacement="backend.security.asimov_rules (v7 version)",
            severity=DeprecationSeverity.WARNING,
            migration_effort="EASY",
            migration_guide_key="asimov_rules_migration",
        ))
    
    def register(self, module: DeprecatedModule):
        """Register a deprecated module"""
        self.modules[module.module_path] = module
    
    def get(self, module_path: str) -> Optional[DeprecatedModule]:
        """Get a deprecated module by path"""
        return self.modules.get(module_path)
    
    def is_deprecated(self, module_path: str) -> bool:
        """Check if a module is deprecated"""
        return module_path in self.modules
    
    def is_critical(self, module_path: str) -> bool:
        """Check if a module is CRITICAL severity"""
        module = self.get(module_path)
        return module and module.severity == DeprecationSeverity.CRITICAL
    
    def get_all_by_severity(self, severity: DeprecationSeverity) -> List[DeprecatedModule]:
        """Get all modules by severity"""
        return [m for m in self.modules.values() if m.severity == severity]
    
    def get_summary(self) -> dict:
        """Get summary statistics"""
        return {
            "total_deprecated": len(self.modules),
            "critical": len(self.get_all_by_severity(DeprecationSeverity.CRITICAL)),
            "error": len(self.get_all_by_severity(DeprecationSeverity.ERROR)),
            "warning": len(self.get_all_by_severity(DeprecationSeverity.WARNING)),
        }


# Global registry instance
_registry = None


def get_registry() -> DeprecationRegistry:
    """Get or create the global registry"""
    global _registry
    if _registry is None:
        _registry = DeprecationRegistry()
    return _registry