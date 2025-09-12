/**
 * KI AutoAgent VS Code Extension
 * Main extension entry point that registers all chat participants
 */
import * as vscode from 'vscode';
import { VSCodeMasterDispatcher } from './core/VSCodeMasterDispatcher';
import { ArchitectAgent } from './agents/ArchitectAgent';
import { OrchestratorAgent } from './agents/OrchestratorAgent';
import { CodeSmithAgent } from './agents/CodeSmithAgent';
import { TradeStratAgent } from './agents/TradeStratAgent';
import { ResearchAgent } from './agents/ResearchAgent';
import { OpusArbitratorAgent } from './agents/OpusArbitratorAgent';
// Multi-Agent Chat UI Components
import { MultiAgentChatPanel } from './ui/MultiAgentChatPanel';
import { ChatWidget } from './ui/ChatWidget';
// TODO: Implement remaining agents
// import { DocuAgent } from './agents/DocuAgent';
// import { ReviewerAgent } from './agents/ReviewerAgent';
// import { FixerAgent } from './agents/FixerAgent';

export function activate(context: vscode.ExtensionContext) {
    console.log('🤖 KI AutoAgent extension is now active!');

    // Show activation in output channel immediately
    const outputChannel = vscode.window.createOutputChannel('KI AutoAgent');
    outputChannel.appendLine('🤖 KI AutoAgent Extension Activated');
    outputChannel.appendLine('======================================');
    outputChannel.appendLine(`⏰ Activation Time: ${new Date().toLocaleString()}`);
    outputChannel.appendLine(`📦 Extension Version: ${context.extension.packageJSON.version}`);
    outputChannel.show(true); // Show and preserve focus

    // Initialize the master dispatcher
    const dispatcher = new VSCodeMasterDispatcher(context);
    
    // Initialize Chat Widget (Status Bar)
    const chatWidget = new ChatWidget(context, dispatcher);
    
    // Register chat panel commands
    const showChatCommand = vscode.commands.registerCommand(
        'ki-autoagent.showChat',
        () => MultiAgentChatPanel.createOrShow(context.extensionUri, dispatcher)
    );
    context.subscriptions.push(showChatCommand);

    // Initialize and register all agents
    const agents = [
        new OrchestratorAgent(context, dispatcher),
        new OpusArbitratorAgent(context, dispatcher),
        new ArchitectAgent(context, dispatcher),
        new CodeSmithAgent(context, dispatcher),
        new TradeStratAgent(context, dispatcher),
        new ResearchAgent(context, dispatcher),
        // TODO: Add remaining agents as they are implemented
        // new DocuAgent(context, dispatcher),
        // new ReviewerAgent(context, dispatcher),
        // new FixerAgent(context, dispatcher),
    ];

    // Register each agent as a chat participant
    agents.forEach(agent => {
        const participantId = (agent as any).config.participantId;
        const participant = vscode.chat.createChatParticipant(
            participantId,
            agent.createHandler()
        );
        
        // Set icon if available
        const iconPath = (agent as any).config.iconPath;
        if (iconPath) {
            participant.iconPath = iconPath;
        }
        
        // Register the agent with dispatcher for orchestration
        dispatcher.registerAgent(participantId.split('.')[1], agent);
        
        // Add to subscriptions for cleanup
        context.subscriptions.push(participant);
        
        console.log(`✅ Registered chat participant: ${participantId}`);
    });

    // Register extension commands
    registerCommands(context, dispatcher);

    // Show welcome message in output channel
    showWelcomeMessage(outputChannel);

    // Log successful activation
    outputChannel.appendLine('✅ All components initialized successfully!');
    outputChannel.appendLine('');
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

    // Register all commands
    context.subscriptions.push(
        createFileCommand,
        insertAtCursorCommand,
        applySuggestionCommand,
        showAgentStatsCommand,
        showHelpCommand,
        planImplementationCommand,
        executeWorkflowCommand
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