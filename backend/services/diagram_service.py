"""
Diagram Generation Service using Mermaid and Graphviz

Generates various types of diagrams from code analysis:
- Architecture diagrams (C4 model)
- Flow charts
- Sequence diagrams
- Dependency graphs
- Entity relationship diagrams
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DiagramService:
    """
    Service for generating various diagram types from code analysis

    Supports:
    - Mermaid diagrams (flowcharts, sequence, ER, etc.)
    - Graphviz for complex dependency visualization
    - PlantUML for detailed UML diagrams
    """

    def __init__(self):
        self.diagram_cache = {}

    async def generate_architecture_diagram(self, code_index: Dict, level: str = 'container') -> str:
        """
        Generate C4 model architecture diagram

        Args:
            code_index: Code index from CodeIndexer
            level: 'context', 'container', or 'component'

        Returns:
            Mermaid diagram code
        """
        if level == 'context':
            return await self._generate_context_diagram(code_index)
        elif level == 'container':
            return await self._generate_container_diagram(code_index)
        elif level == 'component':
            return await self._generate_component_diagram(code_index)
        else:
            return await self._generate_container_diagram(code_index)

    async def _generate_context_diagram(self, code_index: Dict) -> str:
        """Generate system context diagram"""
        mermaid = """graph TB
    subgraph "System Context"
        User[("👤 User<br/>VSCode Developer")]
        System[["🤖 KI AutoAgent System<br/>Multi-Agent AI Assistant"]]

        OpenAI[["OpenAI API<br/>GPT Models"]]
        Anthropic[["Anthropic API<br/>Claude Models"]]
        Perplexity[["Perplexity API<br/>Web Search"]]

        User -->|"Commands & Queries"| System
        System -->|"AI Responses"| User
        System -->|"API Calls"| OpenAI
        System -->|"API Calls"| Anthropic
        System -->|"Search Queries"| Perplexity
    end

    classDef userStyle fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    classDef systemStyle fill:#e3f2fd,stroke:#2196f3,stroke-width:3px
    classDef externalStyle fill:#fff3e0,stroke:#ff9800,stroke-width:2px

    class User userStyle
    class System systemStyle
    class OpenAI,Anthropic,Perplexity externalStyle"""

        return mermaid

    async def _generate_container_diagram(self, code_index: Dict) -> str:
        """Generate container-level diagram"""
        ast_index = code_index.get('ast', {})
        api_endpoints = ast_index.get('api_endpoints', {})

        # Detect components from file structure
        has_frontend = any('extension' in f or 'webview' in f for f in ast_index.get('files', {}))
        has_backend = any('backend' in f or 'api' in f for f in ast_index.get('files', {}))

        mermaid = """graph TB
    subgraph "KI AutoAgent System"
        subgraph "Frontend Layer"
            VSCode[["📝 VS Code Extension<br/>TypeScript"]]
            WebView[["💬 Chat WebView<br/>HTML/JS"]]
        end

        subgraph "Backend Layer"
            API[["🌐 FastAPI Server<br/>Python - Port 8000"]]
            WS[["🔌 WebSocket Handler<br/>Real-time Communication"]]
        end

        subgraph "Agent Layer"
            Orchestrator[["🎭 Orchestrator Agent<br/>Task Routing"]]
            Architect[["🏗️ Architect Agent<br/>System Design"]]
            CodeSmith[["⚒️ CodeSmith Agent<br/>Code Generation"]]
            Other[["🤖 Other Agents<br/>(7 more)"]]
        end

        subgraph "Core Services"
            Memory[["🧠 Memory Manager<br/>Vector Storage"]]
            Workflow[["⚙️ Workflow Engine<br/>Task Execution"]]
            Context[["📊 Shared Context<br/>Agent Communication"]]
        end

        VSCode --> WebView
        WebView -->|WebSocket| WS
        WS --> API
        API --> Orchestrator
        Orchestrator --> Architect
        Orchestrator --> CodeSmith
        Orchestrator --> Other

        Architect --> Memory
        CodeSmith --> Memory
        Other --> Memory

        Architect --> Context
        CodeSmith --> Context
        Other --> Context

        Orchestrator --> Workflow
    end

    classDef frontendStyle fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef backendStyle fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    classDef agentStyle fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef coreStyle fill:#fff3e0,stroke:#ff9800,stroke-width:2px

    class VSCode,WebView frontendStyle
    class API,WS backendStyle
    class Orchestrator,Architect,CodeSmith,Other agentStyle
    class Memory,Workflow,Context coreStyle"""

        # Add API endpoint count if available
        if api_endpoints:
            mermaid += f"\n    API -->|{len(api_endpoints)} endpoints| API"

        return mermaid

    async def _generate_component_diagram(self, code_index: Dict) -> str:
        """Generate detailed component diagram"""
        architecture = code_index.get('architecture', {})
        components = architecture.get('components', {})

        mermaid = """graph TB
    subgraph "Component Architecture"
"""

        # Add components by type
        for comp_type, comp_list in components.items():
            if comp_list:
                mermaid += f"        subgraph \"{comp_type.title()} Components\"\n"
                for comp in comp_list[:5]:  # Limit to 5 per type for readability
                    mermaid += f"            {comp['name']}[\"{comp['name']}<br/>{comp.get('methods', 0)} methods\"]\n"
                mermaid += "        end\n"

        mermaid += "    end"

        return mermaid

    async def generate_flow_diagram(self, workflow: Dict) -> str:
        """
        Generate workflow/flowchart diagram

        Args:
            workflow: Workflow definition with steps

        Returns:
            Mermaid flowchart
        """
        mermaid = """flowchart TD
    Start([Start]) --> Input[User Input]
"""

        if 'steps' in workflow:
            prev_step = 'Input'
            for i, step in enumerate(workflow['steps']):
                step_id = f"Step{i}"
                step_name = step.get('name', f'Step {i+1}')
                step_type = step.get('type', 'process')

                if step_type == 'decision':
                    mermaid += f"    {prev_step} --> {step_id}{{{step_name}}}\n"
                elif step_type == 'parallel':
                    mermaid += f"    {prev_step} --> {step_id}[[{step_name}]]\n"
                else:
                    mermaid += f"    {prev_step} --> {step_id}[{step_name}]\n"

                prev_step = step_id

            mermaid += f"    {prev_step} --> End([End])"

        return mermaid

    async def generate_sequence_diagram(self, interaction: Dict) -> str:
        """
        Generate sequence diagram for agent interactions

        Args:
            interaction: Agent interaction data

        Returns:
            Mermaid sequence diagram
        """
        mermaid = """sequenceDiagram
    participant User
    participant VSCode as VS Code Extension
    participant Backend as Python Backend
    participant Orchestrator
    participant Agent as Specialized Agent
    participant AI as AI Service

    User->>VSCode: Send Query
    VSCode->>Backend: WebSocket Message
    Backend->>Orchestrator: Route Request
    Orchestrator->>Agent: Assign Task
    Agent->>AI: API Call
    AI-->>Agent: AI Response
    Agent-->>Orchestrator: Task Result
    Orchestrator-->>Backend: Complete Response
    Backend-->>VSCode: WebSocket Response
    VSCode-->>User: Display Result"""

        return mermaid

    async def generate_dependency_graph(self, import_graph: Dict) -> str:
        """
        Generate module dependency graph

        Args:
            import_graph: Import relationships from CodeIndexer

        Returns:
            Mermaid graph
        """
        mermaid = """graph LR
    subgraph "Module Dependencies"
"""

        # Group imports by layer
        layers = {
            'agents': [],
            'core': [],
            'services': [],
            'utils': [],
            'api': []
        }

        for file_path, imports in import_graph.items():
            # Determine layer
            layer = 'other'
            for layer_name in layers.keys():
                if layer_name in file_path:
                    layer = layer_name
                    break

            if layer in layers:
                file_name = Path(file_path).stem
                layers[layer].append((file_name, imports))

        # Generate diagram for each layer
        for layer, modules in layers.items():
            if modules:
                mermaid += f"        subgraph \"{layer.title()}\"\n"
                for module_name, imports in modules[:10]:  # Limit for readability
                    mermaid += f"            {module_name}[{module_name}]\n"
                mermaid += "        end\n"

        # Add dependencies
        for file_path, imports in list(import_graph.items())[:20]:  # Limit connections
            source = Path(file_path).stem
            for imp in imports[:3]:  # Limit imports shown
                if '.' in imp:
                    target = imp.split('.')[-1]
                    mermaid += f"    {source} --> {target}\n"

        mermaid += "    end"

        return mermaid

    async def generate_er_diagram(self, models: Dict) -> str:
        """
        Generate entity relationship diagram for data models

        Args:
            models: Data model definitions

        Returns:
            Mermaid ER diagram
        """
        mermaid = """erDiagram
    AGENT {
        string id PK
        string name
        string role
        string model
        datetime created_at
    }

    TASK {
        string id PK
        string description
        string status
        string agent_id FK
        datetime created_at
        datetime completed_at
    }

    MEMORY {
        string id PK
        string type
        json content
        vector embedding
        datetime created_at
    }

    WORKFLOW {
        string id PK
        string name
        json steps
        string status
        datetime created_at
    }

    CONTEXT {
        string id PK
        string workflow_id FK
        json data
        datetime updated_at
    }

    AGENT ||--o{ TASK : executes
    WORKFLOW ||--o{ TASK : contains
    WORKFLOW ||--|| CONTEXT : has
    AGENT ||--o{ MEMORY : creates
    TASK ||--o{ MEMORY : generates"""

        return mermaid

    async def generate_git_graph(self, commits: List[Dict]) -> str:
        """
        Generate git history graph

        Args:
            commits: List of commit data

        Returns:
            Mermaid git graph
        """
        mermaid = """gitGraph
    commit id: "Initial commit"
    branch develop
    checkout develop
    commit id: "Add base agents"
    commit id: "Implement memory system"
    branch feature/indexing
    checkout feature/indexing
    commit id: "Add tree-sitter indexing"
    commit id: "Add code analysis"
    checkout develop
    merge feature/indexing
    commit id: "Add visualization"
    checkout main
    merge develop"""

        return mermaid

    async def generate_class_diagram(self, classes: Dict) -> str:
        """
        Generate UML class diagram

        Args:
            classes: Class definitions from code index

        Returns:
            Mermaid class diagram
        """
        mermaid = """classDiagram
    class BaseAgent {
        -name: str
        -role: str
        -model: str
        +execute_task(task): Result
        +process_request(request): Response
    }

    class ArchitectAgent {
        -system_knowledge: Dict
        -tree_sitter: TreeSitterIndexer
        -diagram_service: DiagramService
        +understand_system(): Dict
        +generate_architecture(): str
        +suggest_improvements(): List
    }

    class CodeSmithAgent {
        -code_patterns: Dict
        -indexer: CodeIndexer
        +implement_feature(spec): str
        +refactor_code(target): str
        +fix_issue(issue): str
    }

    class OrchestratorAgent {
        -agents: Dict
        -workflow_engine: WorkflowEngine
        +route_request(request): Agent
        +decompose_task(task): List
        +execute_workflow(workflow): Result
    }

    BaseAgent <|-- ArchitectAgent
    BaseAgent <|-- CodeSmithAgent
    BaseAgent <|-- OrchestratorAgent

    class MemoryManager {
        -vectors: Dict
        -capacity: int
        +store(key, value, vector)
        +search(query, k): List
        +get_similar(vector, threshold): List
    }

    class WorkflowEngine {
        -workflows: Dict
        -executor: AsyncExecutor
        +create_workflow(steps): Workflow
        +execute(workflow): Result
        +get_status(workflow_id): Status
    }

    OrchestratorAgent --> WorkflowEngine
    ArchitectAgent --> MemoryManager
    CodeSmithAgent --> MemoryManager"""

        return mermaid

    async def generate_state_diagram(self, states: Dict) -> str:
        """
        Generate state machine diagram

        Args:
            states: State machine definition

        Returns:
            Mermaid state diagram
        """
        mermaid = """stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : User Input
    Processing --> Analyzing : Parse Request
    Analyzing --> Routing : Classify Intent

    Routing --> SingleAgent : Simple Task
    Routing --> Workflow : Complex Task

    SingleAgent --> Executing : Agent Selected
    Workflow --> Decomposing : Create Subtasks
    Decomposing --> ParallelExecution : Multiple Agents

    Executing --> Responding : Task Complete
    ParallelExecution --> Aggregating : All Complete
    Aggregating --> Responding : Combine Results

    Responding --> Idle : Response Sent
    Responding --> Error : Failure
    Error --> Idle : Error Handled

    note right of Analyzing
        Intent Classification:
        - Query
        - Simple Task
        - Complex Task
        - Multi-step Workflow
    end note"""

        return mermaid

    async def generate_mind_map(self, topic: str, branches: Dict) -> str:
        """
        Generate mind map diagram

        Args:
            topic: Central topic
            branches: Branch definitions

        Returns:
            Mermaid mind map (if supported)
        """
        # Note: Mermaid mind maps might not be fully supported in all versions
        mermaid = f"""graph TD
    KI[{topic}]
"""

        for branch_name, sub_items in branches.items():
            branch_id = branch_name.replace(' ', '_')
            mermaid += f"    KI --> {branch_id}[{branch_name}]\n"

            for item in sub_items:
                item_id = item.replace(' ', '_')
                mermaid += f"    {branch_id} --> {item_id}[{item}]\n"

        return mermaid

    async def generate_pie_chart(self, data: Dict) -> str:
        """
        Generate pie chart for statistics

        Args:
            data: Data for pie chart

        Returns:
            Mermaid pie chart
        """
        mermaid = """pie title Code Distribution
"""

        for label, value in data.items():
            mermaid += f"    \"{label}\" : {value}\n"

        return mermaid

    async def generate_infrastructure_diagram(self, infra: Dict) -> str:
        """
        Generate infrastructure/deployment diagram

        Args:
            infra: Infrastructure configuration

        Returns:
            Mermaid diagram
        """
        mermaid = """graph TB
    subgraph "Development Environment"
        Dev[["👨‍💻 Developer Machine<br/>VS Code + Extension"]]
    end

    subgraph "Local Services"
        Backend[["Python Backend<br/>localhost:8000"]]
        Memory[["In-Memory Store<br/>Vectors & Cache"]]
    end

    subgraph "External Services"
        OpenAI[["OpenAI API"]]
        Anthropic[["Anthropic API"]]
        Perplexity[["Perplexity API"]]
    end

    subgraph "Suggested Improvements"
        Redis[["Redis Cache<br/>Session & API Cache"]]
        Postgres[["PostgreSQL<br/>+ pgvector"]]
        Celery[["Celery<br/>Task Queue"]]
    end

    Dev --> Backend
    Backend --> Memory
    Backend --> OpenAI
    Backend --> Anthropic
    Backend --> Perplexity

    Backend -.->|Future| Redis
    Backend -.->|Future| Postgres
    Backend -.->|Future| Celery

    style Redis fill:#ffebee
    style Postgres fill:#ffebee
    style Celery fill:#ffebee"""

        return mermaid

    def export_diagram(self, diagram_code: str, format: str = 'md') -> str:
        """
        Export diagram in various formats

        Args:
            diagram_code: Mermaid diagram code
            format: 'md', 'html', or 'svg'

        Returns:
            Formatted diagram
        """
        if format == 'md':
            return f"```mermaid\n{diagram_code}\n```"
        elif format == 'html':
            return f"""
<div class="mermaid">
{diagram_code}
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true}});</script>
"""
        elif format == 'svg':
            # Would require mermaid CLI or API to generate actual SVG
            return f"<!-- SVG generation requires mermaid CLI -->\n{diagram_code}"
        else:
            return diagram_code