/**
 * VS Code Master Dispatcher - Orchestrates AI agents in VS Code context
 * Adapted from CLI MasterDispatcher for VS Code extension environment
 */
import * as vscode from 'vscode';
import { TaskRequest, TaskResult, Intent, WorkspaceContext, ProjectTypeDefinition, WorkflowStep } from '../types';
import { ConversationContextManager } from './ConversationContextManager';

export class VSCodeMasterDispatcher {
    private agents: Map<string, any> = new Map();
    private projectTypes: Map<string, ProjectTypeDefinition> = new Map();
    private contextManager: ConversationContextManager;
    private intentPatterns: Map<string, RegExp[]> = new Map();
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.contextManager = ConversationContextManager.getInstance();
        this.initializeProjectTypes();
        this.initializeIntentPatterns();
    }

    /**
     * Process a task request and route to appropriate agents
     */
    async processRequest(request: TaskRequest): Promise<TaskResult> {
        console.log(`\n🚦 [DISPATCHER] ====== processRequest called ======`);
        console.log(`🚦 [DISPATCHER] request.command: '${request.command}'`);
        console.log(`🚦 [DISPATCHER] request.command type: ${typeof request.command}`);
        console.log(`🚦 [DISPATCHER] request.prompt: "${request.prompt?.substring(0, 50)}..."`);
        console.log(`🚦 [DISPATCHER] Command check results:`);
        console.log(`🚦 [DISPATCHER]   - request.command exists: ${!!request.command}`);
        console.log(`🚦 [DISPATCHER]   - request.command !== 'auto': ${request.command !== 'auto'}`);
        console.log(`🚦 [DISPATCHER]   - request.command !== 'orchestrator': ${request.command !== 'orchestrator'}`);
        
        try {
            // Get workspace context
            const workspaceContext = await this.getWorkspaceContext();
            
            // Check if a specific agent was requested (single agent mode)
            if (request.command && request.command !== 'auto' && request.command !== 'orchestrator') {
                console.log(`🎯 [DISPATCHER] ✅ SINGLE AGENT MODE ACTIVATED`);
                console.log(`🎯 [DISPATCHER] Single agent mode: Using only ${request.command}`);
                
                // Create a single-step workflow for the specific agent
                const workflow = [{
                    id: 'execute',
                    agent: request.command,
                    description: `Execute with ${request.command}`
                }];
                
                console.log(`🎯 [DISPATCHER] Created single-step workflow:`);
                console.log(`🎯 [DISPATCHER]   - Steps count: ${workflow.length}`);
                console.log(`🎯 [DISPATCHER]   - Step[0]: id='${workflow[0].id}', agent='${workflow[0].agent}'`);
                
                // Execute single agent
                const result = await this.executeWorkflow(workflow, {
                    ...request,
                    context: workspaceContext,
                    projectType: request.projectType || 'generic'
                });
                
                return result;
            }
            
            // Auto mode: Detect intent and create multi-step workflow
            console.log(`🎯 [DISPATCHER] ⚠️ AUTO MODE ACTIVATED (not single agent)`);
            console.log(`🎯 [DISPATCHER] Auto mode: Creating workflow based on intent`);
            
            // Detect intent and project type
            const intent = await this.detectIntent(request.prompt);
            const projectType = request.projectType || await this.detectProjectType(workspaceContext);
            
            // Create workflow
            const workflow = this.createWorkflow(intent, projectType);
            
            // Execute workflow
            const result = await this.executeWorkflow(workflow, {
                ...request,
                context: workspaceContext,
                projectType
            });

            return result;
        } catch (error) {
            return {
                status: 'error',
                content: `Error processing request: ${(error as any).message}`,
                metadata: { error: (error as any).message }
            };
        }
    }

    /**
     * Detect user intent from prompt
     */
    async detectIntent(prompt: string): Promise<Intent> {
        const lowerPrompt = prompt.toLowerCase();

        // Check if this is a question rather than a task
        const isQuestion = /^(what|which|how|was|welche|wie|wer|wo|wann|warum|show|list|explain)/i.test(prompt);
        const isImplementation = /(implement|create|build|write|code|develop)/i.test(prompt);

        // Query patterns - questions about the system or information
        if (isQuestion && !isImplementation) {
            // Questions about the system itself, agents, or instructions
            if (this.matchesPatterns(lowerPrompt, ['instruction', 'agent', 'system', 'available', 'haben wir', 'gibt es', 'welche'])) {
                return { type: 'query', confidence: 0.95, agent: 'orchestrator' };
            }
            // Architecture questions
            if (this.matchesPatterns(lowerPrompt, ['architecture', 'design', 'pattern', 'structure'])) {
                return { type: 'query', confidence: 0.9, agent: 'architect' };
            }
            // Research questions
            if (this.matchesPatterns(lowerPrompt, ['research', 'find', 'information', 'latest'])) {
                return { type: 'query', confidence: 0.85, agent: 'research' };
            }
            // Default query
            return { type: 'query', confidence: 0.7, agent: 'orchestrator' };
        }

        // Architecture patterns (for actual design tasks)
        if (this.matchesPatterns(lowerPrompt, ['design', 'architecture', 'system', 'plan', 'structure']) && isImplementation) {
            return { type: 'architecture', confidence: 0.9, agent: 'architect' };
        }

        // Implementation patterns
        if (this.matchesPatterns(lowerPrompt, ['implement', 'code', 'create', 'build', 'develop'])) {
            return { type: 'implementation', confidence: 0.85, agent: 'codesmith' };
        }

        // Documentation patterns
        if (this.matchesPatterns(lowerPrompt, ['document', 'readme', 'docs', 'explain', 'tutorial'])) {
            return { type: 'documentation', confidence: 0.9, agent: 'docu' };
        }

        // Review patterns
        if (this.matchesPatterns(lowerPrompt, ['review', 'check', 'analyze', 'audit', 'security'])) {
            return { type: 'review', confidence: 0.85, agent: 'reviewer' };
        }

        // Debug/Fix patterns
        if (this.matchesPatterns(lowerPrompt, ['fix', 'debug', 'error', 'bug', 'problem', 'issue'])) {
            return { type: 'debug', confidence: 0.9, agent: 'fixer' };
        }

        // Trading patterns
        if (this.matchesPatterns(lowerPrompt, ['trading', 'strategy', 'backtest', 'ron', 'market', 'stock'])) {
            return { type: 'trading', confidence: 0.95, agent: 'tradestrat' };
        }

        // Research patterns
        if (this.matchesPatterns(lowerPrompt, ['research', 'search', 'find', 'information', 'latest'])) {
            return { type: 'research', confidence: 0.8, agent: 'research' };
        }

        // Default - if we can't determine, treat as a query
        return { type: 'query', confidence: 0.5, agent: 'orchestrator' };
    }

    /**
     * Detect project type from workspace context
     */
    async detectProjectType(context?: WorkspaceContext): Promise<string> {
        if (!context?.workspaceRoots || context.workspaceRoots.length === 0) {
            return 'generic_software';
        }

        const workspaceRoot = context.workspaceRoots[0];
        
        try {
            // Check for package.json
            const packageJsonUri = vscode.Uri.joinPath(workspaceRoot.uri, 'package.json');
            try {
                const packageJsonContent = await vscode.workspace.fs.readFile(packageJsonUri);
                const packageJson = JSON.parse(packageJsonContent.toString());
                
                // Trading system indicators
                if (packageJson.dependencies?.['streamlit'] || 
                    packageJson.dependencies?.['yfinance'] ||
                    packageJson.dependencies?.['pandas']) {
                    return 'trading_system';
                }
                
                // Web API indicators
                if (packageJson.dependencies?.['fastapi'] ||
                    packageJson.dependencies?.['express'] ||
                    packageJson.dependencies?.['flask']) {
                    return 'web_api';
                }
                
                // React/Frontend indicators
                if (packageJson.dependencies?.['react'] ||
                    packageJson.dependencies?.['vue'] ||
                    packageJson.dependencies?.['angular']) {
                    return 'web_frontend';
                }
            } catch (error) {
                // package.json not found or invalid
            }

            // Check for requirements.txt (Python)
            const requirementsUri = vscode.Uri.joinPath(workspaceRoot.uri, 'requirements.txt');
            try {
                const requirementsContent = await vscode.workspace.fs.readFile(requirementsUri);
                const requirements = requirementsContent.toString();
                
                if (requirements.includes('yfinance') || 
                    requirements.includes('pandas') ||
                    requirements.includes('streamlit')) {
                    return 'trading_system';
                }
                
                if (requirements.includes('fastapi') ||
                    requirements.includes('flask') ||
                    requirements.includes('django')) {
                    return 'web_api';
                }
            } catch (error) {
                // requirements.txt not found
            }

            // Check for specific files
            const files = await vscode.workspace.findFiles('**/*.{py,js,ts,jsx,tsx}', '**/node_modules/**', 50);
            const filenames = files.map(uri => uri.fsPath.toLowerCase());
            
            if (filenames.some(f => f.includes('strategy') || f.includes('trading') || f.includes('backtest'))) {
                return 'trading_system';
            }
            
            if (filenames.some(f => f.includes('api') || f.includes('server') || f.includes('endpoint'))) {
                return 'web_api';
            }

        } catch (error) {
            console.error('Error detecting project type:', error);
        }

        return 'generic_software';
    }

    /**
     * Create workflow based on intent and project type
     * Note: Uses only available agents (architect, codesmith, tradestrat, research, richter, orchestrator)
     */
    createWorkflow(intent: Intent, projectType: string): WorkflowStep[] {
        const projectDef = this.projectTypes.get(projectType);
        
        // Base workflow based on intent
        let workflow: WorkflowStep[] = [];
        
        switch (intent.type) {
            case 'query':
                // For queries, just use a single step with the appropriate agent
                workflow = [
                    { id: 'answer', agent: intent.agent, description: 'Answer query directly' }
                ];
                break;

            case 'architecture':
                workflow = [
                    { id: 'analyze', agent: 'architect', description: 'Analyze requirements and context' },
                    { id: 'design', agent: 'architect', description: 'Create architecture design' },
                    { id: 'review', agent: 'codesmith', description: 'Review architecture for best practices' } // Using codesmith instead of missing 'reviewer'
                ];
                break;
                
            case 'implementation':
                workflow = [
                    { id: 'plan', agent: 'architect', description: 'Plan implementation approach' },
                    { id: 'implement', agent: 'codesmith', description: 'Implement the solution' },
                    { id: 'test', agent: 'codesmith', description: 'Create tests' },
                    { id: 'review', agent: 'codesmith', description: 'Review implementation' } // Using codesmith instead of missing 'reviewer'
                ];
                break;
                
            case 'trading':
                workflow = [
                    { id: 'strategy_design', agent: 'tradestrat', description: 'Design trading strategy' },
                    { id: 'implement', agent: 'codesmith', description: 'Implement strategy code' },
                    { id: 'backtest', agent: 'tradestrat', description: 'Create backtesting framework' },
                    { id: 'review', agent: 'tradestrat', description: 'Review for trading best practices' } // Using tradestrat instead of missing 'reviewer'
                ];
                break;
                
            case 'debug':
                workflow = [
                    { id: 'analyze', agent: 'codesmith', description: 'Analyze the problem' }, // Using codesmith instead of missing 'fixer'
                    { id: 'fix', agent: 'codesmith', description: 'Implement fix' }, // Using codesmith instead of missing 'fixer'
                    { id: 'test', agent: 'codesmith', description: 'Test the fix' }
                ];
                break;
                
            case 'documentation':
                workflow = [
                    { id: 'analyze', agent: 'architect', description: 'Analyze documentation requirements' },
                    { id: 'document', agent: 'codesmith', description: 'Generate documentation' } // Using codesmith instead of missing 'docu'
                ];
                break;
                
            case 'research':
                workflow = [
                    { id: 'research', agent: 'research', description: 'Research and gather information' }
                ];
                break;
                
            default:
                workflow = [
                    { id: 'execute', agent: intent.agent || 'codesmith', description: 'Execute task' }
                ];
        }

        // Apply project-specific modifications ONLY if NOT a query
        // Queries should always be single-step and not modified
        if (intent.type !== 'query' && projectDef?.workflow) {
            // Merge project-specific workflow steps
            workflow = [...workflow, ...projectDef.workflow.filter(step =>
                !workflow.some(w => w.id === step.id)
            )];
        }

        return workflow;
    }

    /**
     * Execute workflow steps
     */
    async executeWorkflow(workflow: WorkflowStep[], request: TaskRequest): Promise<TaskResult> {
        const results: TaskResult[] = [];
        let finalResult: TaskResult = {
            status: 'success',
            content: '',
            suggestions: [],
            references: []
        };

        console.log(`🚀 [WORKFLOW] Starting workflow execution with ${workflow.length} steps`);
        console.log(`🚀 [WORKFLOW] Workflow steps: ${workflow.map(s => `${s.id}:${s.agent}`).join(' → ')}`);
        console.log(`🚀 [WORKFLOW] Current agent registry size: ${this.agents.size}`);
        console.log(`🚀 [WORKFLOW] Current registered agents: [${Array.from(this.agents.keys()).join(', ')}]`);

        for (const step of workflow) {
            try {
                console.log(`\n🔍 [WORKFLOW STEP] ========================================`);
                console.log(`🔍 [WORKFLOW STEP] Executing: ${step.description}`);
                console.log(`🔍 [WORKFLOW STEP] Looking for agent: "${step.agent}"`);
                console.log(`🔍 [WORKFLOW STEP] Agent registry has ${this.agents.size} agents`);
                console.log(`🔍 [WORKFLOW STEP] Available agents: [${Array.from(this.agents.keys()).join(', ')}]`);

                // Send partial response for workflow progress
                if (request.onPartialResponse) {
                    const stepIndex = workflow.indexOf(step) + 1;
                    request.onPartialResponse(`\n🔄 **Step ${stepIndex}/${workflow.length}**: @${step.agent} - ${step.description}\n\n`);
                }

                let agent = this.agents.get(step.agent);
                console.log(`🔍 [WORKFLOW STEP] Direct lookup for "${step.agent}": ${agent ? 'FOUND' : 'NOT FOUND'}`);
                
                // Try alternative agent mappings if direct lookup fails
                if (!agent) {
                    const agentMappings: Record<string, string[]> = {
                        'architect': ['architect', 'ki-autoagent.architect'],
                        'codesmith': ['codesmith', 'ki-autoagent.codesmith'],  
                        'tradestrat': ['tradestrat', 'ki-autoagent.tradestrat'],
                        'research': ['research', 'ki-autoagent.research'],
                        'richter': ['richter', 'ki-autoagent.richter'],
                        'orchestrator': ['orchestrator', 'ki-autoagent.orchestrator']
                    };
                    
                    // Try all possible names for this agent
                    const possibleNames = agentMappings[step.agent];
                    if (possibleNames) {
                        for (const possibleName of possibleNames) {
                            agent = this.agents.get(possibleName);
                            if (agent) {
                                console.log(`[DEBUG] Found agent ${step.agent} under name: ${possibleName}`);
                                break;
                            }
                        }
                    }
                }
                
                if (!agent) {
                    console.error(`[DEBUG] Agent ${step.agent} not found! Available agents: ${Array.from(this.agents.keys()).join(', ')}`);
                    
                    // TEMPORARY FALLBACK: Use orchestrator for missing agents
                    agent = this.agents.get('orchestrator') || this.agents.get('ki-autoagent.orchestrator');
                    if (agent) {
                        console.warn(`[DEBUG] Using orchestrator as fallback for ${step.agent}`);
                    } else {
                        const errorMsg = `Agent ${step.agent} not found. Registered agents: [${Array.from(this.agents.keys()).join(', ')}]`;
                        console.error(`❌ [WORKFLOW STEP] ${errorMsg}`);
                        throw new Error(errorMsg);
                    }
                }
                
                console.log(`[DEBUG] Found agent: ${step.agent}, executing step: ${step.description}`);
                console.log(`[DEBUG] Passing ${results.length} previous results to agent`);

                // Get recent conversation history from context manager
                const recentHistory = this.contextManager.getFormattedContext(5);
                
                // Create enriched request with accumulated context
                const enrichedRequest = {
                    ...request,
                    prompt: request.prompt,
                    conversationHistory: results.map(r => ({
                        agent: r.metadata?.agent || 'unknown',
                        step: r.metadata?.step || 'unknown',
                        content: r.content
                    })),
                    globalContext: recentHistory
                };

                const stepResult = await agent.executeStep(step, enrichedRequest, results);
                results.push(stepResult);
                
                // Save to conversation history
                this.contextManager.addEntry({
                    timestamp: new Date().toISOString(),
                    agent: step.agent,
                    step: step.id,
                    input: request.prompt,
                    output: stepResult.content,
                    metadata: stepResult.metadata
                });
                
                // Log inter-agent communication
                console.log(`[INTER-AGENT] ${step.agent} completed step '${step.id}' with ${stepResult.content.length} chars`);
                console.log(`[INTER-AGENT] Result saved to conversation history`);
                console.log(`[INTER-AGENT] Result will be passed to next agent in workflow`);
                
                // Send partial response for step completion
                if (request.onPartialResponse) {
                    const preview = stepResult.content.substring(0, 200);
                    request.onPartialResponse(`✅ Completed: ${preview}${stepResult.content.length > 200 ? '...' : ''}\n\n`);
                }

                // For single-step workflows (like queries), use the content directly
                // For multi-step workflows, accumulate results
                if (workflow.length === 1) {
                    finalResult.content = stepResult.content;
                    finalResult.metadata = { ...finalResult.metadata, ...stepResult.metadata, agent: step.agent };
                } else {
                    finalResult.content += `## ${step.description}\n\n${stepResult.content}\n\n`;
                }
                finalResult.suggestions?.push(...(stepResult.suggestions || []));
                finalResult.references?.push(...(stepResult.references || []));

                if (stepResult.status === 'error') {
                    finalResult.status = 'partial_success';
                }
                
            } catch (error) {
                const errorMessage = (error as any).message || error;
                console.error(`❌ Error executing step ${step.id} (${step.agent}): ${errorMessage}`);
                finalResult.status = 'error';
                finalResult.content += `❌ Error in ${step.description}: ${errorMessage}\n\n`;
                
                // Add helpful error message for API issues
                if (errorMessage.includes('not found')) {
                    finalResult.content += `**Troubleshooting:**\n`;
                    finalResult.content += `- Registered agents: [${Array.from(this.agents.keys()).join(', ')}]\n`;
                    finalResult.content += `- Ensure all agents are properly initialized\n\n`;
                } else if (errorMessage.includes('quota') || errorMessage.includes('API')) {
                    finalResult.content += `**API Configuration Required:**\n`;
                    finalResult.content += `1. Open VS Code Settings (Cmd+,)\n`;
                    finalResult.content += `2. Search for "KI AutoAgent"\n`;
                    finalResult.content += `3. Configure your API keys:\n`;
                    finalResult.content += `   - OpenAI API Key\n`;
                    finalResult.content += `   - Anthropic API Key\n`;
                    finalResult.content += `   - Perplexity API Key\n\n`;
                } else if (errorMessage.includes('Claude Web Proxy')) {
                    finalResult.content += `**Claude Web Proxy Required:**\n`;
                    finalResult.content += `The Claude Web Proxy server is not running.\n`;
                    finalResult.content += `Please start the proxy server to use Claude models.\n\n`;
                }
            }
        }

        return finalResult;
    }

    /**
     * Get current workspace context
     */
    async getWorkspaceContext(): Promise<WorkspaceContext> {
        const activeEditor = vscode.window.activeTextEditor;
        const workspaceRoots = vscode.workspace.workspaceFolders;
        const openDocuments = vscode.workspace.textDocuments;
        
        let selectedText = '';
        let currentFile = '';
        
        if (activeEditor) {
            currentFile = activeEditor.document.fileName;
            if (!activeEditor.selection.isEmpty) {
                selectedText = activeEditor.document.getText(activeEditor.selection);
            }
        }

        return {
            activeEditor,
            workspaceRoots,
            openDocuments,
            selectedText,
            currentFile
        };
    }

    /**
     * Register an agent
     */
    registerAgent(agentId: string, agent: any): void {
        console.log(`🔧 [DISPATCHER] Registering agent: ${agentId}`);
        console.log(`🔧 [DISPATCHER] Agent object type: ${typeof agent}`);
        console.log(`🔧 [DISPATCHER] Agent has executeStep: ${typeof agent.executeStep}`);
        console.log(`🔧 [DISPATCHER] Agent config: ${JSON.stringify(agent.config || 'NO CONFIG')}`);
        
        this.agents.set(agentId, agent);
        
        console.log(`🔧 [DISPATCHER] Total registered agents: ${this.agents.size}`);
        console.log(`🔧 [DISPATCHER] All registered agent IDs: [${Array.from(this.agents.keys()).join(', ')}]`);
        console.log(`🔧 [DISPATCHER] Agent storage verification - Can retrieve ${agentId}: ${this.agents.has(agentId) ? 'YES' : 'NO'}`);
        
        // Test immediate retrieval
        const testRetrieve = this.agents.get(agentId);
        console.log(`🔧 [DISPATCHER] Immediate retrieval test for ${agentId}: ${testRetrieve ? 'SUCCESS' : 'FAILED'}`);
    }

    /**
     * Get list of registered agent IDs
     */
    getRegisteredAgents(): string[] {
        return Array.from(this.agents.keys());
    }

    /**
     * Get agent statistics
     */
    async getAgentStats(): Promise<Record<string, any>> {
        const stats: Record<string, any> = {};
        
        for (const [agentId, agent] of this.agents) {
            if (agent.getStats) {
                stats[agentId] = await agent.getStats();
            }
        }
        
        return stats;
    }

    private matchesPatterns(text: string, patterns: string[]): boolean {
        return patterns.some(pattern => text.includes(pattern));
    }

    private initializeProjectTypes(): void {
        // Trading System
        this.projectTypes.set('trading_system', {
            name: 'Trading System',
            patterns: ['streamlit', 'yfinance', 'pandas', 'trading', 'strategy'],
            qualityGates: ['engine_parity', 'trading_validation', 'ron_compliance'],
            workflow: [
                { id: 'strategy_validation', agent: 'tradestrat', description: 'Validate trading strategy logic' },
                { id: 'risk_analysis', agent: 'tradestrat', description: 'Analyze risk management' }
            ],
            primaryAgent: 'tradestrat'
        });

        // Web API
        this.projectTypes.set('web_api', {
            name: 'Web API',
            patterns: ['fastapi', 'flask', 'express', 'api'],
            qualityGates: ['security_review', 'performance_check', 'api_design'],
            workflow: [
                { id: 'security_review', agent: 'codesmith', description: 'Security vulnerability check' }, // Using codesmith instead of missing 'reviewer'
                { id: 'api_documentation', agent: 'codesmith', description: 'Generate API documentation' } // Using codesmith instead of missing 'docu'
            ],
            primaryAgent: 'codesmith'
        });

        // Generic Software
        this.projectTypes.set('generic_software', {
            name: 'Generic Software',
            patterns: [],
            qualityGates: ['code_quality', 'performance', 'security'],
            workflow: [],
            primaryAgent: 'codesmith'
        });
    }

    private initializeIntentPatterns(): void {
        // Define regex patterns for more sophisticated intent detection
        this.intentPatterns.set('architecture', [
            /\b(design|architect|structure|system)\b/i,
            /\b(plan|planning|blueprint)\b/i
        ]);
        
        this.intentPatterns.set('implementation', [
            /\b(implement|code|create|build|develop)\b/i,
            /\b(function|class|method|api)\b/i
        ]);
        
        // Add more patterns as needed
    }
}