/**
 * Agent Configuration Manager
 * Handles per-agent model selection, instruction loading, and self-adaptation
 */
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';
import { 
    AgentModelConfig, 
    InstructionSet, 
    LearningConfig, 
    PerformanceMetrics,
    InstructionAdaptation,
    AgentConfigurationSystem,
    AVAILABLE_MODELS,
    DEFAULT_AGENT_MODELS
} from '../types/AgentConfiguration';

export class AgentConfigurationManager {
    private static instance: AgentConfigurationManager;
    private configPath: string = '';
    private configuration: AgentConfigurationSystem;
    private context: vscode.ExtensionContext;

    private constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.configuration = {
            models: new Map(),
            instructions: new Map(),
            learning: this.getDefaultLearningConfig(),
            metrics: new Map()
        };
    }

    public static getInstance(context: vscode.ExtensionContext): AgentConfigurationManager {
        if (!AgentConfigurationManager.instance) {
            AgentConfigurationManager.instance = new AgentConfigurationManager(context);
        }
        return AgentConfigurationManager.instance;
    }

    /**
     * Initialize configuration system
     */
    public async initialize(): Promise<void> {
        try {
            // Determine configuration path
            await this.determineConfigPath();
            
            // Ensure configuration directory structure exists
            await this.ensureConfigStructure();
            
            // Load existing configuration or create defaults
            await this.loadConfiguration();
            
            // Load instruction sets
            await this.loadInstructionSets();
            
            console.log('✅ AgentConfigurationManager initialized');
        } catch (error) {
            console.error('❌ Failed to initialize AgentConfigurationManager:', error);
            throw error;
        }
    }

    /**
     * Get agent model configuration
     */
    public getAgentModel(agentId: string): string {
        const config = this.configuration.models.get(agentId);
        return config?.selectedModel || DEFAULT_AGENT_MODELS[agentId as keyof typeof DEFAULT_AGENT_MODELS] || 'claude-sonnet-4-20250514';
    }

    /**
     * Set agent model
     */
    public async setAgentModel(agentId: string, modelId: string): Promise<void> {
        const config = this.configuration.models.get(agentId) || this.createDefaultModelConfig(agentId);
        config.selectedModel = modelId;
        config.lastUpdated = new Date().toISOString();
        
        this.configuration.models.set(agentId, config);
        await this.saveModelConfiguration();
        
        console.log(`🤖 Updated ${agentId} model to ${modelId}`);
    }

    /**
     * Get agent instructions
     */
    public async getAgentInstructions(agentId: string): Promise<string> {
        const instructionSet = this.configuration.instructions.get(agentId);
        if (instructionSet) {
            return instructionSet.content;
        }
        
        // Load from file if not in memory
        return await this.loadInstructionFile(agentId);
    }

    /**
     * Update agent instructions (self-adaptation)
     */
    public async updateAgentInstructions(
        agentId: string, 
        newContent: string, 
        reason: string, 
        trigger: 'success' | 'failure' | 'manual' | 'learning'
    ): Promise<void> {
        const currentInstructions = await this.getAgentInstructions(agentId);
        
        // Create adaptation record
        const adaptation: InstructionAdaptation = {
            timestamp: new Date().toISOString(),
            trigger,
            oldContent: currentInstructions,
            newContent,
            reason
        };

        // Update instruction set
        const instructionSet = this.configuration.instructions.get(agentId) || {
            agentId,
            version: '1.0.0',
            content: currentInstructions,
            lastModified: new Date().toISOString(),
            modifiedBy: trigger === 'manual' ? 'user' : 'self-adaptation',
            successRate: 0,
            totalExecutions: 0,
            adaptationHistory: []
        };

        instructionSet.content = newContent;
        instructionSet.lastModified = new Date().toISOString();
        instructionSet.modifiedBy = trigger === 'manual' ? 'user' : 'self-adaptation';
        instructionSet.adaptationHistory.push(adaptation);
        
        // Keep only last 50 adaptations to prevent memory bloat
        if (instructionSet.adaptationHistory.length > 50) {
            instructionSet.adaptationHistory = instructionSet.adaptationHistory.slice(-50);
        }

        this.configuration.instructions.set(agentId, instructionSet);
        
        // Save to file
        await this.saveInstructionFile(agentId, instructionSet);
        
        console.log(`📝 Updated instructions for ${agentId}: ${reason}`);
    }

    /**
     * Record agent performance for learning
     */
    public async recordAgentPerformance(
        agentId: string,
        success: boolean,
        responseTime: number,
        context?: string
    ): Promise<void> {
        const metrics = this.configuration.metrics.get(agentId) || this.createDefaultMetrics(agentId);
        
        metrics.totalExecutions++;
        if (success) {
            metrics.successfulExecutions++;
            metrics.currentStreak++;
            metrics.bestStreak = Math.max(metrics.bestStreak, metrics.currentStreak);
        } else {
            metrics.failedExecutions++;
            metrics.currentStreak = 0;
        }
        
        // Update average response time
        const totalTime = metrics.averageResponseTime * (metrics.totalExecutions - 1) + responseTime;
        metrics.averageResponseTime = totalTime / metrics.totalExecutions;
        metrics.lastExecution = new Date().toISOString();
        
        this.configuration.metrics.set(agentId, metrics);
        
        // Check if auto-learning should trigger
        if (this.configuration.learning.enabled) {
            await this.checkForLearningOpportunity(agentId, success, context);
        }
        
        // Periodically save metrics
        if (metrics.totalExecutions % 10 === 0) {
            await this.saveMetrics();
        }
    }

    /**
     * Get available models for an agent
     */
    public getAvailableModels(): Record<string, any> {
        return AVAILABLE_MODELS;
    }

    /**
     * Get agent performance metrics
     */
    public getAgentMetrics(agentId: string): PerformanceMetrics | undefined {
        return this.configuration.metrics.get(agentId);
    }

    /**
     * Get learning configuration
     */
    public getLearningConfig(): LearningConfig {
        return this.configuration.learning;
    }

    /**
     * Update learning configuration
     */
    public async updateLearningConfig(config: Partial<LearningConfig>): Promise<void> {
        this.configuration.learning = { ...this.configuration.learning, ...config };
        await this.saveLearningConfig();
    }

    // Private methods
    private async determineConfigPath(): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders && workspaceFolders.length > 0) {
            // Use workspace-specific configuration
            this.configPath = path.join(workspaceFolders[0].uri.fsPath, '.kiautoagent');
        } else {
            // Use global configuration in user's home directory
            const homeDir = process.env.HOME || process.env.USERPROFILE || '';
            this.configPath = path.join(homeDir, '.kiautoagent');
        }
    }

    private async ensureConfigStructure(): Promise<void> {
        const directories = [
            this.configPath,
            path.join(this.configPath, 'config'),
            path.join(this.configPath, 'instructionsets'),
            path.join(this.configPath, 'learning')
        ];

        for (const dir of directories) {
            try {
                await fs.mkdir(dir, { recursive: true });
            } catch (error) {
                console.warn(`Could not create directory ${dir}:`, error);
            }
        }
    }

    private async loadConfiguration(): Promise<void> {
        // Load model configurations
        await this.loadModelConfiguration();
        
        // Load learning configuration
        await this.loadLearningConfiguration();
        
        // Load metrics
        await this.loadMetrics();
    }

    private async loadModelConfiguration(): Promise<void> {
        try {
            const configFile = path.join(this.configPath, 'config', 'agent-models.json');
            const data = await fs.readFile(configFile, 'utf-8');
            const configs = JSON.parse(data);
            
            for (const config of configs) {
                this.configuration.models.set(config.agentId, config);
            }
        } catch (error) {
            // Create default configuration
            for (const [agentId, defaultModel] of Object.entries(DEFAULT_AGENT_MODELS)) {
                this.configuration.models.set(agentId, this.createDefaultModelConfig(agentId));
            }
            await this.saveModelConfiguration();
        }
    }

    private async saveModelConfiguration(): Promise<void> {
        try {
            const configFile = path.join(this.configPath, 'config', 'agent-models.json');
            const configs = Array.from(this.configuration.models.values());
            await fs.writeFile(configFile, JSON.stringify(configs, null, 2));
        } catch (error) {
            console.error('Failed to save model configuration:', error);
        }
    }

    private async loadInstructionSets(): Promise<void> {
        const instructionDir = path.join(this.configPath, 'instructionsets');
        const agentIds = ['orchestrator', 'richter', 'architect', 'codesmith', 'tradestrat', 'research'];
        
        for (const agentId of agentIds) {
            try {
                await this.loadInstructionFile(agentId);
            } catch (error) {
                console.warn(`Could not load instructions for ${agentId}:`, error);
                // Copy from extension bundle
                await this.copyDefaultInstructionFile(agentId);
            }
        }
    }

    private async loadInstructionFile(agentId: string): Promise<string> {
        const instructionFile = path.join(this.configPath, 'instructionsets', `${agentId}.md`);
        try {
            const content = await fs.readFile(instructionFile, 'utf-8');
            
            // Update in-memory instruction set
            const instructionSet: InstructionSet = {
                agentId,
                version: '1.0.0',
                content,
                lastModified: new Date().toISOString(),
                modifiedBy: 'user',
                successRate: 0,
                totalExecutions: 0,
                adaptationHistory: []
            };
            
            this.configuration.instructions.set(agentId, instructionSet);
            return content;
        } catch (error) {
            throw new Error(`Could not load instruction file for ${agentId}: ${error}`);
        }
    }

    private async saveInstructionFile(agentId: string, instructionSet: InstructionSet): Promise<void> {
        const instructionFile = path.join(this.configPath, 'instructionsets', `${agentId}.md`);
        await fs.writeFile(instructionFile, instructionSet.content);
    }

    private async copyDefaultInstructionFile(agentId: string): Promise<void> {
        try {
            const sourcePath = path.join(this.context.extensionPath, 'src', 'instructionsets', `${agentId}.md`);
            const targetPath = path.join(this.configPath, 'instructionsets', `${agentId}.md`);
            
            const content = await fs.readFile(sourcePath, 'utf-8');
            await fs.writeFile(targetPath, content);
            
            console.log(`📋 Copied default instructions for ${agentId}`);
        } catch (error) {
            console.error(`Failed to copy default instructions for ${agentId}:`, error);
        }
    }

    private createDefaultModelConfig(agentId: string): AgentModelConfig {
        const defaultModel = DEFAULT_AGENT_MODELS[agentId as keyof typeof DEFAULT_AGENT_MODELS] || 'claude-sonnet-4-20250514';
        
        return {
            agentId,
            displayName: agentId.charAt(0).toUpperCase() + agentId.slice(1),
            selectedModel: defaultModel,
            availableModels: Object.keys(AVAILABLE_MODELS),
            instructionFile: `${agentId}.md`,
            lastUpdated: new Date().toISOString(),
            performanceScore: 0
        };
    }

    private createDefaultMetrics(agentId: string): PerformanceMetrics {
        return {
            agentId,
            totalExecutions: 0,
            successfulExecutions: 0,
            failedExecutions: 0,
            averageResponseTime: 0,
            lastExecution: new Date().toISOString(),
            successPatterns: [],
            failurePatterns: [],
            currentStreak: 0,
            bestStreak: 0
        };
    }

    private getDefaultLearningConfig(): LearningConfig {
        return {
            enabled: true,
            adaptationThreshold: 0.8, // 80% success rate required
            maxAdaptationsPerDay: 3,
            confidenceLevel: 0.9,
            learningModes: {
                successBasedLearning: true,
                failureBasedLearning: false,
                patternRecognition: true,
                contextualAdaptation: true
            }
        };
    }

    private async loadLearningConfiguration(): Promise<void> {
        try {
            const configFile = path.join(this.configPath, 'config', 'learning-settings.json');
            const data = await fs.readFile(configFile, 'utf-8');
            this.configuration.learning = { ...this.configuration.learning, ...JSON.parse(data) };
        } catch (error) {
            // Use defaults and save
            await this.saveLearningConfig();
        }
    }

    private async saveLearningConfig(): Promise<void> {
        try {
            const configFile = path.join(this.configPath, 'config', 'learning-settings.json');
            await fs.writeFile(configFile, JSON.stringify(this.configuration.learning, null, 2));
        } catch (error) {
            console.error('Failed to save learning configuration:', error);
        }
    }

    private async loadMetrics(): Promise<void> {
        try {
            const metricsFile = path.join(this.configPath, 'config', 'performance-metrics.json');
            const data = await fs.readFile(metricsFile, 'utf-8');
            const metricsArray = JSON.parse(data);
            
            for (const metrics of metricsArray) {
                this.configuration.metrics.set(metrics.agentId, metrics);
            }
        } catch (error) {
            // No metrics file yet, will be created on first save
        }
    }

    private async saveMetrics(): Promise<void> {
        try {
            const metricsFile = path.join(this.configPath, 'config', 'performance-metrics.json');
            const metricsArray = Array.from(this.configuration.metrics.values());
            await fs.writeFile(metricsFile, JSON.stringify(metricsArray, null, 2));
        } catch (error) {
            console.error('Failed to save metrics:', error);
        }
    }

    private async checkForLearningOpportunity(agentId: string, success: boolean, context?: string): Promise<void> {
        const metrics = this.configuration.metrics.get(agentId);
        if (!metrics) return;

        const successRate = metrics.successfulExecutions / metrics.totalExecutions;
        
        // Only adapt if we have enough data and high success rate
        if (metrics.totalExecutions < 10) return;
        if (successRate < this.configuration.learning.adaptationThreshold) return;
        
        // Check if we haven't adapted too much today
        const today = new Date().toDateString();
        const instructionSet = this.configuration.instructions.get(agentId);
        const todayAdaptations = instructionSet?.adaptationHistory.filter(
            a => new Date(a.timestamp).toDateString() === today
        ).length || 0;
        
        if (todayAdaptations >= this.configuration.learning.maxAdaptationsPerDay) return;
        
        // Trigger learning adaptation (would call LLM to analyze patterns and suggest improvements)
        console.log(`🧠 Learning opportunity detected for ${agentId}: ${successRate.toFixed(2)} success rate`);
        
        // This would be implemented to call the agent's model to analyze its own performance
        // and suggest instruction improvements
    }
}