/**
 * KI AutoAgent VS Code Extension
 * Main extension entry point that registers all chat participants
 */
import * as vscode from 'vscode';
import { VSCodeMasterDispatcher } from './core/VSCodeMasterDispatcher';
import { getClaudeCodeService } from './services/ClaudeCodeService';
import { AgentConfigurationManager } from './core/AgentConfigurationManager';
import { ArchitectAgent } from './agents/ArchitectAgent';
import { OrchestratorAgent } from './agents/OrchestratorAgent';
import { CodeSmithAgent } from './agents/CodeSmithAgent';
import { TradeStratAgent } from './agents/TradeStratAgent';
import { ResearchAgent } from './agents/ResearchAgent';
import { OpusArbitratorAgent } from './agents/OpusArbitratorAgent';
import { DocuBotAgent } from './agents/DocuBotAgent';
import { ReviewerGPTAgent } from './agents/ReviewerGPTAgent';
// import { FixerBotAgent } from './agents/FixerBotAgent'; // DEPRECATED - Functionality integrated into CodeSmithAgent
// Multi-Agent Chat UI Components
import { MultiAgentChatPanel } from './ui/MultiAgentChatPanel';
import { ChatWidget } from './ui/ChatWidget';

// Global output channel for debugging
let outputChannel: vscode.OutputChannel;

export async function activate(context: vscode.ExtensionContext) {
    // VERSION 2.3.9 - CLAUDE CODE CLI INTEGRATION (CORRECTED)
    console.log('🚀 KI AutoAgent v2.3.9: Extension activation started');
    
    // Create single output channel
    outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
    outputChannel.clear();
    outputChannel.show(true);
    
    outputChannel.appendLine('🚀 KI AutoAgent Extension v2.3.9 Activating');
    outputChannel.appendLine('============================================');
    outputChannel.appendLine(`Time: ${new Date().toLocaleString()}`);
    outputChannel.appendLine(`VS Code Version: ${vscode.version}`);
    outputChannel.appendLine('');
    outputChannel.appendLine('✨ NEW: Claude Code CLI integration - Install with: npm install -g @anthropic-ai/claude-code');

    try {
        // Initialize the Agent Configuration Manager
        outputChannel.appendLine('Initializing Agent Configuration Manager...');
        const configManager = AgentConfigurationManager.getInstance(context);
        await configManager.initialize();
        outputChannel.appendLine('✅ Agent Configuration Manager ready');

        // Initialize the master dispatcher
        outputChannel.appendLine('Initializing Master Dispatcher...');
        const dispatcher = new VSCodeMasterDispatcher(context);
        outputChannel.appendLine('✅ Master Dispatcher ready');
    
        // Initialize Chat Widget (Status Bar)
        outputChannel.appendLine('Initializing Chat Widget...');
        const chatWidget = new ChatWidget(context, dispatcher);
        outputChannel.appendLine('✅ Chat Widget ready');
    
    // Register chat panel commands with error handling
    const commandsToRegister = [
        {
            id: 'ki-autoagent.showChat',
            handler: () => MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher)
        },
        {
            id: 'ki-autoagent.toggleChat',
            handler: () => MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher)
        },
        {
            id: 'ki-autoagent.quickChat',
            handler: () => {
                MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher);
                vscode.window.showInformationMessage('🤖 KI AutoAgent Chat ready! Use @ki for universal assistance or specific agents like @richter, @architect, @codesmith');
            }
        },
        {
            id: 'ki-autoagent.clearUnread',
            handler: () => {
                if (!outputChannel) {
                    outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
                }
                outputChannel.clear();
                outputChannel.appendLine('Cleared messages');
            }
        }
    ];

    // Register commands with duplicate check
    for (const cmd of commandsToRegister) {
        try {
            const disposable = vscode.commands.registerCommand(cmd.id, cmd.handler);
            context.subscriptions.push(disposable);
            outputChannel.appendLine(`  ✅ Registered command: ${cmd.id}`);
        } catch (error) {
            outputChannel.appendLine(`  ⚠️ Command already exists: ${cmd.id} - skipping`);
        }
    }

    // Command registration complete
    outputChannel.appendLine('');

        // Initialize and register all agents 
        outputChannel.appendLine('\nCreating Agent Instances...');
        let agents = [];
        let agentCreationErrors = [];
        
        try {
            agents.push(new OrchestratorAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ OrchestratorAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ OrchestratorAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`OrchestratorAgent: ${error}`);
        }
        
        try {
            agents.push(new OpusArbitratorAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ OpusArbitratorAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ OpusArbitratorAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`OpusArbitratorAgent: ${error}`);
        }
        
        try {
            agents.push(new ArchitectAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ ArchitectAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ ArchitectAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`ArchitectAgent: ${error}`);
        }
        
        try {
            agents.push(new CodeSmithAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ CodeSmithAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ CodeSmithAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`CodeSmithAgent: ${error}`);
        }
        
        try {
            agents.push(new TradeStratAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ TradeStratAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ TradeStratAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`TradeStratAgent: ${error}`);
        }
        
        try {
            agents.push(new ResearchAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ ResearchAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ ResearchAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`ResearchAgent: ${error}`);
        }

        try {
            agents.push(new DocuBotAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ DocuBotAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ DocuBotAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`DocuBotAgent: ${error}`);
        }

        try {
            agents.push(new ReviewerGPTAgent(context, dispatcher));
            outputChannel.appendLine('  ✅ ReviewerGPTAgent created');
        } catch (error) {
            outputChannel.appendLine(`  ❌ ReviewerGPTAgent failed: ${(error as any).message}`);
            agentCreationErrors.push(`ReviewerGPTAgent: ${error}`);
        }

        // DEPRECATED: FixerBot functionality has been integrated into CodeSmithAgent
        // CodeSmith now handles: /fix, /debug, /refactor, /modernize commands
        // try {
        //     agents.push(new FixerBotAgent(context, dispatcher));
        //     outputChannel.appendLine('  ✅ FixerBotAgent created');
        // } catch (error) {
        //     outputChannel.appendLine(`  ❌ FixerBotAgent failed: ${(error as any).message}`);
        //     agentCreationErrors.push(`FixerBotAgent: ${error}`);
        // }

        outputChannel.appendLine(`Agent creation completed: ${agents.length} created, ${agentCreationErrors.length} errors`);
        
        if (agentCreationErrors.length > 0) {
            outputChannel.appendLine('Agent creation errors:');
            agentCreationErrors.forEach(error => outputChannel.appendLine(`  - ${error}`));
        }

    // Initialize all agents (TODO: Update agents to use new BaseAgent system)
    for (const agent of agents) {
        try {
            // Enhanced initialization will be added when agents are updated to use new BaseAgent
            console.log(`✅ Agent ${(agent as any).config?.participantId || 'unknown'} ready`);
        } catch (error) {
            console.warn(`Failed to initialize agent:`, error);
        }
    }

    // Register each agent as a chat participant
    outputChannel.appendLine(`\nRegistering ${agents.length} agents...`);
    let registrationErrors: string[] = [];
    
    agents.forEach((agent, index) => {
        try {
            const participantId = (agent as any).config.participantId;
            const participant = vscode.chat.createChatParticipant(
                participantId,
                agent.createHandler()
            );
            
            // Set icon if available
            const iconPath = (agent as any).config?.iconPath;
            if (iconPath) {
                participant.iconPath = iconPath;
            }
            
            // Register the agent with dispatcher for orchestration
            const dispatcherAgentId = participantId.split('.')[1];
            outputChannel.appendLine(`  Registering with dispatcher: ${participantId} as '${dispatcherAgentId}'`);
            dispatcher.registerAgent(dispatcherAgentId, agent);
            
            // Add to subscriptions for cleanup
            context.subscriptions.push(participant);
            
            outputChannel.appendLine(`  ✅ Registered: ${participantId} (dispatcher ID: ${dispatcherAgentId})`);
            
        } catch (error) {
            const errorMsg = `Failed to register agent ${index + 1}: ${(error as any).message}`;
            outputChannel.appendLine(`  ❌ ${errorMsg}`);
            registrationErrors.push(errorMsg);
        }
    });
    
    // Verify agent registration
    outputChannel.appendLine('\nVerifying agent registration with dispatcher:');
    const registeredAgents = dispatcher.getRegisteredAgents();
    outputChannel.appendLine(`  Registered agents: [${registeredAgents.join(', ')}]`);
    
    outputChannel.appendLine(`Registration completed: ${agents.length - registrationErrors.length} succeeded, ${registrationErrors.length} failed`);
    
    if (registrationErrors.length > 0) {
        outputChannel.appendLine('Registration errors:');
        registrationErrors.forEach(error => outputChannel.appendLine(`  - ${error}`));
    }

    // Register extension commands
    outputChannel.appendLine('\nRegistering extension commands...');
    registerCommands(context, dispatcher);
    outputChannel.appendLine('✅ Extension commands registered');

    // Show welcome message in output channel
    showWelcomeMessage(outputChannel);

    // Final success
    outputChannel.appendLine('\n✅ KI AUTOAGENT EXTENSION ACTIVATED!');
    outputChannel.appendLine('============================================');
    outputChannel.appendLine(`Total agents: ${agents.length}`);
    outputChannel.appendLine(`Registration errors: ${registrationErrors.length}`);
    outputChannel.appendLine(`Activated at: ${new Date().toLocaleString()}`);
    outputChannel.appendLine('\nType "@ki" in chat to get started!');
    
    // Single success notification
    vscode.window.showInformationMessage(`🎉 KI AutoAgent v${context.extension.packageJSON.version} activated! ${agents.length} agents ready.`);
    
    } catch (error) {
        // Handle any errors during extension activation
        const errorMsg = `KI AutoAgent activation failed: ${(error as any).message || error}`;
        console.error(errorMsg);
        
        // Show error
        vscode.window.showErrorMessage(errorMsg);
        
        // Try to show error in output channel if available
        if (outputChannel) {
            outputChannel.appendLine(`\n❌ ACTIVATION ERROR:`);
            outputChannel.appendLine(`Error: ${error}`);
            outputChannel.appendLine(`Message: ${(error as any).message}`);
            outputChannel.appendLine(`Stack: ${(error as any).stack}`);
            outputChannel.show(true);
        }
    }
}

export function deactivate() {
    console.log('👋 KI AutoAgent extension is deactivated');
}

function registerCommands(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
    
    // Command: Create File
    const createFileCommand = vscode.commands.registerCommand(
        'ki-autoagent.createFile',
        async (filename: string, content: string) => {
            try {
                const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
                if (!workspaceFolder) {
                    vscode.window.showErrorMessage('No workspace folder open');
                    return;
                }

                const fileUri = vscode.Uri.joinPath(workspaceFolder.uri, filename);
                await vscode.workspace.fs.writeFile(fileUri, Buffer.from(content, 'utf8'));
                
                // Open the created file
                const document = await vscode.workspace.openTextDocument(fileUri);
                await vscode.window.showTextDocument(document);
                
                vscode.window.showInformationMessage(`✅ Created file: ${filename}`);
            } catch (error) {
                vscode.window.showErrorMessage(`❌ Failed to create file: ${(error as any).message}`);
            }
        }
    );

    // Command: Insert at Cursor
    const insertAtCursorCommand = vscode.commands.registerCommand(
        'ki-autoagent.insertAtCursor',
        async (content: string) => {
            try {
                const editor = vscode.window.activeTextEditor;
                if (!editor) {
                    vscode.window.showErrorMessage('No active text editor');
                    return;
                }

                const position = editor.selection.active;
                await editor.edit(editBuilder => {
                    editBuilder.insert(position, content);
                });
                
                vscode.window.showInformationMessage('✅ Content inserted at cursor');
            } catch (error) {
                vscode.window.showErrorMessage(`❌ Failed to insert content: ${(error as any).message}`);
            }
        }
    );

    // Command: Apply Suggestion
    const applySuggestionCommand = vscode.commands.registerCommand(
        'ki-autoagent.applySuggestion',
        async (suggestionData: any) => {
            try {
                // Handle different types of suggestions
                if (suggestionData.type === 'file_creation') {
                    await vscode.commands.executeCommand(
                        'ki-autoagent.createFile',
                        suggestionData.filename,
                        suggestionData.content
                    );
                } else if (suggestionData.type === 'code_insertion') {
                    await vscode.commands.executeCommand(
                        'ki-autoagent.insertAtCursor',
                        suggestionData.code
                    );
                } else {
                    vscode.window.showInformationMessage(`Applied suggestion: ${suggestionData.description}`);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`❌ Failed to apply suggestion: ${(error as any).message}`);
            }
        }
    );

    // Command: Test Claude Code CLI
    const testClaudeCommand = vscode.commands.registerCommand(
        'ki-autoagent.testClaudeCLI',
        async () => {
            const outputChannel = vscode.window.createOutputChannel('Claude CLI Test');
            outputChannel.show();
            outputChannel.appendLine('🔍 Testing Claude Code CLI Integration...');
            outputChannel.appendLine('==========================================\n');
            
            try {
                const claudeService = getClaudeCodeService();
                
                // Check if CLI is available
                outputChannel.appendLine('1. Checking Claude CLI availability...');
                const isAvailable = await claudeService.isAvailable();
                
                if (!isAvailable) {
                    outputChannel.appendLine('❌ Claude CLI not found!');
                    outputChannel.appendLine('\nTo install Claude CLI:');
                    outputChannel.appendLine('  npm install -g @anthropic-ai/claude-code');
                    outputChannel.appendLine('\nOr use Anthropic API by configuring your API key in VS Code settings.');
                    vscode.window.showErrorMessage('Claude CLI not installed. See output for installation instructions.');
                    return;
                }
                
                outputChannel.appendLine('✅ Claude CLI is available!\n');
                
                // Test connection
                outputChannel.appendLine('2. Testing Claude CLI connection...');
                const testResult = await claudeService.testConnection();
                
                if (testResult.success) {
                    outputChannel.appendLine(`✅ ${testResult.message}\n`);
                    outputChannel.appendLine('3. Claude CLI Integration Status: WORKING');
                    outputChannel.appendLine('==========================================');
                    outputChannel.appendLine('✨ Everything is working correctly!');
                    outputChannel.appendLine('\nYou can now use Claude-powered agents in your chat.');
                    vscode.window.showInformationMessage('✅ Claude CLI is working correctly!');
                } else {
                    outputChannel.appendLine(`❌ ${testResult.message}\n`);
                    outputChannel.appendLine('3. Claude CLI Integration Status: ERROR');
                    outputChannel.appendLine('==========================================');
                    outputChannel.appendLine('Please check the error message above.');
                    vscode.window.showErrorMessage(`Claude CLI test failed: ${testResult.message}`);
                }
                
            } catch (error) {
                outputChannel.appendLine(`\n❌ Test failed with error: ${(error as any).message}`);
                outputChannel.appendLine('\nPlease check your configuration and try again.');
                vscode.window.showErrorMessage(`Claude CLI test failed: ${(error as any).message}`);
            }
        }
    );

    // Command: Show Agent Statistics
    const showAgentStatsCommand = vscode.commands.registerCommand(
        'ki-autoagent.showAgentStats',
        async () => {
            try {
                const stats = await dispatcher.getAgentStats();
                
                if (Object.keys(stats).length === 0) {
                    vscode.window.showInformationMessage('No agent statistics available yet');
                    return;
                }

                // Create a new document to display stats
                const statsContent = formatAgentStats(stats);
                const document = await vscode.workspace.openTextDocument({
                    content: statsContent,
                    language: 'markdown'
                });
                
                await vscode.window.showTextDocument(document);
            } catch (error) {
                vscode.window.showErrorMessage(`❌ Failed to show stats: ${(error as any).message}`);
            }
        }
    );

    // Command: Show Help
    const showHelpCommand = vscode.commands.registerCommand(
        'ki-autoagent.showHelp',
        async (agentId?: string) => {
            const helpContent = generateHelpContent(agentId);
            
            const document = await vscode.workspace.openTextDocument({
                content: helpContent,
                language: 'markdown'
            });
            
            await vscode.window.showTextDocument(document);
        }
    );

    // Command: Plan Implementation
    const planImplementationCommand = vscode.commands.registerCommand(
        'ki-autoagent.planImplementation',
        async (task: string, architecture: string) => {
            // This would trigger the orchestrator to create an implementation plan
            vscode.window.showInformationMessage('Creating implementation plan...');
            // Could open chat with pre-filled message
        }
    );

    // Command: Execute Workflow
    const executeWorkflowCommand = vscode.commands.registerCommand(
        'ki-autoagent.executeWorkflow',
        async (task: string, workflow: string) => {
            vscode.window.showInformationMessage('Executing workflow...');
            // Implementation for workflow execution
        }
    );

    // Command: Configure Agent Models
    const configureAgentModelsCommand = vscode.commands.registerCommand(
        'ki-autoagent.configureAgentModels',
        async () => {
            const configManager = AgentConfigurationManager.getInstance(context);
            const availableModels = configManager.getAvailableModels();
            
            // Show agent model configuration UI
            const agentIds = ['orchestrator', 'richter', 'architect', 'codesmith', 'tradestrat', 'research'];
            
            for (const agentId of agentIds) {
                const currentModel = configManager.getAgentModel(agentId);
                const modelOptions = Object.keys(availableModels).map(modelId => ({
                    label: availableModels[modelId].name,
                    description: `${availableModels[modelId].provider} - ${availableModels[modelId].tier}`,
                    detail: `$${availableModels[modelId].costPerMillion.input}/$${availableModels[modelId].costPerMillion.output} per million tokens`,
                    modelId
                }));
                
                const selected = await vscode.window.showQuickPick(modelOptions, {
                    title: `Select model for ${agentId}`,
                    placeHolder: `Current: ${currentModel}`,
                    ignoreFocusOut: true
                });
                
                if (selected && selected.modelId !== currentModel) {
                    await configManager.setAgentModel(agentId, selected.modelId);
                    vscode.window.showInformationMessage(`✅ Updated ${agentId} model to ${selected.label}`);
                }
            }
        }
    );

    // Command: Show Agent Performance
    const showAgentPerformanceCommand = vscode.commands.registerCommand(
        'ki-autoagent.showAgentPerformance',
        async () => {
            const configManager = AgentConfigurationManager.getInstance(context);
            const agentIds = ['orchestrator', 'richter', 'architect', 'codesmith', 'tradestrat', 'research'];
            
            let performanceReport = '# Agent Performance Report\n\n';
            performanceReport += `Generated: ${new Date().toLocaleString()}\n\n`;
            
            for (const agentId of agentIds) {
                const metrics = configManager.getAgentMetrics(agentId);
                const model = configManager.getAgentModel(agentId);
                
                performanceReport += `## ${agentId.charAt(0).toUpperCase() + agentId.slice(1)}\n`;
                performanceReport += `**Model:** ${model}\n`;
                
                if (metrics) {
                    const successRate = (metrics.successfulExecutions / metrics.totalExecutions * 100).toFixed(1);
                    performanceReport += `**Success Rate:** ${successRate}%\n`;
                    performanceReport += `**Total Executions:** ${metrics.totalExecutions}\n`;
                    performanceReport += `**Average Response Time:** ${metrics.averageResponseTime.toFixed(0)}ms\n`;
                    performanceReport += `**Current Streak:** ${metrics.currentStreak}\n`;
                    performanceReport += `**Best Streak:** ${metrics.bestStreak}\n`;
                } else {
                    performanceReport += `**Status:** No performance data yet\n`;
                }
                performanceReport += '\n';
            }
            
            const document = await vscode.workspace.openTextDocument({
                content: performanceReport,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(document);
        }
    );

    // Command: Open Configuration Directory
    const openConfigDirectoryCommand = vscode.commands.registerCommand(
        'ki-autoagent.openConfigDirectory',
        async () => {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                const configPath = vscode.Uri.joinPath(workspaceFolder.uri, '.kiautoagent');
                try {
                    await vscode.commands.executeCommand('vscode.openFolder', configPath, { forceNewWindow: false });
                } catch {
                    vscode.window.showInformationMessage('Configuration directory will be created when first used');
                }
            } else {
                vscode.window.showWarningMessage('No workspace folder open');
            }
        }
    );

    // Register all commands
    context.subscriptions.push(
        createFileCommand,
        insertAtCursorCommand,
        applySuggestionCommand,
        testClaudeCommand,
        showAgentStatsCommand,
        showHelpCommand,
        planImplementationCommand,
        executeWorkflowCommand,
        configureAgentModelsCommand,
        showAgentPerformanceCommand,
        openConfigDirectoryCommand
    );

    console.log('✅ All extension commands registered');
}

function showWelcomeMessage(outputChannel: vscode.OutputChannel) {
    
    outputChannel.appendLine('🤖 KI AutoAgent VS Code Extension');
    outputChannel.appendLine('=======================================');
    outputChannel.appendLine('');
    outputChannel.appendLine('✅ Extension activated successfully!');
    outputChannel.appendLine('');
    outputChannel.appendLine('Available Agents:');
    outputChannel.appendLine('• @ki - Universal orchestrator (routes to best agent)');
    outputChannel.appendLine('• @richter - ⚖️ Supreme judge & conflict resolver (Opus 4.1)');
    outputChannel.appendLine('• @architect - System architecture & design');
    outputChannel.appendLine('• @codesmith - Code implementation & testing');
    outputChannel.appendLine('• @docu - Documentation generation');
    outputChannel.appendLine('• @reviewer - Code review & security');
    outputChannel.appendLine('• @fixer - Bug fixing & debugging');
    outputChannel.appendLine('• @tradestrat - Trading strategy development');
    outputChannel.appendLine('• @research - Web research & information gathering');
    outputChannel.appendLine('');
    outputChannel.appendLine('Getting Started:');
    outputChannel.appendLine('1. Open VS Code Chat panel (Ctrl+Shift+I)');
    outputChannel.appendLine('2. Type @ki followed by your request');
    outputChannel.appendLine('3. Or use specific agents like @architect, @codesmith, etc.');
    outputChannel.appendLine('');
    outputChannel.appendLine('Configuration:');
    outputChannel.appendLine('• Set your API keys in VS Code Settings');
    outputChannel.appendLine('• Search for "KI AutoAgent" in settings');
    outputChannel.appendLine('• Configure OpenAI, Anthropic, and Perplexity API keys');
    outputChannel.appendLine('');
    outputChannel.appendLine('Need help? Type "@ki /agents" to see all available agents!');
}

function formatAgentStats(stats: Record<string, any>): string {
    let content = '# KI AutoAgent Statistics\n\n';
    content += `Generated at: ${new Date().toLocaleString()}\n\n`;
    
    for (const [agentId, agentStats] of Object.entries(stats)) {
        const { totalExecutions, successRate, averageResponseTime, lastExecution } = agentStats as any;
        
        content += `## ${agentId}\n\n`;
        content += `- **Total Executions:** ${totalExecutions}\n`;
        content += `- **Success Rate:** ${(successRate * 100).toFixed(1)}%\n`;
        content += `- **Average Response Time:** ${averageResponseTime.toFixed(0)}ms\n`;
        
        if (lastExecution) {
            content += `- **Last Execution:** ${new Date(lastExecution).toLocaleString()}\n`;
        }
        
        content += '\n';
    }
    
    return content;
}

function generateHelpContent(agentId?: string): string {
    let content = '# KI AutoAgent Help\n\n';
    
    if (agentId) {
        content += `## Help for ${agentId}\n\n`;
        // Add agent-specific help
    } else {
        content += '## Getting Started\n\n';
        content += 'KI AutoAgent is a universal multi-agent AI development platform for VS Code.\n\n';
        content += '### Available Agents\n\n';
        content += '- **@ki** - Universal orchestrator that automatically routes tasks\n';
        content += '- **@richter** - ⚖️ Supreme judge & conflict resolver (Claude Opus 4.1)\n';
        content += '- **@architect** - System architecture and design expert\n';
        content += '- **@codesmith** - Senior Python/Web developer\n';
        content += '- **@docu** - Technical documentation expert\n';
        content += '- **@reviewer** - Code review and security expert\n';
        content += '- **@fixer** - Bug fixing and optimization expert\n';
        content += '- **@tradestrat** - Trading strategy expert\n';
        content += '- **@research** - Research and information expert\n\n';
        content += '### Usage Examples\n\n';
        content += '```\n';
        content += '@ki create a REST API with FastAPI\n';
        content += '@richter judge which approach is better: microservices vs monolith\n';
        content += '@richter resolve this disagreement between @architect and @codesmith\n';
        content += '@architect design a microservices architecture\n';
        content += '@codesmith implement a Python class for user management\n';
        content += '@tradestrat develop a momentum trading strategy\n';
        content += '@fixer debug this error message\n';
        content += '```\n\n';
        content += '### Configuration\n\n';
        content += '1. Open VS Code Settings (Ctrl+,)\n';
        content += '2. Search for "KI AutoAgent"\n';
        content += '3. Configure your API keys:\n';
        content += '   - OpenAI API Key (for GPT models)\n';
        content += '   - Anthropic API Key (for Claude models)\n';
        content += '   - Perplexity API Key (for research)\n\n';
        content += '### Support\n\n';
        content += 'For issues and feature requests, please visit the GitHub repository.\n';
    }
    
    return content;
}