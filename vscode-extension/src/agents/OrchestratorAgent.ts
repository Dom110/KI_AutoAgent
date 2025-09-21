/**
 * Advanced Orchestrator Agent with Task Decomposition and Intelligent Workflow Management
 * Uses graph-based workflow execution, parallel processing, and memory-enhanced orchestration
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { OpenAIService } from '../utils/OpenAIService';
import { AgentRegistry } from '../core/AgentRegistry';
import { WorkflowEngine, WorkflowNode, ExecutionPlan } from '../core/WorkflowEngine';
import { MemoryManager } from '../core/MemoryManager';
import { SharedContextManager, getSharedContext } from '../core/SharedContextManager';
import { AgentCommunicationBus, getCommunicationBus, MessageType } from '../core/AgentCommunicationBus';
import { MemoryType, TaskMemory, TaskStep as MemoryTaskStep } from '../types/Memory';

interface TaskDecomposition {
    mainGoal: string;
    complexity: 'simple' | 'moderate' | 'complex';
    subtasks: SubTask[];
    dependencies: TaskDependency[];
    estimatedDuration: number;
    requiredAgents: string[];
    parallelizable: boolean;
}

interface SubTask {
    id: string;
    description: string;
    agent: string;
    priority: number;
    dependencies: string[];
    expectedOutput: string;
    estimatedDuration: number;
}

interface TaskDependency {
    from: string;
    to: string;
    type: 'sequential' | 'parallel' | 'conditional';
    condition?: string;
}

export class OrchestratorAgent extends ChatAgent {
    private openAIService: OpenAIService;
    private workflowEngine: WorkflowEngine;
    private memoryManager: MemoryManager;
    private sharedContext: SharedContextManager;
    private communicationBus: AgentCommunicationBus;
    private activeWorkflows: Map<string, string> = new Map(); // workflowId -> description

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.orchestrator',
            name: 'ki',
            fullName: 'Advanced KI AutoAgent Orchestrator',
            description: 'Intelligent task orchestration with decomposition, parallel execution, and memory',
            model: 'gpt-5-2025-09-12',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'orchestrator-icon.svg'),
            capabilities: [
                'Task Decomposition',
                'Parallel Execution',
                'Dynamic Workflow Adjustment',
                'Agent Conflict Resolution',
                'Memory-Based Learning',
                'Multi-Agent Collaboration'
            ],
            commands: [
                { name: 'task', description: 'Execute complex task with intelligent decomposition', handler: 'handleTaskCommand' },
                { name: 'agents', description: 'Show available specialized agents', handler: 'handleAgentsCommand' },
                { name: 'workflow', description: 'Create advanced multi-step workflow', handler: 'handleWorkflowCommand' },
                { name: 'decompose', description: 'Decompose complex task into subtasks', handler: 'handleDecomposeCommand' },
                { name: 'parallel', description: 'Execute tasks in parallel', handler: 'handleParallelCommand' }
            ]
        };

        super(config, context, dispatcher);

        // Initialize advanced systems
        this.openAIService = new OpenAIService();
        this.workflowEngine = new WorkflowEngine();
        this.memoryManager = new MemoryManager({
            maxMemories: 10000,
            similarityThreshold: 0.7,
            patternExtractionEnabled: true
        });
        this.sharedContext = getSharedContext();
        this.communicationBus = getCommunicationBus();

        // Register for inter-agent communication
        this.registerCommunicationHandlers();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        const command = request.command;
        const prompt = request.prompt;

        // Immediate feedback with intelligence indicator
        stream.progress('🧠 Advanced Orchestrator analyzing complexity and decomposing task...');

        this.log(`Advanced Orchestrator processing: ${prompt.substring(0, 100)}...`);

        // Build context with memory
        const enhancedRequest = await this.buildContextWithMemory({
            prompt,
            context: { chatHistory: context.history }
        });

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            // Analyze task complexity
            const complexity = await this.analyzeTaskComplexity(prompt);

            if (complexity === 'simple') {
                await this.handleSimpleTask(prompt, stream, token);
            } else if (complexity === 'moderate') {
                await this.handleModerateTask(prompt, stream, token);
            } else {
                await this.handleComplexTask(prompt, stream, token);
            }
        }
    }

    /**
     * Analyze task complexity to determine orchestration strategy
     */
    private async analyzeTaskComplexity(prompt: string): Promise<'simple' | 'moderate' | 'complex'> {
        // Search memory for similar tasks
        const similarTasks = await this.memoryManager.search(prompt, {
            k: 5,
            type: MemoryType.EPISODIC
        });

        // If we have handled similar tasks, use learned complexity
        if (similarTasks.length > 0) {
            const complexities = similarTasks
                .map(t => (t.entry.content as any).complexity)
                .filter(Boolean);

            if (complexities.length > 0) {
                // Return most common complexity
                const counts = complexities.reduce((acc: any, c: string) => {
                    acc[c] = (acc[c] || 0) + 1;
                    return acc;
                }, {});

                return Object.entries(counts)
                    .sort(([, a]: any, [, b]: any) => b - a)[0][0] as any;
            }
        }

        // Analyze prompt for complexity indicators
        const complexityIndicators = {
            complex: [
                /build.*system/i,
                /implement.*architecture/i,
                /create.*application/i,
                /develop.*platform/i,
                /design.*and.*implement/i,
                /multiple.*components/i,
                /full.*stack/i,
                /end.*to.*end/i,
                /microservices/i,
                /distributed/i
            ],
            moderate: [
                /create.*feature/i,
                /implement.*api/i,
                /add.*functionality/i,
                /refactor/i,
                /optimize/i,
                /debug.*and.*fix/i,
                /integrate/i,
                /migrate/i
            ],
            simple: [
                /fix.*bug/i,
                /update.*documentation/i,
                /write.*function/i,
                /create.*file/i,
                /explain/i,
                /what.*is/i,
                /how.*to/i,
                /show.*me/i,
                /list/i
            ]
        };

        // Check indicators
        for (const [level, patterns] of Object.entries(complexityIndicators)) {
            if (patterns.some(p => p.test(prompt))) {
                return level as any;
            }
        }

        // Default to moderate
        return 'moderate';
    }

    /**
     * Handle simple tasks with direct routing
     */
    private async handleSimpleTask(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        stream.markdown(`## ⚡ Simple Task Execution\n\n`);

        // Get best agent for the task
        const registry = AgentRegistry.getInstance();
        const agent = registry.suggestAgentForTask(prompt);

        if (agent && agent !== 'orchestrator') {
            stream.markdown(`**Routing to @${agent}**\n\n`);

            // Create simple workflow
            const workflow = this.workflowEngine.createWorkflow(`Simple: ${prompt}`);

            const node: WorkflowNode = {
                id: 'execute',
                type: 'task',
                agentId: agent,
                task: prompt
            };

            this.workflowEngine.addNode(workflow.id, node);

            // Execute
            const results = await this.executeWorkflowWithProgress(
                workflow.id,
                prompt,
                stream
            );

            // Display results
            this.displayResults(results, stream);

            // Store in memory
            await this.storeTaskMemory(prompt, 'simple', workflow.id, results);
        } else {
            // Handle directly
            await this.handleDirectResponse(prompt, stream);
        }
    }

    /**
     * Handle moderate complexity tasks with sequential workflow
     */
    private async handleModerateTask(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        stream.markdown(`## 🔄 Moderate Task Workflow\n\n`);

        // Decompose into subtasks
        const decomposition = await this.decomposeTask(prompt);

        stream.markdown(`**Identified ${decomposition.subtasks.length} subtasks**\n\n`);

        // Create workflow
        const workflow = this.workflowEngine.createWorkflow(`Moderate: ${prompt}`);

        // Add nodes for each subtask
        decomposition.subtasks.forEach(subtask => {
            const node: WorkflowNode = {
                id: subtask.id,
                type: 'task',
                agentId: subtask.agent,
                task: subtask.description,
                dependencies: subtask.dependencies
            };

            this.workflowEngine.addNode(workflow.id, node);
        });

        // Add edges based on dependencies
        decomposition.dependencies.forEach(dep => {
            this.workflowEngine.addEdge(workflow.id, {
                from: dep.from,
                to: dep.to
            });
        });

        // Display execution plan
        const plan = this.workflowEngine.createExecutionPlan(workflow.id);
        this.displayExecutionPlan(plan, stream);

        // Execute workflow
        const results = await this.executeWorkflowWithProgress(
            workflow.id,
            prompt,
            stream
        );

        // Display results
        this.displayResults(results, stream);

        // Store in memory
        await this.storeTaskMemory(prompt, 'moderate', workflow.id, results);
    }

    /**
     * Handle complex tasks with parallel execution and collaboration
     */
    private async handleComplexTask(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        stream.markdown(`## 🚀 Complex Task Orchestration\n\n`);
        stream.markdown(`**Initiating advanced multi-agent collaboration...**\n\n`);

        // Decompose into subtasks
        const decomposition = await this.decomposeTask(prompt);

        stream.markdown(`### 📊 Task Analysis\n`);
        stream.markdown(`- **Complexity:** ${decomposition.complexity}\n`);
        stream.markdown(`- **Subtasks:** ${decomposition.subtasks.length}\n`);
        stream.markdown(`- **Required Agents:** ${decomposition.requiredAgents.join(', ')}\n`);
        stream.markdown(`- **Parallelizable:** ${decomposition.parallelizable ? 'Yes' : 'No'}\n`);
        stream.markdown(`- **Estimated Duration:** ${decomposition.estimatedDuration}ms\n\n`);

        // Start collaboration session
        const session = await this.communicationBus.startCollaboration(
            { task: prompt, decomposition },
            decomposition.requiredAgents,
            'orchestrator'
        );

        stream.markdown(`**Collaboration Session Started:** ${session.id}\n\n`);

        // Create advanced workflow with parallel execution
        const workflow = this.workflowEngine.createWorkflow(`Complex: ${prompt}`);

        // Group parallelizable tasks
        const parallelGroups = this.groupParallelTasks(decomposition);

        // Create workflow nodes
        parallelGroups.forEach((group, index) => {
            if (group.length > 1) {
                // Create parallel node
                const parallelNode: WorkflowNode = {
                    id: `parallel_${index}`,
                    type: 'parallel',
                    children: group.map(t => t.id)
                };

                this.workflowEngine.addNode(workflow.id, parallelNode);

                // Add task nodes
                group.forEach(subtask => {
                    const taskNode: WorkflowNode = {
                        id: subtask.id,
                        type: 'task',
                        agentId: subtask.agent,
                        task: subtask.description
                    };
                    this.workflowEngine.addNode(workflow.id, taskNode);
                });
            } else {
                // Single task node
                const subtask = group[0];
                const taskNode: WorkflowNode = {
                    id: subtask.id,
                    type: 'task',
                    agentId: subtask.agent,
                    task: subtask.description,
                    dependencies: subtask.dependencies
                };
                this.workflowEngine.addNode(workflow.id, taskNode);
            }
        });

        // Add edges for dependencies
        decomposition.dependencies.forEach(dep => {
            this.workflowEngine.addEdge(workflow.id, {
                from: dep.from,
                to: dep.to,
                condition: dep.condition ? this.createCondition(dep.condition) : undefined
            });
        });

        // Display execution plan
        const plan = this.workflowEngine.createExecutionPlan(workflow.id);
        this.displayAdvancedExecutionPlan(plan, stream);

        // Execute with checkpointing
        stream.markdown(`### ⚡ Execution Progress\n\n`);

        const results = await this.executeComplexWorkflow(
            workflow.id,
            prompt,
            session.id,
            stream
        );

        // Complete collaboration
        this.communicationBus.completeCollaboration(session.id, results);

        // Display comprehensive results
        this.displayComplexResults(results, stream);

        // Store in memory with patterns
        await this.storeComplexTaskMemory(prompt, decomposition, workflow.id, results);

        // Extract and store patterns
        await this.extractAndStorePatterns(decomposition, results);
    }

    /**
     * Decompose task into subtasks using AI
     */
    private async decomposeTask(prompt: string): Promise<TaskDecomposition> {
        // Check memory for similar decompositions
        const similarTasks = await this.memoryManager.search(prompt, {
            k: 3,
            type: MemoryType.PROCEDURAL
        });

        if (similarTasks.length > 0 && similarTasks[0].similarity > 0.85) {
            // Reuse previous decomposition
            return (similarTasks[0].entry.content as any).decomposition;
        }

        // Use AI to decompose
        const systemPrompt = `You are an expert task decomposer. Your job is to capture ALL requested changes comprehensively.

CRITICAL REQUIREMENTS:
1. **CAPTURE EVERY CHANGE**: Break down the task to ensure NO requested change is missed
2. **BE EXHAUSTIVE**: It's better to have too many subtasks than too few
3. **DETAIL EVERYTHING**: Each distinct modification should be its own subtask
4. **INCLUDE VALIDATION**: Add review/testing steps after implementation
5. **NO LIMITS**: Create as many subtasks as needed (10, 20, 50+ if necessary)

${this.getSystemContextPrompt()}

Analyze the task and provide a JSON response with:
{
  "mainGoal": "primary objective",
  "complexity": "simple|moderate|complex",
  "subtasks": [
    {
      "id": "unique_id",
      "description": "DETAILED description of what to do",
      "agent": "best agent for this",
      "priority": 1-5,
      "dependencies": ["other_task_ids"],
      "expectedOutput": "what this produces",
      "estimatedDuration": milliseconds,
      "files": ["specific files to modify if known"]
    }
  ],
  "dependencies": [
    {
      "from": "task_id",
      "to": "task_id",
      "type": "sequential|parallel|conditional",
      "condition": "optional condition"
    }
  ],
  "estimatedDuration": total_milliseconds,
  "requiredAgents": ["agent1", "agent2"],
  "parallelizable": boolean,
  "verificationSteps": ["how to verify completeness"]
}

IMPORTANT: Err on the side of being TOO detailed rather than missing something.
Each UI change, each function modification, each bug fix should be its own subtask.

Available agents: architect, codesmith, docu, reviewer, fixer, tradestrat, opus-arbitrator, research`;

        const response = await this.openAIService.chat([
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `Decompose this task: ${prompt}` }
        ]);

        try {
            const decomposition = JSON.parse(response);

            // Store in memory for future use
            await this.memoryManager.store(
                'orchestrator',
                { prompt, decomposition },
                MemoryType.PROCEDURAL,
                { importance: 0.8 }
            );

            return decomposition;
        } catch (error) {
            // Fallback to simple decomposition
            return this.createSimpleDecomposition(prompt);
        }
    }

    /**
     * Create simple decomposition as fallback
     */
    private createSimpleDecomposition(prompt: string): TaskDecomposition {
        const registry = AgentRegistry.getInstance();
        const agent = registry.suggestAgentForTask(prompt) || 'codesmith';

        return {
            mainGoal: prompt,
            complexity: 'simple',
            subtasks: [{
                id: 'task_1',
                description: prompt,
                agent,
                priority: 1,
                dependencies: [],
                expectedOutput: 'Task result',
                estimatedDuration: 5000
            }],
            dependencies: [],
            estimatedDuration: 5000,
            requiredAgents: [agent],
            parallelizable: false
        };
    }

    /**
     * Group tasks that can be executed in parallel
     */
    private groupParallelTasks(decomposition: TaskDecomposition): SubTask[][] {
        const groups: SubTask[][] = [];
        const processed = new Set<string>();

        // Sort by priority
        const sorted = [...decomposition.subtasks].sort((a, b) => a.priority - b.priority);

        sorted.forEach(task => {
            if (processed.has(task.id)) return;

            // Find tasks that can run in parallel with this one
            const parallelGroup = [task];
            processed.add(task.id);

            sorted.forEach(other => {
                if (processed.has(other.id)) return;

                // Check if they can run in parallel (no dependencies between them)
                const hasDirectDependency = decomposition.dependencies.some(dep =>
                    (dep.from === task.id && dep.to === other.id) ||
                    (dep.from === other.id && dep.to === task.id)
                );

                if (!hasDirectDependency && other.dependencies.length === task.dependencies.length) {
                    parallelGroup.push(other);
                    processed.add(other.id);
                }
            });

            groups.push(parallelGroup);
        });

        return groups;
    }

    /**
     * Execute workflow with progress updates
     */
    private async executeWorkflowWithProgress(
        workflowId: string,
        description: string,
        stream: vscode.ChatResponseStream
    ): Promise<Map<string, any>> {
        this.activeWorkflows.set(workflowId, description);

        // Subscribe to workflow events
        const workflow = this.workflowEngine['workflows'].get(workflowId);
        if (workflow) {
            this.workflowEngine['eventBus'].on('node-started', (event: any) => {
                if (event.workflowId === workflowId) {
                    stream.progress(`⚡ Executing: ${event.node.id}`);
                }
            });

            this.workflowEngine['eventBus'].on('node-completed', (event: any) => {
                if (event.workflowId === workflowId) {
                    stream.markdown(`✅ Completed: ${event.node.id}\n`);
                }
            });
        }

        // Execute workflow
        const context = new Map<string, any>([
            ['prompt', description],
            ['sharedContext', this.sharedContext.getContext()]
        ]);

        const results = await this.workflowEngine.execute(workflowId, context);

        this.activeWorkflows.delete(workflowId);
        return results;
    }

    /**
     * Execute complex workflow with checkpointing and dynamic adjustment
     */
    private async executeComplexWorkflow(
        workflowId: string,
        description: string,
        sessionId: string,
        stream: vscode.ChatResponseStream
    ): Promise<Map<string, any>> {
        const results = new Map<string, any>();
        const workflow = this.workflowEngine['workflows'].get(workflowId);

        if (!workflow) return results;

        // Set up event handlers for real-time updates
        this.workflowEngine['eventBus'].on('stage-started', (event: any) => {
            if (event.workflowId === workflowId) {
                stream.markdown(`\n**Stage Started:** ${event.stage.stageId}\n`);

                // Update collaboration context
                this.communicationBus.updateCollaborationContext(
                    sessionId,
                    'orchestrator',
                    'current_stage',
                    event.stage
                );
            }
        });

        this.workflowEngine['eventBus'].on('node-completed', (event: any) => {
            if (event.workflowId === workflowId) {
                // Check if adjustment needed based on result
                if (event.result.status === 'failure') {
                    // Request help from other agents
                    this.requestAgentHelp(event.node, event.result.error);
                }

                // Update shared context
                this.sharedContext.updateContext(
                    'orchestrator',
                    `result_${event.node.id}`,
                    event.result
                );
            }
        });

        // Create checkpoints at critical stages
        this.workflowEngine['eventBus'].on('stage-completed', (event: any) => {
            if (event.workflowId === workflowId) {
                this.workflowEngine.createCheckpoint(workflowId, event.stage.stageId);
                stream.markdown(`💾 Checkpoint created at ${event.stage.stageId}\n`);
            }
        });

        // Execute with context
        const context = new Map<string, any>([
            ['prompt', description],
            ['sessionId', sessionId],
            ['sharedContext', this.sharedContext.getContext()]
        ]);

        try {
            return await this.workflowEngine.execute(workflowId, context);
        } catch (error) {
            stream.markdown(`\n⚠️ **Workflow error, attempting recovery...**\n`);

            // Try to recover from last checkpoint
            const checkpoints = workflow.checkpoints;
            if (checkpoints.length > 0) {
                const lastCheckpoint = checkpoints[checkpoints.length - 1];
                this.workflowEngine.restoreFromCheckpoint(workflowId, lastCheckpoint.id);

                stream.markdown(`♻️ Restored from checkpoint: ${lastCheckpoint.nodeId}\n`);

                // Retry execution
                return await this.workflowEngine.execute(workflowId, context);
            }

            throw error;
        }
    }

    /**
     * Request help from other agents when stuck
     */
    private async requestAgentHelp(node: WorkflowNode, error: string): Promise<void> {
        const helpResponse = await this.communicationBus.requestHelp(
            'orchestrator',
            {
                node,
                error,
                context: this.sharedContext.getContext()
            }
        );

        if (helpResponse && helpResponse.length > 0) {
            // Apply first suggested solution
            const solution = helpResponse[0];

            // Adjust workflow based on help
            this.workflowEngine.adjustWorkflow(node.id, {
                type: 'modify-node',
                nodeId: node.id,
                modifications: {
                    task: solution.suggestion || node.task
                }
            });
        }
    }

    /**
     * Display execution plan
     */
    private displayExecutionPlan(plan: ExecutionPlan, stream: vscode.ChatResponseStream): void {
        stream.markdown(`### 📋 Execution Plan\n\n`);
        stream.markdown(`**Stages:** ${plan.stages.length}\n`);
        stream.markdown(`**Parallelism:** ${plan.parallelism}x\n`);
        stream.markdown(`**Estimated Duration:** ${plan.estimatedDuration}ms\n\n`);

        plan.stages.forEach((stage, index) => {
            stream.markdown(`**Stage ${index + 1}:** ${stage.parallel ? '⚡ Parallel' : '📝 Sequential'}\n`);
            stage.nodes.forEach(node => {
                stream.markdown(`  - ${node.agentId || 'system'}: ${node.id}\n`);
            });
        });

        stream.markdown(`\n**Critical Path:** ${plan.criticalPath.join(' → ')}\n\n`);
    }

    /**
     * Display advanced execution plan
     */
    private displayAdvancedExecutionPlan(plan: ExecutionPlan, stream: vscode.ChatResponseStream): void {
        stream.markdown(`### 🚀 Advanced Execution Strategy\n\n`);

        // Create visual representation
        stream.markdown(`\`\`\`mermaid\ngraph TB\n`);

        plan.stages.forEach((stage, index) => {
            if (stage.parallel) {
                stream.markdown(`  subgraph "Stage ${index + 1} - Parallel"\n`);
                stage.nodes.forEach(node => {
                    stream.markdown(`    ${node.id}["${node.agentId}: ${node.id}"]\n`);
                });
                stream.markdown(`  end\n`);
            } else {
                stage.nodes.forEach(node => {
                    stream.markdown(`  ${node.id}["${node.agentId}: ${node.id}"]\n`);
                });
            }
        });

        // Add dependencies as edges
        plan.stages.forEach((stage, index) => {
            if (index > 0) {
                const prevStage = plan.stages[index - 1];
                prevStage.nodes.forEach(prevNode => {
                    stage.nodes.forEach(currNode => {
                        if (currNode.dependencies?.includes(prevNode.id)) {
                            stream.markdown(`  ${prevNode.id} --> ${currNode.id}\n`);
                        }
                    });
                });
            }
        });

        stream.markdown(`\`\`\`\n\n`);

        // Performance metrics
        stream.markdown(`**Performance Optimization:**\n`);
        stream.markdown(`- Parallel Execution Speed-up: ${plan.parallelism}x\n`);
        stream.markdown(`- Critical Path Length: ${plan.criticalPath.length} steps\n`);
        stream.markdown(`- Total Estimated Time: ${(plan.estimatedDuration / 1000).toFixed(1)}s\n\n`);
    }

    /**
     * Display simple results
     */
    private displayResults(results: Map<string, any>, stream: vscode.ChatResponseStream): void {
        stream.markdown(`\n### 📊 Results\n\n`);

        results.forEach((result, nodeId) => {
            if (result.status === 'success') {
                stream.markdown(`**✅ ${nodeId}:**\n${result.output?.result || result.output || 'Completed'}\n\n`);
            } else if (result.status === 'failure') {
                stream.markdown(`**❌ ${nodeId}:** ${result.error}\n\n`);
            }
        });
    }

    /**
     * Display complex results with insights
     */
    private displayComplexResults(results: Map<string, any>, stream: vscode.ChatResponseStream): void {
        stream.markdown(`\n### 🎯 Comprehensive Results\n\n`);

        // Group results by status
        const successes: any[] = [];
        const failures: any[] = [];

        results.forEach((result, nodeId) => {
            if (result.status === 'success') {
                successes.push({ nodeId, ...result });
            } else {
                failures.push({ nodeId, ...result });
            }
        });

        // Display successes
        if (successes.length > 0) {
            stream.markdown(`#### ✅ Successful Tasks (${successes.length})\n\n`);
            successes.forEach(result => {
                stream.markdown(`**${result.nodeId}:**\n`);
                stream.markdown(`${result.output?.result || result.output || 'Completed'}\n\n`);
            });
        }

        // Display failures
        if (failures.length > 0) {
            stream.markdown(`#### ⚠️ Failed Tasks (${failures.length})\n\n`);
            failures.forEach(result => {
                stream.markdown(`**${result.nodeId}:** ${result.error}\n`);
                stream.markdown(`*Suggestion:* Try using @fixer to resolve this issue\n\n`);
            });
        }

        // Display insights
        const insights = this.generateInsights(results);
        if (insights.length > 0) {
            stream.markdown(`#### 💡 Insights & Recommendations\n\n`);
            insights.forEach(insight => {
                stream.markdown(`- ${insight}\n`);
            });
        }

        // Display collaboration metrics
        const collaborationStats = this.communicationBus.getStats();
        stream.markdown(`\n#### 📈 Collaboration Metrics\n\n`);
        stream.markdown(`- Total Messages Exchanged: ${collaborationStats.totalMessages}\n`);
        stream.markdown(`- Average Response Time: ${collaborationStats.averageResponseTime.toFixed(0)}ms\n`);
        stream.markdown(`- Active Sessions: ${collaborationStats.activeSessions}\n`);
    }

    /**
     * Generate insights from results
     */
    private generateInsights(results: Map<string, any>): string[] {
        const insights: string[] = [];

        // Calculate success rate
        let successes = 0;
        let total = 0;

        results.forEach(result => {
            total++;
            if (result.status === 'success') successes++;
        });

        const successRate = (successes / total) * 100;

        if (successRate === 100) {
            insights.push('🎉 Perfect execution! All tasks completed successfully.');
        } else if (successRate >= 80) {
            insights.push(`✅ Good performance with ${successRate.toFixed(0)}% success rate.`);
        } else {
            insights.push(`⚠️ Room for improvement with ${successRate.toFixed(0)}% success rate.`);
        }

        // Analyze patterns
        const agents = new Map<string, number>();
        results.forEach((result, nodeId) => {
            const agent = (result as any).agent || 'unknown';
            agents.set(agent, (agents.get(agent) || 0) + 1);
        });

        const mostUsedAgent = Array.from(agents.entries())
            .sort(([, a], [, b]) => b - a)[0];

        if (mostUsedAgent) {
            insights.push(`📊 Most active agent: @${mostUsedAgent[0]} (${mostUsedAgent[1]} tasks)`);
        }

        // Check for bottlenecks
        const longRunning = Array.from(results.entries())
            .filter(([, r]) => r.duration > 10000)
            .map(([id]) => id);

        if (longRunning.length > 0) {
            insights.push(`⏱️ Potential bottlenecks detected in: ${longRunning.join(', ')}`);
        }

        return insights;
    }

    /**
     * Store task memory for learning
     */
    private async storeTaskMemory(
        prompt: string,
        complexity: string,
        workflowId: string,
        results: Map<string, any>
    ): Promise<void> {
        const taskMemory: TaskMemory = {
            taskId: workflowId,
            description: prompt,
            decomposition: [],
            outcome: {
                status: this.determineOverallStatus(results),
                quality: this.calculateQuality(results),
                improvements: this.suggestImprovements(results)
            },
            duration: this.calculateTotalDuration(results),
            agentsInvolved: this.extractAgents(results),
            lessonsLearned: this.extractLessons(results)
        };

        await this.memoryManager.store(
            'orchestrator',
            { prompt, complexity, taskMemory },
            MemoryType.EPISODIC,
            { importance: 0.7 }
        );
    }

    /**
     * Store complex task memory with patterns
     */
    private async storeComplexTaskMemory(
        prompt: string,
        decomposition: TaskDecomposition,
        workflowId: string,
        results: Map<string, any>
    ): Promise<void> {
        const taskMemory: TaskMemory = {
            taskId: workflowId,
            description: prompt,
            decomposition: decomposition.subtasks.map(st => ({
                stepId: st.id,
                description: st.description,
                assignedAgent: st.agent,
                status: results.has(st.id) && results.get(st.id).status === 'success'
                    ? 'completed'
                    : 'failed',
                output: results.get(st.id),
                dependencies: st.dependencies
            })),
            outcome: {
                status: this.determineOverallStatus(results),
                quality: this.calculateQuality(results),
                improvements: this.suggestImprovements(results)
            },
            duration: this.calculateTotalDuration(results),
            agentsInvolved: decomposition.requiredAgents,
            lessonsLearned: this.extractLessons(results)
        };

        await this.memoryManager.store(
            'orchestrator',
            { prompt, decomposition, taskMemory },
            MemoryType.EPISODIC,
            { importance: 0.9 }
        );
    }

    /**
     * Extract and store patterns from successful execution
     */
    private async extractAndStorePatterns(
        decomposition: TaskDecomposition,
        results: Map<string, any>
    ): Promise<void> {
        // Look for successful patterns
        const successfulSubtasks = decomposition.subtasks.filter(st =>
            results.has(st.id) && results.get(st.id).status === 'success'
        );

        if (successfulSubtasks.length > 0) {
            // Store as procedural memory
            await this.memoryManager.store(
                'orchestrator',
                {
                    pattern: 'successful_decomposition',
                    mainGoal: decomposition.mainGoal,
                    successfulApproach: successfulSubtasks.map(st => ({
                        agent: st.agent,
                        task: st.description,
                        priority: st.priority
                    }))
                },
                MemoryType.PROCEDURAL,
                { importance: 0.85 }
            );
        }

        // Identify agent collaboration patterns
        const collaborations = new Map<string, string[]>();
        decomposition.dependencies.forEach(dep => {
            const fromAgent = decomposition.subtasks.find(st => st.id === dep.from)?.agent;
            const toAgent = decomposition.subtasks.find(st => st.id === dep.to)?.agent;

            if (fromAgent && toAgent) {
                if (!collaborations.has(fromAgent)) {
                    collaborations.set(fromAgent, []);
                }
                collaborations.get(fromAgent)!.push(toAgent);
            }
        });

        if (collaborations.size > 0) {
            await this.memoryManager.store(
                'orchestrator',
                {
                    pattern: 'agent_collaboration',
                    collaborations: Object.fromEntries(collaborations)
                },
                MemoryType.SEMANTIC,
                { importance: 0.75 }
            );
        }
    }

    // Utility methods for result analysis

    private determineOverallStatus(results: Map<string, any>): 'success' | 'partial' | 'failure' {
        let successes = 0;
        let total = 0;

        results.forEach(result => {
            total++;
            if (result.status === 'success') successes++;
        });

        const rate = successes / total;
        if (rate === 1) return 'success';
        if (rate >= 0.5) return 'partial';
        return 'failure';
    }

    private calculateQuality(results: Map<string, any>): number {
        let totalQuality = 0;
        let count = 0;

        results.forEach(result => {
            count++;
            totalQuality += result.status === 'success' ? 1 : 0;
        });

        return count > 0 ? totalQuality / count : 0;
    }

    private suggestImprovements(results: Map<string, any>): string[] {
        const improvements: string[] = [];

        results.forEach((result, nodeId) => {
            if (result.status === 'failure') {
                improvements.push(`Improve error handling for ${nodeId}`);
            }
            if (result.duration > 15000) {
                improvements.push(`Optimize performance of ${nodeId}`);
            }
        });

        return improvements;
    }

    private calculateTotalDuration(results: Map<string, any>): number {
        let total = 0;
        results.forEach(result => {
            total += result.duration || 0;
        });
        return total;
    }

    private extractAgents(results: Map<string, any>): string[] {
        const agents = new Set<string>();
        results.forEach(result => {
            if ((result as any).agent) {
                agents.add((result as any).agent);
            }
        });
        return Array.from(agents);
    }

    private extractLessons(results: Map<string, any>): string[] {
        const lessons: string[] = [];

        // Analyze failures
        results.forEach((result, nodeId) => {
            if (result.status === 'failure') {
                lessons.push(`Task ${nodeId} failed: ${result.error}`);
            }
        });

        // Analyze successes
        const successCount = Array.from(results.values())
            .filter(r => r.status === 'success').length;

        if (successCount === results.size) {
            lessons.push('All tasks completed successfully - workflow is reliable');
        }

        return lessons;
    }

    private createCondition(conditionStr: string): (context: any) => boolean {
        return (context: any) => {
            // Simple condition evaluation
            // In production, use proper expression parser
            return true;
        };
    }

    /**
     * Handle direct response for simple queries
     */
    private async handleDirectResponse(
        prompt: string,
        stream: vscode.ChatResponseStream
    ): Promise<void> {
        const systemPrompt = `You are an intelligent orchestrator. Answer directly and concisely.
${this.getSystemContextPrompt()}`;

        const response = await this.openAIService.chat([
            { role: 'system', content: systemPrompt },
            { role: 'user', content: prompt }
        ]);

        stream.markdown(response);
    }

    /**
     * Register communication handlers
     */
    private registerCommunicationHandlers(): void {
        this.communicationBus.register({
            agentId: 'orchestrator',
            messageTypes: [
                MessageType.CONFLICT,
                MessageType.STATUS_UPDATE,
                MessageType.ERROR
            ],
            handler: async (message) => {
                return await this.handleAgentMessage(message);
            }
        });
    }

    /**
     * Handle messages from other agents
     */
    private async handleAgentMessage(message: any): Promise<any> {
        switch (message.type) {
            case MessageType.CONFLICT:
                // Trigger OpusArbitrator for conflict resolution
                return await this.resolveConflict(message.content);

            case MessageType.STATUS_UPDATE:
                // Update workflow status
                this.updateWorkflowStatus(message.content);
                return { acknowledged: true };

            case MessageType.ERROR:
                // Handle agent errors
                return await this.handleAgentError(message.content);

            default:
                return { acknowledged: true };
        }
    }

    /**
     * Resolve conflicts between agents
     */
    private async resolveConflict(conflict: any): Promise<any> {
        // Route to OpusArbitrator
        await this.communicationBus.send({
            from: 'orchestrator',
            to: 'OpusArbitrator',
            type: MessageType.CONFLICT,
            content: conflict,
            metadata: {
                priority: 'critical',
                requiresResponse: true
            }
        });

        return { routing: 'OpusArbitrator' };
    }

    /**
     * Update workflow status based on agent updates
     */
    private updateWorkflowStatus(update: any): void {
        // Update shared context
        this.sharedContext.updateContext(
            'orchestrator',
            `workflow_status_${update.workflowId}`,
            update
        );
    }

    /**
     * Handle errors from agents
     */
    private async handleAgentError(error: any): Promise<any> {
        // Check if we can recover
        const recovery = await this.attemptRecovery(error);

        if (recovery) {
            return { recovery: true, action: recovery };
        }

        // Escalate to user
        return { recovery: false, escalate: true };
    }

    /**
     * Attempt to recover from agent errors
     */
    private async attemptRecovery(error: any): Promise<any> {
        // Search memory for similar errors
        const similarErrors = await this.memoryManager.search(error, {
            k: 3,
            type: MemoryType.EPISODIC
        });

        if (similarErrors.length > 0) {
            // Found similar error with solution
            const solution = (similarErrors[0].entry.content as any).solution;
            if (solution) {
                return solution;
            }
        }

        // Try alternative agent
        const registry = AgentRegistry.getInstance();
        const alternativeAgent = registry.suggestAgentForTask(error.task);

        if (alternativeAgent && alternativeAgent !== error.agent) {
            return {
                type: 'retry',
                agent: alternativeAgent
            };
        }

        return null;
    }

    /**
     * Build context with memory
     */
    private async buildContextWithMemory(request: any): Promise<any> {
        // Search for relevant memories
        const memories = await this.memoryManager.search(request.prompt, {
            k: 10,
            type: MemoryType.EPISODIC
        });

        // Get shared context
        const sharedContext = this.sharedContext.getContext();

        return {
            ...request,
            memories: memories.map(m => m.entry.content),
            sharedContext,
            activeAgents: this.sharedContext.getActiveAgents()
        };
    }

    // Command handlers remain similar but use new orchestration methods
    // ... (rest of the command handlers can be kept or adapted as needed)

    // Required by ChatAgent abstract class
    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        // Use AI to intelligently decide how to handle the request
        const classificationPrompt = `You are the advanced orchestrator of a multi-agent AI system.

${this.getSystemAgentContext()}

Classify this request and decide how to handle it:
Request: "${request.prompt}"

Respond with a JSON object:
{
  "requestType": "query" | "simple_task" | "complex_task",
  "shouldAnswer": true/false (should orchestrator answer directly?),
  "reasoning": "brief explanation",
  "suggestedAgent": "agent_name or null if orchestrator handles it"
}

Rules:
- "query": Information requests, questions about the system, agent capabilities
- "simple_task": Single-step implementation, bug fix, or straightforward coding
- "complex_task": Multi-step projects requiring multiple agents
- Set shouldAnswer=true for queries about agents, system capabilities, or general questions
- Set shouldAnswer=false for implementation tasks that need specialist agents`;

        try {
            // Get AI classification
            const classificationResponse = await this.openAIService.chat([
                { role: 'system', content: classificationPrompt },
                { role: 'user', content: request.prompt }
            ]);

            let classification;
            try {
                classification = JSON.parse(classificationResponse);
            } catch {
                // Fallback if JSON parsing fails
                classification = {
                    requestType: 'query',
                    shouldAnswer: true,
                    reasoning: 'Failed to parse, treating as query'
                };
            }

            // Handle based on classification
            if (classification.shouldAnswer) {
                // Orchestrator answers directly with full context
                const answerPrompt = `You are the Advanced KI AutoAgent Orchestrator, the central intelligence coordinating a sophisticated multi-agent AI system.

${this.getSystemAgentContext()}

Important: When asked about agents, provide comprehensive details including:
- Agent names and their @mentions
- Specific capabilities and expertise
- AI models they use
- How they collaborate
- System features like memory, parallel execution, and learning

Answer this question thoroughly and helpfully:
"${request.prompt}"

Provide a complete, informative response with specific details about our capabilities.`;

                const response = await this.openAIService.chat([
                    { role: 'system', content: answerPrompt },
                    { role: 'user', content: request.prompt }
                ]);

                return {
                    status: 'success',
                    content: response,
                    metadata: {
                        step: step.id,
                        agent: 'orchestrator',
                        type: classification.requestType,
                        reasoning: classification.reasoning
                    }
                };
            }

            // For tasks, check complexity and handle accordingly
            if (classification.requestType === 'simple_task' && classification.suggestedAgent) {
                // Route to specific agent
                const node: WorkflowNode = {
                    id: step.id,
                    type: 'task',
                    agentId: classification.suggestedAgent,
                    task: request.prompt
                };

                const workflow = this.workflowEngine.createWorkflow(`Simple: ${request.prompt}`);
                this.workflowEngine.addNode(workflow.id, node);
                const results = await this.workflowEngine.execute(workflow.id);

                const stepResult = results.get(step.id);
                // Map workflow status to TaskResult status
                let taskStatus: 'success' | 'partial_success' | 'error' = 'error';
                if (stepResult?.status === 'success') {
                    taskStatus = 'success';
                } else if (stepResult?.status === 'failure') {
                    taskStatus = 'error';
                } else if (stepResult?.status === 'skipped') {
                    taskStatus = 'partial_success';
                }

                return {
                    status: taskStatus,
                    content: stepResult?.output?.result || stepResult?.output || 'Task completed',
                    metadata: {
                        step: step.id,
                        agent: classification.suggestedAgent,
                        type: 'routed_task'
                    }
                };
            }

            // For complex tasks, use full decomposition
            if (classification.requestType === 'complex_task') {
                const decomposition = await this.decomposeTask(request.prompt);

                // Create and execute workflow
                const workflow = this.workflowEngine.createWorkflow(`Complex: ${request.prompt}`);

                decomposition.subtasks.forEach(subtask => {
                    const node: WorkflowNode = {
                        id: subtask.id,
                        type: 'task',
                        agentId: subtask.agent,
                        task: subtask.description,
                        dependencies: subtask.dependencies
                    };
                    this.workflowEngine.addNode(workflow.id, node);
                });

                const results = await this.workflowEngine.execute(workflow.id);

                // Compile results
                const summary = this.compileWorkflowResults(results);

                return {
                    status: 'success',
                    content: summary,
                    metadata: {
                        step: step.id,
                        agent: 'orchestrator',
                        type: 'complex_workflow',
                        subtasks: decomposition.subtasks.length
                    }
                };
            }

            // Fallback: Orchestrator handles directly
            const response = await this.openAIService.chat([
                { role: 'system', content: `You are the Orchestrator. ${this.getSystemContextPrompt()}` },
                { role: 'user', content: request.prompt }
            ]);

            return {
                status: 'success',
                content: response,
                metadata: {
                    step: step.id,
                    agent: 'orchestrator',
                    type: 'direct_response'
                }
            };

        } catch (error) {
            return {
                status: 'error',
                content: `Error processing request: ${(error as any).message}`,
                metadata: {
                    step: step.id,
                    agent: 'orchestrator',
                    error: (error as any).message
                }
            };
        }
    }

    /**
     * Compile workflow results into a coherent summary
     */
    private compileWorkflowResults(results: Map<string, any>): string {
        const sections: string[] = [];

        sections.push('## Workflow Execution Complete\n');

        results.forEach((result, nodeId) => {
            if (result.status === 'success') {
                sections.push(`### ✅ ${nodeId}`);
                sections.push(result.output?.result || result.output || 'Completed');
                sections.push('');
            }
        });

        const failures = Array.from(results.entries())
            .filter(([, r]) => r.status !== 'success');

        if (failures.length > 0) {
            sections.push('### ⚠️ Issues Encountered');
            failures.forEach(([nodeId, result]) => {
                sections.push(`- **${nodeId}**: ${result.error || 'Failed'}`);
            });
        }

        return sections.join('\n');
    }

    /**
     * Dynamically generate system context about agents and capabilities
     */
    private getSystemAgentContext(): string {
        const registry = AgentRegistry.getInstance();
        const agents = registry.getRegisteredAgents();

        // Build dynamic context about available agents
        const agentDescriptions = agents.map(agent => {
            return `- **${agent.id}** (${agent.name}): ${agent.specialization}. Can handle: ${agent.canHandle.join(', ')}`;
        }).join('\n');

        return `You are part of an advanced multi-agent AI system with the following capabilities:

## Available Specialist Agents:
${agentDescriptions}

## System Features:
- **Memory System**: 10k capacity with semantic search and pattern recognition
- **Parallel Execution**: Can run multiple tasks simultaneously for 5x speedup
- **Inter-Agent Collaboration**: Agents share knowledge and help each other
- **Learning**: System improves from past executions with 85% similarity threshold
- **Conflict Resolution**: OpusArbitrator resolves disagreements with superior reasoning

## Your Role as Orchestrator:
You coordinate these agents, decompose complex tasks, and ensure efficient execution.
For simple queries, you can answer directly. For complex tasks, orchestrate the appropriate agents.`;
    }
}