/**
 * Web Search Service for real-time research and information gathering
 */
import * as vscode from 'vscode';

export interface SearchResult {
    title: string;
    url: string;
    snippet: string;
    content?: string;
}

export interface SearchResponse {
    query: string;
    results: SearchResult[];
    totalResults: number;
}

export class WebSearchService {
    private config: vscode.WorkspaceConfiguration;

    constructor() {
        this.config = vscode.workspace.getConfiguration('kiAutoAgent');
    }

    async search(query: string): Promise<SearchResponse> {
        const webAccessEnabled = this.config.get<boolean>('webAccess.enabled', true);
        
        if (!webAccessEnabled) {
            throw new Error('Web access is disabled in settings');
        }

        const searchEngine = this.config.get<string>('webAccess.searchEngine', 'perplexity');
        const maxResults = this.config.get<number>('webAccess.maxResults', 5);

        switch (searchEngine) {
            case 'perplexity':
                return await this.searchWithPerplexity(query, maxResults);
            case 'tavily':
                return await this.searchWithTavily(query, maxResults);
            case 'serp':
                return await this.searchWithSERP(query, maxResults);
            case 'custom':
                return await this.searchWithCustom(query, maxResults);
            default:
                throw new Error(`Unknown search engine: ${searchEngine}`);
        }
    }

    private async searchWithPerplexity(query: string, maxResults: number): Promise<SearchResponse> {
        const apiKey = this.config.get<string>('perplexity.apiKey');
        
        if (!apiKey) {
            throw new Error('Perplexity API key not configured');
        }

        try {
            const response = await fetch('https://api.perplexity.ai/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'llama-3.1-sonar-small-128k-online',
                    messages: [
                        {
                            role: 'system',
                            content: 'You are a helpful research assistant. Provide comprehensive information with sources.'
                        },
                        {
                            role: 'user',
                            content: `Research and provide detailed information about: ${query}`
                        }
                    ],
                    max_tokens: 1000,
                    temperature: 0.2,
                    return_citations: true
                })
            });

            if (!response.ok) {
                throw new Error(`Perplexity API error: ${response.statusText}`);
            }

            const data = await response.json() as any;
            const content = data.choices[0]?.message?.content || '';
            const citations = data.citations || [];

            // Convert Perplexity response to SearchResponse format
            const results: SearchResult[] = citations.slice(0, maxResults).map((citation: any, index: number) => ({
                title: `Source ${index + 1}`,
                url: citation.url || '',
                snippet: citation.text || '',
                content: content
            }));

            // If no citations but we have content, create a general result
            if (results.length === 0 && content) {
                results.push({
                    title: 'Perplexity Research Result',
                    url: 'https://perplexity.ai',
                    snippet: content.substring(0, 200) + '...',
                    content: content
                });
            }

            return {
                query,
                results,
                totalResults: results.length
            };

        } catch (error) {
            throw new Error(`Perplexity search failed: ${error}`);
        }
    }

    private async searchWithTavily(query: string, maxResults: number): Promise<SearchResponse> {
        const apiKey = this.config.get<string>('tavily.apiKey');
        
        if (!apiKey) {
            throw new Error('Tavily API key not configured');
        }

        try {
            const response = await fetch('https://api.tavily.com/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_key: apiKey,
                    query: query,
                    search_depth: 'advanced',
                    include_answer: true,
                    include_images: false,
                    include_raw_content: true,
                    max_results: maxResults
                })
            });

            if (!response.ok) {
                throw new Error(`Tavily API error: ${response.statusText}`);
            }

            const data = await response.json() as any;
            
            const results: SearchResult[] = (data.results || []).map((result: any) => ({
                title: result.title || '',
                url: result.url || '',
                snippet: result.content || '',
                content: result.raw_content || result.content
            }));

            return {
                query,
                results,
                totalResults: data.results?.length || 0
            };

        } catch (error) {
            throw new Error(`Tavily search failed: ${error}`);
        }
    }

    private async searchWithSERP(query: string, maxResults: number): Promise<SearchResponse> {
        const apiKey = this.config.get<string>('serp.apiKey');
        
        if (!apiKey) {
            throw new Error('SERP API key not configured');
        }

        try {
            const url = new URL('https://serpapi.com/search');
            url.searchParams.append('q', query);
            url.searchParams.append('api_key', apiKey);
            url.searchParams.append('engine', 'google');
            url.searchParams.append('num', maxResults.toString());

            const response = await fetch(url.toString());

            if (!response.ok) {
                throw new Error(`SERP API error: ${response.statusText}`);
            }

            const data = await response.json() as any;
            
            const results: SearchResult[] = (data.organic_results || []).map((result: any) => ({
                title: result.title || '',
                url: result.link || '',
                snippet: result.snippet || '',
                content: result.snippet || ''
            }));

            return {
                query,
                results,
                totalResults: data.organic_results?.length || 0
            };

        } catch (error) {
            throw new Error(`SERP search failed: ${error}`);
        }
    }

    private async searchWithCustom(query: string, maxResults: number): Promise<SearchResponse> {
        const endpoint = this.config.get<string>('customSearch.endpoint');
        const apiKey = this.config.get<string>('customSearch.apiKey');
        
        if (!endpoint) {
            throw new Error('Custom search endpoint not configured');
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
                },
                body: JSON.stringify({
                    query,
                    max_results: maxResults
                })
            });

            if (!response.ok) {
                throw new Error(`Custom search API error: ${response.statusText}`);
            }

            const data = await response.json() as any;
            
            // Assume custom API returns results in our expected format
            return {
                query,
                results: data.results || [],
                totalResults: data.total_results || 0
            };

        } catch (error) {
            throw new Error(`Custom search failed: ${error}`);
        }
    }

    async isWebAccessAvailable(): Promise<boolean> {
        const webAccessEnabled = this.config.get<boolean>('webAccess.enabled', true);
        
        if (!webAccessEnabled) {
            return false;
        }

        const searchEngine = this.config.get<string>('webAccess.searchEngine', 'perplexity');
        
        switch (searchEngine) {
            case 'perplexity':
                return !!this.config.get<string>('perplexity.apiKey');
            case 'tavily':
                return !!this.config.get<string>('tavily.apiKey');
            case 'serp':
                return !!this.config.get<string>('serp.apiKey');
            case 'custom':
                return !!this.config.get<string>('customSearch.endpoint');
            default:
                return false;
        }
    }

    getSearchEngineStatus(): { engine: string; configured: boolean; error?: string } {
        const searchEngine = this.config.get<string>('webAccess.searchEngine', 'perplexity');
        
        switch (searchEngine) {
            case 'perplexity':
                return {
                    engine: 'Perplexity',
                    configured: !!this.config.get<string>('perplexity.apiKey')
                };
            case 'tavily':
                return {
                    engine: 'Tavily',
                    configured: !!this.config.get<string>('tavily.apiKey')
                };
            case 'serp':
                return {
                    engine: 'SERP API',
                    configured: !!this.config.get<string>('serp.apiKey')
                };
            case 'custom':
                return {
                    engine: 'Custom',
                    configured: !!this.config.get<string>('customSearch.endpoint')
                };
            default:
                return {
                    engine: searchEngine,
                    configured: false,
                    error: 'Unknown search engine'
                };
        }
    }
}