"""
Framework Comparison System (Systemvergleich-Analyse) v1.0

Compares KI_AutoAgent with other agent frameworks and analyzes best practices.
This is a META-LEVEL analysis tool that extends (not replaces) existing scanners.

Key Concepts:
- Framework Analysis: Compare with AutoGen, CrewAI, BabyAGI, ChatDev, etc.
- Pattern Recognition: Identify successful patterns in other frameworks
- Best Practices: Extract industry standards
- Gap Analysis: Identify what KI_AutoAgent could learn from others
- Differentiation: Understand KI_AutoAgent's unique strengths

Use Cases:
1. Architect uses this to understand if proposed architecture aligns with best practices
2. Identify patterns from successful frameworks that could be adopted
3. Learn from other systems' solutions to common problems
4. Validate design decisions against industry standards

Note: This EXTENDS code-level scanners, not replaces them.
      Code scanners analyze user's code, this analyzes agent frameworks.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class FrameworkCategory(Enum):
    """Categories of agent frameworks"""
    MULTI_AGENT = "multi_agent"  # Multiple collaborating agents
    SINGLE_AGENT = "single_agent"  # Single intelligent agent
    WORKFLOW = "workflow"  # Workflow/pipeline based
    RESEARCH = "research"  # Research-focused
    CODING = "coding"  # Code generation focused


@dataclass
class FrameworkFeature:
    """A feature of an agent framework"""
    name: str
    description: str
    benefit: str
    implementation_complexity: str  # "low", "medium", "high"
    examples: List[str] = field(default_factory=list)


@dataclass
class FrameworkProfile:
    """Profile of an agent framework"""
    name: str
    category: FrameworkCategory
    description: str
    key_features: List[FrameworkFeature]
    strengths: List[str]
    weaknesses: List[str]
    best_for: List[str]
    architecture_pattern: str
    source_url: Optional[str] = None
    popularity_score: float = 0.0  # 0.0-1.0


class FrameworkDatabase:
    """
    Database of known agent frameworks and their characteristics

    This serves as knowledge base for comparison
    """

    def __init__(self):
        self.frameworks: Dict[str, FrameworkProfile] = {}
        self._initialize_framework_knowledge()

    def _initialize_framework_knowledge(self):
        """Initialize knowledge base with known frameworks"""

        # AutoGen (Microsoft)
        self.frameworks["autogen"] = FrameworkProfile(
            name="AutoGen",
            category=FrameworkCategory.MULTI_AGENT,
            description="Microsoft's framework for building multi-agent conversation systems",
            key_features=[
                FrameworkFeature(
                    name="Conversable Agents",
                    description="Agents communicate through structured conversations",
                    benefit="Natural collaboration between agents",
                    implementation_complexity="medium",
                    examples=["UserProxyAgent", "AssistantAgent"]
                ),
                FrameworkFeature(
                    name="Human-in-the-Loop",
                    description="Seamless human intervention in agent workflows",
                    benefit="Maintains control and oversight",
                    implementation_complexity="low",
                    examples=["UserProxyAgent with human_input_mode"]
                ),
                FrameworkFeature(
                    name="Group Chat",
                    description="Multiple agents collaborate in group discussions",
                    benefit="Complex multi-agent reasoning",
                    implementation_complexity="medium",
                    examples=["GroupChat", "GroupChatManager"]
                )
            ],
            strengths=[
                "Strong Microsoft backing",
                "Excellent documentation",
                "Active community",
                "Flexible agent communication"
            ],
            weaknesses=[
                "Can be complex for simple tasks",
                "Requires careful prompt engineering",
                "Token usage can be high"
            ],
            best_for=[
                "Multi-agent conversations",
                "Research and exploration",
                "Tasks requiring back-and-forth reasoning"
            ],
            architecture_pattern="Conversational Multi-Agent",
            source_url="https://github.com/microsoft/autogen",
            popularity_score=0.9
        )

        # CrewAI
        self.frameworks["crewai"] = FrameworkProfile(
            name="CrewAI",
            category=FrameworkCategory.MULTI_AGENT,
            description="Framework for orchestrating role-playing autonomous AI agents",
            key_features=[
                FrameworkFeature(
                    name="Role-Based Agents",
                    description="Agents have specific roles and backstories",
                    benefit="Clear separation of concerns",
                    implementation_complexity="low",
                    examples=["Researcher", "Writer", "Analyst"]
                ),
                FrameworkFeature(
                    name="Task Assignment",
                    description="Explicit task assignment to agents",
                    benefit="Predictable execution flow",
                    implementation_complexity="low",
                    examples=["Task with agent assignment"]
                ),
                FrameworkFeature(
                    name="Process Types",
                    description="Sequential or hierarchical execution",
                    benefit="Flexible workflow patterns",
                    implementation_complexity="medium",
                    examples=["Sequential", "Hierarchical"]
                )
            ],
            strengths=[
                "Simple and intuitive API",
                "Role-based design is natural",
                "Good for task delegation",
                "Built-in tools integration"
            ],
            weaknesses=[
                "Less flexible than conversation-based",
                "Limited dynamic adaptation",
                "Sequential bias"
            ],
            best_for=[
                "Task-based workflows",
                "Role-playing scenarios",
                "Hierarchical organizations"
            ],
            architecture_pattern="Role-Based Task Delegation",
            source_url="https://github.com/joaomdmoura/crewAI",
            popularity_score=0.85
        )

        # BabyAGI
        self.frameworks["babyagi"] = FrameworkProfile(
            name="BabyAGI",
            category=FrameworkCategory.SINGLE_AGENT,
            description="Task-driven autonomous agent with memory and prioritization",
            key_features=[
                FrameworkFeature(
                    name="Task Creation",
                    description="Agent creates new tasks based on results",
                    benefit="Autonomous goal pursuit",
                    implementation_complexity="medium",
                    examples=["Task creation agent"]
                ),
                FrameworkFeature(
                    name="Task Prioritization",
                    description="Dynamic priority adjustment",
                    benefit="Efficient task ordering",
                    implementation_complexity="medium",
                    examples=["Prioritization agent"]
                ),
                FrameworkFeature(
                    name="Vector Memory",
                    description="Pinecone/Weaviate integration for context",
                    benefit="Long-term context retention",
                    implementation_complexity="high",
                    examples=["Pinecone memory"]
                )
            ],
            strengths=[
                "Self-directed task generation",
                "Priority-based execution",
                "Long-term memory",
                "Simple core loop"
            ],
            weaknesses=[
                "Can spiral into too many tasks",
                "Resource intensive",
                "Requires external vector DB",
                "Less suitable for defined workflows"
            ],
            best_for=[
                "Open-ended research",
                "Exploratory tasks",
                "Autonomous operation"
            ],
            architecture_pattern="Task Loop with Memory",
            source_url="https://github.com/yoheinakajima/babyagi",
            popularity_score=0.75
        )

        # ChatDev
        self.frameworks["chatdev"] = FrameworkProfile(
            name="ChatDev",
            category=FrameworkCategory.CODING,
            description="Simulates a software company with role-playing agents",
            key_features=[
                FrameworkFeature(
                    name="Software Company Simulation",
                    description="CEO, CTO, Designer, Engineer, Tester roles",
                    benefit="Realistic software development process",
                    implementation_complexity="high",
                    examples=["CEO → CTO → Designer → Engineer → Tester"]
                ),
                FrameworkFeature(
                    name="Phase-Based Development",
                    description="Demand Analysis → Design → Coding → Testing",
                    benefit="Structured SDLC",
                    implementation_complexity="medium",
                    examples=["DemandAnalysis phase", "Coding phase"]
                ),
                FrameworkFeature(
                    name="Artifact Generation",
                    description="Generates requirements, designs, code, docs",
                    benefit="Complete software deliverables",
                    implementation_complexity="medium",
                    examples=["requirements.txt", "design.png", "code.py"]
                )
            ],
            strengths=[
                "Realistic development process",
                "Multiple perspectives (roles)",
                "Complete software lifecycle",
                "Good documentation generation"
            ],
            weaknesses=[
                "Can be slow (many phases)",
                "High token usage",
                "Overkill for simple tasks",
                "Fixed role structure"
            ],
            best_for=[
                "Complete software projects",
                "Learning agent collaboration",
                "Demonstration purposes"
            ],
            architecture_pattern="Phase-Based Role Simulation",
            source_url="https://github.com/OpenBMB/ChatDev",
            popularity_score=0.7
        )

        # LangGraph (Our Foundation)
        self.frameworks["langgraph"] = FrameworkProfile(
            name="LangGraph",
            category=FrameworkCategory.WORKFLOW,
            description="Graph-based framework for building stateful multi-agent applications",
            key_features=[
                FrameworkFeature(
                    name="State Graphs",
                    description="Explicit state management in graphs",
                    benefit="Clear state transitions and control flow",
                    implementation_complexity="medium",
                    examples=["StateGraph", "MessageGraph"]
                ),
                FrameworkFeature(
                    name="Conditional Edges",
                    description="Dynamic routing based on state",
                    benefit="Flexible workflow adaptation",
                    implementation_complexity="medium",
                    examples=["add_conditional_edges"]
                ),
                FrameworkFeature(
                    name="Persistence",
                    description="Built-in checkpointing and state persistence",
                    benefit="Resume from failures, time travel debugging",
                    implementation_complexity="low",
                    examples=["MemorySaver", "SqliteSaver"]
                )
            ],
            strengths=[
                "Excellent state management",
                "Visual graph representation",
                "Flexible routing",
                "LangChain ecosystem integration"
            ],
            weaknesses=[
                "Learning curve",
                "Verbose for simple cases",
                "Relatively new"
            ],
            best_for=[
                "Complex stateful workflows",
                "Agent collaboration",
                "Production systems"
            ],
            architecture_pattern="Stateful Graph Workflow",
            source_url="https://github.com/langchain-ai/langgraph",
            popularity_score=0.8
        )


class FrameworkComparator:
    """
    Compares frameworks and provides recommendations

    This is the main analysis engine
    """

    def __init__(self):
        self.db = FrameworkDatabase()
        self.comparison_history: List[Dict[str, Any]] = []

    def compare_architecture_decision(
        self,
        decision: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze an architecture decision against framework best practices

        Args:
            decision: The architecture decision to analyze
            context: Context about the project/task

        Returns:
            Analysis with:
            - similar_patterns: Patterns from other frameworks
            - recommendations: Suggestions based on comparisons
            - best_practices: Industry best practices
            - risk_assessment: Potential issues
        """
        logger.info(f"🔍 Analyzing architecture decision: {decision[:60]}...")

        similar_patterns = self._find_similar_patterns(decision, context)
        recommendations = self._generate_recommendations(decision, similar_patterns, context)
        best_practices = self._extract_best_practices(similar_patterns)
        risk_assessment = self._assess_risks(decision, similar_patterns)

        analysis = {
            "decision": decision,
            "similar_patterns": similar_patterns,
            "recommendations": recommendations,
            "best_practices": best_practices,
            "risk_assessment": risk_assessment,
            "frameworks_analyzed": len(self.db.frameworks)
        }

        self.comparison_history.append(analysis)

        return analysis

    def _find_similar_patterns(
        self,
        decision: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find similar patterns in other frameworks"""
        patterns = []

        decision_lower = decision.lower()

        # Pattern: Multi-agent collaboration
        if any(keyword in decision_lower for keyword in ["multi-agent", "collaboration", "agents work together"]):
            patterns.append({
                "pattern": "Multi-Agent Collaboration",
                "frameworks": ["autogen", "crewai", "langgraph"],
                "approaches": [
                    {
                        "framework": "AutoGen",
                        "approach": "Conversational agents with GroupChat",
                        "benefit": "Natural back-and-forth reasoning"
                    },
                    {
                        "framework": "CrewAI",
                        "approach": "Role-based task delegation",
                        "benefit": "Clear separation of responsibilities"
                    },
                    {
                        "framework": "LangGraph",
                        "approach": "Graph-based state sharing",
                        "benefit": "Explicit state management"
                    }
                ]
            })

        # Pattern: Task decomposition
        if any(keyword in decision_lower for keyword in ["decompose", "break down", "subtasks"]):
            patterns.append({
                "pattern": "Task Decomposition",
                "frameworks": ["babyagi", "chatdev", "crewai"],
                "approaches": [
                    {
                        "framework": "BabyAGI",
                        "approach": "Dynamic task creation based on results",
                        "benefit": "Autonomous goal pursuit"
                    },
                    {
                        "framework": "ChatDev",
                        "approach": "Fixed phase-based decomposition",
                        "benefit": "Predictable, structured process"
                    },
                    {
                        "framework": "CrewAI",
                        "approach": "Manual task assignment to roles",
                        "benefit": "Explicit control over workflow"
                    }
                ]
            })

        # Pattern: State management
        if any(keyword in decision_lower for keyword in ["state", "context", "memory"]):
            patterns.append({
                "pattern": "State Management",
                "frameworks": ["langgraph", "babyagi", "autogen"],
                "approaches": [
                    {
                        "framework": "LangGraph",
                        "approach": "Explicit state graphs with persistence",
                        "benefit": "Resume from failures, clear state flow"
                    },
                    {
                        "framework": "BabyAGI",
                        "approach": "Vector database for long-term memory",
                        "benefit": "Context retention across tasks"
                    },
                    {
                        "framework": "AutoGen",
                        "approach": "Conversation history as state",
                        "benefit": "Natural state progression"
                    }
                ]
            })

        # Pattern: Human oversight
        if any(keyword in decision_lower for keyword in ["approval", "human", "oversight", "review"]):
            patterns.append({
                "pattern": "Human-in-the-Loop",
                "frameworks": ["autogen", "chatdev"],
                "approaches": [
                    {
                        "framework": "AutoGen",
                        "approach": "UserProxyAgent with human_input_mode",
                        "benefit": "Seamless intervention points"
                    },
                    {
                        "framework": "ChatDev",
                        "approach": "Phase-based approval gates",
                        "benefit": "Structured review points"
                    }
                ]
            })

        # Pattern: Code generation
        if any(keyword in decision_lower for keyword in ["code", "implement", "generate"]):
            patterns.append({
                "pattern": "Code Generation",
                "frameworks": ["chatdev", "autogen", "crewai"],
                "approaches": [
                    {
                        "framework": "ChatDev",
                        "approach": "Multi-phase with review (Design → Code → Test)",
                        "benefit": "Quality through multiple perspectives"
                    },
                    {
                        "framework": "AutoGen",
                        "approach": "Conversational code refinement",
                        "benefit": "Iterative improvement"
                    }
                ]
            })

        return patterns

    def _generate_recommendations(
        self,
        decision: str,
        patterns: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on pattern analysis"""
        recommendations = []

        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            approaches = pattern_info.get("approaches", [])

            if pattern == "Multi-Agent Collaboration":
                recommendations.append({
                    "category": "Architecture",
                    "recommendation": "Consider combining CrewAI's role clarity with LangGraph's state management",
                    "rationale": "Clear roles prevent overlap, explicit state prevents confusion",
                    "priority": "high"
                })

            if pattern == "Task Decomposition":
                recommendations.append({
                    "category": "Planning",
                    "recommendation": "Use hybrid approach: AI-driven decomposition with human validation",
                    "rationale": "BabyAGI shows autonomous decomposition works, but ChatDev shows structure helps",
                    "priority": "medium"
                })

            if pattern == "Human-in-the-Loop":
                recommendations.append({
                    "category": "Control",
                    "recommendation": "Implement architecture approval gates like ChatDev",
                    "rationale": "Prevents wasted effort on incorrect architectures",
                    "priority": "high"
                })

            if pattern == "Code Generation":
                recommendations.append({
                    "category": "Quality",
                    "recommendation": "Multi-phase approach: Design → Implement → Review → Fix",
                    "rationale": "ChatDev demonstrates this catches more issues",
                    "priority": "high"
                })

        return recommendations

    def _extract_best_practices(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract best practices from pattern analysis"""
        best_practices = []

        for pattern_info in patterns:
            for approach in pattern_info.get("approaches", []):
                best_practices.append(f"{approach['framework']}: {approach['benefit']}")

        # Add general best practices
        best_practices.extend([
            "Explicit state management prevents confusion (LangGraph)",
            "Role-based agents improve clarity (CrewAI)",
            "Human oversight gates prevent wasted effort (AutoGen, ChatDev)",
            "Vector memory enables long-term context (BabyAGI)",
            "Phase-based workflows ensure completeness (ChatDev)"
        ])

        return list(set(best_practices))  # Remove duplicates

    def _assess_risks(
        self,
        decision: str,
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Assess risks based on other frameworks' experiences"""
        risks = []

        decision_lower = decision.lower()

        # Risk: Too many agents
        if "agent" in decision_lower:
            risks.append({
                "risk": "Agent Communication Overhead",
                "description": "AutoGen shows too many agents increases token usage and latency",
                "mitigation": "Limit to essential agents, use hierarchical communication",
                "severity": "medium"
            })

        # Risk: Autonomous task creation
        if any(keyword in decision_lower for keyword in ["autonomous", "self-directed", "dynamic"]):
            risks.append({
                "risk": "Task Explosion",
                "description": "BabyAGI demonstrates autonomous agents can create too many subtasks",
                "mitigation": "Implement task limits and priority-based pruning",
                "severity": "high"
            })

        # Risk: No approval gates
        if "approval" not in decision_lower and "review" not in decision_lower:
            risks.append({
                "risk": "Missing Human Oversight",
                "description": "ChatDev shows approval gates prevent wasted effort on wrong directions",
                "mitigation": "Add architecture approval before implementation",
                "severity": "high"
            })

        return risks

    def get_framework_profile(self, framework_name: str) -> Optional[FrameworkProfile]:
        """Get detailed profile of a specific framework"""
        return self.db.frameworks.get(framework_name.lower())

    def list_frameworks(self) -> List[str]:
        """List all known frameworks"""
        return list(self.db.frameworks.keys())

    def get_comparison_summary(self) -> Dict[str, Any]:
        """Get summary of all comparisons made"""
        return {
            "total_comparisons": len(self.comparison_history),
            "frameworks_in_db": len(self.db.frameworks),
            "framework_categories": list(set(
                f.category.value for f in self.db.frameworks.values()
            ))
        }
