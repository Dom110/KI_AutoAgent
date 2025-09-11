/**
 * VS Code Master Dispatcher - Orchestrates AI agents in VS Code context
 * Adapted from CLI MasterDispatcher for VS Code extension environment
 */
import * as vscode from 'vscode';
import { TaskRequest, TaskResult, Intent, WorkspaceContext, ProjectTypeDefinition, WorkflowStep } from '../types';

export class VSCodeMasterDispatcher {
    private agents: Map<string, any> = new Map();
    private projectTypes: Map<string, ProjectTypeDefinition> = new Map();
    private intentPatterns: Map<string, RegExp[]> = new Map();
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.initializeProjectTypes();
        this.initializeIntentPatterns();
    }

    /**
     * Process a task request and route to appropriate agents
     */
    async processRequest(request: TaskRequest): Promise<TaskResult> {
        try {
            // Get workspace context
            const workspaceContext = await this.getWorkspaceContext();
            
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
        
        // Architecture patterns
        if (this.matchesPatterns(lowerPrompt, ['design', 'architecture', 'system', 'plan', 'structure'])) {
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
        
        // Default to implementation
        return { type: 'implementation', confidence: 0.5, agent: 'codesmith' };
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
     */
    createWorkflow(intent: Intent, projectType: string): WorkflowStep[] {
        const projectDef = this.projectTypes.get(projectType);
        
        // Base workflow based on intent
        let workflow: WorkflowStep[] = [];
        
        switch (intent.type) {
            case 'architecture':
                workflow = [
                    { id: 'analyze', agent: 'architect', description: 'Analyze requirements and context' },
                    { id: 'design', agent: 'architect', description: 'Create architecture design' },
                    { id: 'review', agent: 'reviewer', description: 'Review architecture for best practices' }
                ];
                break;
                
            case 'implementation':
                workflow = [
                    { id: 'plan', agent: 'architect', description: 'Plan implementation approach' },
                    { id: 'implement', agent: 'codesmith', description: 'Implement the solution' },
                    { id: 'test', agent: 'codesmith', description: 'Create tests' },
                    { id: 'review', agent: 'reviewer', description: 'Review implementation' }
                ];
                break;
                
            case 'trading':
                workflow = [
                    { id: 'strategy_design', agent: 'tradestrat', description: 'Design trading strategy' },
                    { id: 'implement', agent: 'codesmith', description: 'Implement strategy code' },
                    { id: 'backtest', agent: 'tradestrat', description: 'Create backtesting framework' },
                    { id: 'review', agent: 'reviewer', description: 'Review for trading best practices' }
                ];
                break;
                
            case 'debug':
                workflow = [
                    { id: 'analyze', agent: 'fixer', description: 'Analyze the problem' },
                    { id: 'fix', agent: 'fixer', description: 'Implement fix' },
                    { id: 'test', agent: 'codesmith', description: 'Test the fix' }
                ];
                break;
                
            default:
                workflow = [
                    { id: 'execute', agent: intent.agent, description: 'Execute task' }
                ];
        }
        
        // Apply project-specific modifications
        if (projectDef?.workflow) {
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

        for (const step of workflow) {
            try {
                const agent = this.agents.get(step.agent);
                if (!agent) {
                    throw new Error(`Agent ${step.agent} not found`);
                }

                const stepResult = await agent.executeStep(step, request, results);
                results.push(stepResult);
                
                // Accumulate results
                finalResult.content += `## ${step.description}\n\n${stepResult.content}\n\n`;
                finalResult.suggestions?.push(...(stepResult.suggestions || []));
                finalResult.references?.push(...(stepResult.references || []));
                
                if (stepResult.status === 'error') {
                    finalResult.status = 'partial_success';
                }
                
            } catch (error) {
                finalResult.status = 'error';
                finalResult.content += `❌ Error in ${step.description}: ${(error as any).message}\n\n`;
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
        this.agents.set(agentId, agent);
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
                { id: 'security_review', agent: 'reviewer', description: 'Security vulnerability check' },
                { id: 'api_documentation', agent: 'docu', description: 'Generate API documentation' }
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