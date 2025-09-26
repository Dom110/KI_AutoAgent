"""
Generic Software Development Workflow
Provides a flexible workflow template for general software development projects
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .base_workflow import BaseWorkflow
from ..shared_context import SharedContext

logger = logging.getLogger(__name__)

class GenericSoftwareWorkflow(BaseWorkflow):
    """
    Generic workflow suitable for most software development projects
    Implements standard software development lifecycle stages
    """
    
    def __init__(self, name: str = "Generic Software Workflow"):
        super().__init__(name)
        self.workflow_steps = [
            "requirements_analysis",
            "architecture_design", 
            "implementation_planning",
            "code_development",
            "testing_validation",
            "documentation_creation",
            "quality_assurance",
            "deployment_preparation"
        ]
    
    def get_workflow_steps(self) -> List[str]:
        """Return the standard software development workflow steps"""
        return self.workflow_steps
    
    def get_step_agents(self, step: str) -> List[str]:
        """Map workflow steps to appropriate agents"""
        step_agent_mapping = {
            "requirements_analysis": ["ArchitectGPT", "ResearchBot"],
            "architecture_design": ["ArchitectGPT"],
            "implementation_planning": ["ArchitectGPT", "CodeSmithClaude"],
            "code_development": ["CodeSmithClaude"],
            "testing_validation": ["CodeSmithClaude", "ReviewerGPT"],
            "documentation_creation": ["DocuBot"],
            "quality_assurance": ["ReviewerGPT"],
            "deployment_preparation": ["ArchitectGPT", "CodeSmithClaude"]
        }
        return step_agent_mapping.get(step, ["CodeSmithClaude"])
    
    def get_step_instructions(self, step: str, context: SharedContext) -> str:
        """Provide specific instructions for each workflow step"""
        
        base_context = f"""
PROJECT CONTEXT: {getattr(context, 'user_request', 'General Software Development')}
CURRENT STEP: {step}
ITERATION: {getattr(context, 'current_iteration', 0) + 1}

"""
        
        step_instructions = {
            "requirements_analysis": """
REQUIREMENTS ANALYSIS PHASE:

Your task is to analyze and clarify the software requirements:

1. FUNCTIONAL REQUIREMENTS:
   - Identify core features and capabilities
   - Define user stories and use cases
   - Specify input/output requirements
   - Determine integration points

2. NON-FUNCTIONAL REQUIREMENTS:
   - Performance requirements
   - Security considerations
   - Scalability needs
   - Usability standards
   - Maintenance requirements

3. DELIVERABLES:
   - Requirements specification document
   - User story breakdown
   - Acceptance criteria
   - Technical constraints list

Focus on clarity, completeness, and testability of requirements.
""",

            "architecture_design": """
ARCHITECTURE DESIGN PHASE:

Design the system architecture and technical approach:

1. SYSTEM ARCHITECTURE:
   - High-level system design
   - Component breakdown
   - Data flow diagrams
   - Integration patterns

2. TECHNICAL DECISIONS:
   - Technology stack selection
   - Framework choices
   - Database design
   - API design patterns

3. DESIGN PATTERNS:
   - Appropriate design patterns
   - Code organization structure
   - Module dependencies
   - Error handling strategy

4. DELIVERABLES:
   - Architecture diagrams
   - Technical specification
   - Technology justification
   - Implementation roadmap

Ensure scalability, maintainability, and adherence to best practices.
""",

            "implementation_planning": """
IMPLEMENTATION PLANNING PHASE:

Create detailed implementation plan:

1. DEVELOPMENT BREAKDOWN:
   - Task decomposition
   - Priority ordering
   - Dependency mapping
   - Time estimation

2. DEVELOPMENT STANDARDS:
   - Coding standards
   - Version control strategy
   - Testing strategy
   - Code review process

3. RISK MITIGATION:
   - Technical risks identification
   - Mitigation strategies
   - Fallback plans
   - Quality checkpoints

4. DELIVERABLES:
   - Implementation plan
   - Development guidelines
   - Risk assessment
   - Milestone definitions

Focus on realistic planning and quality assurance.
""",

            "code_development": """
CODE DEVELOPMENT PHASE:

Implement the software according to specifications:

1. IMPLEMENTATION REQUIREMENTS:
   - Follow architecture design
   - Implement all specified features
   - Adhere to coding standards
   - Include error handling

2. CODE QUALITY:
   - Write clean, readable code
   - Add appropriate comments
   - Follow naming conventions
   - Implement proper logging

3. TESTING INTEGRATION:
   - Unit tests for core functions
   - Integration test preparation
   - Mock external dependencies
   - Test data preparation

4. DELIVERABLES:
   - Complete source code
   - Unit tests
   - Configuration files
   - Build scripts

Prioritize code quality, maintainability, and testability.
""",

            "testing_validation": """
TESTING & VALIDATION PHASE:

Ensure code quality and functionality:

1. TEST EXECUTION:
   - Run unit tests
   - Perform integration testing
   - Execute functional tests
   - Validate edge cases

2. QUALITY VALIDATION:
   - Code review
   - Performance testing
   - Security validation
   - Compatibility testing

3. BUG RESOLUTION:
   - Identify and document issues
   - Prioritize bug fixes
   - Implement corrections
   - Regression testing

4. DELIVERABLES:
   - Test results report
   - Bug tracking log
   - Performance metrics
   - Quality assessment

Ensure comprehensive testing and high code quality.
""",

            "documentation_creation": """
DOCUMENTATION CREATION PHASE:

Create comprehensive project documentation:

1. USER DOCUMENTATION:
   - Installation guide
   - User manual
   - API documentation
   - Configuration guide

2. DEVELOPER DOCUMENTATION:
   - Code documentation
   - Architecture overview
   - Development setup
   - Contributing guidelines

3. OPERATIONAL DOCUMENTATION:
   - Deployment guide
   - Troubleshooting guide
   - Maintenance procedures
   - Monitoring setup

4. DELIVERABLES:
   - README files
   - API documentation
   - User guides
   - Technical documentation

Focus on clarity, completeness, and maintainability.
""",

            "quality_assurance": """
QUALITY ASSURANCE PHASE:

Final quality validation and improvement:

1. CODE REVIEW:
   - Architecture compliance
   - Code quality standards
   - Security best practices
   - Performance optimization

2. FUNCTIONALITY VALIDATION:
   - Feature completeness
   - User experience testing
   - Error handling validation
   - Edge case testing

3. COMPLIANCE CHECK:
   - Coding standards compliance
   - Documentation completeness
   - Test coverage validation
   - Security requirements

4. DELIVERABLES:
   - Quality assessment report
   - Improvement recommendations
   - Compliance checklist
   - Final validation report

Ensure production readiness and quality standards.
""",

            "deployment_preparation": """
DEPLOYMENT PREPARATION PHASE:

Prepare for production deployment:

1. DEPLOYMENT PACKAGE:
   - Build production version
   - Configuration management
   - Dependency packaging
   - Environment setup

2. DEPLOYMENT STRATEGY:
   - Deployment plan
   - Rollback procedures
   - Monitoring setup
   - Health checks

3. OPERATIONAL READINESS:
   - Performance benchmarks
   - Security hardening
   - Backup procedures
   - Maintenance schedules

4. DELIVERABLES:
   - Deployment package
   - Deployment guide
   - Operational runbook
   - Monitoring configuration

Ensure smooth production deployment and operation.
"""
        }
        
        instruction = step_instructions.get(step, f"Execute {step} according to your role and expertise.")
        return base_context + instruction
    
    def validate_step_completion(self, step: str, step_output: Dict[str, Any]) -> bool:
        """Validate that a workflow step has been completed successfully"""
        
        if not step_output or 'content' not in step_output:
            return False
        
        content = step_output['content'].lower()
        
        # Step-specific validation criteria
        validation_criteria = {
            "requirements_analysis": [
                "requirement", "functional", "non-functional", "user story"
            ],
            "architecture_design": [
                "architecture", "design", "component", "pattern"
            ],
            "implementation_planning": [
                "plan", "task", "milestone", "implementation"
            ],
            "code_development": [
                "code", "function", "class", "implementation"
            ],
            "testing_validation": [
                "test", "validation", "quality", "bug"
            ],
            "documentation_creation": [
                "documentation", "guide", "readme", "manual"
            ],
            "quality_assurance": [
                "quality", "review", "compliance", "standard"
            ],
            "deployment_preparation": [
                "deployment", "production", "configuration", "setup"
            ]
        }
        
        criteria = validation_criteria.get(step, [])
        matches = sum(1 for criterion in criteria if criterion in content)
        
        # Require at least 50% of criteria to be mentioned
        return matches >= len(criteria) * 0.5
    
    def get_workflow_description(self) -> str:
        """Describe the generic software workflow"""
        return """
Generic Software Development Workflow

This workflow implements a standard software development lifecycle suitable for most software projects:

1. Requirements Analysis - Gather and analyze project requirements
2. Architecture Design - Design system architecture and technical approach
3. Implementation Planning - Create detailed development plans
4. Code Development - Implement the software solution
5. Testing & Validation - Ensure quality and functionality
6. Documentation Creation - Create comprehensive documentation
7. Quality Assurance - Final quality validation
8. Deployment Preparation - Prepare for production deployment

The workflow is flexible and can be adapted to different project types and methodologies.
Each step includes specific instructions and validation criteria to ensure quality output.
"""

    def get_success_criteria(self) -> Dict[str, List[str]]:
        """Define success criteria for the workflow"""
        return {
            "requirements_analysis": [
                "Clear functional requirements identified",
                "Non-functional requirements specified",
                "User stories documented",
                "Acceptance criteria defined"
            ],
            "architecture_design": [
                "System architecture designed",
                "Technology stack selected",
                "Design patterns chosen",
                "Architecture documented"
            ],
            "implementation_planning": [
                "Implementation plan created",
                "Tasks broken down",
                "Dependencies identified",
                "Quality checkpoints defined"
            ],
            "code_development": [
                "All features implemented",
                "Code follows standards",
                "Unit tests included",
                "Error handling implemented"
            ],
            "testing_validation": [
                "All tests passing",
                "Code quality validated",
                "Performance tested",
                "Security validated"
            ],
            "documentation_creation": [
                "User documentation complete",
                "Developer documentation available",
                "API documentation created",
                "README files updated"
            ],
            "quality_assurance": [
                "Code review completed",
                "Quality standards met",
                "Compliance verified",
                "Production readiness confirmed"
            ],
            "deployment_preparation": [
                "Deployment package ready",
                "Deployment procedures documented",
                "Monitoring configured",
                "Rollback procedures available"
            ]
        }