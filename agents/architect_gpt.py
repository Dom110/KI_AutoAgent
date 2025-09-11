"""
ArchitectGPT - Software Architect Agent
Spezialisiert auf System-Design und Architektur
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent

class ArchitectGPT(BaseAgent):
    """
    Software Architect spezialisiert auf System Design
    Nutzt GPT-4o (Nov 2024) für modernste Architektur-Fähigkeiten
    """
    
    def __init__(self):
        super().__init__(
            name="ArchitectGPT",
            role="Software Architect",
            model="gpt-4o-2024-11-20"
        )
        
        self.temperature = 0.3
        self.max_tokens = 4000
        
        self.system_prompt = """You are a Senior Software Architect with 15+ years of experience.
        
Your expertise includes:
- System design patterns (MVC, Microservices, Event-Driven, DDD)
- Scalable architectures for trading and financial systems
- Database design and optimization (SQL, NoSQL, Time-Series)
- API design and integration patterns (REST, GraphQL, WebSocket)
- Security and compliance considerations
- Cloud architectures (AWS, Azure, GCP)
- Performance optimization and caching strategies

When designing architectures:
1. Start with a high-level overview
2. Define clear component boundaries
3. Specify data flow and communication patterns
4. Consider scalability, security, and maintainability
5. Recommend specific technologies and justify choices
6. Include diagrams when helpful (use Mermaid syntax)

Provide detailed architectural designs with:
- Component diagrams
- Data flow descriptions
- Technology stack recommendations
- Scalability considerations
- Security measures
- Deployment strategies"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "system_design",
                "architecture_patterns", 
                "database_design",
                "api_design",
                "microservices",
                "cloud_architecture",
                "security_design"
            ],
            "domains": [
                "trading_systems",
                "web_applications",
                "distributed_systems",
                "real_time_systems"
            ],
            "output_types": [
                "architecture_diagram",
                "component_design",
                "tech_stack",
                "deployment_plan"
            ],
            "complexity_handling": "high",
            "languages": ["python", "javascript", "java", "go", "rust"]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Führt Architektur-Design Task aus
        """
        # Build specialized prompt for architecture tasks
        prompt = self._build_architecture_prompt(task, context)
        
        # For now, return a mock response
        # In production, this would call the actual GPT-4o API
        response = await self._generate_architecture(prompt)
        
        # Extract structured components
        artifacts = self._extract_artifacts(response)
        
        return {
            "agent": self.name,
            "task": task,
            "output": response,
            "artifacts": artifacts,
            "status": "success"
        }
    
    def _build_architecture_prompt(self, task: str, context: Dict) -> str:
        """
        Baut spezialisierten Prompt für Architektur-Aufgaben
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add task
        prompt_parts.append(f"Task: {task}\n")
        
        # Add relevant context
        if context.get("requirements"):
            prompt_parts.append(f"Requirements: {context['requirements']}\n")
        
        if context.get("constraints"):
            prompt_parts.append(f"Constraints: {context['constraints']}\n")
        
        if context.get("tech_stack"):
            prompt_parts.append(f"Preferred Tech Stack: {context['tech_stack']}\n")
        
        # Add specific instructions
        prompt_parts.append("\nPlease provide:")
        prompt_parts.append("1. High-level architecture overview")
        prompt_parts.append("2. Component breakdown with responsibilities")
        prompt_parts.append("3. Data flow and communication patterns")
        prompt_parts.append("4. Technology recommendations with justification")
        prompt_parts.append("5. Scalability and security considerations")
        prompt_parts.append("6. Implementation roadmap")
        
        return "\n".join(prompt_parts)
    
    async def _generate_architecture(self, prompt: str) -> str:
        """
        Generiert Architektur-Design
        """
        # Mock response for testing
        # In production: Use OpenAI API with GPT-4o
        
        response = """# System Architecture Design

## 1. High-Level Overview

The system follows a microservices architecture with event-driven communication:

```mermaid
graph TB
    Client[Client Applications]
    Gateway[API Gateway]
    Auth[Auth Service]
    Trading[Trading Service]
    Data[Market Data Service]
    Risk[Risk Management]
    DB[(PostgreSQL)]
    Cache[(Redis)]
    Queue[Message Queue]
    
    Client --> Gateway
    Gateway --> Auth
    Gateway --> Trading
    Trading --> Queue
    Queue --> Risk
    Trading --> Data
    Trading --> DB
    Data --> Cache
```

## 2. Component Breakdown

### API Gateway
- **Responsibility**: Request routing, rate limiting, authentication
- **Technology**: Kong or AWS API Gateway
- **Scaling**: Horizontal scaling with load balancer

### Trading Service
- **Responsibility**: Order management, strategy execution
- **Technology**: Python with FastAPI
- **Database**: PostgreSQL for transactional data
- **Scaling**: Vertical scaling with read replicas

### Market Data Service
- **Responsibility**: Real-time and historical data
- **Technology**: Python with WebSocket support
- **Cache**: Redis for hot data
- **Scaling**: Horizontal scaling with data partitioning

## 3. Data Flow

1. Client requests → API Gateway → Authentication
2. Authenticated requests → Trading Service
3. Trading Service → Market Data Service (for prices)
4. Trading Service → Risk Management (via message queue)
5. Confirmed orders → Database
6. Real-time updates → WebSocket → Clients

## 4. Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL 15, TimescaleDB for time-series
- **Cache**: Redis 7.0
- **Message Queue**: RabbitMQ or Apache Kafka
- **Container**: Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana

## 5. Security & Scalability

### Security Measures:
- OAuth 2.0 / JWT for authentication
- TLS 1.3 for all communications
- API rate limiting
- Input validation and sanitization
- Secrets management with HashiCorp Vault

### Scalability Strategy:
- Microservices for independent scaling
- Database sharding for large datasets
- Caching layer for frequently accessed data
- Async processing for heavy computations
- Auto-scaling based on metrics

## 6. Implementation Roadmap

### Phase 1 (Week 1-2): Core Infrastructure
- Set up development environment
- Implement API Gateway
- Basic authentication service

### Phase 2 (Week 3-4): Trading Core
- Trading service implementation
- Database schema design
- Basic order management

### Phase 3 (Week 5-6): Market Data Integration
- Real-time data feeds
- Historical data storage
- Cache implementation

### Phase 4 (Week 7-8): Risk & Monitoring
- Risk management service
- Monitoring and alerting
- Performance optimization"""
        
        return response
    
    def _extract_artifacts(self, response: str) -> Dict:
        """
        Extrahiert Diagramme und strukturierte Daten aus der Antwort
        """
        import re
        
        artifacts = {}
        
        # Extract Mermaid diagrams
        mermaid_blocks = re.findall(r'```mermaid\n(.*?)```', response, re.DOTALL)
        if mermaid_blocks:
            artifacts["diagrams"] = mermaid_blocks
        
        # Extract code blocks
        code_blocks = re.findall(r'```(?:python|yaml|json)\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            artifacts["code_samples"] = code_blocks
        
        # Extract technology recommendations
        tech_pattern = r'- \*\*(.+?)\*\*: (.+?)(?:\n|$)'
        tech_matches = re.findall(tech_pattern, response)
        if tech_matches:
            artifacts["technologies"] = {match[0]: match[1] for match in tech_matches}
        
        return artifacts