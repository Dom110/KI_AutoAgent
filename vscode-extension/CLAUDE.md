# 🤖 KI AutoAgent VS Code Extension - Development Guide

**Comprehensive development documentation for the KI AutoAgent VS Code Extension**

> **⚠️ VERSION MANAGEMENT RULE**: Bei jeder Anpassung der Extension MUSS die Versionsnummer in `package.json` erhöht und diese Dokumentation aktualisiert werden.

---

## 📊 Project Status & Version Information

### Current Version: **1.0.1** (2025-01-12)

**Key Properties:**
- **Extension ID**: `ki-autoagent-vscode`
- **Publisher**: `ki-autoagent`
- **Display Name**: `KI AutoAgent`
- **VS Code Engine**: `^1.90.0`
- **License**: MIT
- **Repository**: KI_AutoAgent/vscode-extension/

**Recent Changes (v1.0.1):**
- ✅ Claude Pro Web Integration via browser sessions
- ✅ Service Mode Selection (web/api)
- ✅ Claude Max Plan support with higher rate limits
- ✅ Enhanced error handling and user guidance
- ✅ Dynamic service switching between API and web modes

---

## 🏗️ Extension Architecture

### Core Components

```
vscode-extension/
├── 📁 src/
│   ├── 🎛️ extension.ts                    # Main extension entry point
│   ├── 🤖 agents/                         # Multi-agent system
│   │   ├── base/ChatAgent.ts                # Base agent class
│   │   ├── OrchestratorAgent.ts            # Universal orchestrator (@ki)
│   │   ├── ArchitectAgent.ts               # System architect (@architect)
│   │   ├── CodeSmithAgent.ts               # Python developer (@codesmith)
│   │   ├── TradeStratAgent.ts              # Trading expert (@tradestrat)
│   │   └── ResearchAgent.ts                # Research analyst (@research)
│   ├── 🔧 core/
│   │   └── VSCodeMasterDispatcher.ts       # Workflow orchestration
│   ├── 🛠️ utils/
│   │   ├── OpenAIService.ts                # GPT-4o integration
│   │   ├── AnthropicService.ts             # Claude 3.5 Sonnet (API)
│   │   ├── ClaudeWebService.ts             # Claude Pro web integration
│   │   ├── WebSearchService.ts             # Perplexity research
│   │   └── errorHandler.ts                 # Error handling utilities
│   └── 📋 types/
│       └── index.ts                        # TypeScript interfaces
├── 📄 package.json                        # Extension manifest & configuration
├── 📄 tsconfig.json                       # TypeScript configuration
├── 🛠️ scripts/
│   └── build.sh                           # Dynamic build & packaging script
├── 📚 README.md                          # User documentation
├── 📝 CHANGELOG.md                       # Version history
├── 🔧 DEVELOPMENT.md                     # Developer setup guide
└── 🤖 CLAUDE.md                         # This file
```

---

## 🎯 Multi-Agent Chat System

### Agent Registration Pattern

Each agent follows the VS Code Chat Participant API:

```typescript
// 1. Define in package.json
"chatParticipants": [
  {
    "id": "ki-autoagent.agent-name",
    "name": "agent-name", 
    "fullName": "Agent Display Name",
    "description": "Agent description",
    "isSticky": false,
    "commands": [...]
  }
]

// 2. Register in extension.ts
const agent = new AgentClass(context, dispatcher);
context.subscriptions.push(agent.register());

// 3. Implement ChatAgent base class
export class AgentClass extends ChatAgent {
  protected async handleRequest(
    request: vscode.ChatRequest,
    context: vscode.ChatContext, 
    stream: vscode.ChatResponseStream,
    token: vscode.CancellationToken
  ): Promise<void> {
    // Agent logic here
  }
}
```

### Current Agent Lineup (7 Agents)

| Agent ID | Chat Name | Model | Primary Function |
|----------|-----------|--------|------------------|
| `ki-autoagent.orchestrator` | `@ki` | GPT-4o | Universal task routing & orchestration |
| `ki-autoagent.architect` | `@architect` | GPT-4o | System architecture & design patterns |
| `ki-autoagent.codesmith` | `@codesmith` | Claude 3.5 | Python/web development & implementation |
| `ki-autoagent.tradestrat` | `@tradestrat` | Claude 3.5 | Trading strategy development & analysis |
| `ki-autoagent.research` | `@research` | Perplexity Pro | Web research & information gathering |
| `ki-autoagent.docu` | `@docu` | GPT-4o | Technical documentation creation |
| `ki-autoagent.reviewer` | `@reviewer` | GPT-4o-mini | Code review & security analysis |

---

## 🌐 Service Architecture: API vs Web Modes

### Dual Service Support

The extension supports two service modes for AI model access:

#### 🔑 **API Mode** (Traditional)
```typescript
// Direct API integration
const anthropicService = new AnthropicService();
const response = await anthropicService.chat(messages);
```

**Configuration:**
- `kiAutoAgent.serviceMode`: `"api"`
- `kiAutoAgent.openai.apiKey`: Required for GPT models
- `kiAutoAgent.anthropic.apiKey`: Required for Claude models
- `kiAutoAgent.perplexity.apiKey`: Required for research

**Pros:** Fast response times, full API control
**Cons:** Additional API costs beyond existing subscriptions

#### 🌐 **Web Mode** (Recommended)
```typescript
// Claude Pro web integration via proxy
const claudeWebService = new ClaudeWebService();
const response = await claudeWebService.chat(messages);
```

**Configuration:**
- `kiAutoAgent.serviceMode`: `"web"` (default)
- `kiAutoAgent.claudeWeb.serverUrl`: Proxy server URL (default: localhost:8000)
- `kiAutoAgent.claudeWeb.planType`: `"pro"` or `"max"` for rate limits
- `kiAutoAgent.claudeWeb.autoStart`: Auto-start proxy server option

**Pros:** Uses existing Claude Pro/Max plan, no additional API costs
**Cons:** Requires claude_web_proxy server, slightly slower responses

### Dynamic Service Selection

Agents automatically detect and use the configured service mode:

```typescript
// Service configuration validation
private async validateServiceConfig(stream?: vscode.ChatResponseStream): Promise<boolean> {
  const config = vscode.workspace.getConfiguration('kiAutoAgent');
  const serviceMode = config.get<string>('serviceMode', 'web');

  if (serviceMode === 'api') {
    // Validate API keys
    if (!config.get<string>('anthropic.apiKey')) {
      stream?.markdown('❌ API key required for API mode');
      return false;
    }
  } else if (serviceMode === 'web') {
    // Test web service connection
    const isAvailable = await this.claudeWebService.testConnection();
    if (!isAvailable) {
      const status = await this.claudeWebService.getServerStatus();
      stream?.markdown(`❌ Web service unavailable: ${status.error}`);
      return false;
    }
  }
  return true;
}

// Dynamic service getter
private async getClaudeService(): Promise<{ chat: (messages: any[]) => Promise<string> }> {
  const serviceMode = vscode.workspace.getConfiguration('kiAutoAgent').get<string>('serviceMode', 'web');
  
  return serviceMode === 'web' 
    ? { chat: (messages) => this.claudeWebService.chat(messages) }
    : { chat: (messages) => this.anthropicService.chat(messages) };
}
```

---

## ⚙️ Configuration System

### Extension Settings Schema

Located in `package.json` → `contributes.configuration.properties`:

```json
{
  "kiAutoAgent.serviceMode": {
    "type": "string",
    "enum": ["api", "web"],
    "default": "web",
    "description": "Service mode: 'api' for API keys, 'web' for Claude Pro web session"
  },
  "kiAutoAgent.claudeWeb.enabled": {
    "type": "boolean", 
    "default": true,
    "description": "Enable Claude Pro web integration"
  },
  "kiAutoAgent.claudeWeb.serverUrl": {
    "type": "string",
    "default": "http://localhost:8000",
    "description": "Claude Web Proxy server URL"
  },
  "kiAutoAgent.claudeWeb.planType": {
    "type": "string",
    "enum": ["pro", "max"],
    "default": "pro", 
    "description": "Claude plan type for rate limit optimization"
  }
}
```

### Configuration Access Pattern

```typescript
// Get configuration in agents
const config = vscode.workspace.getConfiguration('kiAutoAgent');
const serviceMode = config.get<string>('serviceMode', 'web');
const serverUrl = config.get<string>('claudeWeb.serverUrl', 'http://localhost:8000');
const planType = config.get<string>('claudeWeb.planType', 'pro');
```

---

## 🔄 Build & Deployment System

### Dynamic Build Script

The `scripts/build.sh` automatically handles version management:

```bash
#!/bin/bash
# Get version from package.json dynamically
VERSION=$(node -p "require('./package.json').version")
print_status "Extension version: $VERSION"

# Package with correct version
vsce package --out ki-autoagent-vscode-$VERSION.vsix

# Install with version-specific name
code --install-extension ki-autoagent-vscode-$VERSION.vsix --force
```

**Usage:**
```bash
cd vscode-extension
./scripts/build.sh
# Automatically uses current package.json version
```

### Version Workflow

1. **Update version in package.json**:
   ```json
   {
     "version": "1.0.2"  // Increment appropriately
   }
   ```

2. **Update CHANGELOG.md** with new features

3. **Run build script**:
   ```bash
   ./scripts/build.sh
   ```

4. **Test thoroughly** before distribution

---

## 🧪 Development & Testing

### TypeScript Configuration

**tsconfig.json settings:**
```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "out",
    "rootDir": "src",
    "sourceMap": true,
    "useUnknownInCatchVariables": false  // For error handling compatibility
  }
}
```

### Error Handling Pattern

```typescript
// Consistent error handling with type assertions
try {
  const response = await apiCall();
  return response;
} catch (error) {
  const errorMessage = (error as any).message || 'Unknown error';
  throw new Error(`Operation failed: ${errorMessage}`);
}
```

### Local Development Setup

```bash
# 1. Install dependencies
npm install

# 2. Compile TypeScript
npm run compile

# 3. Watch mode for development  
npm run watch

# 4. Open Extension Development Host
# Press F5 in VS Code to launch Extension Development Host
```

### Testing Checklist

Before releasing any version:

- [ ] **Compilation**: `npm run compile` succeeds without errors
- [ ] **Service Modes**: Test both API and web modes work correctly  
- [ ] **Agent Functionality**: Each agent responds appropriately to test prompts
- [ ] **Error Handling**: Invalid configurations show helpful error messages
- [ ] **Settings UI**: VS Code settings UI displays correctly
- [ ] **Performance**: Agents respond within reasonable timeframes
- [ ] **Documentation**: README and CHANGELOG are updated

---

## 📝 VERSION MANAGEMENT RULES

### 🔴 CRITICAL: Version Update Protocol

**EVERY extension change requires version update:**

1. **Increment version in package.json**:
   ```bash
   # For bug fixes (1.0.1 → 1.0.2)
   # For new features (1.0.1 → 1.1.0)  
   # For breaking changes (1.0.1 → 2.0.0)
   ```

2. **Update CHANGELOG.md** with specific changes

3. **Update this CLAUDE.md** with new version info

4. **Test thoroughly** with `./scripts/build.sh`

5. **Commit with descriptive message**:
   ```bash
   git commit -m "feat: add Claude Max plan support - v1.0.1"
   ```

### Version Numbering Convention

- **Major (X.0.0)**: Breaking changes, architecture overhauls
- **Minor (1.X.0)**: New features, new agents, significant enhancements  
- **Patch (1.0.X)**: Bug fixes, configuration updates, documentation

### Automated Version Tracking

The build script automatically:
- ✅ Reads version from package.json
- ✅ Creates versioned VSIX file name
- ✅ Uses correct version in installation
- ✅ Displays version in build output

**Never hardcode version numbers in scripts or documentation!**

---

## 🤝 Adding New Agents

### Step-by-Step Agent Creation

1. **Create agent class** in `src/agents/`:
```typescript
// src/agents/MyNewAgent.ts
import { ChatAgent } from './base/ChatAgent';

export class MyNewAgent extends ChatAgent {
  constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
    const config: AgentConfig = {
      participantId: 'ki-autoagent.mynew',
      name: 'mynew',
      fullName: 'My New Agent',
      description: 'Agent description',
      model: 'gpt-4o',
      capabilities: ['capability1', 'capability2']
    };
    super(config, context, dispatcher);
  }

  protected async handleRequest(
    request: vscode.ChatRequest,
    context: vscode.ChatContext,
    stream: vscode.ChatResponseStream,
    token: vscode.CancellationToken
  ): Promise<void> {
    // Implementation here
  }
}
```

2. **Register in package.json**:
```json
{
  "chatParticipants": [
    {
      "id": "ki-autoagent.mynew",
      "name": "mynew",
      "fullName": "My New Agent", 
      "description": "Agent description"
    }
  ],
  "activationEvents": [
    "onChatParticipant:ki-autoagent.mynew"
  ]
}
```

3. **Register in extension.ts**:
```typescript
import { MyNewAgent } from './agents/MyNewAgent';

export function activate(context: vscode.ExtensionContext) {
  const dispatcher = new VSCodeMasterDispatcher(context);
  
  const agents = [
    // ... existing agents
    new MyNewAgent(context, dispatcher)
  ];

  agents.forEach(agent => {
    context.subscriptions.push(agent.register());
  });
}
```

4. **Update version and rebuild**:
```bash
# Update package.json version (minor increment for new agent)
# Update CHANGELOG.md with new agent info
./scripts/build.sh
```

---

## 🔍 Troubleshooting Guide

### Common Development Issues

#### TypeScript Compilation Errors
```bash
# Error: TS18046: 'error' is of type 'unknown'
# Solution: Add type assertion (error as any).message

# Error: Cannot find module
# Solution: Check imports and run npm install
```

#### Extension Not Loading
```bash
# Check VS Code Developer Console (Help → Toggle Developer Tools)
# Look for activation errors
# Verify package.json syntax is valid JSON
```

#### Agent Not Responding  
```bash
# Check service configuration in VS Code settings
# Verify API keys or web service connection
# Check VS Code Output panel for error messages
```

#### Build Script Issues
```bash
# Ensure you're in vscode-extension directory
cd vscode-extension

# Make script executable
chmod +x scripts/build.sh

# Check Node.js and npm versions
node --version  # Should be 14+ 
npm --version   # Should be 6+
```

### Debug Mode

Enable verbose logging:
```bash
# Set in VS Code settings
"kiAutoAgent.enableLogging": true

# Or via environment
export KI_AUTOAGENT_DEBUG=true
code
```

---

## 📚 Resources & Documentation

### Key Files to Understand

1. **package.json**: Extension manifest, agent definitions, settings schema
2. **extension.ts**: Main entry point, agent registration
3. **ChatAgent.ts**: Base class for all agents, common functionality
4. **ClaudeWebService.ts**: Claude Pro web integration implementation
5. **build.sh**: Dynamic build and packaging script

### VS Code Extension API References

- [Chat Extensions](https://code.visualstudio.com/api/extension-guides/chat)
- [Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest)
- [Configuration Schema](https://code.visualstudio.com/api/references/contribution-points#contributes.configuration)
- [Activation Events](https://code.visualstudio.com/api/references/activation-events)

### External Dependencies

- **VS Code**: `^1.90.0` (minimum supported version)
- **TypeScript**: `^5.0.0` (development)
- **OpenAI SDK**: `^4.0.0` (GPT models)
- **Anthropic SDK**: `^0.24.0` (Claude models)
- **Axios**: `^1.6.0` (HTTP client for web services)

---

## 🎯 Roadmap & Future Development

### Version 1.1 (Planned)
- [ ] **Enhanced Web Integration**: Auto-start claude_web_proxy server
- [ ] **Workflow Templates**: Pre-configured agent workflows for common tasks
- [ ] **Agent Statistics**: Performance metrics and usage analytics
- [ ] **Custom Commands**: User-defined agent commands and shortcuts

### Version 1.2 (Planned)
- [ ] **Team Collaboration**: Shared agent configurations and workflows
- [ ] **Extension API**: Allow other extensions to integrate with agents
- [ ] **Advanced Context**: Better workspace understanding and memory
- [ ] **Mobile Support**: Companion mobile app integration

### Long-term Vision
- [ ] **AI-Powered Extension Development**: Agents that can create and modify VS Code extensions
- [ ] **Natural Language Workflows**: Create complex automations through conversation
- [ ] **Multi-IDE Support**: Expand beyond VS Code to other editors
- [ ] **Cloud Sync**: Synchronize configurations and workflows across devices

---

## 📄 License & Contributing

**License**: MIT License - See [LICENSE](../LICENSE) for details

**Contributing Guidelines**:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/agent-name`
3. Follow TypeScript and VS Code extension best practices
4. Add tests for new functionality
5. Update documentation (README, CHANGELOG, this file)
6. **CRITICAL**: Increment version number in package.json
7. Submit pull request with detailed description

**Code Standards**:
- Use TypeScript strict mode
- Follow VS Code extension API patterns
- Implement proper error handling with user-friendly messages
- Add JSDoc comments for public methods
- Maintain backwards compatibility when possible

---

**🤖 Generated and maintained by KI AutoAgent System**
*Last updated: 2025-01-12 - Version 1.0.1*

> Remember: **Every change requires version increment and documentation update!**