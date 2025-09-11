"""
ResearchBot - Research and Information Gathering Agent
Nutzt Perplexity Pro für umfassende Recherchen
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class ResearchBot(BaseAgent):
    """
    Research Expert mit Perplexity Pro
    Sammelt und analysiert Informationen aus dem Internet
    """
    
    def __init__(self):
        super().__init__(
            name="ResearchBot",
            role="Research Specialist",
            model="perplexity-pro"  # Using Perplexity's most advanced model
        )
        
        self.temperature = 0.2  # Lower for factual accuracy
        self.max_tokens = 4000
        
        self.system_prompt = """You are ResearchBot, an expert research specialist with access to real-time internet data.

Your expertise includes:
- Technical research and documentation analysis
- Market research and competitive analysis  
- Academic paper synthesis
- Technology stack evaluation
- Library and framework comparisons
- Best practices and industry standards
- Security vulnerability research
- Performance benchmarking data

Research approach:
1. Identify authoritative sources
2. Cross-reference multiple sources
3. Verify facts and data
4. Synthesize findings clearly
5. Provide citations and references
6. Highlight conflicting information
7. Note information gaps

Types of research:
- Technical documentation
- API specifications
- Framework comparisons
- Security advisories
- Performance benchmarks
- Industry trends
- Academic papers
- Patent searches

Always provide:
- Verified, up-to-date information
- Multiple perspectives when relevant
- Source citations
- Confidence levels for findings
- Recommendations based on research"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "skills": [
                "web_research",
                "documentation_analysis",
                "market_research",
                "competitive_analysis",
                "technical_evaluation",
                "academic_research",
                "fact_checking"
            ],
            "research_types": [
                "technical_documentation",
                "api_research",
                "framework_comparison",
                "security_research",
                "performance_analysis",
                "market_trends",
                "best_practices"
            ],
            "sources": [
                "official_docs",
                "github",
                "stackoverflow",
                "academic_papers",
                "tech_blogs",
                "security_advisories",
                "benchmarks"
            ],
            "special_features": [
                "real_time_data",
                "source_verification",
                "multi_source_synthesis",
                "citation_generation"
            ]
        }
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """
        Führt Recherche durch und liefert fundierte Informationen
        """
        # Analyze research needs
        research_plan = self._create_research_plan(task, context)
        
        # Build research prompt
        prompt = self._build_research_prompt(task, context, research_plan)
        
        # Conduct research
        research_results = await self._conduct_research(prompt, context)
        
        # Synthesize findings
        synthesis = self._synthesize_findings(research_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(synthesis)
        
        return {
            "agent": self.name,
            "task": task,
            "output": research_results,
            "research_plan": research_plan,
            "synthesis": synthesis,
            "recommendations": recommendations,
            "sources_count": len(synthesis.get("sources", [])),
            "confidence": synthesis.get("confidence", "medium"),
            "status": "success"
        }
    
    def _create_research_plan(self, task: str, context: Dict) -> Dict:
        """
        Erstellt einen Recherche-Plan
        """
        plan = {
            "research_type": "general",
            "priority_sources": [],
            "search_queries": [],
            "depth": "comprehensive",
            "time_relevance": "recent"  # Focus on recent information
        }
        
        task_lower = task.lower()
        
        # Determine research type
        if "api" in task_lower or "documentation" in task_lower:
            plan["research_type"] = "technical_documentation"
            plan["priority_sources"] = ["official_docs", "github"]
        elif "security" in task_lower or "vulnerability" in task_lower:
            plan["research_type"] = "security"
            plan["priority_sources"] = ["cve_database", "security_advisories"]
        elif "performance" in task_lower or "benchmark" in task_lower:
            plan["research_type"] = "performance"
            plan["priority_sources"] = ["benchmarks", "tech_blogs"]
        elif "compare" in task_lower or "vs" in task_lower:
            plan["research_type"] = "comparison"
            plan["priority_sources"] = ["comparisons", "reviews"]
        elif "best practice" in task_lower or "standard" in task_lower:
            plan["research_type"] = "best_practices"
            plan["priority_sources"] = ["official_guides", "industry_standards"]
        
        # Extract specific technologies/topics
        if context.get("technologies"):
            for tech in context["technologies"]:
                plan["search_queries"].append(f"{tech} documentation")
                plan["search_queries"].append(f"{tech} best practices")
        
        # Set research depth
        if context.get("depth"):
            plan["depth"] = context["depth"]
        
        return plan
    
    def _build_research_prompt(self, task: str, context: Dict, research_plan: Dict) -> str:
        """
        Baut spezialisierten Prompt für Recherche
        """
        prompt_parts = [self.system_prompt, "\n"]
        
        # Add research task
        prompt_parts.append(f"Research Task: {task}\n")
        
        # Add research plan details
        prompt_parts.append(f"Research Type: {research_plan['research_type']}")
        prompt_parts.append(f"Depth: {research_plan['depth']}")
        prompt_parts.append(f"Time Relevance: {research_plan['time_relevance']}\n")
        
        # Add priority sources
        if research_plan["priority_sources"]:
            prompt_parts.append(f"Priority Sources: {', '.join(research_plan['priority_sources'])}\n")
        
        # Add specific queries
        if research_plan["search_queries"]:
            prompt_parts.append("Specific queries to research:")
            for query in research_plan["search_queries"]:
                prompt_parts.append(f"  - {query}")
            prompt_parts.append("")
        
        # Add context
        if context.get("requirements"):
            prompt_parts.append(f"Requirements: {context['requirements']}\n")
        
        if context.get("constraints"):
            prompt_parts.append(f"Constraints: {context['constraints']}\n")
        
        # Specific instructions
        prompt_parts.append("\nPlease provide:")
        prompt_parts.append("1. Comprehensive research findings")
        prompt_parts.append("2. Multiple authoritative sources")
        prompt_parts.append("3. Verification of critical information")
        prompt_parts.append("4. Pros and cons where applicable")
        prompt_parts.append("5. Current best practices")
        prompt_parts.append("6. Relevant examples and case studies")
        prompt_parts.append("7. Clear citations for all sources")
        
        return "\n".join(prompt_parts)
    
    async def _conduct_research(self, prompt: str, context: Dict) -> str:
        """
        Führt die eigentliche Recherche durch
        """
        # Mock implementation for testing
        # In production, this would use Perplexity API
        research = '''# Research Report: Modern Python Web Framework Comparison

## Executive Summary

Based on comprehensive research of current documentation, benchmarks, and community feedback (as of January 2025), here's an analysis of the top Python web frameworks for building scalable APIs and web applications.

## Research Findings

### 1. FastAPI

**Overview:**
FastAPI has emerged as the leading modern Python web framework, especially for API development. Built on Starlette and Pydantic, it offers exceptional performance and developer experience.

**Key Findings:**
- **Performance**: Benchmarks show FastAPI handling 50,000+ requests/second [1]
- **Adoption**: 71.5k GitHub stars, used by Microsoft, Netflix, Uber [2]
- **Type Safety**: Native Python type hints with automatic validation
- **Documentation**: Auto-generated OpenAPI/Swagger docs

**Pros:**
- Fastest Python framework for APIs (on par with NodeJS/Go)
- Excellent async/await support
- Automatic data validation and serialization
- Built-in OAuth2, JWT support
- WebSocket support

**Cons:**
- Relatively new (less mature ecosystem)
- Smaller community compared to Django/Flask
- Limited built-in features for full-stack apps

**Best For:** Microservices, APIs, real-time applications

### 2. Django

**Overview:**
Django remains the most comprehensive "batteries-included" framework, ideal for rapid development of full-featured web applications.

**Key Findings:**
- **Market Share**: Powers 82,000+ websites including Instagram, Mozilla [3]
- **Performance**: 10,000-15,000 req/sec with optimizations [4]
- **Ecosystem**: Largest plugin ecosystem with 4,000+ packages
- **Security**: Built-in protection against OWASP Top 10

**Pros:**
- Comprehensive ORM with migrations
- Built-in admin interface
- Authentication system included
- Extensive middleware support
- Battle-tested in production

**Cons:**
- Monolithic architecture
- Steeper learning curve
- Slower than modern async frameworks
- Opinionated structure

**Best For:** CMS, e-commerce, enterprise applications

### 3. Flask

**Overview:**
Flask continues to be popular for its simplicity and flexibility, making it ideal for small to medium projects.

**Key Findings:**
- **Popularity**: 65k GitHub stars, 2nd most used Python framework [5]
- **Performance**: 8,000-12,000 req/sec [6]
- **Flexibility**: Minimal core with extensive extensions

**Pros:**
- Simple and easy to learn
- Highly flexible architecture
- Large community and resources
- Extensive documentation
- Great for prototyping

**Cons:**
- Requires many decisions and configurations
- No built-in ORM or admin
- Limited async support
- Can become complex for large apps

**Best For:** Prototypes, small APIs, educational projects

### 4. Emerging Frameworks

**Litestar (formerly Starlite):**
- Performance: 60,000+ req/sec [7]
- Features: Type-driven, built on Pydantic
- Status: Rapidly growing, production-ready

**Quart:**
- Performance: 40,000+ req/sec
- Features: Async Flask-compatible API
- Status: Good Flask migration path

## Performance Benchmarks

Based on TechEmpower Round 21 benchmarks [8]:

```
JSON Serialization (req/sec):
1. Litestar:     62,305
2. FastAPI:      51,492  
3. Sanic:        45,831
4. Quart:        38,442
5. Flask:        11,231
6. Django:        9,826

Database Queries (req/sec):
1. FastAPI:      28,142
2. Litestar:     26,831
3. Django:       12,421
4. Flask:         8,932
```

## Security Considerations

**Built-in Security Features Comparison:**

| Framework | CSRF | XSS | SQL Injection | Auth | Rate Limiting |
|-----------|------|-----|---------------|------|---------------|
| Django    | ✓    | ✓   | ✓ (ORM)      | ✓    | ✓ (middleware) |
| FastAPI   | Ø    | ✓   | ✓ (Pydantic) | ✓    | Ø (external)   |
| Flask     | Ø    | ✓   | Ø             | Ø    | Ø (external)   |
| Litestar  | ✓    | ✓   | ✓             | ✓    | ✓             |

## Community and Ecosystem

**GitHub Statistics (Jan 2025):**
- Django: 76k stars, 30k forks, 2.3k contributors
- Flask: 65k stars, 16k forks, 700 contributors  
- FastAPI: 71k stars, 6k forks, 500 contributors
- Litestar: 4.5k stars, 300 forks, 150 contributors

**Package Ecosystem:**
- Django: 4,000+ packages
- Flask: 1,500+ extensions
- FastAPI: 500+ packages
- Litestar: 50+ plugins

## Recommendations by Use Case

### For APIs and Microservices:
**Primary: FastAPI**
- Best performance for APIs
- Excellent developer experience
- Native async support
- Auto-documentation

**Alternative: Litestar**
- Even better performance
- Similar features to FastAPI
- Growing ecosystem

### For Full-Stack Web Applications:
**Primary: Django**
- Most comprehensive features
- Battle-tested in production
- Extensive ecosystem
- Built-in admin and ORM

### For Prototypes and Small Projects:
**Primary: Flask**
- Simple and flexible
- Quick to start
- Extensive learning resources
- Easy deployment

### For Real-time Applications:
**Primary: FastAPI + WebSockets**
- Native WebSocket support
- High performance
- Async architecture

**Alternative: Quart**
- Flask-like API with async
- Good WebSocket support

## Migration Paths

**Flask to FastAPI:**
- Gradual migration possible
- Similar routing concepts
- Need to adopt type hints
- Async conversion required

**Django to FastAPI:**
- Best for API extraction
- Keep Django for admin/ORM
- Use FastAPI for new APIs
- Hybrid architecture works well

## Future Trends

1. **Type-Driven Development**: Frameworks leveraging Python type hints
2. **Edge Computing**: Lightweight frameworks for edge deployment
3. **AI Integration**: Native ML model serving capabilities
4. **GraphQL**: Better GraphQL support across frameworks
5. **Rust Extensions**: Performance-critical parts in Rust

## Sources

[1] FastAPI Benchmarks - https://www.techempower.com/benchmarks/#hw=ph&test=json&section=data-r21
[2] FastAPI GitHub Repository - https://github.com/tiangolo/fastapi
[3] Django Sites Database - https://djangosites.org/
[4] Django Performance Optimization Guide - https://docs.djangoproject.com/en/5.0/topics/performance/
[5] Python Developer Survey 2024 - https://www.jetbrains.com/python-developer-survey-2024/
[6] Flask Performance Analysis - https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxi-performance
[7] Litestar Benchmarks - https://docs.litestar.dev/latest/benchmarks/
[8] TechEmpower Framework Benchmarks Round 21 - https://www.techempower.com/benchmarks/

## Confidence Level

**High Confidence (95%)**: Performance benchmarks, GitHub statistics, feature comparisons
**Medium Confidence (75%)**: Future trends, migration complexity estimates
**Note**: All data verified from multiple sources as of January 2025
'''
        
        return research
    
    def _synthesize_findings(self, research_results: str) -> Dict[str, Any]:
        """
        Synthestisiert Recherche-Ergebnisse
        """
        # Extract key information from research
        import re
        
        # Extract sources
        sources = re.findall(r'\[\d+\].*?https?://[^\s]+', research_results)
        
        # Determine confidence level
        confidence = "high" if "High Confidence" in research_results else "medium"
        
        # Extract key findings
        key_findings = []
        if "Key Findings:" in research_results:
            findings_section = research_results.split("Key Findings:")[1].split("\n\n")[0]
            key_findings = [line.strip("- ") for line in findings_section.split("\n") if line.strip().startswith("-")]
        
        return {
            "sources": sources[:10],  # Top 10 sources
            "confidence": confidence,
            "key_findings": key_findings,
            "has_benchmarks": "benchmark" in research_results.lower(),
            "has_comparisons": "comparison" in research_results.lower() or "vs" in research_results.lower(),
            "has_recommendations": "recommend" in research_results.lower(),
            "data_recency": "2025" if "2025" in research_results else "2024",
            "topics_covered": [
                "performance",
                "security",
                "ecosystem",
                "community",
                "use_cases"
            ]
        }
    
    def _generate_recommendations(self, synthesis: Dict) -> List[str]:
        """
        Generiert Empfehlungen basierend auf Recherche
        """
        recommendations = []
        
        # High confidence recommendations
        if synthesis.get("confidence") == "high":
            recommendations.append("Based on comprehensive research with high confidence:")
            
            if synthesis.get("has_benchmarks"):
                recommendations.append("1. Performance data is available - use benchmarks for decision making")
            
            if synthesis.get("has_comparisons"):
                recommendations.append("2. Multiple options compared - choose based on specific requirements")
            
            if synthesis.get("key_findings"):
                recommendations.append("3. Key findings provide actionable insights for implementation")
        
        # Medium confidence recommendations
        else:
            recommendations.append("Based on available research with medium confidence:")
            recommendations.append("1. Consider conducting additional research for critical decisions")
            recommendations.append("2. Validate findings with proof-of-concept implementations")
        
        # General recommendations
        recommendations.extend([
            "4. Consider long-term maintenance and community support",
            "5. Evaluate security implications for your use case",
            "6. Test performance with your specific workload",
            "7. Plan for scalability from the beginning"
        ])
        
        return recommendations