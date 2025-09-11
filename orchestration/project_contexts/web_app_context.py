"""
Web Application Project Context for KI_AutoAgent

This module provides web application-specific context for building REST APIs, 
web services, and full-stack applications.
"""

from typing import Dict, List, Any
from .base_project_context import BaseProjectContext, ProjectSpecification
import json

# Web Application Development Guidelines
WEB_APP_GUIDELINES = {
    "project_type": "web_application",
    "development_principles": {
        "security_first": "Security by design, not as afterthought",
        "scalability": "Design for horizontal and vertical scaling",
        "performance": "Optimize for speed and efficiency",
        "maintainability": "Clean, readable, documented code",
        "testing": "Comprehensive test coverage (unit, integration, e2e)"
    },
    
    "architecture_patterns": {
        "api_design": "RESTful API design with proper HTTP methods",
        "data_layer": "Repository pattern with ORM abstraction",
        "authentication": "JWT tokens with refresh mechanism",
        "authorization": "Role-based access control (RBAC)",
        "caching": "Redis for session and application caching",
        "logging": "Structured logging with correlation IDs"
    },
    
    "security_requirements": {
        "input_validation": "Validate and sanitize all user inputs",
        "sql_injection": "Use parameterized queries, ORM protection",
        "xss_protection": "Escape outputs, CSP headers",
        "csrf_protection": "CSRF tokens for state-changing operations",
        "https_only": "TLS encryption for all communications",
        "rate_limiting": "API rate limiting and DDoS protection",
        "secrets_management": "Environment variables, never in code"
    },
    
    "performance_standards": {
        "response_times": {
            "api_endpoints": "< 200ms average response time",
            "database_queries": "< 100ms for simple queries",
            "page_loads": "< 2s initial page load",
            "static_assets": "CDN delivery, gzip compression"
        },
        "scalability": {
            "concurrent_users": "Handle 1000+ concurrent users",
            "database_connections": "Connection pooling",
            "caching_strategy": "Multi-level caching (browser, CDN, application)",
            "horizontal_scaling": "Stateless application design"
        }
    },
    
    "code_quality_standards": {
        "code_style": "Follow language-specific style guides (PEP8, Prettier)",
        "documentation": "Comprehensive API documentation (OpenAPI/Swagger)",
        "error_handling": "Consistent error responses with proper HTTP codes",
        "logging": "Structured logs with appropriate levels",
        "testing": "Minimum 80% code coverage",
        "dependencies": "Regular security audits of dependencies"
    }
}

# Technology Stack Recommendations
TECH_STACK_OPTIONS = {
    "backend_frameworks": {
        "python": ["FastAPI", "Django", "Flask"],
        "javascript": ["Express.js", "NestJS", "Koa"],
        "java": ["Spring Boot", "Quarkus"],
        "go": ["Gin", "Echo", "Fiber"],
        "rust": ["Axum", "Actix-web", "Warp"]
    },
    
    "databases": {
        "relational": ["PostgreSQL", "MySQL", "SQLite"],
        "document": ["MongoDB", "CouchDB"],
        "cache": ["Redis", "Memcached"],
        "search": ["Elasticsearch", "Solr"]
    },
    
    "frontend_frameworks": {
        "react": ["Next.js", "Vite + React", "Create React App"],
        "vue": ["Nuxt.js", "Vue CLI", "Vite + Vue"],
        "angular": ["Angular CLI"],
        "svelte": ["SvelteKit", "Vite + Svelte"]
    },
    
    "deployment": {
        "containers": ["Docker", "Podman"],
        "orchestration": ["Kubernetes", "Docker Compose"],
        "cloud_platforms": ["AWS", "Google Cloud", "Azure", "DigitalOcean"],
        "ci_cd": ["GitHub Actions", "GitLab CI", "Jenkins"]
    }
}


class WebAppProjectContext(BaseProjectContext):
    """Web application-specific project context"""
    
    def __init__(self, project_name: str = "web_application"):
        super().__init__(project_name)
    
    def get_domain_instructions(self) -> str:
        """Return web application-specific instructions for agents"""
        return f"""
WEB APPLICATION DEVELOPMENT INSTRUCTIONS:

PROJECT: {self.project_name}

1. WEB DEVELOPMENT GUIDELINES:
{json.dumps(WEB_APP_GUIDELINES, indent=2)}

2. RECOMMENDED TECHNOLOGY STACKS:
{json.dumps(TECH_STACK_OPTIONS, indent=2)}

CRITICAL IMPLEMENTATION RULES:
- SECURITY FIRST: Implement authentication, authorization, input validation
- API DESIGN: RESTful endpoints with proper HTTP methods and status codes
- DATABASE: Use parameterized queries, connection pooling, migrations
- PERFORMANCE: Implement caching, optimize queries, compress responses
- TESTING: Unit tests, integration tests, API tests
- DOCUMENTATION: OpenAPI/Swagger documentation for APIs
- MONITORING: Structured logging, health checks, metrics
- DEPLOYMENT: Containerized applications with CI/CD pipelines

SECURITY CHECKLIST:
- Input validation and sanitization
- SQL injection prevention
- XSS protection with CSP headers
- CSRF token implementation
- HTTPS/TLS encryption
- Rate limiting and DDoS protection
- Secure session management
- Environment-based configuration

AGENT-SPECIFIC ENHANCEMENTS:
{json.dumps(self.get_agent_enhancement_instructions(), indent=2)}
"""
    
    def get_quality_gates(self) -> List[str]:
        """Return web app-specific quality gate class names"""
        return [
            "SecurityQualityGate",
            "PerformanceQualityGate",
            "APIQualityGate",
            "DatabaseQualityGate",
            "TestCoverageQualityGate"
        ]
    
    def get_project_specifics(self) -> ProjectSpecification:
        """Return web application project specifications"""
        return ProjectSpecification(
            name=self.project_name,
            domain="Web Application Development",
            programming_languages=["Python", "JavaScript", "TypeScript"],
            frameworks=[
                "FastAPI", "Django", "Flask",  # Backend
                "React", "Vue.js", "Angular",  # Frontend
                "PostgreSQL", "Redis",         # Databases
                "Docker", "Kubernetes"         # Deployment
            ],
            architecture_patterns=[
                "RESTful API Design",
                "MVC/MVP Architecture",
                "Repository Pattern",
                "JWT Authentication",
                "Role-Based Access Control",
                "Multi-layer Caching",
                "Microservices Architecture"
            ],
            special_requirements=[
                "OWASP Top 10 compliance",
                "GDPR data protection",
                "API rate limiting",
                "Horizontal scaling capability",
                "Real-time features (WebSockets)",
                "Mobile-responsive design",
                "SEO optimization",
                "Accessibility (WCAG 2.1)"
            ],
            compliance_standards=[
                "OWASP Security Guidelines",
                "REST API Best Practices",
                "Web Content Accessibility Guidelines",
                "GDPR Data Protection",
                "ISO 27001 Security Standards"
            ]
        )
    
    def get_agent_enhancement_instructions(self) -> Dict[str, str]:
        """Return agent-specific enhancements for web development"""
        return {
            "ResearchBot": """
WEB DEVELOPMENT RESEARCH FOCUS:
- Latest web framework documentation and best practices
- Security vulnerability research (OWASP Top 10)
- Performance optimization techniques
- API design patterns and standards
- Database optimization and indexing strategies
- Frontend accessibility and UX patterns
- Cloud deployment and scaling strategies
- Testing frameworks and methodologies
""",
            
            "ArchitectGPT": """
WEB ARCHITECTURE FOCUS:
- Design scalable API architecture (REST/GraphQL)
- Plan database schema with proper normalization
- Design authentication and authorization systems
- Plan caching strategies (Redis, CDN, browser)
- Design microservices architecture if needed
- Plan deployment and CI/CD pipelines
- Design monitoring and logging systems
- Plan security architecture and threat mitigation
""",
            
            "CodeSmithClaude": """
WEB IMPLEMENTATION FOCUS:
- Implement secure authentication and authorization
- Create RESTful APIs with proper error handling
- Implement database models with relationships
- Add comprehensive input validation
- Implement caching layers (application, database)
- Create responsive frontend components
- Add structured logging and monitoring
- Implement automated testing (unit, integration)
""",
            
            "ReviewerGPT": """
WEB REVIEW FOCUS:
- Security review (SQL injection, XSS, CSRF)
- API design review (REST principles, error handling)
- Database review (queries, indexing, migrations)
- Performance review (N+1 queries, caching)
- Code quality review (patterns, maintainability)
- Test coverage review (unit, integration, e2e)
- Documentation review (API docs, README)
- Accessibility review (WCAG compliance)
""",
            
            "FixerBot": """
WEB FIXES FOCUS:
- Fix security vulnerabilities without breaking functionality
- Optimize performance bottlenecks
- Fix API endpoint issues and error handling
- Resolve database query problems
- Fix frontend responsive design issues
- Resolve authentication and authorization bugs
- Fix deployment and configuration issues
""",
            
            "TradeStrat": """
WEB STRATEGY FOCUS:
- Plan user authentication flows
- Design API endpoint strategies
- Plan database migration strategies
- Design caching and performance strategies
- Plan testing and quality assurance strategies
- Design deployment and scaling strategies
""",
            
            "DocuBot": """
WEB DOCUMENTATION FOCUS:
- Create comprehensive API documentation (OpenAPI/Swagger)
- Document database schema and relationships
- Create deployment and setup guides
- Document security measures and best practices
- Create user guides and API examples
- Document testing procedures and coverage
"""
        }
    
    def get_iteration_limits(self) -> Dict[str, int]:
        """Web apps may need standard iteration limits"""
        return {
            "max_iterations": 10,
            "complexity_boost_threshold": 7,
            "quality_gate_failures_limit": 3
        }