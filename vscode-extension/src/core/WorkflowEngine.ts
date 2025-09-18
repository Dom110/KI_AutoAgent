/**
 * WorkflowEngine - Graph-based workflow execution for complex task orchestration
 * Enables parallel execution, conditional flows, and dynamic plan adjustment
 */

import { EventEmitter } from 'events';

export interface WorkflowNode {
    id: string;
    type: 'task' | 'decision' | 'parallel' | 'sequential' | 'loop';
    agentId?: string;
    task?: any;
    condition?: (context: any) => boolean;
    children?: string[];
    dependencies?: string[];
    retryPolicy?: RetryPolicy;
    timeout?: number;
    metadata?: any;
}

export interface WorkflowEdge {
    from: string;
    to: string;
    condition?: (context: any) => boolean;
    weight?: number;
}

export interface Workflow {
    id: string;
    name: string;
    nodes: Map<string, WorkflowNode>;
    edges: WorkflowEdge[];
    startNode: string;
    endNodes: string[];
    context: Map<string, any>;
    checkpoints: Checkpoint[];
    status: WorkflowStatus;
}

export interface WorkflowStatus {
    state: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
    currentNodes: string[];
    completedNodes: string[];
    failedNodes: string[];
    startTime?: number;
    endTime?: number;
    error?: string;
}

export interface Checkpoint {
    id: string;
    nodeId: string;
    timestamp: number;
    context: Map<string, any>;
    results: Map<string, any>;
}

export interface RetryPolicy {
    maxAttempts: number;
    backoffMultiplier: number;
    maxBackoffMs: number;
}

export interface ExecutionPlan {
    stages: ExecutionStage[];
    estimatedDuration: number;
    parallelism: number;
    criticalPath: string[];
}

export interface ExecutionStage {
    stageId: string;
    nodes: WorkflowNode[];
    parallel: boolean;
    dependencies: string[];
    estimatedDuration: number;
}

export interface TaskResult {
    nodeId: string;
    status: 'success' | 'failure' | 'skipped';
    output?: any;
    error?: string;
    duration: number;
    retries: number;
}

export class WorkflowEngine {
    private workflows: Map<string, Workflow> = new Map();
    private eventBus: EventEmitter;
    private executors: Map<string, WorkflowExecutor> = new Map();
    private templates: Map<string, WorkflowTemplate> = new Map();

    constructor() {
        this.eventBus = new EventEmitter();
        this.initializeTemplates();
    }

    /**
     * Create a new workflow
     */
    public createWorkflow(name: string, template?: string): Workflow {
        const id = this.generateWorkflowId();

        const workflow: Workflow = {
            id,
            name,
            nodes: new Map(),
            edges: [],
            startNode: '',
            endNodes: [],
            context: new Map(),
            checkpoints: [],
            status: {
                state: 'pending',
                currentNodes: [],
                completedNodes: [],
                failedNodes: []
            }
        };

        // Apply template if provided
        if (template && this.templates.has(template)) {
            this.applyTemplate(workflow, this.templates.get(template)!);
        }

        this.workflows.set(id, workflow);
        this.eventBus.emit('workflow-created', workflow);

        return workflow;
    }

    /**
     * Add a node to the workflow
     */
    public addNode(workflowId: string, node: WorkflowNode): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }

        workflow.nodes.set(node.id, node);

        // Set as start node if it's the first
        if (!workflow.startNode) {
            workflow.startNode = node.id;
        }

        this.eventBus.emit('node-added', { workflowId, node });
    }

    /**
     * Add an edge between nodes
     */
    public addEdge(workflowId: string, edge: WorkflowEdge): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }

        // Validate nodes exist
        if (!workflow.nodes.has(edge.from) || !workflow.nodes.has(edge.to)) {
            throw new Error(`Invalid edge: nodes not found`);
        }

        workflow.edges.push(edge);

        // Update node children
        const fromNode = workflow.nodes.get(edge.from)!;
        if (!fromNode.children) {
            fromNode.children = [];
        }
        fromNode.children.push(edge.to);

        // Update node dependencies
        const toNode = workflow.nodes.get(edge.to)!;
        if (!toNode.dependencies) {
            toNode.dependencies = [];
        }
        toNode.dependencies.push(edge.from);

        this.eventBus.emit('edge-added', { workflowId, edge });
    }

    /**
     * Create execution plan for the workflow
     */
    public createExecutionPlan(workflowId: string): ExecutionPlan {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }

        // Topological sort to find execution order
        const sortedNodes = this.topologicalSort(workflow);

        // Group nodes into stages based on dependencies
        const stages = this.groupIntoStages(workflow, sortedNodes);

        // Calculate critical path
        const criticalPath = this.findCriticalPath(workflow);

        // Estimate durations
        const estimatedDuration = this.estimateDuration(stages);
        const parallelism = this.calculateParallelism(stages);

        return {
            stages,
            estimatedDuration,
            parallelism,
            criticalPath
        };
    }

    /**
     * Execute a workflow
     */
    public async execute(workflowId: string, context?: Map<string, any>): Promise<Map<string, TaskResult>> {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }

        // Initialize context
        if (context) {
            workflow.context = new Map([...workflow.context, ...context]);
        }

        // Create executor
        const executor = new WorkflowExecutor(workflow, this.eventBus);
        this.executors.set(workflowId, executor);

        // Update status
        workflow.status.state = 'running';
        workflow.status.startTime = Date.now();
        this.eventBus.emit('workflow-started', workflow);

        try {
            // Create execution plan
            const plan = this.createExecutionPlan(workflowId);

            // Execute plan
            const results = await executor.execute(plan);

            // Update status
            workflow.status.state = 'completed';
            workflow.status.endTime = Date.now();
            this.eventBus.emit('workflow-completed', { workflow, results });

            return results;
        } catch (error) {
            workflow.status.state = 'failed';
            workflow.status.error = error instanceof Error ? error.message : String(error);
            workflow.status.endTime = Date.now();
            this.eventBus.emit('workflow-failed', { workflow, error });
            throw error;
        } finally {
            this.executors.delete(workflowId);
        }
    }

    /**
     * Pause a running workflow
     */
    public pause(workflowId: string): void {
        const executor = this.executors.get(workflowId);
        if (executor) {
            executor.pause();
        }
    }

    /**
     * Resume a paused workflow
     */
    public resume(workflowId: string): void {
        const executor = this.executors.get(workflowId);
        if (executor) {
            executor.resume();
        }
    }

    /**
     * Cancel a workflow
     */
    public cancel(workflowId: string): void {
        const executor = this.executors.get(workflowId);
        if (executor) {
            executor.cancel();
        }
    }

    /**
     * Create a checkpoint
     */
    public createCheckpoint(workflowId: string, nodeId: string): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return;

        const checkpoint: Checkpoint = {
            id: this.generateCheckpointId(),
            nodeId,
            timestamp: Date.now(),
            context: new Map(workflow.context),
            results: new Map()
        };

        workflow.checkpoints.push(checkpoint);
        this.eventBus.emit('checkpoint-created', { workflowId, checkpoint });
    }

    /**
     * Restore from checkpoint
     */
    public restoreFromCheckpoint(workflowId: string, checkpointId: string): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return;

        const checkpoint = workflow.checkpoints.find(cp => cp.id === checkpointId);
        if (!checkpoint) {
            throw new Error(`Checkpoint ${checkpointId} not found`);
        }

        // Restore context
        workflow.context = new Map(checkpoint.context);

        // Reset status to continue from checkpoint
        workflow.status.completedNodes = workflow.status.completedNodes.filter(
            nodeId => this.isNodeBeforeCheckpoint(workflow, nodeId, checkpoint.nodeId)
        );

        this.eventBus.emit('checkpoint-restored', { workflowId, checkpoint });
    }

    /**
     * Adjust workflow dynamically
     */
    public adjustWorkflow(workflowId: string, adjustment: WorkflowAdjustment): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return;

        switch (adjustment.type) {
            case 'add-node':
                this.addNode(workflowId, adjustment.node!);
                break;

            case 'remove-node':
                this.removeNode(workflowId, adjustment.nodeId!);
                break;

            case 'modify-node':
                this.modifyNode(workflowId, adjustment.nodeId!, adjustment.modifications!);
                break;

            case 'reroute':
                this.rerouteEdges(workflowId, adjustment.rerouting!);
                break;
        }

        this.eventBus.emit('workflow-adjusted', { workflowId, adjustment });
    }

    /**
     * Initialize workflow templates
     */
    private initializeTemplates(): void {
        // Complex Task Template
        this.templates.set('complex-task', {
            name: 'Complex Task',
            nodes: [
                { id: 'research', type: 'task', agentId: 'ResearchAgent' },
                { id: 'architect', type: 'task', agentId: 'ArchitectAgent', dependencies: ['research'] },
                { id: 'review-arch', type: 'task', agentId: 'ReviewerGPT', dependencies: ['architect'] },
                { id: 'implement', type: 'task', agentId: 'CodeSmithAgent', dependencies: ['review-arch'] },
                { id: 'test', type: 'task', agentId: 'FixerBot', dependencies: ['implement'] },
                { id: 'document', type: 'task', agentId: 'DocuBot', dependencies: ['test'] }
            ]
        });

        // Parallel Research Template
        this.templates.set('parallel-research', {
            name: 'Parallel Research',
            nodes: [
                { id: 'split', type: 'parallel' },
                { id: 'research1', type: 'task', agentId: 'ResearchAgent' },
                { id: 'research2', type: 'task', agentId: 'ResearchAgent' },
                { id: 'research3', type: 'task', agentId: 'ResearchAgent' },
                { id: 'merge', type: 'sequential', dependencies: ['research1', 'research2', 'research3'] },
                { id: 'synthesize', type: 'task', agentId: 'OrchestratorAgent', dependencies: ['merge'] }
            ]
        });

        // Iterative Improvement Template
        this.templates.set('iterative-improvement', {
            name: 'Iterative Improvement',
            nodes: [
                { id: 'initial', type: 'task', agentId: 'CodeSmithAgent' },
                { id: 'review', type: 'task', agentId: 'ReviewerGPT', dependencies: ['initial'] },
                { id: 'decision', type: 'decision', dependencies: ['review'] },
                { id: 'improve', type: 'task', agentId: 'FixerBot', dependencies: ['decision'] },
                { id: 'loop', type: 'loop', dependencies: ['improve'] }
            ]
        });
    }

    /**
     * Topological sort for node ordering
     */
    private topologicalSort(workflow: Workflow): WorkflowNode[] {
        const sorted: WorkflowNode[] = [];
        const visited = new Set<string>();
        const visiting = new Set<string>();

        const visit = (nodeId: string) => {
            if (visited.has(nodeId)) return;
            if (visiting.has(nodeId)) {
                throw new Error('Circular dependency detected in workflow');
            }

            visiting.add(nodeId);
            const node = workflow.nodes.get(nodeId);

            if (node?.children) {
                node.children.forEach(childId => visit(childId));
            }

            visiting.delete(nodeId);
            visited.add(nodeId);
            if (node) sorted.unshift(node);
        };

        // Start from root node
        visit(workflow.startNode);

        // Visit any disconnected nodes
        workflow.nodes.forEach((_, nodeId) => {
            if (!visited.has(nodeId)) {
                visit(nodeId);
            }
        });

        return sorted;
    }

    /**
     * Group nodes into execution stages
     */
    private groupIntoStages(workflow: Workflow, sortedNodes: WorkflowNode[]): ExecutionStage[] {
        const stages: ExecutionStage[] = [];
        const nodeStage = new Map<string, number>();

        sortedNodes.forEach(node => {
            let stage = 0;

            // Find maximum stage of dependencies
            if (node.dependencies) {
                node.dependencies.forEach(depId => {
                    const depStage = nodeStage.get(depId) || 0;
                    stage = Math.max(stage, depStage + 1);
                });
            }

            nodeStage.set(node.id, stage);

            // Add to stage
            if (!stages[stage]) {
                stages[stage] = {
                    stageId: `stage_${stage}`,
                    nodes: [],
                    parallel: true,
                    dependencies: stage > 0 ? [`stage_${stage - 1}`] : [],
                    estimatedDuration: 0
                };
            }

            stages[stage].nodes.push(node);
        });

        return stages;
    }

    /**
     * Find critical path through workflow
     */
    private findCriticalPath(workflow: Workflow): string[] {
        const distances = new Map<string, number>();
        const previous = new Map<string, string>();

        // Initialize distances
        workflow.nodes.forEach((_, nodeId) => {
            distances.set(nodeId, 0);
        });

        // Calculate longest path (critical path)
        const sortedNodes = this.topologicalSort(workflow);

        sortedNodes.forEach(node => {
            const nodeDistance = distances.get(node.id) || 0;

            node.children?.forEach(childId => {
                const edgeWeight = 1; // Could use actual task duration estimates
                const childDistance = distances.get(childId) || 0;

                if (nodeDistance + edgeWeight > childDistance) {
                    distances.set(childId, nodeDistance + edgeWeight);
                    previous.set(childId, node.id);
                }
            });
        });

        // Find the end node with maximum distance
        let maxDistance = 0;
        let endNode = '';

        workflow.nodes.forEach((node, nodeId) => {
            if (!node.children || node.children.length === 0) {
                const distance = distances.get(nodeId) || 0;
                if (distance > maxDistance) {
                    maxDistance = distance;
                    endNode = nodeId;
                }
            }
        });

        // Reconstruct path
        const path: string[] = [];
        let current = endNode;

        while (current) {
            path.unshift(current);
            current = previous.get(current) || '';
        }

        return path;
    }

    /**
     * Estimate workflow duration
     */
    private estimateDuration(stages: ExecutionStage[]): number {
        return stages.reduce((total, stage) => {
            const stageDuration = stage.parallel
                ? Math.max(...stage.nodes.map(n => n.timeout || 5000))
                : stage.nodes.reduce((sum, n) => sum + (n.timeout || 5000), 0);
            return total + stageDuration;
        }, 0);
    }

    /**
     * Calculate workflow parallelism
     */
    private calculateParallelism(stages: ExecutionStage[]): number {
        const parallelCounts = stages.map(stage =>
            stage.parallel ? stage.nodes.length : 1
        );
        return Math.max(...parallelCounts);
    }

    /**
     * Check if node is before checkpoint
     */
    private isNodeBeforeCheckpoint(workflow: Workflow, nodeId: string, checkpointNodeId: string): boolean {
        // Simple check - in production, do proper graph traversal
        const sorted = this.topologicalSort(workflow);
        const nodeIdx = sorted.findIndex(n => n.id === nodeId);
        const checkpointIdx = sorted.findIndex(n => n.id === checkpointNodeId);
        return nodeIdx < checkpointIdx;
    }

    /**
     * Remove a node from workflow
     */
    private removeNode(workflowId: string, nodeId: string): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return;

        // Remove node
        workflow.nodes.delete(nodeId);

        // Remove edges
        workflow.edges = workflow.edges.filter(
            edge => edge.from !== nodeId && edge.to !== nodeId
        );

        // Update dependencies
        workflow.nodes.forEach(node => {
            if (node.dependencies) {
                node.dependencies = node.dependencies.filter(dep => dep !== nodeId);
            }
            if (node.children) {
                node.children = node.children.filter(child => child !== nodeId);
            }
        });
    }

    /**
     * Modify a node
     */
    private modifyNode(workflowId: string, nodeId: string, modifications: Partial<WorkflowNode>): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return;

        const node = workflow.nodes.get(nodeId);
        if (!node) return;

        Object.assign(node, modifications);
    }

    /**
     * Reroute edges
     */
    private rerouteEdges(workflowId: string, rerouting: { from: string; to: string; newTo: string }[]): void {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return;

        rerouting.forEach(route => {
            const edgeIdx = workflow.edges.findIndex(
                e => e.from === route.from && e.to === route.to
            );

            if (edgeIdx >= 0) {
                workflow.edges[edgeIdx].to = route.newTo;
            }
        });
    }

    /**
     * Apply template to workflow
     */
    private applyTemplate(workflow: Workflow, template: WorkflowTemplate): void {
        template.nodes.forEach(nodeConfig => {
            const node: WorkflowNode = {
                id: nodeConfig.id,
                type: nodeConfig.type,
                agentId: nodeConfig.agentId,
                dependencies: nodeConfig.dependencies
            };
            workflow.nodes.set(node.id, node);
        });

        // Auto-create edges based on dependencies
        workflow.nodes.forEach(node => {
            if (node.dependencies) {
                node.dependencies.forEach(depId => {
                    workflow.edges.push({ from: depId, to: node.id });
                });
            }
        });

        if (template.nodes.length > 0) {
            workflow.startNode = template.nodes[0].id;
        }
    }

    /**
     * Generate workflow ID
     */
    private generateWorkflowId(): string {
        return `wf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Generate checkpoint ID
     */
    private generateCheckpointId(): string {
        return `cp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

/**
 * Workflow Executor - Handles actual execution of workflow
 */
class WorkflowExecutor {
    private workflow: Workflow;
    private eventBus: EventEmitter;
    private paused: boolean = false;
    private cancelled: boolean = false;
    private results: Map<string, TaskResult> = new Map();

    constructor(workflow: Workflow, eventBus: EventEmitter) {
        this.workflow = workflow;
        this.eventBus = eventBus;
    }

    public async execute(plan: ExecutionPlan): Promise<Map<string, TaskResult>> {
        for (const stage of plan.stages) {
            if (this.cancelled) break;

            // Wait if paused
            while (this.paused && !this.cancelled) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // Execute stage
            await this.executeStage(stage);

            // Create checkpoint after each stage
            this.createCheckpoint(stage.stageId);
        }

        return this.results;
    }

    private async executeStage(stage: ExecutionStage): Promise<void> {
        this.eventBus.emit('stage-started', { workflowId: this.workflow.id, stage });

        if (stage.parallel) {
            // Execute nodes in parallel
            const promises = stage.nodes.map(node => this.executeNode(node));
            await Promise.all(promises);
        } else {
            // Execute nodes sequentially
            for (const node of stage.nodes) {
                await this.executeNode(node);
            }
        }

        this.eventBus.emit('stage-completed', { workflowId: this.workflow.id, stage });
    }

    private async executeNode(node: WorkflowNode): Promise<void> {
        const startTime = Date.now();
        let retries = 0;
        const maxRetries = node.retryPolicy?.maxAttempts || 1;

        this.workflow.status.currentNodes.push(node.id);
        this.eventBus.emit('node-started', { workflowId: this.workflow.id, node });

        while (retries < maxRetries) {
            try {
                // Execute based on node type
                let output: any;

                switch (node.type) {
                    case 'task':
                        output = await this.executeTask(node);
                        break;

                    case 'decision':
                        output = await this.executeDecision(node);
                        break;

                    case 'parallel':
                        output = await this.executeParallel(node);
                        break;

                    case 'sequential':
                        output = await this.executeSequential(node);
                        break;

                    case 'loop':
                        output = await this.executeLoop(node);
                        break;

                    default:
                        throw new Error(`Unknown node type: ${node.type}`);
                }

                // Store result
                const result: TaskResult = {
                    nodeId: node.id,
                    status: 'success',
                    output,
                    duration: Date.now() - startTime,
                    retries
                };

                this.results.set(node.id, result);
                this.workflow.status.completedNodes.push(node.id);
                this.workflow.status.currentNodes = this.workflow.status.currentNodes.filter(
                    id => id !== node.id
                );

                this.eventBus.emit('node-completed', { workflowId: this.workflow.id, node, result });
                return;

            } catch (error) {
                retries++;

                if (retries < maxRetries) {
                    // Calculate backoff
                    const backoff = Math.min(
                        1000 * Math.pow(node.retryPolicy?.backoffMultiplier || 2, retries),
                        node.retryPolicy?.maxBackoffMs || 30000
                    );

                    this.eventBus.emit('node-retry', {
                        workflowId: this.workflow.id,
                        node,
                        attempt: retries,
                        error
                    });

                    await new Promise(resolve => setTimeout(resolve, backoff));
                } else {
                    // Max retries exceeded
                    const result: TaskResult = {
                        nodeId: node.id,
                        status: 'failure',
                        error: error instanceof Error ? error.message : String(error),
                        duration: Date.now() - startTime,
                        retries
                    };

                    this.results.set(node.id, result);
                    this.workflow.status.failedNodes.push(node.id);
                    this.workflow.status.currentNodes = this.workflow.status.currentNodes.filter(
                        id => id !== node.id
                    );

                    this.eventBus.emit('node-failed', { workflowId: this.workflow.id, node, result });
                    throw error;
                }
            }
        }
    }

    private async executeTask(node: WorkflowNode): Promise<any> {
        // Placeholder for actual task execution
        // In production, this would call the appropriate agent
        await new Promise(resolve => setTimeout(resolve, 1000));
        return { result: `Task ${node.id} completed by ${node.agentId}` };
    }

    private async executeDecision(node: WorkflowNode): Promise<any> {
        if (!node.condition) {
            throw new Error(`Decision node ${node.id} missing condition`);
        }

        const decision = node.condition(this.workflow.context);
        return { decision };
    }

    private async executeParallel(node: WorkflowNode): Promise<any> {
        if (!node.children) return {};

        const childNodes = node.children
            .map(childId => this.workflow.nodes.get(childId))
            .filter(Boolean) as WorkflowNode[];

        const promises = childNodes.map(child => this.executeNode(child));
        const results = await Promise.all(promises);

        return { parallel: true, results };
    }

    private async executeSequential(node: WorkflowNode): Promise<any> {
        if (!node.children) return {};

        const results: any[] = [];

        for (const childId of node.children) {
            const childNode = this.workflow.nodes.get(childId);
            if (childNode) {
                await this.executeNode(childNode);
                results.push(this.results.get(childId));
            }
        }

        return { sequential: true, results };
    }

    private async executeLoop(node: WorkflowNode): Promise<any> {
        if (!node.condition || !node.children || node.children.length === 0) {
            throw new Error(`Loop node ${node.id} missing condition or children`);
        }

        const results: any[] = [];
        let iteration = 0;
        const maxIterations = 100; // Safety limit

        while (node.condition(this.workflow.context) && iteration < maxIterations) {
            for (const childId of node.children) {
                const childNode = this.workflow.nodes.get(childId);
                if (childNode) {
                    await this.executeNode(childNode);
                    results.push(this.results.get(childId));
                }
            }
            iteration++;
        }

        return { loop: true, iterations: iteration, results };
    }

    private createCheckpoint(stageId: string): void {
        const checkpoint: Checkpoint = {
            id: `cp_${Date.now()}`,
            nodeId: stageId,
            timestamp: Date.now(),
            context: new Map(this.workflow.context),
            results: new Map(this.results)
        };

        this.workflow.checkpoints.push(checkpoint);
        this.eventBus.emit('checkpoint-created', { workflowId: this.workflow.id, checkpoint });
    }

    public pause(): void {
        this.paused = true;
        this.workflow.status.state = 'paused';
        this.eventBus.emit('workflow-paused', this.workflow);
    }

    public resume(): void {
        this.paused = false;
        this.workflow.status.state = 'running';
        this.eventBus.emit('workflow-resumed', this.workflow);
    }

    public cancel(): void {
        this.cancelled = true;
        this.workflow.status.state = 'failed';
        this.workflow.status.error = 'Workflow cancelled by user';
        this.eventBus.emit('workflow-cancelled', this.workflow);
    }
}

/**
 * Workflow Template
 */
interface WorkflowTemplate {
    name: string;
    nodes: Array<{
        id: string;
        type: 'task' | 'decision' | 'parallel' | 'sequential' | 'loop';
        agentId?: string;
        dependencies?: string[];
    }>;
}

/**
 * Workflow Adjustment
 */
interface WorkflowAdjustment {
    type: 'add-node' | 'remove-node' | 'modify-node' | 'reroute';
    node?: WorkflowNode;
    nodeId?: string;
    modifications?: Partial<WorkflowNode>;
    rerouting?: Array<{ from: string; to: string; newTo: string }>;
}