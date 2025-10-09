/**
 * Model Configuration Settings for VS Code Extension
 * Manages dynamic AI model selection and discovery
 */

import * as vscode from 'vscode';
import { BackendClient } from '../backend/BackendClient';

export interface ModelConfig {
    provider: string;
    models: string[];
    latest: string[];
    recommended: {
        general: string;
        code: string;
        fast: string;
        reasoning: string;
    };
    descriptions?: Array<{
        id: string;
        name: string;
        tier: string;
        bestFor: string;
        pros: string[];
        cons: string[];
        costPerMToken: {
            input: number;
            output: number;
        };
    }>;
}

export class ModelSettingsManager {
    private static instance: ModelSettingsManager;
    private backendClient: BackendClient;
    private cachedModels: Map<string, ModelConfig> = new Map();

    private constructor(backendClient: BackendClient) {
        this.backendClient = backendClient;
    }

    static getInstance(backendClient: BackendClient): ModelSettingsManager {
        if (!ModelSettingsManager.instance) {
            ModelSettingsManager.instance = new ModelSettingsManager(backendClient);
        }
        return ModelSettingsManager.instance;
    }

    /**
     * Fetch available models from backend and update settings
     */
    async refreshAvailableModels(): Promise<void> {
        try {
            // Fetch all available models
            const response = await fetch(`http://${this.backendClient.getBackendUrl()}/api/models`);
            const allModels = await response.json();

            // Fetch details for each provider
            for (const provider of ['openai', 'anthropic', 'perplexity']) {
                const providerResponse = await fetch(`http://${this.backendClient.getBackendUrl()}/api/models/${provider}`);
                const providerData = await providerResponse.json() as ModelConfig;
                this.cachedModels.set(provider, providerData);
            }

            // Update VS Code settings schema dynamically
            await this.updateSettingsSchema();

            const modelData = allModels as Record<string, any>;
            vscode.window.showInformationMessage(`✅ Model discovery complete! Found models from ${Object.keys(modelData).length} providers`);
        } catch (error) {
            console.error('Failed to refresh models:', error);
            vscode.window.showWarningMessage('⚠️ Failed to discover AI models. Using defaults.');
        }
    }

    /**
     * Discover models with rich descriptions on startup
     * Differentiates GPT (15), Claude (5), Perplexity (5)
     */
    async discoverModelsOnStartup(): Promise<void> {
        try {
            console.log('🔍 Discovering available AI models with descriptions...');

            // Fetch model descriptions from backend
            const response = await fetch(`http://${this.backendClient.getBackendUrl()}/api/models/descriptions`);

            if (!response.ok) {
                // v6.0.0: Model discovery endpoint not available in integrated server
                // This is expected - just use defaults silently
                if (response.status === 404) {
                    console.log('ℹ️  Model discovery not available in v6 backend (using defaults)');
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const descriptions = await response.json() as any;

            // Store in cache with rich metadata
            this.cachedModels.clear();
            for (const [provider, data] of Object.entries(descriptions)) {
                const providerData = data as any;
                this.cachedModels.set(provider, {
                    provider,
                    models: providerData.models.map((m: any) => m.id),
                    latest: providerData.models.slice(0, 3).map((m: any) => m.id),
                    recommended: providerData.recommended,
                    descriptions: providerData.models // Full descriptions with pros/cons
                });
            }

            console.log(`✅ Discovered ${descriptions.openai.total} GPT models, ${descriptions.anthropic.total} Claude models, ${descriptions.perplexity.total} Perplexity models`);

            // Show notification with summary
            vscode.window.showInformationMessage(
                `🤖 Model Discovery Complete!\n` +
                `• ${descriptions.openai.total} GPT models (incl. Realtime, o1)\n` +
                `• ${descriptions.anthropic.total} Claude models (Opus, Sonnet)\n` +
                `• ${descriptions.perplexity.total} Perplexity models (Research)`
            );

        } catch (error) {
            // v6.0.0: Silently use defaults if backend doesn't support model discovery
            console.log('ℹ️  Model discovery not available (using defaults)');
            // Don't show warning - this is expected in v6
        }
    }

    /**
     * Show rich model picker with descriptions, pros/cons, and cost
     */
    async showRichModelPicker(provider: string, agentId?: string): Promise<string | undefined> {
        const modelData = this.cachedModels.get(provider);

        // If no cached data, discover first
        if (!modelData || !modelData.descriptions) {
            await this.discoverModelsOnStartup();
            const refreshedData = this.cachedModels.get(provider);
            if (!refreshedData || !refreshedData.descriptions) {
                vscode.window.showWarningMessage(`No models available for ${provider}`);
                return undefined;
            }
            return this.showRichModelPicker(provider, agentId);
        }

        // Build rich quick pick items
        const items = modelData.descriptions.map((model: any) => {
            const costInfo = `${model.costPerMToken.input}/${model.costPerMToken.output} $/M tokens`;
            const prosText = model.pros.join(', ');
            const consText = model.cons.join(', ');

            return {
                label: `$(star-full) ${model.name}`,
                description: `${model.tier} • ${costInfo}`,
                detail: `✅ Best for: ${model.bestFor}\n` +
                        `👍 Pros: ${prosText}\n` +
                        `👎 Cons: ${consText}`,
                model: model.id
            };
        });

        // Add recommended badge
        if (modelData.recommended) {
            const recommendedIds = Object.values(modelData.recommended);
            items.forEach((item: { label: string; description: string; detail: string; model: string }) => {
                if (recommendedIds.includes(item.model)) {
                    item.label = `⭐ ${item.label} (Recommended)`;
                }
            });
        }

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: agentId ?
                `Select model for ${agentId}` :
                `Select ${provider} model`,
            title: `${provider.toUpperCase()} Model Selection`,
            matchOnDescription: true,
            matchOnDetail: true
        });

        return selected ? (selected as any).model : undefined;
    }

    /**
     * Store discovered models for dropdown options
     * NOTE: Does NOT automatically update user settings - user must select manually
     */
    private async updateSettingsSchema(): Promise<void> {
        // Just cache the discovered models for dropdown options
        // DO NOT automatically update user settings

        const openaiModels = this.cachedModels.get('openai');
        const anthropicModels = this.cachedModels.get('anthropic');
        const perplexityModels = this.cachedModels.get('perplexity');

        // Log available models for user information
        if (openaiModels && openaiModels.latest.length > 0) {
            console.log(`OpenAI models available: ${openaiModels.latest.join(', ')}`);
        }

        if (anthropicModels && anthropicModels.latest.length > 0) {
            console.log(`Anthropic models available: ${anthropicModels.latest.join(', ')}`);
        }

        if (perplexityModels && perplexityModels.latest.length > 0) {
            console.log(`Perplexity models available: ${perplexityModels.latest.join(', ')}`);
        }

        // The discovered models are now cached and can be used for dropdown options
        // User must manually select them in VS Code settings
    }

    /**
     * Get model selection for a specific agent
     */
    getAgentModel(agentName: string): string {
        const config = vscode.workspace.getConfiguration('kiAutoAgent.models');

        // Map agent names to config keys
        const agentModelMap: { [key: string]: string } = {
            'architect': config.get('openai.architect') || 'gpt-4o-2024-11-20',
            'orchestrator': config.get('openai.orchestrator') || 'gpt-4o-2024-11-20',
            'docubot': config.get('openai.docubot') || 'gpt-4o-2024-11-20',
            'reviewer': config.get('openai.reviewer') || 'gpt-4o-mini-2024-07-18',
            'performancebot': config.get('openai.performancebot') || 'gpt-4o-2024-11-20',
            'codesmith': config.get('anthropic.codesmith') || 'claude-3.5-sonnet-20241022',
            'fixer': config.get('anthropic.fixer') || 'claude-3.5-sonnet-20241022',
            'tradestrat': config.get('anthropic.tradestrat') || 'claude-3.5-sonnet-20241022',
            'opus': config.get('anthropic.opus') || 'claude-3-opus-20240229',
            'research': config.get('perplexity.research') || 'llama-3.1-sonar-huge-128k-online'
        };

        return agentModelMap[agentName.toLowerCase()] || 'gpt-4o-2024-11-20';
    }

    /**
     * Show model selection quick pick
     */
    async showModelSelectionPicker(provider: string): Promise<string | undefined> {
        const modelConfig = this.cachedModels.get(provider);
        if (!modelConfig || modelConfig.models.length === 0) {
            await this.refreshAvailableModels();
        }

        const models = this.cachedModels.get(provider)?.models || [];
        if (models.length === 0) {
            vscode.window.showWarningMessage(`No models available for ${provider}`);
            return undefined;
        }

        const items = models.map(model => ({
            label: model,
            description: this.getModelDescription(model),
            detail: this.isRecommended(provider, model) ? '⭐ Recommended' : undefined
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: `Select a ${provider} model`,
            title: `${provider.toUpperCase()} Model Selection`
        });

        return selected?.label;
    }

    private getModelDescription(model: string): string {
        // Provide descriptions for common models
        if (model.includes('gpt-5')) return '🚀 Latest GPT-5 model';
        if (model.includes('gpt-4o')) return '⚡ Optimized GPT-4';
        if (model.includes('gpt-4')) return '🧠 GPT-4 model';
        if (model.includes('mini')) return '💨 Fast, lightweight model';
        if (model.includes('opus')) return '🎭 Most capable Claude model';
        if (model.includes('sonnet')) return '🎵 Balanced Claude model';
        if (model.includes('haiku')) return '⚡ Fast Claude model';
        if (model.includes('huge')) return '🔍 Most capable search model';
        if (model.includes('large')) return '📊 Large search model';
        if (model.includes('small')) return '💨 Fast search model';
        return '🤖 AI Model';
    }

    private isRecommended(provider: string, model: string): boolean {
        const config = this.cachedModels.get(provider);
        if (!config) return false;

        return Object.values(config.recommended).includes(model);
    }

    /**
     * Register commands for model management
     */
    registerCommands(context: vscode.ExtensionContext): void {
        // Command to refresh models
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.refreshModels', async () => {
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: "Discovering AI Models",
                    cancellable: false
                }, async (progress) => {
                    progress.report({ message: "Querying API endpoints..." });
                    await this.discoverModelsOnStartup();
                });
            })
        );

        // Command to configure agent models (per-agent selection)
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.configureAgentModels', async () => {
                // Show agent picker first
                const agents = [
                    { label: '🎯 Orchestrator', id: 'orchestrator', provider: 'openai' },
                    { label: '🏗️ Architect', id: 'architect', provider: 'openai' },
                    { label: '💻 CodeSmith', id: 'codesmith', provider: 'anthropic' },
                    { label: '🔍 Reviewer', id: 'reviewer', provider: 'openai' },
                    { label: '🔧 Fixer', id: 'fixer', provider: 'anthropic' },
                    { label: '📝 DocBot', id: 'docubot', provider: 'openai' },
                    { label: '🔬 Research', id: 'research', provider: 'perplexity' },
                    { label: '📈 TradeStrat', id: 'tradestrat', provider: 'anthropic' },
                    { label: '⚖️ OpusArbitrator', id: 'opus', provider: 'anthropic' },
                    { label: '⚡ Performance', id: 'performancebot', provider: 'openai' }
                ];

                const selectedAgent = await vscode.window.showQuickPick(agents, {
                    placeHolder: 'Select agent to configure model',
                    title: 'Agent Model Configuration'
                });

                if (!selectedAgent) return;

                // Show rich model picker for that agent's provider
                const model = await this.showRichModelPicker(
                    selectedAgent.provider,
                    selectedAgent.id
                );

                if (model) {
                    const config = vscode.workspace.getConfiguration('kiAutoAgent.models');
                    await config.update(
                        `${selectedAgent.provider}.${selectedAgent.id}`,
                        model,
                        vscode.ConfigurationTarget.Global
                    );

                    vscode.window.showInformationMessage(
                        `✅ ${selectedAgent.label} model set to: ${model}`
                    );
                }
            })
        );

        // Command to select OpenAI model (shows all GPT models)
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.selectOpenAIModel', async () => {
                const model = await this.showRichModelPicker('openai');
                if (model) {
                    vscode.window.showInformationMessage(`Selected GPT model: ${model}\n\nUse "Configure Agent Models" to assign it to a specific agent.`);
                }
            })
        );

        // Command to select Anthropic model (shows all Claude models)
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.selectAnthropicModel', async () => {
                const model = await this.showRichModelPicker('anthropic');
                if (model) {
                    vscode.window.showInformationMessage(`Selected Claude model: ${model}\n\nUse "Configure Agent Models" to assign it to a specific agent.`);
                }
            })
        );

        // Command to select Perplexity model (shows all Perplexity models)
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.selectPerplexityModel', async () => {
                const model = await this.showRichModelPicker('perplexity');
                if (model) {
                    vscode.window.showInformationMessage(`Selected Perplexity model: ${model}\n\nUse "Configure Agent Models" to assign it to a specific agent.`);
                }
            })
        );
    }
}