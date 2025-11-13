# 🤖 KI AutoAgent VS Code Extension

**Universal Multi-Agent AI Development Platform for VS Code**

Transform your VS Code into an AI-powered development environment with 8 specialized agents that automatically orchestrate to solve complex development tasks.

## 🌟 Features

- **🧠 Universal Orchestrator**: AI that automatically routes tasks to the best specialized agent
- **🎯 8 Specialized Agents**: Each expert in their domain
- **⚖️ Supreme Arbitrator**: OpusArbitrator powered by Claude Opus 4.1 for conflict resolution
- **🔄 Intelligent Workflows**: Multi-step development processes 
- **📁 Workspace-Aware**: Understands your project context
- **⚡ One-Click Actions**: Create files, apply fixes, run tests directly from chat
- **🎛️ Modern AI Models**: GPT-4o, Claude 3.5 Sonnet, Perplexity Pro
- **🌐 Claude Pro Integration**: Use your Claude Pro account via web sessions (no API costs!)

## 🤖 Meet Your AI Team

| Agent | Expertise | AI Model | Use Cases |
|-------|-----------|----------|-----------|
| **@ki** | Universal Orchestrator | GPT-4o | Routes tasks to optimal agents |
| **@richter** | Supreme Judge | Claude Opus 4.1 | **Conflict resolution, final decisions** |
| **@architect** | System Architecture | GPT-4o | Design patterns, tech stack planning |
| **@codesmith** | Implementation | Claude Sonnet 4 | Python, web dev, testing |
| **@docu** | Documentation | GPT-4o | READMEs, API docs, tutorials |
| **@reviewer** | Code Review | GPT-4o-mini | Security, performance, quality |
| **@fixer** | Bug Fixing | Claude Sonnet 4 | Debugging, optimization |
| **@tradestrat** | Trading Systems | Claude Sonnet 4 | RON strategy, backtesting |
| **@research** | Information Gathering | Perplexity Pro | Web research, documentation |

## 🚀 Quick Start

### 1. Installation

1. Install from VS Code Marketplace (coming soon)
2. Or install from VSIX:
   ```bash
   code --install-extension ki-autoagent-vscode-1.0.2.vsix
   ```

### 2. Choose Your Service Mode

**Option A: Claude Pro Web Integration (Recommended - No API costs!)**
1. Open VS Code Settings (`Ctrl+,`)
2. Search for "KI AutoAgent" 
3. Set `Service Mode` to **"web"**
4. Start Claude Web Proxy server:
   ```bash
   # Make sure you're logged into Claude.ai in your browser
   cd /your/KI_AutoAgent/directory
   python -m uvicorn claude_web_proxy.fastapi_server:app --host 0.0.0.0 --port 8000
   ```

**Option B: API Keys Mode**
1. Open VS Code Settings (`Ctrl+,`)
2. Search for "KI AutoAgent"
3. Set `Service Mode` to **"api"**
4. Configure your API keys:
   - **OpenAI API Key** (for GPT models)
   - **Anthropic API Key** (for Claude models)  
   - **Perplexity API Key** (for research)

### 3. Start Coding with AI

1. Open VS Code Chat panel (`Ctrl+Shift+I`)
2. Type `@ki` followed by your request
3. Watch as AI agents collaborate to solve your task!

> 💡 **Pro Tip**: Web mode uses your Claude Pro account directly through browser sessions, so you get unlimited Claude 3.5 Sonnet usage without API costs!

## 💡 Usage Examples

### Universal Orchestrator
```
@ki create a REST API with FastAPI for user management
@ki implement a momentum trading strategy with backtesting
@ki debug this performance issue in my Python code
```

### Specialized Agents
```
@richter judge which approach is better: microservices vs monolith
@richter resolve this disagreement between @architect and @codesmith
@architect design a microservices architecture for e-commerce
@codesmith implement a Python class for data processing
@tradestrat create RON strategy with risk management
@fixer debug this error message and optimize performance
@research find the latest Python testing frameworks
```

### Auto-Routing Magic
Just describe what you need naturally:
```
"Build a trading bot with risk management"
"Create a React component for user authentication" 
"Fix the memory leak in this function"
```

The orchestrator automatically:
1. 🎯 Detects your intent
2. 🏗️ Identifies your project type
3. 👥 Selects optimal agents
4. 🔄 Creates multi-step workflow
5. ⚡ Executes and delivers results

## 🎯 Project Type Intelligence

KI AutoAgent automatically detects your project type and applies specialized workflows:

- **🏦 Trading Systems**: RON strategy validation, backtesting frameworks
- **🌐 Web APIs**: Security reviews, performance optimization  
- **📱 Frontend Apps**: Component patterns, state management
- **🔧 Generic Software**: Code quality, testing, documentation

## 🛠️ Key Capabilities

### Smart Code Generation
- Context-aware implementations
- Framework-specific patterns
- Automatic testing generation
- Documentation creation

### Intelligent Workflows
- Multi-agent collaboration
- Step-by-step execution
- Progress tracking
- Quality gates

### Workspace Integration
- File creation and editing
- Project structure analysis
- Current context awareness
- One-click apply suggestions

### Advanced Features
- Real-time collaboration between agents
- Automatic project type detection
- Quality gate enforcement
- Performance optimization

## ⚙️ Configuration

### Extension Settings

**Service Configuration:**
- `kiAutoAgent.serviceMode`: Choose "web" (Claude Pro) or "api" (API keys)
- `kiAutoAgent.claudeWeb.enabled`: Enable Claude Pro web integration
- `kiAutoAgent.claudeWeb.serverUrl`: Claude Web Proxy server URL (default: localhost:8000)
- `kiAutoAgent.claudeWeb.autoStart`: Auto-start proxy server
- `kiAutoAgent.claudeWeb.planType`: Claude plan type ("pro" or "max" for higher rate limits)

**API Configuration (for API mode):**
- `kiAutoAgent.openai.apiKey`: OpenAI API key
- `kiAutoAgent.anthropic.apiKey`: Anthropic API key  
- `kiAutoAgent.perplexity.apiKey`: Perplexity API key

**General Settings:**
- `kiAutoAgent.defaultModel`: Default AI model to use
- `kiAutoAgent.maxTokens`: Maximum tokens per request (100-32000)
- `kiAutoAgent.enableLogging`: Enable detailed logging

### Commands

- `Ki AutoAgent: Show Agent Statistics` - View performance metrics
- `Ki AutoAgent: Create File` - Create new files from AI suggestions
- `Ki AutoAgent: Insert at Cursor` - Insert code at current position

## 🏗️ Architecture

```
KI AutoAgent Extension
├── Universal Orchestrator (@ki)
│   ├── Intent Recognition
│   ├── Project Type Detection  
│   ├── Agent Selection
│   └── Workflow Orchestration
├── Specialized Agents
│   ├── ArchitectGPT
│   ├── CodeSmithClaude
│   ├── DocuBot
│   ├── ReviewerGPT
│   ├── FixerBot
│   ├── TradeStrat
│   └── ResearchBot
└── VS Code Integration
    ├── Chat Interface
    ├── File Operations
    ├── Workspace Context
    └── Action Buttons
```

## 🤝 Contributing

This extension is based on the open-source KI AutoAgent system. Contributions welcome!

1. Fork the repository
2. Create your feature branch
3. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/yourusername/KI_AutoAgent)
- [Documentation](https://docs.ki-autoagent.com)
- [Issue Tracker](https://github.com/yourusername/KI_AutoAgent/issues)

---

**Made with ❤️ by the KI AutoAgent Team**

*Transform your development workflow with AI-powered multi-agent assistance!*