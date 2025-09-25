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
     * Update the package.json settings schema with discovered models
     */
    private async updateSettingsSchema(): Promise<void> {
        const config = vscode.workspace.getConfiguration('kiAutoAgent.models');

        // Get latest models for each provider
        const openaiModels = this.cachedModels.get('openai');
        const anthropicModels = this.cachedModels.get('anthropic');
        const perplexityModels = this.cachedModels.get('perplexity');

        // Update settings with latest models
        if (openaiModels && openaiModels.latest.length > 0) {
            await config.update('openai.architect', openaiModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('openai.orchestrator', openaiModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('openai.docubot', openaiModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('openai.reviewer', openaiModels.latest[1] || openaiModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('openai.performancebot', openaiModels.latest[0], vscode.ConfigurationTarget.Global);
        }

        if (anthropicModels && anthropicModels.latest.length > 0) {
            await config.update('anthropic.codesmith', anthropicModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('anthropic.fixer', anthropicModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('anthropic.tradestrat', anthropicModels.latest[0], vscode.ConfigurationTarget.Global);
            await config.update('anthropic.opus', anthropicModels.recommended.reasoning || anthropicModels.latest[0], vscode.ConfigurationTarget.Global);
        }

        if (perplexityModels && perplexityModels.latest.length > 0) {
            await config.update('perplexity.research', perplexityModels.latest[0], vscode.ConfigurationTarget.Global);
        }
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
                await this.refreshAvailableModels();
            })
        );

        // Command to select OpenAI model
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.selectOpenAIModel', async () => {
                const model = await this.showModelSelectionPicker('openai');
                if (model) {
                    const config = vscode.workspace.getConfiguration('kiAutoAgent.models');
                    await config.update('openai.default', model, vscode.ConfigurationTarget.Global);
                    vscode.window.showInformationMessage(`✅ OpenAI model set to: ${model}`);
                }
            })
        );

        // Command to select Anthropic model
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.selectAnthropicModel', async () => {
                const model = await this.showModelSelectionPicker('anthropic');
                if (model) {
                    const config = vscode.workspace.getConfiguration('kiAutoAgent.models');
                    await config.update('anthropic.default', model, vscode.ConfigurationTarget.Global);
                    vscode.window.showInformationMessage(`✅ Anthropic model set to: ${model}`);
                }
            })
        );

        // Command to select Perplexity model
        context.subscriptions.push(
            vscode.commands.registerCommand('ki-autoagent.selectPerplexityModel', async () => {
                const model = await this.showModelSelectionPicker('perplexity');
                if (model) {
                    const config = vscode.workspace.getConfiguration('kiAutoAgent.models');
                    await config.update('perplexity.default', model, vscode.ConfigurationTarget.Global);
                    vscode.window.showInformationMessage(`✅ Perplexity model set to: ${model}`);
                }
            })
        );
    }
}