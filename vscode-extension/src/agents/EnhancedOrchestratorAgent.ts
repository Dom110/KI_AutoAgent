/**
 * Enhanced Orchestrator Agent with Plan Storage and Execution
 * Fixes the issue where "mach das" doesn't execute the proposed plan
 */

import * as vscode from 'vscode';
import { OrchestratorAgent } from './OrchestratorAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { WorkflowNode } from '../core/WorkflowEngine';
import { IntentClassifier } from './intelligence/IntentClassifier';
import { ConversationContext } from './intelligence/ConversationContext';
import { AIClassificationService } from '../services/AIClassificationService';
import {
    IntentClassification,
    ConversationMessage,
    ProposedPlan as IntentProposedPlan,
    PlanStep as IntentPlanStep
} from '../types/IntentTypes';

// Use types from IntentTypes.ts, with local alias
type ProposedPlan = IntentProposedPlan & {
    prompt: string;  // Add original prompt field
};
type PlanStep = IntentPlanStep;

/**
 * Enhanced Orchestrator with Plan Management
 */
export class EnhancedOrchestratorAgent extends OrchestratorAgent {
    // Store proposed plans
    private proposedPlans: Map<string, ProposedPlan> = new Map();
    private lastProposedPlanId: string | null = null;
    private debugMode: boolean = true;

    // Output channel for debugging
    private outputChannel: vscode.OutputChannel;

    // AI Classification components
    private intentClassifier: IntentClassifier;
    private conversationContext: ConversationContext;
    private aiService: AIClassificationService;

    // State tracking
    private awaitingClarification: boolean = false;
    private lastUncertainClassification: IntentClassification | null = null;

    constructor(
        context: vscode.ExtensionContext,
        dispatcher: VSCodeMasterDispatcher,
        enableDebug: boolean = false,
        outputChannel?: vscode.OutputChannel
    ) {
        super(context, dispatcher);

        // Use provided output channel or create new one
        this.outputChannel = outputChannel || vscode.window.createOutputChannel('KI AutoAgent Orchestrator Debug');
        this.debugMode = enableDebug;

        // Initialize AI Classification components
        this.aiService = new AIClassificationService();
        this.conversationContext = new ConversationContext();
        this.intentClassifier = new IntentClassifier(this.aiService, this.conversationContext);

        // Load saved learning data if available
        this.loadLearningData(context);

        // Override config to add new commands
        this.config.commands?.push(
            { name: 'execute-plan', description: 'Execute the proposed plan', handler: 'handleExecutePlan' },
            { name: 'show-plan', description: 'Show the current proposed plan', handler: 'handleShowPlan' }
        );

        this.debug('Enhanced Orchestrator initialized with AI-based intent classification');
    }

    /**
     * Debug logging
     */
    private debug(message: string, data?: any): void {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}`;

        // Log to output channel
        this.outputChannel.appendLine(logMessage);
        if (data) {
            this.outputChannel.appendLine(JSON.stringify(data, null, 2));
        }

        // Also log to console
        console.log(`[EnhancedOrchestrator] ${message}`, data || '');
    }

    /**
     * Override handleRequest to intercept "mach das" and similar confirmations
     */
    public async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        const prompt = request.prompt;

        this.debug(`Received request: "${prompt}"`);

        // Add to conversation context
        this.conversationContext.addMessage({
            role: 'user',
            content: prompt,
            timestamp: new Date()
        });

        // Get last proposed plan
        const lastPlan = this.lastProposedPlanId
            ? this.proposedPlans.get(this.lastProposedPlanId) || null
            : null;

        // Use AI to classify user intent
        const classification = await this.detectUserIntent(prompt, lastPlan, stream);

        this.debug('Intent classification result', classification);

        // Handle based on classified intent
        switch (classification.intent) {
            case 'confirm_execution':
                if (lastPlan && classification.confidence > 0.7) {
                    this.debug('High confidence execution confirmation');
                    this.conversationContext.learnFromInteraction('confirm_execution', true);
                    await this.executePlan(lastPlan, stream, token);
                } else if (lastPlan && classification.confidence > 0.5) {
                    stream.markdown(`🤔 Ich bin zu ${(classification.confidence * 100).toFixed(0)}% sicher, dass Sie den Plan ausführen möchten. Ist das korrekt?`);
                    this.awaitingClarification = true;
                } else {
                    stream.markdown('❌ Kein Plan zum Ausführen vorhanden. Bitte beschreiben Sie zuerst, was Sie tun möchten.');
                }
                return;

            case 'request_clarification':
                if (lastPlan) {
                    await this.providePlanDetails(lastPlan, stream);
                } else {
                    stream.markdown('Gerne erkläre ich mehr. Was möchten Sie genau wissen?');
                }
                return;

            case 'modify_plan':
                if (lastPlan) {
                    await this.handlePlanModification(prompt, classification, stream);
                } else {
                    stream.markdown('Es gibt keinen Plan zum Modifizieren. Möchten Sie einen neuen erstellen?');
                }
                return;

            case 'reject':
                if (lastPlan) {
                    this.clearProposedPlan();
                    this.conversationContext.learnFromInteraction('reject', true);
                    stream.markdown('✅ Plan wurde verworfen. Wie kann ich Ihnen anders helfen?');
                } else {
                    stream.markdown('Verstanden. Wie kann ich Ihnen helfen?');
                }
                return;

            case 'new_request':
                // Handle as new request
                await super.handleRequest(request, context, stream, token);
                return;

            case 'uncertain':
            default:
                if (classification.confidence < 0.4) {
                    await this.handleUncertainIntent(classification, stream);
                } else {
                    // Try to handle as new request
                    await super.handleRequest(request, context, stream, token);
                }
                return;
        }
    }

    /**
     * AI-based intent detection
     */
    private async detectUserIntent(
        prompt: string,
        lastPlan: ProposedPlan | null,
        stream: vscode.ChatResponseStream
    ): Promise<IntentClassification> {
        this.debug('Starting AI intent classification');

        try {
            // Get conversation history
            const history = this.conversationContext.getRecentContext(5);

            // Check if AI classification is enabled
            const config = vscode.workspace.getConfiguration('kiAutoAgent.ai.intentClassification');
            const aiEnabled = config.get('enabled', true);

            if (!aiEnabled) {
                // Fallback to simple classification
                return this.getFallbackClassification(prompt, lastPlan);
            }

            // Use AI classifier
            const classification = await this.intentClassifier.classifyIntent(
                prompt,
                lastPlan,
                history,
                {
                    minConfidence: config.get('confidenceThreshold', 0.7),
                    detectSarcasm: true,
                    analyzeUrgency: true,
                    timeout: 10000
                }
            );

            // Handle low confidence
            if (classification.confidence < 0.6 && !this.awaitingClarification) {
                await this.handleUncertainIntent(classification, stream);
            }

            return classification;
        } catch (error) {
            this.debug('AI classification failed, using fallback', error);
            return this.getFallbackClassification(prompt, lastPlan);
        }
    }

    /**
     * Simple fallback classification when AI is unavailable
     */
    private getFallbackClassification(
        prompt: string,
        lastPlan: ProposedPlan | null
    ): IntentClassification {
        const lowerPrompt = prompt.toLowerCase();

        // Simple keyword matching as fallback
        if (/(mach das|ja|ok|los|start|go)/i.test(lowerPrompt) && lastPlan) {
            return {
                intent: 'confirm_execution',
                confidence: 0.6,
                reasoning: 'Keyword-based fallback',
                suggestedAction: 'Execute plan',
                contextFactors: {
                    timeElapsed: lastPlan ? (Date.now() - lastPlan.timestamp.getTime()) / 1000 : 0,
                    previousIntent: null,
                    userTone: 'neutral',
                    hasConditions: false,
                    language: 'de',
                    sarcasmDetected: false,
                    urgencyLevel: 'medium'
                }
            };
        }

        return {
            intent: 'new_request',
            confidence: 0.5,
            reasoning: 'Fallback classification',
            suggestedAction: 'Process as new request',
            contextFactors: {
                timeElapsed: 0,
                previousIntent: null,
                userTone: 'neutral',
                hasConditions: false,
                language: 'unknown',
                sarcasmDetected: false,
                urgencyLevel: 'medium'
            }
        };
    }

    /**
     * Handle uncertain intent with clarification
     */
    private async handleUncertainIntent(
        classification: IntentClassification,
        stream: vscode.ChatResponseStream
    ): Promise<void> {
        const clarificationMessages: Record<string, string> = {
            'confirm_execution': `Ich bin mir nicht sicher, ob Sie den Plan ausführen möchten. Bitte bestätigen Sie mit "Ja, ausführen" oder sagen Sie mir, was Sie stattdessen tun möchten.`,
            'modify_plan': `Möchten Sie Änderungen am Plan vornehmen? Bitte beschreiben Sie, was angepasst werden soll.`,
            'reject': `Soll ich den Plan verwerfen? Sagen Sie "Ja, verwerfen" oder erklären Sie, was Sie möchten.`,
            'uncertain': `Ich bin unsicher, was Sie möchten. Optionen:\n• "Plan ausführen" - Führt den vorgeschlagenen Plan aus\n• "Mehr Details" - Zeigt weitere Informationen\n• "Neuer Plan" - Erstellt einen neuen Plan`
        };

        const message = clarificationMessages[classification.intent] || clarificationMessages['uncertain'];
        stream.markdown(`🤔 ${message}\n\n*Confidence: ${(classification.confidence * 100).toFixed(0)}%*`);
        stream.markdown(`\n*AI Reasoning: ${classification.reasoning}*`);

        this.awaitingClarification = true;
        this.lastUncertainClassification = classification;
    }

    /**
     * Check if this is a UI/button query
     */
    private isUIQuery(prompt: string): boolean {
        const uiPatterns = [
            'button',
            'buttons',
            'ui',
            'user interface',
            'oberfläche',
            'schaltfläche',
            'komponente',
            'element'
        ];

        return uiPatterns.some(pattern => prompt.includes(pattern));
    }

    /**
     * Handle UI queries with proper workflow
     */
    private async handleUIQuery(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        this.debug('Handling UI query');

        stream.markdown(`## 🎨 UI Component Analysis\n\n`);
        stream.markdown(`Um die passenden Buttons für Ihr Projekt zu bestimmen, werde ich eine umfassende Analyse durchführen.\n\n`);

        // Create a plan for UI analysis
        const plan: ProposedPlan = {
            id: `plan-${Date.now()}`,
            description: 'UI Component Analysis and Recommendations',
            originalPrompt: prompt,
            prompt: prompt,
            timestamp: new Date(),
            status: 'proposed',
            steps: [
                {
                    order: 1,
                    agentName: 'architect',
                    task: 'Analyze project architecture and UI framework',
                    description: 'Projektarchitektur analysieren und UI-Framework identifizieren',
                    estimatedDuration: 30
                },
                {
                    order: 2,
                    agentName: 'codesmith',
                    task: 'Scan for existing UI components and buttons',
                    description: 'Vorhandene UI-Komponenten und Buttons im Code identifizieren',
                    estimatedDuration: 30
                },
                {
                    order: 3,
                    agentName: 'research',
                    task: 'Research best practices for UI components',
                    description: 'Best Practices und moderne UI-Patterns recherchieren',
                    estimatedDuration: 45
                },
                {
                    order: 4,
                    agentName: 'codesmith',
                    task: 'Implement recommended button components',
                    description: 'Empfohlene Button-Komponenten implementieren',
                    estimatedDuration: 60
                },
                {
                    order: 5,
                    agentName: 'reviewer',
                    task: 'Review implementation for accessibility and quality',
                    description: 'Implementierung auf Barrierefreiheit und Qualität prüfen',
                    estimatedDuration: 30
                },
                {
                    order: 6,
                    agentName: 'docubot',
                    task: 'Document UI component usage',
                    description: 'Verwendung der UI-Komponenten dokumentieren',
                    estimatedDuration: 30
                }
            ]
        };

        // Store the plan
        this.proposedPlans.set(plan.id, plan);
        this.lastProposedPlanId = plan.id;

        this.debug('Created and stored UI analysis plan', { planId: plan.id });

        // Display the plan
        stream.markdown(`### 📋 Geplanter Ablauf:\n\n`);

        for (const step of plan.steps) {
            stream.markdown(`**${step.order}. ${step.description}**\n`);
            stream.markdown(`   Agent: @${step.agentName}\n`);
            stream.markdown(`   Task: ${step.task}\n\n`);
        }

        stream.markdown(`### ✨ Was Sie davon erwarten können:\n\n`);
        stream.markdown(`- **Projektspezifische Empfehlungen**: Buttons passend zu Ihrer Architektur\n`);
        stream.markdown(`- **Best Practices**: Moderne und barrierefreie UI-Komponenten\n`);
        stream.markdown(`- **Konsistentes Design**: Einheitlicher Look & Feel\n`);
        stream.markdown(`- **Dokumentation**: Klare Anleitung zur Verwendung\n\n`);

        stream.markdown(`### 🚀 Bereit zum Start?\n\n`);
        stream.markdown(`Sagen Sie einfach **"mach das"** oder **"ja"**, und ich koordiniere die Agenten für Sie.\n`);
        stream.markdown(`\n💡 *Tipp: Sie können auch einzelne Schritte überspringen oder anpassen.*\n`);
    }

    /**
     * Execute a stored plan
     */
    private async executePlan(
        plan: ProposedPlan,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        this.debug('Starting plan execution', {
            planId: plan.id,
            steps: plan.steps.length
        });

        stream.markdown(`## ⚡ Führe Plan aus: ${plan.description}\n\n`);
        stream.progress('🔄 Starte Workflow-Ausführung...');

        // Create workflow from plan
        const workflow = (this as any).workflowEngine.createWorkflow(plan.description);

        this.debug('Created workflow', { workflowId: workflow.id });

        // Add nodes for each step
        for (const step of plan.steps) {
            const node: WorkflowNode = {
                id: `step-${step.order}`,
                type: 'task',
                agentId: step.agentName,
                task: step.task,
                dependencies: step.dependencies
            };

            (this as any).workflowEngine.addNode(workflow.id, node);

            this.debug(`Added workflow node`, {
                nodeId: node.id,
                agent: step.agentName,
                task: step.task
            });
        }

        // Add edges for sequential execution
        for (let i = 0; i < plan.steps.length - 1; i++) {
            (this as any).workflowEngine.addEdge(workflow.id, {
                from: `step-${plan.steps[i].order}`,
                to: `step-${plan.steps[i + 1].order}`
            });
        }

        // Display execution progress
        stream.markdown(`### 📊 Workflow-Schritte:\n\n`);

        for (const step of plan.steps) {
            stream.markdown(`**Schritt ${step.order}:** @${step.agentName} - ${step.description}\n`);
        }

        stream.markdown(`\n### ⚙️ Ausführung:\n\n`);

        // Execute each step with detailed feedback
        for (const step of plan.steps) {
            const stepStartTime = Date.now();

            stream.markdown(`\n🔄 **Schritt ${step.order}/${plan.steps.length}:** @${step.agentName}\n`);
            stream.markdown(`   *${step.description}*\n`);
            stream.progress(`Führe Schritt ${step.order} aus: ${step.agentName}...`);

            this.debug(`Executing step ${step.order}`, {
                agent: step.agentName,
                task: step.task
            });

            try {
                // Create task request
                const taskRequest: TaskRequest = {
                    prompt: step.task,
                    context: {
                        workspaceFolder: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
                        currentFile: vscode.window.activeTextEditor?.document.uri.fsPath || ''
                    }
                } as TaskRequest;

                // Get the agent
                const agent = (this.dispatcher as any).getAgent(step.agentName);
                if (!agent) {
                    throw new Error(`Agent ${step.agentName} nicht gefunden`);
                }

                // Execute the step
                const workflowStep: WorkflowStep = {
                    id: `step-${step.order}`,
                    agent: step.agentName,
                    description: step.description,
                    input: step.task
                };

                const result = await agent.executeStep(workflowStep, taskRequest, []);

                const stepDuration = Date.now() - stepStartTime;

                this.debug(`Step ${step.order} completed`, {
                    agent: step.agentName,
                    status: result.status,
                    duration: stepDuration
                });

                if (result.status === 'success') {
                    stream.markdown(`   ✅ Erfolgreich abgeschlossen (${(stepDuration / 1000).toFixed(1)}s)\n`);

                    // Show a snippet of the result if available
                    if (result.content) {
                        const preview = result.content.substring(0, 200);
                        stream.markdown(`   > ${preview}${result.content.length > 200 ? '...' : ''}\n`);
                    }
                } else {
                    stream.markdown(`   ⚠️ Schritt mit Warnungen abgeschlossen\n`);
                    if (result.error) {
                        stream.markdown(`   > Fehler: ${result.error}\n`);
                    }
                }

            } catch (error) {
                const errorMessage = (error as any).message || 'Unbekannter Fehler';

                this.debug(`Step ${step.order} failed`, {
                    agent: step.agentName,
                    error: errorMessage
                });

                stream.markdown(`   ❌ Fehler: ${errorMessage}\n`);
                stream.markdown(`   > Überspringe diesen Schritt und fahre fort...\n`);
            }
        }

        stream.markdown(`\n### ✅ Plan-Ausführung abgeschlossen\n`);
        stream.markdown(`\nAlle Schritte wurden verarbeitet. Die Ergebnisse stehen nun zur Verfügung.\n`);

        // Clear the executed plan
        this.proposedPlans.delete(plan.id);
        if (this.lastProposedPlanId === plan.id) {
            this.lastProposedPlanId = null;
        }

        this.debug('Plan execution completed and cleared from storage', { planId: plan.id });
    }

    /**
     * Handle simple task with plan storage
     */
    private async handleSimpleTaskWithPlan(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        this.debug('Handling simple task', { prompt: prompt.substring(0, 100) });

        // Check if this looks like it needs a plan
        if (this.shouldCreatePlan(prompt)) {
            await this.createAndProposePlan(prompt, stream, token);
        } else {
            // Let the parent class handle as a simple task without plan
            // Since handleSimpleTask is private in parent, we can't call it directly
            // Instead, we'll handle it here
            stream.markdown(`Processing your request: ${prompt}`);
        }
    }

    /**
     * Handle moderate task with plan storage
     */
    private async handleModerateTaskWithPlan(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        this.debug('Handling moderate task', { prompt: prompt.substring(0, 100) });

        // Always create a plan for moderate tasks
        await this.createAndProposePlan(prompt, stream, token);
    }

    /**
     * Handle complex task with plan storage
     */
    private async handleComplexTaskWithPlan(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        this.debug('Handling complex task', { prompt: prompt.substring(0, 100) });

        // Always create a plan for complex tasks
        await this.createAndProposePlan(prompt, stream, token);
    }

    /**
     * Check if we should create a plan
     */
    private shouldCreatePlan(prompt: string): boolean {
        // Create a plan if the prompt is asking about capabilities or multi-step tasks
        const planIndicators = [
            'welche',
            'was kann',
            'was könnt',
            'zeig',
            'liste',
            'erkläre',
            'wie',
            'implementier',
            'erstelle',
            'baue'
        ];

        const lowerPrompt = prompt.toLowerCase();
        return planIndicators.some(indicator => lowerPrompt.includes(indicator));
    }

    /**
     * Create and propose a plan instead of executing immediately
     */
    private async createAndProposePlan(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        this.debug('Creating plan for task', { prompt: prompt.substring(0, 100) });

        // Decompose the task (access private method via any cast)
        const decomposition = await (this as any).decomposeTask(prompt);

        // Create plan from decomposition
        const plan: ProposedPlan = {
            id: `plan-${Date.now()}`,
            description: prompt,
            originalPrompt: prompt,
            prompt: prompt,  // Keep for backward compatibility
            timestamp: new Date(),
            status: 'proposed',
            steps: decomposition.subtasks.map((subtask: any, index: number) => ({
                order: index + 1,
                agentName: subtask.agent,
                task: subtask.description,
                description: subtask.expectedOutput,
                dependencies: subtask.dependencies,
                estimatedDuration: 30  // Default estimate
            }))
        };

        // Store the plan
        this.proposedPlans.set(plan.id, plan);
        this.lastProposedPlanId = plan.id;

        this.debug('Created and stored plan', {
            planId: plan.id,
            steps: plan.steps.length
        });

        // Display the plan to user
        stream.markdown(`## 📋 Vorgeschlagener Plan\n\n`);
        stream.markdown(`Um Ihre Anfrage zu bearbeiten, schlage ich folgendes Vorgehen vor:\n\n`);

        for (const step of plan.steps) {
            stream.markdown(`**${step.order}. ${step.agentName}**\n`);
            stream.markdown(`   ${step.description}\n\n`);
        }

        stream.markdown(`### 🚀 Bereit zur Ausführung?\n\n`);
        stream.markdown(`Wenn Sie mit diesem Plan einverstanden sind, sagen Sie einfach **"mach das"** oder **"ja"**.\n`);
        stream.markdown(`\nSie können auch einzelne Schritte anpassen oder weitere Details hinzufügen.\n`);
    }

    /**
     * Handle show plan command
     */
    private async handleShowPlan(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        if (!this.lastProposedPlanId) {
            stream.markdown('❌ Kein Plan vorhanden.');
            return;
        }

        const plan = this.proposedPlans.get(this.lastProposedPlanId);
        if (!plan) {
            stream.markdown('❌ Plan nicht mehr verfügbar.');
            return;
        }

        stream.markdown(`## 📋 Aktueller Plan\n\n`);
        stream.markdown(`**Beschreibung:** ${plan.description}\n`);
        stream.markdown(`**Erstellt:** ${plan.timestamp.toLocaleString()}\n\n`);

        for (const step of plan.steps) {
            stream.markdown(`**${step.order}. @${step.agentName}**\n`);
            stream.markdown(`   ${step.description}\n\n`);
        }
    }

    /**
     * Handle execute plan command
     */
    private async handleExecutePlan(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        if (!this.lastProposedPlanId) {
            stream.markdown('❌ Kein Plan zum Ausführen vorhanden.');
            return;
        }

        const plan = this.proposedPlans.get(this.lastProposedPlanId);
        if (!plan) {
            stream.markdown('❌ Plan nicht mehr verfügbar.');
            return;
        }

        await this.executePlan(plan, stream, token);
    }

    /**
     * Show debug channel
     */
    public showDebugOutput(): void {
        this.outputChannel.show();
    }

    /**
     * Provide detailed information about a plan
     */
    private async providePlanDetails(
        plan: ProposedPlan,
        stream: vscode.ChatResponseStream
    ): Promise<void> {
        stream.markdown(`### 📋 Plan Details: ${plan.description}\n\n`);
        stream.markdown(`**Created:** ${new Date(plan.timestamp).toLocaleString()}\n`);
        stream.markdown(`**Original Request:** ${plan.originalPrompt}\n\n`);
        stream.markdown(`**Steps:**\n`);

        for (const step of plan.steps) {
            stream.markdown(`${step.order}. **${step.agentName}**: ${step.description}\n`);
            stream.markdown(`   Task: ${step.task}\n`);
            if (step.estimatedDuration) {
                stream.markdown(`   Estimated: ${step.estimatedDuration}s\n`);
            }
            stream.markdown(`\n`);
        }

        stream.markdown(`\n*You can say "execute" to run this plan or "modify" to make changes.*`);
    }

    /**
     * Handle plan modification request
     */
    private async handlePlanModification(
        prompt: string,
        classification: IntentClassification,
        stream: vscode.ChatResponseStream
    ): Promise<void> {
        stream.markdown(`🔧 I understand you want to modify the plan.\n\n`);
        stream.markdown(`Current plan: ${this.proposedPlans.get(this.lastProposedPlanId!)?.description}\n\n`);
        stream.markdown(`Please describe what changes you'd like to make, or I can create a new plan based on your requirements.`);

        // Mark the plan as modified
        const plan = this.proposedPlans.get(this.lastProposedPlanId!);
        if (plan) {
            plan.status = 'modified';
        }

        // Learn from this interaction
        this.conversationContext.learnFromInteraction('modify_plan', true);
    }

    /**
     * Clear proposed plan
     */
    private clearProposedPlan(): void {
        if (this.lastProposedPlanId) {
            const plan = this.proposedPlans.get(this.lastProposedPlanId);
            if (plan) {
                plan.status = 'rejected';
                this.conversationContext.addProposedPlan(plan);
            }
            this.proposedPlans.delete(this.lastProposedPlanId);
            this.lastProposedPlanId = null;
        }
        this.awaitingClarification = false;
        this.lastUncertainClassification = null;
    }

    /**
     * Load learning data from persistent storage
     */
    private loadLearningData(context: vscode.ExtensionContext): void {
        try {
            const savedData = context.globalState.get<string>('orchestrator.learning.data');
            if (savedData) {
                this.conversationContext.importLearningData(savedData);
                this.debug('Loaded learning data from storage');
            }
        } catch (error) {
            this.debug('Failed to load learning data', error);
        }
    }

    /**
     * Save learning data to persistent storage
     */
    private saveLearningData(context: vscode.ExtensionContext): void {
        try {
            const learningData = this.conversationContext.exportLearningData();
            context.globalState.update('orchestrator.learning.data', learningData);
            this.debug('Saved learning data to storage');
        } catch (error) {
            this.debug('Failed to save learning data', error);
        }
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        // Save learning data before disposing
        if ((global as any).extensionContext) {
            this.saveLearningData((global as any).extensionContext);
        }

        this.outputChannel.dispose();
        this.proposedPlans.clear();
        this.conversationContext.clear();
        this.intentClassifier.clearCache();
        this.aiService.clearCache();
        // Parent class doesn't have dispose method
    }
}