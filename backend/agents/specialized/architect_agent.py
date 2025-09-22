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

# Setup logger first
logger = logging.getLogger(__name__)

# Import new analysis and visualization tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import new analysis tools with graceful fallback
try:
    from core.indexing.tree_sitter_indexer import TreeSitterIndexer
    from core.indexing.code_indexer import CodeIndexer
    INDEXING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Code indexing modules not available: {e}")
    INDEXING_AVAILABLE = False
    TreeSitterIndexer = None
    CodeIndexer = None

try:
    from core.analysis.semgrep_analyzer import SemgrepAnalyzer
    from core.analysis.vulture_analyzer import VultureAnalyzer
    from core.analysis.radon_metrics import RadonMetrics
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Analysis modules not available: {e}")
    ANALYSIS_AVAILABLE = False
    SemgrepAnalyzer = None
    VultureAnalyzer = None
    RadonMetrics = None

try:
    from services.diagram_service import DiagramService
    DIAGRAM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Diagram service not available: {e}")
    DIAGRAM_AVAILABLE = False
    DiagramService = None

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

        # Initialize code analysis tools if available
        if INDEXING_AVAILABLE:
            self.tree_sitter = TreeSitterIndexer()
            self.code_indexer = CodeIndexer()
        else:
            self.tree_sitter = None
            self.code_indexer = None
            logger.warning("Code indexing tools not available - some features will be limited")

        if ANALYSIS_AVAILABLE:
            self.semgrep = SemgrepAnalyzer()
            self.vulture = VultureAnalyzer()
            self.metrics = RadonMetrics()
        else:
            self.semgrep = None
            self.vulture = None
            self.metrics = None
            logger.warning("Analysis tools not available - some features will be limited")

        if DIAGRAM_AVAILABLE:
            self.diagram_service = DiagramService()
        else:
            self.diagram_service = None
            logger.warning("Diagram service not available - visualization features disabled")

        # System knowledge cache
        self.system_knowledge = None
        self.last_index_time = None

        # Architecture patterns library
        self.architecture_patterns = self._load_architecture_patterns()

        # Technology stack recommendations
        self.tech_stacks = self._load_tech_stacks()

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute architecture design task - ENHANCED to use v4.0.0 tools and create files
        """
        start_time = datetime.now()
        files_created = []

        # Get client_id for progress updates
        client_id = request.context.get('client_id')

        try:
            # Get workspace path
            workspace_path = request.context.get('workspace_path', os.getcwd())
            ki_autoagent_dir = os.path.join(workspace_path, '.ki_autoagent')
            os.makedirs(ki_autoagent_dir, exist_ok=True)

            # Send initial progress
            await self._send_progress(client_id, "🏗️ Architect starting system analysis...")

            # Determine which tools to use based on the request
            prompt_lower = request.prompt.lower()

            # Tool 1: understand_system() - Always use for infrastructure tasks
            if any(word in prompt_lower for word in ['understand', 'analyze', 'infrastructure', 'improve', 'optimize']):
                logger.info("🔍 Using understand_system() to analyze workspace...")
                await self._send_progress(client_id, "🔍 Using understand_system() to analyze workspace...")

                if INDEXING_AVAILABLE and self.code_indexer:
                    system_analysis = await self.understand_system(workspace_path, client_id, request.prompt)

                    # Save to file
                    analysis_file = os.path.join(ki_autoagent_dir, 'system_analysis.json')
                    with open(analysis_file, 'w') as f:
                        json.dump(system_analysis, f, indent=2)
                    files_created.append(analysis_file)
                    logger.info(f"✅ Created: {analysis_file}")
                else:
                    # Fallback analysis
                    system_analysis = await self.analyze_requirements(request.prompt)

                # Tool 2: analyze_infrastructure_improvements()
                if 'improve' in prompt_lower or 'optimization' in prompt_lower:
                    logger.info("🔧 Using analyze_infrastructure_improvements()...")

                    if ANALYSIS_AVAILABLE:
                        improvements = await self.analyze_infrastructure_improvements()

                        # Format improvements as markdown
                        improvements_md = "# Infrastructure Improvements\n\n"
                        for imp in improvements:
                            improvements_md += f"## {imp['title']} ({imp['priority']})\n"
                            improvements_md += f"**Problem:** {imp['problem']}\n"
                            improvements_md += f"**Solution:** {imp.get('solution', 'See code example')}\n"
                            if 'code' in imp:
                                improvements_md += f"```python\n{imp['code']}\n```\n"
                            improvements_md += f"**Impact:** {imp.get('impact', 'Performance improvement')}\n\n"

                        # Save improvements
                        improvements_file = os.path.join(ki_autoagent_dir, 'improvements.md')
                        with open(improvements_file, 'w') as f:
                            f.write(improvements_md)
                        files_created.append(improvements_file)
                        logger.info(f"✅ Created: {improvements_file}")
                    else:
                        improvements_md = "Analysis tools not available. Install with: pip install semgrep radon vulture"

                # Tool 3: generate_architecture_flowchart()
                if 'diagram' in prompt_lower or 'flowchart' in prompt_lower or 'visualize' in prompt_lower:
                    logger.info("📊 Using generate_architecture_flowchart()...")

                    if DIAGRAM_AVAILABLE:
                        diagram = await self.generate_architecture_flowchart()

                        # Save diagram
                        diagram_file = os.path.join(ki_autoagent_dir, 'architecture.mermaid')
                        with open(diagram_file, 'w') as f:
                            f.write(diagram)
                        files_created.append(diagram_file)
                        logger.info(f"✅ Created: {diagram_file}")
                    else:
                        diagram = "graph TB\n  A[System] --> B[Not Available]\n  B --> C[Install mermaid-py]"

                # Create summary
                summary = f"Actively analyzed system and created {len(files_created)} files:\n"
                for file in files_created:
                    summary += f"- {os.path.basename(file)}\n"

                if not files_created:
                    # Fallback to old behavior if no specific tools triggered
                    requirements = await self.analyze_requirements(request.prompt)
                    design = await self.design_architecture(requirements)
                    documentation = await self.generate_documentation(design)
                    summary = documentation
                else:
                    summary += f"\nAll files saved in: {ki_autoagent_dir}"

            else:
                # Standard architecture design (not infrastructure)
                requirements = await self.analyze_requirements(request.prompt)
                design = await self.design_architecture(requirements)
                documentation = await self.generate_documentation(design)
                summary = documentation

            execution_time = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                status="success",
                content=summary,
                agent=self.config.agent_id,
                metadata={
                    "files_created": files_created,
                    "tools_used": ["understand_system", "analyze_infrastructure_improvements", "generate_architecture_flowchart"] if files_created else [],
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

    async def understand_system(self, root_path: str = '.', client_id: str = None, request_prompt: str = '') -> Dict[str, Any]:
        """
        Build comprehensive understanding of the system through code analysis

        This method performs deep analysis using:
        - Tree-sitter AST indexing
        - Semantic code analysis
        - Metrics calculation
        - Architecture extraction
        """
        if not INDEXING_AVAILABLE:
            logger.warning("Code indexing not available - returning limited analysis")
            return {
                'error': 'Code analysis tools not installed',
                'message': 'Please install requirements: pip install -r backend/requirements.txt'
            }

        logger.info("Building comprehensive system understanding...")
        await self._send_progress(client_id, "🏗️ Building comprehensive system understanding...")

        # Detect request type for smart analysis
        request_type = self._detect_request_type(request_prompt)
        logger.info(f"Request type detected: {request_type}")

        # Phase 1: Complete code indexing
        logger.info("Phase 1: Indexing codebase with AST parsing")
        await self._send_progress(client_id, "📂 Phase 1: Indexing codebase with AST parsing...")

        # Create progress callback
        async def progress_callback(msg: str):
            await self._send_progress(client_id, msg)

        code_index = await self.code_indexer.build_full_index(root_path, progress_callback, request_type)

        # Phase 2: Security and quality analysis
        logger.info("Phase 2: Running security and quality analysis")
        await self._send_progress(client_id, "🔒 Phase 2: Running security and quality analysis...")
        security_analysis = await self.semgrep.run_analysis(root_path)
        dead_code = await self.vulture.find_dead_code(root_path)
        metrics = await self.metrics.calculate_all_metrics(root_path)

        # Phase 3: Generate visualizations
        logger.info("Phase 3: Generating architecture diagrams")
        await self._send_progress(client_id, "📊 Phase 3: Generating architecture diagrams...")
        diagrams = {
            'system_context': await self.diagram_service.generate_architecture_diagram(code_index, 'context'),
            'container': await self.diagram_service.generate_architecture_diagram(code_index, 'container'),
            'component': await self.diagram_service.generate_architecture_diagram(code_index, 'component'),
            'dependency_graph': await self.diagram_service.generate_dependency_graph(
                code_index.get('import_graph', {})
            ),
            'sequence': await self.diagram_service.generate_sequence_diagram({}),
            'state': await self.diagram_service.generate_state_diagram({})
        }

        # Store system knowledge
        self.system_knowledge = {
            'code_index': code_index,
            'security': security_analysis,
            'dead_code': dead_code,
            'metrics': metrics,
            'diagrams': diagrams,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"System understanding complete: {len(code_index.get('ast', {}).get('files', {}))} files analyzed")
        return self.system_knowledge

    async def analyze_infrastructure_improvements(self) -> str:
        """
        Analyze codebase and suggest infrastructure improvements

        This is the main method to answer: "Was kann an der Infrastruktur verbessert werden?"
        """
        if not self.system_knowledge:
            await self.understand_system('.', None, 'infrastructure improvements')

        # Extract insights from analysis
        code_index = self.system_knowledge['code_index']
        security = self.system_knowledge['security']
        metrics = self.system_knowledge['metrics']
        dead_code = self.system_knowledge['dead_code']

        # Build comprehensive response
        response = []
        response.append("## 🔍 System-Analyse Report\n")

        # Statistics
        stats = code_index.get('statistics', {})
        response.append(f"### 📊 Code-Index Status")
        response.append(f"- **{stats.get('total_files', 0)}** Files vollständig indiziert")
        response.append(f"- **{stats.get('total_functions', 0)}** Functions analysiert")
        response.append(f"- **{stats.get('total_classes', 0)}** Classes dokumentiert")
        response.append(f"- **{stats.get('total_api_endpoints', 0)}** API Endpoints gefunden")
        response.append(f"- **{stats.get('lines_of_code', 0)}** Lines of Code\n")

        # Architecture Overview (with Mermaid diagram)
        response.append("### 🏗️ Architecture Overview")
        response.append("```mermaid")
        response.append(self.system_knowledge['diagrams']['container'])
        response.append("```\n")

        # Security Analysis
        security_summary = security.get('summary', {})
        if security_summary:
            response.append("### 🔒 Security Analysis")
            if security_summary.get('critical', 0) > 0:
                response.append(f"- ⛔ **{security_summary['critical']} Critical** issues found")
            if security_summary.get('high', 0) > 0:
                response.append(f"- 🔴 **{security_summary['high']} High** risk vulnerabilities")
            if security_summary.get('medium', 0) > 0:
                response.append(f"- 🟡 **{security_summary['medium']} Medium** risk issues")
            response.append("")

        # Performance Metrics
        metrics_summary = metrics.get('summary', {})
        response.append("### 📈 Performance Metrics")
        response.append(f"- **Average Complexity**: {metrics_summary.get('average_complexity', 0):.1f}")
        response.append(f"- **Maintainability Index**: {metrics_summary.get('average_maintainability', 0):.1f}")
        response.append(f"- **Quality Score**: {metrics_summary.get('quality_score', 0):.1f}/100")

        # Dead Code
        dead_code_summary = dead_code.get('summary', {})
        if dead_code_summary.get('total_dead_code', 0) > 0:
            response.append(f"\n### 🧹 Dead Code: **{dead_code_summary['total_dead_code']}** unused items found\n")

        # Concrete Improvements
        response.append("### 🚀 Konkrete Verbesserungen (Priorisiert)\n")

        improvements = await self._generate_improvement_suggestions()
        for i, improvement in enumerate(improvements, 1):
            response.append(f"#### {i}. {improvement['title']} [{improvement['priority']}]")
            response.append(f"**Problem**: {improvement['problem']}")
            response.append(f"**Lösung**: {improvement['solution']}")
            if 'code' in improvement:
                response.append(f"```python\n{improvement['code']}\n```")
            response.append(f"**Impact**: {improvement['impact']}\n")

        # Dependency Graph
        response.append("### 📊 Dependency Graph")
        response.append("```mermaid")
        response.append(self.system_knowledge['diagrams']['dependency_graph'])
        response.append("```\n")

        return "\n".join(response)

    async def _generate_improvement_suggestions(self) -> List[Dict[str, str]]:
        """
        Generate specific improvement suggestions based on analysis
        """
        improvements = []

        # Check for missing caching
        code_index = self.system_knowledge['code_index']
        has_redis = await self._check_for_technology("redis")
        has_cache = await self._check_for_technology("cache")

        if not has_redis and not has_cache:
            improvements.append({
                'title': 'Add Redis Caching',
                'priority': 'QUICK WIN',
                'problem': 'No caching layer detected - all API responses computed fresh',
                'solution': 'Implement Redis for session and response caching',
                'code': '''# backend/utils/cache_service.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_response(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Compute and cache
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator''',
                'impact': '70% reduction in API response time, 60% less AI API calls'
            })

        # Check for connection pooling
        has_pool = await self._check_for_technology("pool")
        if not has_pool:
            improvements.append({
                'title': 'Connection Pooling',
                'priority': 'QUICK WIN',
                'problem': 'Creating new HTTP connections for each API call',
                'solution': 'Use connection pooling for API clients',
                'code': '''# backend/utils/http_pool.py
import httpx

# Singleton connection pool
class ConnectionPool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                )
            )
        return cls._instance

pool = ConnectionPool()''',
                'impact': '40% faster external API calls, reduced latency'
            })

        # Check for async issues
        patterns = self.system_knowledge['code_index'].get('patterns', {})
        perf_issues = patterns.get('performance_issues', [])

        for issue in perf_issues:
            if 'sync_in_async' in str(issue):
                improvements.append({
                    'title': 'Fix Sync Operations in Async Functions',
                    'priority': 'MEDIUM',
                    'problem': f"Blocking operations in async context: {issue.get('file', 'multiple files')}",
                    'solution': 'Replace with async alternatives',
                    'impact': 'Better concurrency and responsiveness'
                })
                break

        # Check complexity
        metrics = self.system_knowledge['metrics']
        if metrics.get('summary', {}).get('average_complexity', 0) > 10:
            improvements.append({
                'title': 'Reduce Code Complexity',
                'priority': 'MEDIUM',
                'problem': f"High average complexity: {metrics['summary']['average_complexity']:.1f}",
                'solution': 'Refactor complex functions, extract methods',
                'impact': 'Better maintainability and fewer bugs'
            })

        # Add database optimization if no indexes found
        has_indexes = await self._check_for_technology("index")
        has_postgres = await self._check_for_technology("postgres")

        if has_postgres and not has_indexes:
            improvements.append({
                'title': 'Add Database Indexes',
                'priority': 'QUICK WIN',
                'problem': 'No database indexes detected for queries',
                'solution': 'Add indexes for frequently queried columns',
                'impact': '10-100x faster database queries'
            })

        return improvements[:5]  # Return top 5 improvements

    async def _check_for_technology(self, tech: str) -> bool:
        """
        Check if a technology is used in the codebase
        """
        if not self.system_knowledge:
            return False

        # Search in code index
        results = await self.code_indexer.tree_sitter.search_pattern(tech)
        return len(results) > 0

    async def generate_architecture_flowchart(self) -> str:
        """
        Generate a detailed architecture flowchart of the current system
        """
        if not self.system_knowledge:
            await self.understand_system('.', None, 'architecture flowchart')

        # Generate comprehensive flowchart
        flowchart = await self.diagram_service.generate_architecture_diagram(
            self.system_knowledge['code_index'],
            'component'
        )

        return f"## System Architecture Flowchart\n\n```mermaid\n{flowchart}\n```"

    def _detect_request_type(self, prompt: str) -> str:
        """Detect the type of request from the prompt"""
        prompt_lower = prompt.lower()

        # Check for specific request types
        if any(word in prompt_lower for word in ['infrastructure', 'infra', 'caching', 'redis', 'database', 'scale']):
            return 'infrastructure'
        elif any(word in prompt_lower for word in ['architecture', 'design', 'pattern', 'structure']):
            return 'architecture'
        elif any(word in prompt_lower for word in ['refactor', 'restructure', 'reorganize']):
            return 'refactor'
        elif any(word in prompt_lower for word in ['optimize', 'performance', 'speed', 'faster']):
            return 'optimize'
        elif any(word in prompt_lower for word in ['dead code', 'unused', 'cleanup']):
            return 'dead_code'
        elif any(word in prompt_lower for word in ['security', 'vulnerability', 'exploit']):
            return 'security'
        elif any(word in prompt_lower for word in ['dependency', 'dependencies', 'imports', 'requires']):
            return 'dependencies'
        elif any(word in prompt_lower for word in ['impact', 'affect', 'change', 'modify']):
            return 'impact_analysis'
        else:
            return 'general'

    async def _send_progress(self, client_id: str, message: str):
        """Send progress update to WebSocket client"""
        if not client_id:
            return

        try:
            # Import here to avoid circular imports
            from api.server import manager

            if manager and client_id in manager.active_connections:
                await manager.send_json(client_id, {
                    "type": "agent_progress",
                    "agent": "architect",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.debug(f"Could not send progress update: {e}")
