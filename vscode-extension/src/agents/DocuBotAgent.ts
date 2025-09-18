/**
 * DocuBot - Technical Documentation Expert
 * Creates comprehensive documentation, READMEs, and API references
 */
import * as vscode from 'vscode';
import { ChatAgent } from './base/ChatAgent';
import { AgentConfig, TaskRequest, TaskResult, WorkflowStep } from '../types';
import { VSCodeMasterDispatcher } from '../core/VSCodeMasterDispatcher';
import { OpenAIService } from '../utils/OpenAIService';
import * as path from 'path';
import * as fs from 'fs/promises';

export class DocuBotAgent extends ChatAgent {
    private openAIService: OpenAIService;

    constructor(context: vscode.ExtensionContext, dispatcher: VSCodeMasterDispatcher) {
        const config: AgentConfig = {
            participantId: 'ki-autoagent.docu',
            name: 'docu',
            fullName: 'DocuBot',
            description: 'Technical Documentation Expert - Creates READMEs, API docs, user guides',
            model: 'gpt-5-2025-09-12',
            iconPath: vscode.Uri.joinPath(context.extensionUri, 'media', 'docu-icon.svg'),
            capabilities: [
                'README Generation',
                'API Documentation',
                'User Guides',
                'Code Comments',
                'Technical Writing',
                'Markdown Formatting',
                'JSDoc/DocStrings',
                'Changelog Creation'
            ],
            commands: [
                { name: 'readme', description: 'Generate README for project', handler: 'handleReadmeCommand' },
                { name: 'api', description: 'Create API documentation', handler: 'handleApiCommand' },
                { name: 'guide', description: 'Write user guide or tutorial', handler: 'handleGuideCommand' },
                { name: 'comments', description: 'Add documentation comments to code', handler: 'handleCommentsCommand' },
                { name: 'changelog', description: 'Generate changelog from commits', handler: 'handleChangelogCommand' },
                { name: 'update-instructions', description: 'Update agent instruction files', handler: 'handleUpdateInstructionsCommand' },
                { name: 'view-instructions', description: 'View agent instruction files', handler: 'handleViewInstructionsCommand' }
            ]
        };

        super(config, context, dispatcher);
        this.openAIService = new OpenAIService();
    }

    protected async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        const command = request.command;
        const prompt = request.prompt;

        this.log(`Processing ${command ? `/${command}` : 'general'} documentation request: ${prompt.substring(0, 100)}...`);

        if (command) {
            await this.handleCommand(command, prompt, stream, token);
        } else {
            await this.handleGeneralDocumentationRequest(prompt, stream, token);
        }
    }

    protected async processWorkflowStep(
        step: WorkflowStep,
        request: TaskRequest,
        previousResults: TaskResult[]
    ): Promise<TaskResult> {

        try {
            let documentationContent = '';

            switch (step.id) {
                case 'document_code':
                    documentationContent = await this.generateCodeDocumentation(request, previousResults);
                    break;

                case 'create_readme':
                    documentationContent = await this.generateReadme(request, previousResults);
                    break;

                case 'api_docs':
                    documentationContent = await this.generateApiDocs(request, previousResults);
                    break;

                default:
                    documentationContent = await this.generateGeneralDocs(request, previousResults);
            }

            return {
                status: 'success',
                content: documentationContent,
                metadata: {
                    step: step.id,
                    agent: 'docu',
                    type: 'documentation'
                }
            };

        } catch (error) {
            throw new Error(`Failed to process documentation step ${step.id}: ${(error as any).message}`);
        }
    }

    // Command Handlers

    private async handleReadmeCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📝 Analyzing project structure...');

        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                stream.markdown('❌ No workspace folder found');
                return;
            }

            // Analyze project structure
            const projectInfo = await this.analyzeProjectStructure(workspaceFolder.uri.fsPath);

            stream.progress('📝 Generating README...');

            const readmeContent = await this.createReadme(projectInfo, prompt);

            stream.markdown('## 📝 Generated README\n\n');
            stream.markdown('```markdown\n' + readmeContent + '\n```');

            // Offer to save
            this.createActionButton(
                '💾 Save README.md',
                'ki-autoagent.saveFile',
                ['README.md', readmeContent],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ README generation failed: ${(error as any).message}`);
        }
    }

    private async handleApiCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('🔍 Analyzing code for API endpoints...');

        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                stream.markdown('❌ No workspace folder found');
                return;
            }

            // Find and analyze API endpoints
            const apiInfo = await this.analyzeApiEndpoints(workspaceFolder.uri.fsPath);

            stream.progress('📖 Generating API documentation...');

            const apiDocs = await this.createApiDocumentation(apiInfo, prompt);

            stream.markdown('## 📖 API Documentation\n\n');
            stream.markdown('```markdown\n' + apiDocs + '\n```');

            // Offer to save
            this.createActionButton(
                '💾 Save API.md',
                'ki-autoagent.saveFile',
                ['docs/API.md', apiDocs],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ API documentation generation failed: ${(error as any).message}`);
        }
    }

    private async handleGuideCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📚 Creating user guide...');

        try {
            const guide = await this.createUserGuide(prompt);

            stream.markdown('## 📚 User Guide\n\n');
            stream.markdown(guide);

            // Offer to save
            this.createActionButton(
                '💾 Save Guide',
                'ki-autoagent.saveFile',
                ['docs/USER_GUIDE.md', guide],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Guide creation failed: ${(error as any).message}`);
        }
    }

    private async handleCommentsCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            stream.markdown('❌ No active editor found. Please open a file to document.');
            return;
        }

        stream.progress('💬 Adding documentation comments...');

        try {
            const document = editor.document;
            const code = document.getText();
            const language = document.languageId;

            const documentedCode = await this.addDocumentationComments(code, language, prompt);

            stream.markdown('## 💬 Documented Code\n\n');
            stream.markdown('```' + language + '\n' + documentedCode + '\n```');

            // Offer to replace
            this.createActionButton(
                '💾 Apply Comments',
                'ki-autoagent.replaceContent',
                [documentedCode],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Comment generation failed: ${(error as any).message}`);
        }
    }

    private async handleChangelogCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📋 Analyzing commit history...');

        try {
            // Get git log
            const gitLog = await this.getGitLog();

            stream.progress('📋 Generating changelog...');

            const changelog = await this.createChangelog(gitLog, prompt);

            stream.markdown('## 📋 Changelog\n\n');
            stream.markdown('```markdown\n' + changelog + '\n```');

            // Offer to save
            this.createActionButton(
                '💾 Save CHANGELOG.md',
                'ki-autoagent.saveFile',
                ['CHANGELOG.md', changelog],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Changelog generation failed: ${(error as any).message}`);
        }
    }

    private async handleGeneralDocumentationRequest(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📝 Creating documentation...');

        try {
            const documentation = await this.createGeneralDocumentation(prompt);

            stream.markdown('## 📝 Documentation\n\n');
            stream.markdown(documentation);

        } catch (error) {
            stream.markdown(`❌ Documentation creation failed: ${(error as any).message}`);
        }
    }

    private async handleUpdateInstructionsCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📝 Updating agent instructions...');

        try {
            // Parse agent name from prompt
            const agentMatch = prompt.match(/\b(orchestrator|architect|codesmith|tradestrat|research|opus-arbitrator|docu|reviewer|fixer)\b/i);
            if (!agentMatch) {
                stream.markdown('❌ Please specify which agent instructions to update (e.g., "update-instructions for codesmith")');
                return;
            }

            const agentName = agentMatch[1].toLowerCase();

            // Read current instructions
            const currentInstructions = await this.readInstructionFile(agentName);

            stream.progress('📝 Analyzing and improving instructions...');

            // Generate improvements
            const improvedInstructions = await this.improveInstructions(agentName, currentInstructions, prompt);

            stream.markdown(`## 📝 Improved Instructions for ${agentName}\n\n`);
            stream.markdown('```markdown\n' + improvedInstructions + '\n```');

            // Offer to save
            this.createActionButton(
                '💾 Save Updated Instructions',
                'ki-autoagent.saveInstructions',
                [agentName, improvedInstructions],
                stream
            );

        } catch (error) {
            stream.markdown(`❌ Instruction update failed: ${(error as any).message}`);
        }
    }

    private async handleViewInstructionsCommand(
        prompt: string,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {

        stream.progress('📖 Loading agent instructions...');

        try {
            // Parse agent name from prompt or list all
            const agentMatch = prompt.match(/\b(orchestrator|architect|codesmith|tradestrat|research|opus-arbitrator|docu|reviewer|fixer)\b/i);

            if (agentMatch) {
                const agentName = agentMatch[1].toLowerCase();
                const instructions = await this.readInstructionFile(agentName);

                stream.markdown(`## 📖 Instructions for ${agentName}\n\n`);
                stream.markdown('```markdown\n' + instructions + '\n```');
            } else {
                // List all available instruction files
                stream.markdown('## 📖 Available Agent Instructions\n\n');
                stream.markdown('Choose an agent to view instructions:\n');
                stream.markdown('- orchestrator\n');
                stream.markdown('- architect\n');
                stream.markdown('- codesmith\n');
                stream.markdown('- tradestrat\n');
                stream.markdown('- research\n');
                stream.markdown('- opus-arbitrator (richter)\n');
                stream.markdown('- docu\n');
                stream.markdown('- reviewer\n');
                stream.markdown('- fixer\n\n');
                stream.markdown('Use: `/view-instructions [agent-name]` to view specific instructions');
            }

        } catch (error) {
            stream.markdown(`❌ Failed to view instructions: ${(error as any).message}`);
        }
    }

    // Helper Methods

    private async analyzeProjectStructure(workspacePath: string): Promise<any> {
        // Analyze project files, package.json, etc.
        const projectInfo: {
            name: string;
            path: string;
            hasPackageJson: boolean;
            dependencies: string[];
            scripts: Record<string, string>;
            mainFiles: string[];
        } = {
            name: path.basename(workspacePath),
            path: workspacePath,
            hasPackageJson: false,
            dependencies: [],
            scripts: {},
            mainFiles: []
        };

        try {
            const packageJsonPath = path.join(workspacePath, 'package.json');
            const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf-8'));
            projectInfo.hasPackageJson = true;
            projectInfo.dependencies = Object.keys(packageJson.dependencies || {});
            projectInfo.scripts = packageJson.scripts || {};
        } catch (error) {
            // No package.json or error reading it
        }

        return projectInfo;
    }

    private async analyzeApiEndpoints(workspacePath: string): Promise<any> {
        // Analyze code for API endpoints
        // This would be more sophisticated in a real implementation
        return {
            endpoints: [],
            baseUrl: '',
            authentication: 'unknown'
        };
    }

    private async createReadme(projectInfo: any, additionalContext: string): Promise<string> {
        const prompt = `Create a comprehensive README.md for a project with the following information:

Project Name: ${projectInfo.name}
Has package.json: ${projectInfo.hasPackageJson}
Dependencies: ${projectInfo.dependencies.join(', ')}
Scripts: ${JSON.stringify(projectInfo.scripts, null, 2)}

Additional context: ${additionalContext}

Create a professional README with sections for:
- Project title and description
- Features
- Installation
- Usage
- Configuration (if applicable)
- API Reference (if applicable)
- Contributing
- License

Use proper markdown formatting with badges where appropriate.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert technical writer specializing in creating clear, comprehensive documentation.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async createApiDocumentation(apiInfo: any, additionalContext: string): Promise<string> {
        const prompt = `Create comprehensive API documentation based on the following:

${JSON.stringify(apiInfo, null, 2)}

Additional context: ${additionalContext}

Include:
- API overview
- Authentication
- Endpoints with request/response examples
- Error codes
- Rate limiting (if applicable)
- Examples in multiple languages

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating clear, comprehensive API documentation.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async createUserGuide(context: string): Promise<string> {
        const prompt = `Create a comprehensive user guide for the following:

${context}

Include:
- Getting Started
- Key Features
- Step-by-step tutorials
- Common use cases
- Troubleshooting
- FAQ

Make it user-friendly and easy to follow.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating user-friendly documentation and guides.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async addDocumentationComments(code: string, language: string, context: string): Promise<string> {
        const prompt = `Add comprehensive documentation comments to this ${language} code:

${code}

Additional context: ${context}

Use the appropriate comment style for ${language} (JSDoc for JavaScript/TypeScript, docstrings for Python, etc.)
Document all functions, classes, and complex logic.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in code documentation and technical writing.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async createChangelog(gitLog: string, context: string): Promise<string> {
        const prompt = `Create a CHANGELOG.md based on the following git history:

${gitLog}

Additional context: ${context}

Format using Keep a Changelog standard (https://keepachangelog.com/)
Group changes by version and category (Added, Changed, Deprecated, Removed, Fixed, Security)

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating clear, organized changelogs.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async createGeneralDocumentation(context: string): Promise<string> {
        const prompt = `Create comprehensive documentation for:

${context}

Make it clear, well-structured, and professional.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert technical writer creating clear, comprehensive documentation.' },
            { role: 'user', content: prompt }
        ]);
    }

    private async getGitLog(): Promise<string> {
        // Execute git log command
        const cp = require('child_process');
        return new Promise((resolve, reject) => {
            cp.exec('git log --oneline -50', (error: any, stdout: string, stderr: string) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    // Workflow helper methods
    private async generateCodeDocumentation(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        return this.createGeneralDocumentation(`Document the following code/feature:\n${request.prompt}\n\nContext from previous steps:\n${context}`);
    }

    private async generateReadme(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            throw new Error('No workspace folder found');
        }
        const projectInfo = await this.analyzeProjectStructure(workspaceFolder.uri.fsPath);
        const context = this.buildContextFromResults(previousResults);
        return this.createReadme(projectInfo, `${request.prompt}\n\nContext:\n${context}`);
    }

    private async generateApiDocs(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            throw new Error('No workspace folder found');
        }
        const apiInfo = await this.analyzeApiEndpoints(workspaceFolder.uri.fsPath);
        const context = this.buildContextFromResults(previousResults);
        return this.createApiDocumentation(apiInfo, `${request.prompt}\n\nContext:\n${context}`);
    }

    private async generateGeneralDocs(request: TaskRequest, previousResults: TaskResult[]): Promise<string> {
        const context = this.buildContextFromResults(previousResults);
        return this.createGeneralDocumentation(`${request.prompt}\n\nContext from previous steps:\n${context}`);
    }

    private buildContextFromResults(results: TaskResult[]): string {
        return results
            .filter(r => r.status === 'success')
            .map(r => `${r.metadata?.step || 'Step'}: ${r.content}`)
            .join('\n\n');
    }

    private async readInstructionFile(agentName: string): Promise<string> {
        try {
            // Map agent names to instruction file names
            const fileNameMap: Record<string, string> = {
                'orchestrator': 'orchestrator-instructions',
                'architect': 'architect-instructions',
                'codesmith': 'codesmith-instructions',
                'tradestrat': 'tradestrat-instructions',
                'research': 'research-instructions',
                'opus-arbitrator': 'richter-instructions',
                'docu': 'docubot-instructions',
                'reviewer': 'reviewergpt-instructions',
                'fixer': 'fixerbot-instructions'
            };

            const fileName = fileNameMap[agentName] || `${agentName}-instructions`;
            const instructionPath = path.join(
                this.context.extensionPath,
                'src',
                'instructions',
                `${fileName}.md`
            );

            return await fs.readFile(instructionPath, 'utf-8');
        } catch (error) {
            throw new Error(`Failed to read instructions for ${agentName}: ${(error as any).message}`);
        }
    }

    private async writeInstructionFile(agentName: string, content: string): Promise<void> {
        try {
            // Map agent names to instruction file names
            const fileNameMap: Record<string, string> = {
                'orchestrator': 'orchestrator-instructions',
                'architect': 'architect-instructions',
                'codesmith': 'codesmith-instructions',
                'tradestrat': 'tradestrat-instructions',
                'research': 'research-instructions',
                'opus-arbitrator': 'richter-instructions',
                'docu': 'docubot-instructions',
                'reviewer': 'reviewergpt-instructions',
                'fixer': 'fixerbot-instructions'
            };

            const fileName = fileNameMap[agentName] || `${agentName}-instructions`;
            const instructionPath = path.join(
                this.context.extensionPath,
                'src',
                'instructions',
                `${fileName}.md`
            );

            await fs.writeFile(instructionPath, content, 'utf-8');
        } catch (error) {
            throw new Error(`Failed to write instructions for ${agentName}: ${(error as any).message}`);
        }
    }

    private async improveInstructions(agentName: string, currentInstructions: string, userContext: string): Promise<string> {
        const prompt = `Improve the instruction set for the ${agentName} agent.

Current instructions:
${currentInstructions}

User context and requirements:
${userContext}

Please improve these instructions by:
1. Ensuring clarity and completeness
2. Adding any missing capabilities or commands
3. Improving formatting and organization
4. Updating best practices
5. Ensuring consistency with the agent's role
6. Adding examples where helpful
7. Keeping the same markdown structure

Return the complete improved instruction set in markdown format.

${this.getSystemContextPrompt()}`;

        return await this.openAIService.chat([
            { role: 'system', content: 'You are DocuBot, an expert in creating and improving technical documentation and agent instructions.' },
            { role: 'user', content: prompt }
        ]);
    }
}