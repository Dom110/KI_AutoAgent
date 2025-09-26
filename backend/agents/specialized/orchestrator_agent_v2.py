"""
OrchestratorAgent V2 - Full implementation with real AI services
Provides the same functionality as the TypeScript version
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..base.chat_agent import ChatAgent
from ..base.base_agent import (
    AgentConfig, TaskRequest, TaskResult, AgentCapability
)
from utils.openai_service import OpenAIService

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    """Subtask for decomposition"""
    id: str
    description: str
    agent: str
    priority: int
    dependencies: List[str] = field(default_factory=list)
    expected_output: str = ""
    estimated_duration: float = 0.0
    status: str = "pending"
    result: Optional[str] = None

@dataclass
class TaskDecomposition:
    """Complete task decomposition"""
    main_goal: str
    complexity: str
    subtasks: List[SubTask]
    estimated_duration: float
    execution_mode: str  # 'sequential' or 'parallel'
    summary: str

class OrchestratorAgentV2(ChatAgent):
    """
    Real Orchestrator Agent with full AI integration
    """

    def __init__(self):
        config = AgentConfig(
            agent_id="orchestrator",
            name="OrchestratorAgent",
            full_name="Advanced KI AutoAgent Orchestrator",
            description="Intelligent task orchestration with real AI-powered decomposition",
            model="gpt-4o-2024-11-20",  # Using GPT-4o
            capabilities=[
                AgentCapability.TASK_DECOMPOSITION,
                AgentCapability.PARALLEL_EXECUTION
            ],
            temperature=0.7,
            max_tokens=4000,
            icon="🎯",
            instructions_path=".kiautoagent/instructions/orchestrator-v2-instructions.md"
        )
        super().__init__(config)

        # Initialize OpenAI service with specific model
        self.ai_service = OpenAIService(model=self.config.model)

        # Agent registry reference (will be set by registry)
        self.agent_registry = None

        # Track active workflows
        self.active_workflows: Dict[str, Any] = {}

    async def execute(self, request: TaskRequest) -> TaskResult:
        """
        Execute orchestration with real AI
        """
        try:
            logger.info(f"🚀 Orchestrator execute started with prompt: {request.prompt[:100]}...")
            prompt = request.prompt
            mode = request.mode if hasattr(request, 'mode') else 'auto'
            logger.info(f"📋 Mode: {mode}")

            # Extract client_id and manager for progress updates
            client_id = None
            manager = None
            if hasattr(request, 'context') and isinstance(request.context, dict):
                client_id = request.context.get('client_id')
                manager = request.context.get('manager')  # Extract manager from context
                logger.info(f"📡 Client ID: {client_id}")
                logger.debug(f"📊 Manager passed: {manager is not None}")

            # Send initial progress
            await self._send_progress(client_id, "🤔 Analyzing your request...", manager)

            # In Auto mode, always use multi-agent workflow for complex tasks
            if mode == 'auto':
                # For infrastructure/complex questions, always use workflow
                keywords = ['infrastructure', 'caching', 'optimize', 'improve', 'architecture',
                           'performance', 'system', 'verstehen', 'analyse', 'verbessern']
                if any(word in prompt.lower() for word in keywords):
                    matched_keywords = [w for w in keywords if w in prompt.lower()]
                    logger.info(f"Auto mode: Detected keywords: {matched_keywords}")
                    await self._send_progress(client_id, f"🎯 Detected complex task: {', '.join(matched_keywords)}", manager)
                    logger.info(f"Auto mode: Triggering multi-agent workflow for infrastructure analysis")
                    return await self._handle_complex_task(request)

            # First, understand what the user is asking
            logger.info(f"🔍 Analyzing intent...")
            await self._send_progress(client_id, "🔍 Understanding what you're asking...", manager)
            intent = await self._analyze_intent(prompt, client_id, manager)
            logger.info(f"✅ Intent identified: {intent}")
            await self._send_progress(client_id, f"📝 Intent: {intent}", manager)

            # Handle different intents
            if intent == "self_description":
                # User is asking about the system itself
                return await self._describe_system()

            elif intent == "simple_question":
                # Direct question that doesn't need decomposition
                return await self._answer_directly(prompt)

            else:
                # Complex task requiring decomposition
                return await self._handle_complex_task(request)

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return TaskResult(
                status="error",
                content=f"I encountered an error: {str(e)}",
                agent=self.config.agent_id
            )

    async def _analyze_intent(self, prompt: str, client_id: str = None, manager=None) -> str:
        """
        Analyze user intent using AI
        """
        logger.info(f"🧠 Starting intent analysis for prompt: {prompt[:50]}...")
        await self._send_progress(client_id, "🧠 Analyzing intent with AI...", manager)

        system_prompt = """Analyze the user's request and categorize it into one of these intents:
        - 'self_description': User asking about what this system is, what you are, your capabilities
        - 'simple_question': A simple question that can be answered directly
        - 'complex_task': A task requiring multiple steps, code implementation, or agent collaboration

        UI/Code improvements, button styling, interface enhancements = 'complex_task'
        Questions about "this project", "this system", "these buttons" = 'complex_task'

        Respond with ONLY the intent category name."""

        logger.info(f"📡 Calling AI service for intent analysis...")
        await self._send_progress(client_id, "📡 Calling OpenAI GPT-4o for analysis...", manager)
        try:
            # Use longer timeout for complex infrastructure queries
            timeout = 120.0 if any(word in prompt.lower() for word in ['infrastructure', 'analyze', 'architecture', 'improve']) else 30.0
            response = await self.ai_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=0.3,
                timeout=timeout
            )
            logger.info(f"📥 AI service response: {response}")
            await self._send_progress(client_id, f"✅ AI identified: {response}", manager)
        except Exception as e:
            logger.error(f"❌ AI service error during intent analysis: {e}")
            await self._send_progress(client_id, f"❌ Error: {str(e)}", manager)
            raise

        # Check if we got an error response
        if "error" in response.lower():
            raise Exception(f"Intent analysis failed: {response}\nPlease check API keys and model configuration.")

        intent = response.strip().lower().replace("'", "").replace('"', '')

        # Fallback to complex_task if unclear
        if intent not in ["self_description", "simple_question", "complex_task"]:
            intent = "complex_task"

        return intent

    async def _describe_system(self) -> TaskResult:
        """
        Describe what the KI AutoAgent system is
        """
        description = """## 🤖 KI AutoAgent System

I am the **KI AutoAgent Orchestrator**, the central intelligence of a sophisticated multi-agent AI development platform integrated into VS Code.

### 🎯 What I Do:
- **Task Orchestration**: I analyze your requests and intelligently decompose complex tasks into manageable subtasks
- **Agent Coordination**: I manage a team of specialized AI agents, each expert in different domains
- **Parallel Execution**: I can execute multiple tasks simultaneously for faster results
- **Intelligent Routing**: I determine which agent is best suited for each part of your request

### 👥 My Team of Specialized Agents:
1. **🏗️ ArchitectAgent** - System design and architecture expert (GPT-5)
2. **💻 CodeSmithAgent** - Code implementation specialist (Claude 4.1)
3. **📚 DocuBot** - Documentation and explanation expert
4. **🔍 ReviewerGPT** - Code review and validation specialist
5. **🔧 FixerBot** - Bug fixing and optimization expert
6. **🔬 ResearchAgent** - Web research and information gathering
7. **📈 TradeStrat** - Trading and financial analysis specialist
8. **⚖️ OpusArbitrator** - Conflict resolution when agents disagree

### 💪 My Capabilities:
- **Natural Language Understanding**: Simply describe what you need
- **Context Awareness**: I remember our conversation history
- **Multi-Modal Support**: Handle code, documentation, research, and more
- **Learning & Adaptation**: I improve from past interactions
- **Real-Time Collaboration**: All agents work together seamlessly

### 🚀 How to Use Me:
Simply tell me what you need! Examples:
- "Help me build a REST API with FastAPI"
- "Review this code for security issues"
- "Explain how async/await works in Python"
- "Research best practices for microservices"
- "Fix the bug in my authentication logic"

I'm here to make your development process faster, smarter, and more efficient. How can I help you today?"""

        return TaskResult(
            status="success",
            content=description,
            agent=self.config.agent_id,
            metadata={
                "intent": "self_description",
                "response_type": "informational"
            }
        )

    async def _answer_directly(self, prompt: str) -> TaskResult:
        """
        Answer a simple question directly using AI
        """
        system_prompt = """You are the KI AutoAgent Orchestrator.
        Answer the user's question directly and concisely.
        Use markdown formatting for clarity."""

        response = await self.ai_service.get_completion(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.7,
            max_tokens=2000
        )

        return TaskResult(
            status="success",
            content=response,
            agent=self.config.agent_id,
            metadata={
                "intent": "simple_question",
                "response_type": "direct_answer"
            }
        )

    async def _handle_complex_task(self, request: TaskRequest) -> TaskResult:
        """
        Handle complex tasks with decomposition
        """
        prompt = request.prompt

        # Extract client_id and manager for progress updates
        client_id = None
        manager = None
        if hasattr(request, 'context') and isinstance(request.context, dict):
            client_id = request.context.get('client_id')
            manager = request.context.get('manager')

        # Decompose the task using AI
        logger.info("🔧 Starting task decomposition...")
        await self._send_progress(client_id, "🔧 Breaking down your request into subtasks...", manager)
        decomposition = await self._decompose_task_with_ai(prompt, client_id, manager)

        # Execute the workflow with request context
        logger.info(f"🎯 Executing workflow with {len(decomposition.subtasks)} subtasks")
        await self._send_progress(client_id, f"🎯 Executing {len(decomposition.subtasks)} subtasks...", manager)
        results = await self._execute_workflow(decomposition, request)

        # Format the final response
        logger.info("📦 Synthesizing final results...")
        await self._send_progress(client_id, "📦 Synthesizing results from all agents...", manager)
        final_response = await self._synthesize_results(decomposition, results, prompt)

        return TaskResult(
            status="success",
            content=final_response,
            agent=self.config.agent_id,
            metadata={
                "intent": "complex_task",
                "subtask_count": len(decomposition.subtasks),
                "execution_mode": decomposition.execution_mode
            }
        )

    async def _decompose_task_with_ai(self, prompt: str, client_id: str = None, manager=None) -> TaskDecomposition:
        """
        Use AI to decompose task into subtasks
        """
        # Check if this is an infrastructure improvement task
        keywords = ['infrastructure', 'caching', 'optimize', 'improve', 'architecture', 'performance', 'verbessern', 'system']
        if any(word in prompt.lower() for word in keywords):
            matched = [w for w in keywords if w in prompt.lower()]
            logger.info(f"🏗️ Infrastructure keywords detected: {matched}")
            await self._send_progress(client_id, f"🏗️ Infrastructure task detected: {', '.join(matched)}", manager)
            return await self._create_infrastructure_workflow(prompt, client_id, manager)

        system_prompt = """You are an expert task decomposer. Analyze the given task and break it down into subtasks.

Available agents and their specialties:
- architect: System design, architecture patterns, UI/UX design, component architecture, VSCode extension design
  TOOLS: understand_system(), analyze_infrastructure_improvements(), generate_architecture_flowchart()
- codesmith: Code implementation, CSS/HTML/TypeScript, UI components, button styling, VSCode API integration
  TOOLS: Creates actual files, config, docker-compose, implementation code
- research: Web research, finding best practices, UI/UX trends, design patterns, VSCode extension examples
  TOOLS: Web search for state-of-the-art solutions
- reviewer: Code review, security analysis, quality checks, accessibility testing
- docubot: Documentation, explanations, tutorials, API documentation
- fixer: Bug fixing, optimization, performance improvements, CSS fixes
- tradestrat: Trading systems, financial algorithms (NOT for UI tasks)
- opus-arbitrator: Conflict resolution (only when agents disagree)

Respond with a JSON object containing:
{
    "main_goal": "Clear description of the main goal",
    "complexity": "simple|moderate|complex",
    "execution_mode": "sequential|parallel",
    "subtasks": [
        {
            "id": "task_1",
            "description": "Clear description of subtask",
            "agent": "agent_name",
            "priority": 1,
            "dependencies": [],
            "expected_output": "What this subtask should produce"
        }
    ],
    "estimated_duration": 10.0,
    "summary": "Brief summary of the approach"
}

Guidelines:
- For simple tasks, use 1-2 subtasks
- For moderate tasks, use 2-4 subtasks
- For complex tasks, use 3-6 subtasks
- Consider dependencies between tasks
- Choose the most appropriate agent for each subtask"""

        # Use longer timeout for complex task decomposition
        timeout = 180.0 if any(word in prompt.lower() for word in ['infrastructure', 'analyze', 'architecture', 'improve', 'complex']) else 60.0
        response = await self.ai_service.get_completion(
            system_prompt=system_prompt,
            user_prompt=f"Decompose this task: {prompt}\n\nIMPORTANT: Return ONLY valid JSON, no additional text.",
            temperature=0.5,
            max_tokens=2000,
            timeout=timeout
        )

        # Debug logging
        logger.info(f"📊 Raw decomposition response (first 200 chars): {response[:200]}")

        # Try to extract JSON from response (sometimes GPT adds text around it)
        json_match = None
        if response.strip().startswith('{'):
            json_str = response
        else:
            # Try to find JSON in the response
            import re
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            if matches:
                json_str = matches[0]
                logger.info("📋 Extracted JSON from text response")
            else:
                json_str = response

        try:
            # Parse the JSON response
            data = json.loads(json_str)

            # Create SubTask objects
            subtasks = [
                SubTask(
                    id=st["id"],
                    description=st["description"],
                    agent=st["agent"],
                    priority=st["priority"],
                    dependencies=st.get("dependencies", []),
                    expected_output=st.get("expected_output", "")
                )
                for st in data["subtasks"]
            ]

            return TaskDecomposition(
                main_goal=data["main_goal"],
                complexity=data["complexity"],
                subtasks=subtasks,
                estimated_duration=data.get("estimated_duration", 10.0),
                execution_mode=data.get("execution_mode", "sequential"),
                summary=data.get("summary", "")
            )

        except (json.JSONDecodeError, KeyError) as e:
            error_msg = f"Failed to parse task decomposition JSON: {e}\nRaw response: {response[:500]}\nPlease check GPT model configuration."
            logger.error(error_msg)
            raise Exception(error_msg)

    async def _create_infrastructure_workflow(self, prompt: str, client_id: str = None, manager=None) -> TaskDecomposition:
        """
        Create active workflow for infrastructure improvements
        """
        # Get workspace path from context if available
        import os
        workspace_path = os.getenv('VSCODE_WORKSPACE', os.getcwd())

        workflow = TaskDecomposition(
            main_goal=f"Actively improve system infrastructure: {prompt}",
            complexity="complex",
            execution_mode="sequential",  # Changed to sequential to avoid timeout
            subtasks=[
                SubTask(
                    id="analyze_system",
                    description="Use understand_system() to analyze the workspace and create system_analysis.json in .ki_autoagent/ folder",
                    agent="architect",
                    priority=1,
                    dependencies=[],
                    expected_output="Complete system analysis saved to .ki_autoagent/system_analysis.json"
                ),
                SubTask(
                    id="research_best_practices",
                    description="Search web for latest caching strategies, performance optimization libraries, and best practices for the detected technology stack",
                    agent="research",
                    priority=2,
                    dependencies=[],
                    expected_output="State-of-the-art research findings saved to .ki_autoagent/research_results.md"
                ),
                SubTask(
                    id="analyze_improvements",
                    description="Use analyze_infrastructure_improvements() to identify specific issues and create detailed improvement recommendations",
                    agent="architect",
                    priority=3,
                    dependencies=["analyze_system"],
                    expected_output="Detailed improvements document saved to .ki_autoagent/improvements.md"
                ),
                SubTask(
                    id="create_diagrams",
                    description="Use generate_architecture_flowchart() to visualize current architecture and proposed improvements",
                    agent="architect",
                    priority=4,
                    dependencies=["analyze_improvements"],
                    expected_output="Architecture diagrams saved to .ki_autoagent/architecture_current.mermaid and architecture_improved.mermaid"
                ),
                SubTask(
                    id="implement_caching",
                    description="Create redis.config, docker-compose.yml, and cache_manager.py implementation based on the analysis",
                    agent="codesmith",
                    priority=5,
                    dependencies=["analyze_improvements", "research_best_practices"],
                    expected_output="Created redis.config, docker-compose.yml, and backend/core/cache_manager.py"
                ),
                SubTask(
                    id="create_tests",
                    description="Create comprehensive test files for the new caching infrastructure",
                    agent="codesmith",
                    priority=6,
                    dependencies=["implement_caching"],
                    expected_output="Test files created in backend/tests/test_cache_manager.py"
                )
            ],
            estimated_duration=300.0,
            summary="Active infrastructure improvement with file creation and implementation"
        )

        logger.info(f"🏗️ Infrastructure workflow created with {len(workflow.subtasks)} tasks")
        await self._send_progress(client_id, f"🏗️ Created workflow with {len(workflow.subtasks)} analysis tasks", manager)
        return workflow

    async def _execute_workflow(self, decomposition: TaskDecomposition, original_request: TaskRequest = None) -> Dict[str, Any]:
        """
        Execute the workflow with real agent dispatching
        """
        results = {}

        # Get agent registry
        if not self.agent_registry:
            from agents.agent_registry import get_agent_registry
            self.agent_registry = get_agent_registry()

        # Log workflow start
        logger.info(f"🚀 Starting workflow with {len(decomposition.subtasks)} tasks in {decomposition.execution_mode} mode")

        # Execute based on mode
        if decomposition.execution_mode == "parallel":
            # Execute tasks in parallel
            tasks = []
            for subtask in decomposition.subtasks:
                if not subtask.dependencies:  # Only start tasks with no dependencies
                    logger.info(f"▶️ Starting parallel task: {subtask.id} with agent {subtask.agent}")
                    tasks.append(self._execute_subtask(subtask, original_request))

            if tasks:
                # Use gather with return_exceptions=True to handle failures gracefully
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                for subtask, result in zip(decomposition.subtasks, task_results):
                    if isinstance(result, Exception):
                        error_msg = f"ERROR: {str(result)}"
                        results[subtask.id] = error_msg
                        logger.error(f"❌ Parallel task failed: {subtask.id} - {error_msg}")
                    else:
                        results[subtask.id] = result
                        logger.info(f"✅ Completed parallel task: {subtask.id}")

        else:
            # Execute sequentially
            for i, subtask in enumerate(decomposition.subtasks, 1):
                logger.info(f"▶️ Step {i}/{len(decomposition.subtasks)}: Executing {subtask.id} with agent {subtask.agent}")
                try:
                    result = await self._execute_subtask(subtask, original_request)
                    results[subtask.id] = result
                    subtask.result = result
                    logger.info(f"✅ Step {i}/{len(decomposition.subtasks)} completed: {subtask.id}")
                except Exception as e:
                    # If a subtask fails, stop the workflow
                    error_msg = f"❌ Workflow stopped at step {i}/{len(decomposition.subtasks)}: {str(e)}"
                    logger.error(error_msg)
                    results[subtask.id] = f"ERROR: {str(e)}"
                    # Return results so far with error
                    results['workflow_error'] = error_msg
                    break  # Stop executing further tasks

        logger.info(f"🎯 Workflow complete with {len(results)} results")
        return results

    async def _execute_subtask(self, subtask: SubTask, original_request: TaskRequest = None) -> str:
        """
        Execute a single subtask with the appropriate agent
        """
        # Try to dispatch to the actual agent
        if self.agent_registry and subtask.agent in self.agent_registry.agents:
            try:
                # Add timeout to prevent hanging
                import asyncio

                # Preserve original context including client_id
                context = {"expected_output": subtask.expected_output}
                if original_request and hasattr(original_request, 'context'):
                    # Merge original context - ensure it's a dict
                    if isinstance(original_request.context, dict):
                        context.update(original_request.context)
                    elif isinstance(original_request.context, str):
                        logger.warning(f"Original request context was string: {original_request.context}, converting to dict")
                        # Try to parse as JSON or just add as a value
                        try:
                            import json
                            context.update(json.loads(original_request.context))
                        except:
                            context['original_context'] = original_request.context
                    else:
                        logger.warning(f"Unexpected context type: {type(original_request.context)}")

                request = TaskRequest(
                    prompt=subtask.description,
                    context=context
                )

                # Dynamic timeout based on task complexity
                # Infrastructure analysis and complex tasks need more time
                timeout = 120.0  # Default 2 minutes for complex tasks

                # For simple queries, use shorter timeout
                if any(word in request.prompt.lower() for word in ['list', 'what', 'which', 'show']):
                    timeout = 30.0
                # For infrastructure analysis or complex tasks, use longer timeout
                elif any(word in request.prompt.lower() for word in ['infrastructure', 'analyze', 'improve', 'architecture', 'optimize', 'refactor']):
                    timeout = 180.0  # 3 minutes for infrastructure analysis

                result = await asyncio.wait_for(
                    self.agent_registry.dispatch_task(subtask.agent, request),
                    timeout=timeout
                )

                # Check if the result is an error
                if hasattr(result, 'status') and result.status == 'error':
                    error_msg = f"Agent {subtask.agent} returned error: {result.content}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                if result.content and "Error" not in result.content:
                    return result.content
                else:
                    # If content contains error or is empty, raise exception
                    error_msg = f"Agent {subtask.agent} failed with: {result.content if result.content else 'Empty response'}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            except asyncio.TimeoutError:
                error_msg = f"Agent {subtask.agent} timed out after {timeout} seconds. This might be a complex task - please try again or break it into smaller tasks."
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Agent {subtask.agent} failed: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)

        # No fallback - fail with clear error
        error_msg = f"Agent '{subtask.agent}' is not available in the registry. Available agents: {list(self.agent_registry.agents.keys()) if self.agent_registry else 'No registry'}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def _simulate_agent_response(self, subtask: SubTask) -> str:
        """
        Simulate agent response using AI when actual agent not available
        """
        agent_prompts = {
            "architect": "You are a UI/UX architect specializing in VSCode extensions. Design modern, beautiful UI components with specific CSS and layout recommendations.",
            "codesmith": "You are an expert in CSS, TypeScript, and VSCode API. Provide SPECIFIC code examples with modern CSS styles, animations, and TypeScript implementations.",
            "research": "You are a UI/UX research specialist. Find current design trends for VSCode extensions and modern button designs. Provide specific examples.",
            "reviewer": "You are a code reviewer focusing on accessibility, performance, and VSCode theme compatibility. Review the UI implementation.",
            "docubot": "You are a documentation expert. Document the UI components and their usage.",
            "fixer": "You are a CSS/TypeScript specialist. Fix UI bugs and optimize performance.",
            "tradestrat": "You are a trading strategy expert. Design algorithmic trading systems.",
            "opus-arbitrator": "You are the supreme arbitrator. Resolve conflicts with binding decisions."
        }

        system_prompt = agent_prompts.get(
            subtask.agent,
            "You are a helpful AI assistant. Complete the given task."
        )

        # Add specific instructions for concrete implementations
        enhanced_prompt = f"""Task: {subtask.description}

Expected Output: {subtask.expected_output if hasattr(subtask, 'expected_output') else 'Detailed solution'}

IMPORTANT: Provide SPECIFIC, CONCRETE implementations:
- Include actual CSS code with properties and values
- Show TypeScript/JavaScript code examples
- Use modern design patterns (gradients, shadows, animations)
- Reference VSCode theme variables (--vscode-button-background, etc.)
- Include hover states and transitions
- Be specific about colors, sizes, and effects

DO NOT provide general advice. PROVIDE ACTUAL CODE."""

        response = await self.ai_service.get_completion(
            system_prompt=system_prompt,
            user_prompt=enhanced_prompt,
            temperature=0.7,
            max_tokens=1500
        )

        return response

    async def _synthesize_results(
        self,
        decomposition: TaskDecomposition,
        results: Dict[str, Any],
        original_prompt: str
    ) -> str:
        """
        Synthesize all subtask results into a final response
        """
        # Build context from results
        subtask_summaries = []
        for subtask in decomposition.subtasks:
            result = results.get(subtask.id, "No result")
            subtask_summaries.append(f"**{subtask.description}**:\n{result}")

        context = "\n\n".join(subtask_summaries)

        system_prompt = """You are the KI AutoAgent Orchestrator synthesizing results from multiple specialized agents.
        Create a comprehensive, well-structured response that combines all the subtask results.
        Use markdown formatting for clarity.

        Guidelines:
        - Start with a brief overview
        - Present the combined solution/answer
        - Highlight key points from each agent's contribution
        - Provide a clear conclusion or next steps if applicable"""

        user_prompt = f"""Original request: {original_prompt}

Task decomposition summary: {decomposition.summary}

Subtask results:
{context}

Please synthesize these results into a comprehensive response."""

        # Use shorter synthesis for moderate complexity
        if decomposition.complexity == "moderate" and len(decomposition.subtasks) <= 3:
            # Create quick summary
            response = "## 🎨 Button Design Improvements\n\n"

            for subtask in decomposition.subtasks:
                result = results.get(subtask.id, "")
                if result:
                    response += f"### {subtask.agent.title()}: {subtask.description}\n"
                    response += f"{result[:500]}...\n\n"  # Limit each result

        else:
            # Full synthesis for complex tasks
            response = await self.ai_service.get_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2000  # Reduced from 3000
            )

        # Add execution metadata
        response += f"\n\n---\n*Executed {len(decomposition.subtasks)} subtasks in {decomposition.execution_mode} mode*"

        return response

    async def _send_progress(self, client_id: str, message: str, manager=None):
        """Send progress update to WebSocket client"""
        logger.debug(f"🔍 _send_progress called with client_id={client_id}, message={message}")
        if not client_id:
            logger.debug("⚠️ No client_id, skipping progress message")
            return

        try:
            # First try to use manager from parameter (passed through context)
            if not manager:
                # Fall back to importing (though this may not work due to circular imports)
                logger.debug("📦 Manager not passed, attempting to import from api.server")
                try:
                    from api.server import manager
                except ImportError:
                    logger.warning("⚠️ Could not import manager from api.server")
                    return

            from datetime import datetime
            logger.debug(f"✅ Manager available: {manager}")
            logger.debug(f"📊 Active connections: {list(manager.active_connections.keys()) if manager else 'No manager'}")

            if manager and client_id in manager.active_connections:
                try:
                    logger.info(f"📡 About to send progress via manager.send_json to {client_id}")
                    await manager.send_json(client_id, {
                        "type": "agent_progress",
                        "agent": "orchestrator",
                        "content": message,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"📤 Successfully sent progress to client {client_id}: {message}")
                except Exception as send_err:
                    logger.error(f"❌ Failed to send via manager.send_json: {send_err}")
            else:
                if not manager:
                    logger.warning(f"⚠️ No manager instance available")
                else:
                    logger.warning(f"⚠️ Client {client_id} not in active connections: {list(manager.active_connections.keys())}")
        except Exception as e:
            logger.error(f"❌ Could not send progress update: {e}")

    async def _process_agent_request(self, message: Any) -> Any:
        """Process request from another agent"""
        # Convert agent request to TaskRequest
        request = TaskRequest(
            prompt=message.get("prompt", ""),
            context=message.get("context", {})
        )
        result = await self.execute(request)
        return result.content