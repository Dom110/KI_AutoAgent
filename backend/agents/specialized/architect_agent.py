"""
ArchitectAgent - System design and architecture specialist
Uses GPT-5 for architectural decisions and technology selection
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.openai_service import OpenAIService

logger = logging.getLogger(__name__)

@dataclass
class ArchitectureDesign:
    """Architecture design specification"""
    project_name: str
    architecture_type: str  # monolithic, microservices, serverless, etc.
    components: List[Dict[str, Any]]
    technologies: List[str]
    patterns: List[str]
    data_flow: Dict[str, Any]
    deployment: Dict[str, Any]
    scalability_notes: str
    security_considerations: str

class ArchitectAgent(ChatAgent):
    """
    Architecture and System Design Specialist
    - System architecture design
    - Technology selection
    - Design patterns recommendation
    - Scalability planning
    - Security architecture
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="architect",
            name="ArchitectAgent",
            full_name="System Architecture Specialist",
            description="Expert in system design, architecture patterns, and technology selection",
            model="gpt-5-2025-09-12",
            capabilities=[
                AgentCapability.ARCHITECTURE_DESIGN
            ],
            temperature=0.7,
            max_tokens=4000,
            icon="🏗️"
        )
        super().__init__(config)

        # Initialize OpenAI service
        self.openai = OpenAIService()

        # Architecture patterns library
        self.architecture_patterns = self._load_architecture_patterns()

        # Technology stack recommendations
        self.tech_stacks = self._load_tech_stacks()

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute architecture design task
        """
        start_time = datetime.now()

        try:
            # Analyze project requirements
            requirements = await self.analyze_requirements(request.prompt)

            # Design architecture
            design = await self.design_architecture(requirements)

            # Generate architecture documentation
            documentation = await self.generate_documentation(design)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                status="success",
                content=documentation,
                agent=self.config.agent_id,
                metadata={
                    "architecture_type": design.architecture_type,
                    "component_count": len(design.components),
                    "technologies": design.technologies,
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Architecture design failed: {e}")
            return TaskResult(
                status="error",
                content=f"Failed to design architecture: {str(e)}",
                agent=self.config.agent_id
            )

    async def analyze_requirements(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze project requirements from prompt
        """
        system_prompt = """
        You are a senior system architect.
        Analyze the project requirements and identify:
        1. Project type (web app, API, mobile, desktop, etc.)
        2. Scale requirements (users, requests, data volume)
        3. Performance requirements (latency, throughput)
        4. Security requirements
        5. Integration needs
        6. Special constraints

        Provide structured analysis.
        """

        analysis_prompt = f"""
        Project Description:
        {prompt}

        Analyze and provide requirements in JSON format:
        {{
            "project_type": "type",
            "scale": {{"users": "estimated", "requests_per_second": "estimated"}},
            "performance": {{"latency": "requirement", "throughput": "requirement"}},
            "security": ["requirement1", "requirement2"],
            "integrations": ["system1", "system2"],
            "constraints": ["constraint1", "constraint2"],
            "key_features": ["feature1", "feature2"]
        }}
        """

        response = await self.openai.complete(analysis_prompt, system_prompt)

        try:
            return json.loads(response)
        except:
            # Fallback to basic analysis
            return {
                "project_type": "web application",
                "scale": {"users": "medium", "requests_per_second": "1000"},
                "performance": {"latency": "< 200ms", "throughput": "high"},
                "security": ["authentication", "authorization"],
                "integrations": [],
                "constraints": [],
                "key_features": self._extract_features(prompt)
            }

    async def design_architecture(
        self,
        requirements: Dict[str, Any]
    ) -> ArchitectureDesign:
        """
        Design system architecture based on requirements
        """
        system_prompt = """
        You are an expert system architect.
        Design a comprehensive system architecture that:
        1. Meets all requirements
        2. Follows best practices
        3. Is scalable and maintainable
        4. Uses modern, proven technologies
        5. Considers security from the start

        Be specific and practical.
        """

        design_prompt = f"""
        Requirements:
        {json.dumps(requirements, indent=2)}

        Design a complete system architecture including:
        1. Architecture type (monolithic, microservices, serverless, etc.)
        2. Main components and their responsibilities
        3. Technology stack (languages, frameworks, databases, etc.)
        4. Design patterns to use
        5. Data flow between components
        6. Deployment architecture
        7. Scalability strategy
        8. Security measures

        Provide detailed, actionable architecture design.
        """

        response = await self.openai.complete(design_prompt, system_prompt)

        # Parse response into ArchitectureDesign
        return self._parse_architecture_response(response, requirements)

    def _parse_architecture_response(
        self,
        response: str,
        requirements: Dict[str, Any]
    ) -> ArchitectureDesign:
        """
        Parse architecture response into structured design
        """
        # Extract key information from response
        # This is a simplified parser - could be enhanced with better NLP

        architecture_type = "microservices"  # Default
        if "monolithic" in response.lower():
            architecture_type = "monolithic"
        elif "serverless" in response.lower():
            architecture_type = "serverless"

        # Extract components (simplified)
        components = []
        if "frontend" in response.lower():
            components.append({
                "name": "Frontend",
                "type": "UI",
                "technology": "React/Next.js",
                "responsibility": "User interface"
            })

        if "backend" in response.lower() or "api" in response.lower():
            components.append({
                "name": "Backend API",
                "type": "API",
                "technology": "Python/FastAPI",
                "responsibility": "Business logic and data management"
            })

        if "database" in response.lower():
            components.append({
                "name": "Database",
                "type": "Storage",
                "technology": "PostgreSQL",
                "responsibility": "Data persistence"
            })

        # Extract technologies
        technologies = []
        tech_keywords = ["python", "javascript", "typescript", "react", "fastapi",
                        "postgresql", "redis", "docker", "kubernetes", "aws", "azure"]

        for tech in tech_keywords:
            if tech in response.lower():
                technologies.append(tech.capitalize())

        # Design patterns
        patterns = []
        pattern_keywords = ["mvc", "mvvm", "repository", "factory", "singleton",
                           "observer", "strategy", "decorator", "cqrs", "event sourcing"]

        for pattern in pattern_keywords:
            if pattern in response.lower():
                patterns.append(pattern.upper())

        return ArchitectureDesign(
            project_name=requirements.get("project_type", "System"),
            architecture_type=architecture_type,
            components=components,
            technologies=technologies,
            patterns=patterns,
            data_flow={"type": "REST API", "protocol": "HTTPS"},
            deployment={"platform": "Cloud", "containerization": "Docker"},
            scalability_notes="Horizontal scaling with load balancer",
            security_considerations="OAuth2, HTTPS, rate limiting, input validation"
        )

    async def generate_documentation(self, design: ArchitectureDesign) -> str:
        """
        Generate architecture documentation
        """
        doc = []
        doc.append(f"# 🏗️ System Architecture Design\n")
        doc.append(f"## Project: {design.project_name}\n")
        doc.append(f"**Architecture Type**: {design.architecture_type}\n")

        doc.append("\n## 📦 Components\n")
        for component in design.components:
            doc.append(f"### {component['name']}")
            doc.append(f"- **Type**: {component['type']}")
            doc.append(f"- **Technology**: {component['technology']}")
            doc.append(f"- **Responsibility**: {component['responsibility']}\n")

        doc.append("\n## 🛠️ Technology Stack\n")
        for tech in design.technologies:
            doc.append(f"- {tech}")

        doc.append("\n## 📐 Design Patterns\n")
        for pattern in design.patterns:
            doc.append(f"- {pattern}")

        doc.append("\n## 🔄 Data Flow\n")
        doc.append(f"- **Type**: {design.data_flow.get('type', 'N/A')}")
        doc.append(f"- **Protocol**: {design.data_flow.get('protocol', 'N/A')}\n")

        doc.append("\n## 🚀 Deployment\n")
        doc.append(f"- **Platform**: {design.deployment.get('platform', 'N/A')}")
        doc.append(f"- **Containerization**: {design.deployment.get('containerization', 'N/A')}\n")

        doc.append("\n## 📈 Scalability\n")
        doc.append(design.scalability_notes + "\n")

        doc.append("\n## 🔒 Security Considerations\n")
        doc.append(design.security_considerations + "\n")

        doc.append("\n---\n")
        doc.append("*Generated by ArchitectAgent (GPT-5)*")

        return "\n".join(doc)

    def _extract_features(self, prompt: str) -> List[str]:
        """
        Extract key features from prompt
        """
        features = []

        feature_keywords = [
            "authentication", "authorization", "api", "database",
            "real-time", "messaging", "payment", "search",
            "analytics", "reporting", "dashboard", "admin"
        ]

        prompt_lower = prompt.lower()
        for keyword in feature_keywords:
            if keyword in prompt_lower:
                features.append(keyword)

        return features[:5]  # Return top 5 features

    def _load_architecture_patterns(self) -> List[Dict[str, Any]]:
        """
        Load architecture patterns library
        """
        return [
            {
                "name": "Microservices",
                "when_to_use": "Large, complex applications with multiple teams",
                "pros": ["Independent deployment", "Technology diversity", "Fault isolation"],
                "cons": ["Complexity", "Network latency", "Data consistency"]
            },
            {
                "name": "Monolithic",
                "when_to_use": "Simple applications, MVPs, small teams",
                "pros": ["Simple deployment", "Easy debugging", "Low latency"],
                "cons": ["Scaling challenges", "Technology lock-in", "Team coordination"]
            },
            {
                "name": "Serverless",
                "when_to_use": "Event-driven, variable load, rapid development",
                "pros": ["No infrastructure management", "Auto-scaling", "Cost-effective"],
                "cons": ["Vendor lock-in", "Cold starts", "Debugging challenges"]
            }
        ]

    def _load_tech_stacks(self) -> Dict[str, List[str]]:
        """
        Load technology stack recommendations
        """
        return {
            "web": ["React", "Next.js", "FastAPI", "PostgreSQL", "Redis"],
            "mobile": ["React Native", "Flutter", "Firebase", "GraphQL"],
            "api": ["FastAPI", "Node.js", "Go", "PostgreSQL", "MongoDB"],
            "data": ["Python", "Apache Spark", "Kafka", "Elasticsearch"],
            "ml": ["Python", "TensorFlow", "PyTorch", "MLflow", "Kubeflow"]
        }
    async def _process_agent_request(self, message) -> Any:
        """
        Process request from another agent
        Implementation of abstract method from BaseAgent
        """
        # Handle architecture requests from other agents
        if message.content.get("requesting_architecture"):
            task = message.content.get("task", "")
            result = await self.execute(TaskRequest(prompt=task))
            return {"architecture_result": result.content}

        return {"message": "Architect received request"}
