# 🛠️ KI AutoAgent VS Code Extension - Development Guide

This guide helps you develop, test, and extend the KI AutoAgent VS Code Extension.

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and **npm**
- **VS Code** with Extension Development support
- **TypeScript** knowledge
- **API Keys** for OpenAI, Anthropic, and Perplexity

### Setup Development Environment

1. **Clone and Setup**
   ```bash
   cd vscode-extension
   npm install
   ```

2. **Start Development Mode**
   ```bash
   ./scripts/dev.sh
   ```
   This starts TypeScript compiler in watch mode.

3. **Launch Extension**
   - Press `F5` in VS Code to open Extension Development Host
   - Or use "Run Extension" from Run and Debug panel

4. **Test Your Changes**
   - Open Chat panel (`Ctrl+Shift+I`) in Extension Development Host
   - Test with: `@ki hello world`
   - Reload with `Ctrl+R` when you make changes

## 📁 Project Structure

```
vscode-extension/
├── 📄 package.json              # Extension manifest
├── 📄 tsconfig.json             # TypeScript configuration
├── 📂 src/
│   ├── 📄 extension.ts          # Main extension entry point
│   ├── 📂 agents/               # All AI agents
│   │   ├── 📂 base/             # Base classes
│   │   │   └── ChatAgent.ts     # Abstract base agent
│   │   ├── OrchestratorAgent.ts # Universal router
│   │   ├── ArchitectAgent.ts    # Architecture expert
│   │   ├── CodeSmithAgent.ts    # Implementation expert
│   │   └── TradeStratAgent.ts   # Trading expert
│   ├── 📂 core/                 # Core system
│   │   └── VSCodeMasterDispatcher.ts # Orchestration logic
│   ├── 📂 types/                # TypeScript definitions
│   │   └── index.ts             # All type definitions
│   └── 📂 utils/                # Utilities
│       ├── OpenAIService.ts     # GPT integration
│       └── AnthropicService.ts  # Claude integration
├── 📂 scripts/                  # Build and dev scripts
│   ├── build.sh                 # Production build
│   └── dev.sh                   # Development mode
└── 📂 .vscode/                  # VS Code configuration
    ├── launch.json              # Debug configuration
    ├── tasks.json               # Build tasks
    └── settings.json            # Workspace settings
```

## 🔧 Development Workflow

### Adding a New Agent

1. **Create Agent Class**
   ```typescript
   // src/agents/MyNewAgent.ts
   import { ChatAgent } from './base/ChatAgent';
   
   export class MyNewAgent extends ChatAgent {
       constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
           const config: AgentConfig = {
               participantId: 'ki-autoagent.mynew',
               name: 'mynew',
               fullName: 'My New Agent',
               // ... configuration
           };
           super(config, context, dispatcher);
       }
       
       protected async handleRequest(...) {
           // Implementation
       }
       
       protected async processWorkflowStep(...) {
           // Workflow step processing
       }
   }
   ```

2. **Register in Extension**
   ```typescript
   // src/extension.ts
   import { MyNewAgent } from './agents/MyNewAgent';
   
   // Add to agents array
   const agents = [
       new OrchestratorAgent(context, dispatcher),
       new MyNewAgent(context, dispatcher), // Add here
       // ... other agents
   ];
   ```

3. **Update Package.json**
   ```json
   {
     "contributes": {
       "chatParticipants": [
         {
           "id": "ki-autoagent.mynew",
           "name": "mynew",
           "fullName": "My New Agent",
           // ... configuration
         }
       ]
     }
   }
   ```

### Testing Your Agent

1. **Rebuild Extension**
   ```bash
   npm run compile
   ```

2. **Reload Extension Host**
   - `Ctrl+R` in Extension Development Host

3. **Test in Chat**
   ```
   @mynew test my new functionality
   ```

### Adding New Commands

1. **Define Command in Agent**
   ```typescript
   commands: [
       { 
           name: 'mycommand', 
           description: 'My custom command', 
           handler: 'handleMyCommand' 
       }
   ]
   ```

2. **Implement Handler**
   ```typescript
   private async handleMyCommand(
       prompt: string,
       stream: vscode.ChatResponseStream,
       token: vscode.CancellationToken
   ): Promise<void> {
       stream.progress('🔄 Processing...');
       // Implementation
       stream.markdown('Result here');
   }
   ```

3. **Test Command**
   ```
   @mynew /mycommand test input
   ```

## 🧪 Testing

### Manual Testing

1. **Start Development Host**
   ```bash
   # Terminal 1: Start compiler
   ./scripts/dev.sh
   
   # VS Code: Press F5 to launch Extension Development Host
   ```

2. **Test Scenarios**
   ```
   # Basic functionality
   @ki hello world
   
   # Agent routing
   @ki create a Python function
   @ki design a web API
   
   # Specific agents
   @architect design microservices
   @codesmith implement a class
   @tradestrat create RON strategy
   
   # Commands
   @architect /design create system architecture
   @codesmith /implement user authentication
   ```

3. **Test Configuration**
   - Open VS Code Settings
   - Search "KI AutoAgent"
   - Set test API keys
   - Verify agents can connect

### Debugging

1. **Extension Debugging**
   - Set breakpoints in TypeScript
   - Use "Run Extension" debug configuration
   - Check Debug Console for logs

2. **Agent Debugging**
   ```typescript
   // Add logging in agents
   this.log('Debug message', 'info');
   console.log('Direct console output');
   ```

3. **API Debugging**
   - Enable logging in settings
   - Check VS Code Output panel
   - Monitor network requests

## 🚀 Building and Packaging

### Development Build
```bash
npm run compile
```

### Production Build
```bash
./scripts/build.sh
```

This script:
1. Installs dependencies
2. Compiles TypeScript
3. Packages extension as `.vsix`
4. Optionally installs locally

### Manual Packaging
```bash
npm install -g vsce
vsce package
```

## 📊 Performance Optimization

### Best Practices

1. **Lazy Loading**
   - Only activate agents when needed
   - Use activationEvents sparingly

2. **Memory Management**
   - Dispose unused resources
   - Limit context size for AI requests

3. **API Efficiency**
   - Cache responses when appropriate
   - Use streaming for long responses
   - Implement rate limiting

### Performance Monitoring

```typescript
// Add performance tracking
const startTime = Date.now();
// ... operation
const duration = Date.now() - startTime;
this.log(`Operation took ${duration}ms`);
```

## 🔐 Security Considerations

### API Key Security

1. **Never hardcode API keys**
2. **Use VS Code's secure storage**
3. **Validate API keys before use**
4. **Handle API errors gracefully**

### Input Validation

```typescript
// Validate user input
if (!prompt || prompt.trim().length === 0) {
    stream.markdown('❌ Please provide a valid prompt');
    return;
}

// Sanitize file paths
const safePath = path.normalize(userProvidedPath);
if (!safePath.startsWith(workspaceRoot)) {
    throw new Error('Invalid file path');
}
```

## 🐛 Common Issues and Solutions

### TypeScript Compilation Errors

```bash
# Clean and rebuild
rm -rf out/
npm run compile
```

### Extension Not Loading

1. Check `package.json` syntax
2. Verify activation events
3. Check console for errors

### API Connection Issues

1. Verify API keys in settings
2. Check network connectivity
3. Test with minimal requests

### Chat Participant Not Appearing

1. Check participant ID uniqueness
2. Verify registration in `extension.ts`
3. Reload Extension Development Host

## 🔄 Extending the System

### Adding New AI Services

1. **Create Service Class**
   ```typescript
   // src/utils/NewAIService.ts
   export class NewAIService {
       async chat(messages: ChatMessage[]): Promise<string> {
           // Implementation
       }
   }
   ```

2. **Integrate in Agent**
   ```typescript
   private newAIService: NewAIService;
   
   constructor(...) {
       // ...
       this.newAIService = new NewAIService();
   }
   ```

### Custom Workflow Steps

```typescript
// Add to VSCodeMasterDispatcher
createWorkflow(intent: Intent, projectType: string): WorkflowStep[] {
    if (projectType === 'my_custom_type') {
        return [
            { id: 'custom_step', agent: 'mynew', description: 'Custom processing' }
        ];
    }
    // ... existing logic
}
```

## 📝 Contributing

1. **Fork Repository**
2. **Create Feature Branch**
3. **Follow Coding Standards**
   - Use TypeScript
   - Add proper error handling
   - Include logging
   - Update documentation

4. **Test Thoroughly**
5. **Submit Pull Request**

## 📚 Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [VS Code Chat Extension Guide](https://code.visualstudio.com/api/extension-guides/chat)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Reference](https://docs.anthropic.com/claude/reference)

---

**Happy coding! 🚀**

*Need help? Open an issue on GitHub or ask in our Discord community.*