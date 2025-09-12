/**
 * ResearchBot - Research & Information Expert
 * Uses web search for real-time information gathering and analysis
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { WebSearchService, SearchResponse } from '../utils/WebSearchService';
import { OpenAIService } from '../utils/OpenAIService';

export class ResearchAgent extends ChatAgent {
    private webSearchService: WebSearchService;
    private openAIService: OpenAIService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.research',
            name: 'research',
            fullName: 'ResearchBot',
            description: 'Research & Information Expert with real-time web access',
            model: 'gpt-4o',
            capabilities: [
                'Web Research',
                'Real-time Information',
                'Technical Documentation Search',
                'Market Analysis',
                'Trend Research',
                'Competitive Analysis'
            ],
            commands: [
                { name: 'search', description: 'Search web for current information', handler: 'handleSearchCommand' },
                { name: 'documentation', description: 'Find and analyze technical documentation', handler: 'handleDocumentationCommand' },
                { name: 'market', description: 'Research market trends and analysis', handler: 'handleMarketCommand' },
                { name: 'compare', description: 'Compare technologies, tools, or solutions', handler: 'handleCompareCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.webSearchService = new WebSearchService();
        this.openAIService = new OpenAIService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        // Check if web access is available
        const webAccessAvailable = await this.webSearchService.isWebAccessAvailable();
        
        if (!webAccessAvailable) {
            const status = this.webSearchService.getSearchEngineStatus();
            stream.markdown(`❌ **Web access not configured**\n\n`);
            stream.markdown(`**Current search engine**: ${status.engine}\n`);
            stream.markdown(`**Status**: ${status.configured ? 'Configured' : 'Not configured'}\n\n`);
            stream.markdown(`💡 **To enable web research:**\n`);
            stream.markdown(`1. Open VS Code Settings (Cmd+,)\n`);
            stream.markdown(`2. Search for "KI AutoAgent"\n`);
            stream.markdown(`3. Configure your preferred search API:\n`);
            stream.markdown(`   - **Perplexity API** (recommended)\n`);
            stream.markdown(`   - **Tavily API** (web search specialist)\n`);
            stream.markdown(`   - **SERP API** (Google search)\n`);
            return;
        }

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} research request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralResearchRequest(prompt, stream, token);
        }
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {
        
        try {
            let searchQuery = '';
            let analysisPrompt = '';

            switch (step.id) {
                case 'market_research':
                    searchQuery = `${request.prompt} market trends analysis 2024`;
                    analysisPrompt = 'Analyze market trends and opportunities';
                    break;
                    
                case 'tech_research':
                    searchQuery = `${request.prompt} technical documentation best practices`;
                    analysisPrompt = 'Research technical solutions and documentation';
                    break;
                    
                case 'competitive_analysis':
                    searchQuery = `${request.prompt} competitors alternatives comparison`;
                    analysisPrompt = 'Compare competitive solutions and alternatives';
                    break;
                    
                default:
                    searchQuery = request.prompt;
                    analysisPrompt = 'Research and analyze the given topic';
            }

            // Perform web search
            const searchResults = await this.webSearchService.search(searchQuery);
            
            // Analyze results with AI
            const analysis = await this.analyzeSearchResults(searchResults, analysisPrompt);

            return {
                status: 'success',
                content: analysis,
                metadata: { 
                    step: step.id,
                    agent: 'research',
                    searchQuery,
                    resultsCount: searchResults.results.length
                }
            };

        } catch (error) {
            throw new Error(`Failed to process research step ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleSearchCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('🔍 Searching the web for current information...');
        
        try {
            const searchResults = await this.webSearchService.search(prompt);
            
            stream.markdown(`## 🔍 Web Search Results\n\n`);
            stream.markdown(`**Query**: ${searchResults.query}\n`);
            stream.markdown(`**Results Found**: ${searchResults.totalResults}\n\n`);

            // Display search results
            for (let i = 0; i < searchResults.results.length; i++) {
                const result = searchResults.results[i];
                stream.markdown(`### ${i + 1}. ${result.title}\n`);
                stream.markdown(`**URL**: [${result.url}](${result.url})\n`);
                stream.markdown(`**Summary**: ${result.snippet}\n\n`);
            }

            // Analyze and synthesize results
            stream.progress('🧠 Analyzing search results...');
            const analysis = await this.analyzeSearchResults(searchResults, 'Provide a comprehensive analysis and synthesis of the search results');
            
            stream.markdown(`## 📊 Analysis & Insights\n\n`);
            stream.markdown(analysis);

            // Add source references
            searchResults.results.forEach((result, index) => {
                this.createActionButton(
                    `📖 Read Source ${index + 1}`,
                    'vscode.open',
                    [vscode.Uri.parse(result.url)],
                    stream
                );
            });

        } catch (error) {
            stream.markdown(`❌ Search failed: ${(error as any).message}`);
        }
    }

    private async handleDocumentationCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('📚 Searching for technical documentation...');
        
        const techQuery = `${prompt} documentation tutorial guide API reference`;
        
        try {
            const searchResults = await this.webSearchService.search(techQuery);
            
            stream.markdown(`## 📚 Documentation Research\n\n`);
            stream.markdown(`**Topic**: ${prompt}\n\n`);

            // Filter for documentation sources
            const docResults = searchResults.results.filter(result => 
                result.url.includes('docs') || 
                result.url.includes('documentation') ||
                result.url.includes('api') ||
                result.url.includes('guide') ||
                result.title.toLowerCase().includes('documentation') ||
                result.title.toLowerCase().includes('guide')
            );

            if (docResults.length > 0) {
                stream.markdown(`### 📖 Official Documentation Found\n\n`);
                docResults.forEach((result, index) => {
                    stream.markdown(`**${index + 1}. ${result.title}**\n`);
                    stream.markdown(`- [${result.url}](${result.url})\n`);
                    stream.markdown(`- ${result.snippet}\n\n`);
                });
            }

            // Provide comprehensive analysis
            const analysis = await this.analyzeSearchResults(searchResults, 
                'Provide a comprehensive guide based on the documentation found, including key concepts, usage examples, and best practices');
            
            stream.markdown(`## 📋 Documentation Summary\n\n`);
            stream.markdown(analysis);

        } catch (error) {
            stream.markdown(`❌ Documentation search failed: ${(error as any).message}`);
        }
    }

    private async handleMarketCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('📈 Researching market trends...');
        
        const marketQuery = `${prompt} market trends 2024 analysis statistics growth`;
        
        try {
            const searchResults = await this.webSearchService.search(marketQuery);
            
            stream.markdown(`## 📈 Market Research\n\n`);
            
            const analysis = await this.analyzeSearchResults(searchResults, 
                'Provide a comprehensive market analysis including current trends, growth statistics, key players, opportunities, and challenges');
            
            stream.markdown(analysis);

            // Offer to create market report
            this.createActionButton(
                '📊 Create Market Report',
                'ki-autoagent.createFile',
                [`market_research_${Date.now()}.md`, `# Market Research: ${prompt}\n\n${analysis}`],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Market research failed: ${(error as any).message}`);
        }
    }

    private async handleCompareCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('⚖️ Comparing solutions...');
        
        const compareQuery = `${prompt} comparison alternatives pros cons review`;
        
        try {
            const searchResults = await this.webSearchService.search(compareQuery);
            
            stream.markdown(`## ⚖️ Comparison Analysis\n\n`);
            
            const analysis = await this.analyzeSearchResults(searchResults, 
                'Provide a detailed comparison including pros and cons, use cases, pricing (if available), and recommendations');
            
            stream.markdown(analysis);

            // Offer to create comparison table
            this.createActionButton(
                '📋 Create Comparison Table',
                'ki-autoagent.createComparisonTable',
                [prompt, analysis],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Comparison research failed: ${(error as any).message}`);
        }
    }

    private async handleGeneralResearchRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        
        stream.progress('🔍 Conducting research...');
        
        try {
            const searchResults = await this.webSearchService.search(prompt);
            
            // Quick summary
            stream.markdown(`## 🔍 Research Summary\n\n`);
            stream.markdown(`**Topic**: ${prompt}\n`);
            stream.markdown(`**Sources**: ${searchResults.totalResults} results found\n\n`);

            // Comprehensive analysis
            const analysis = await this.analyzeSearchResults(searchResults, 
                'Provide comprehensive research findings with key insights, current state, and actionable information');
            
            stream.markdown(analysis);

            // Show top sources
            if (searchResults.results.length > 0) {
                stream.markdown(`\n## 📚 Key Sources\n\n`);
                searchResults.results.slice(0, 3).forEach((result, index) => {
                    stream.markdown(`${index + 1}. [${result.title}](${result.url})\n`);
                });
            }

        } catch (error) {
            stream.markdown(`❌ Research failed: ${(error as any).message}`);
        }
    }

    // Helper Methods

    private async analyzeSearchResults(searchResults: SearchResponse, analysisPrompt: string): Promise<string> {
        const resultsContent = searchResults.results
            .map(result => `Title: ${result.title}\nURL: ${result.url}\nContent: ${result.snippet}`)
            .join('\n\n---\n\n');

        const systemPrompt = `You are ResearchBot, an expert research analyst. Analyze web search results and provide comprehensive, accurate, and actionable insights.

Key principles:
1. Synthesize information from multiple sources
2. Highlight key findings and trends
3. Provide actionable recommendations
4. Note any conflicting information
5. Include relevant statistics and data
6. Maintain objectivity and cite sources when possible

Format your response with clear headings and bullet points for readability.`;

        const userPrompt = `${analysisPrompt}

Search Query: ${searchResults.query}

Search Results:
${resultsContent}

Please provide a comprehensive analysis based on these search results.`;

        try {
            return await this.openAIService.chat([
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userPrompt }
            ]);
        } catch (error) {
            return `Error analyzing results: ${(error as any).message}`;
        }
    }
}