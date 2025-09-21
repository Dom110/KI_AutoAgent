/**
 * Automatic Versioning and DocuBot Integration
 * Triggers version updates and documentation on code changes
 */

import * as vscode from 'vscode';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

export class AutoVersioning {
    private dispatcher: any;
    private docuBotActive: boolean = false;
    private lastVersion: string = '';

    constructor(dispatcher: any) {
        this.dispatcher = dispatcher;
        this.loadLastVersion();
    }

    /**
     * Load the last version from package.json
     */
    private loadLastVersion(): void {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0];
            if (workspaceRoot) {
                const packageJsonPath = path.join(workspaceRoot.uri.fsPath, 'vscode-extension', 'package.json');
                if (fs.existsSync(packageJsonPath)) {
                    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
                    this.lastVersion = packageJson.version || '0.0.0';
                    console.log(`[AUTO-VERSION] Current version: ${this.lastVersion}`);
                }
            }
        } catch (error) {
            console.error('[AUTO-VERSION] Error loading version:', error);
            this.lastVersion = '0.0.0';
        }
    }

    /**
     * Handle code changes and trigger versioning/documentation
     */
    public async onCodeChange(files: string[]): Promise<void> {
        // Filter for relevant code changes
        const hasCodeChanges = files.some(f =>
            f.endsWith('.ts') ||
            f.endsWith('.js') ||
            f.endsWith('.py') ||
            f.endsWith('.tsx') ||
            f.endsWith('.jsx')
        );

        if (!hasCodeChanges) {
            return;
        }

        console.log('[AUTO-VERSION] Code changes detected in files:', files);

        try {
            // Calculate new version based on commit type
            const newVersion = await this.calculateVersion();

            if (newVersion !== this.lastVersion) {
                console.log(`[AUTO-VERSION] Version update: ${this.lastVersion} → ${newVersion}`);

                // Update package.json
                await this.updatePackageVersion(newVersion);

                // Update CHANGELOG.md in CLAUDE.md format
                await this.updateChangelog(newVersion, files);

                // Trigger DocuBot
                await this.triggerDocuBot(newVersion, files);

                // Show notification
                vscode.window.showInformationMessage(
                    `✅ Version ${newVersion} created, documentation updated`,
                    'View Changes'
                ).then(selection => {
                    if (selection === 'View Changes') {
                        vscode.commands.executeCommand('git.viewFileChanges');
                    }
                });

                this.lastVersion = newVersion;
            }
        } catch (error) {
            console.error('[AUTO-VERSION] Error in versioning workflow:', error);
            vscode.window.showErrorMessage(`Versioning error: ${error}`);
        }
    }

    /**
     * Calculate new version based on conventional commits
     */
    private async calculateVersion(): Promise<string> {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceRoot) return this.lastVersion;

            // Get latest git commits
            const commits = execSync('git log --oneline -n 10', {
                cwd: workspaceRoot.uri.fsPath
            }).toString();

            // Parse version parts
            const [major, minor, patch] = this.lastVersion.split('.').map(Number);

            // Check for breaking changes
            if (commits.includes('BREAKING CHANGE') || commits.includes('!:')) {
                return `${major + 1}.0.0`;
            }

            // Check for features
            if (commits.match(/feat:|feature:/)) {
                return `${major}.${minor + 1}.0`;
            }

            // Default to patch
            return `${major}.${minor}.${patch + 1}`;
        } catch (error) {
            console.error('[AUTO-VERSION] Error calculating version:', error);
            // Increment patch as fallback
            const [major, minor, patch] = this.lastVersion.split('.').map(Number);
            return `${major}.${minor}.${patch + 1}`;
        }
    }

    /**
     * Update package.json with new version
     */
    private async updatePackageVersion(version: string): Promise<void> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceRoot) return;

        const packageJsonPath = path.join(workspaceRoot.uri.fsPath, 'vscode-extension', 'package.json');

        if (fs.existsSync(packageJsonPath)) {
            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
            packageJson.version = version;

            fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n');
            console.log(`[AUTO-VERSION] Updated package.json to version ${version}`);
        }
    }

    /**
     * Update CHANGELOG.md following CLAUDE.md format
     */
    private async updateChangelog(version: string, files: string[]): Promise<void> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceRoot) return;

        const changelogPath = path.join(workspaceRoot.uri.fsPath, 'CHANGELOG.md');
        const claudePath = path.join(workspaceRoot.uri.fsPath, 'CLAUDE.md');

        const date = new Date().toLocaleDateString('de-DE', {
            day: 'numeric',
            month: 'numeric',
            year: 'numeric'
        });

        // Get recent commit messages for description
        const commits = execSync('git log --oneline -n 5', {
            cwd: workspaceRoot.uri.fsPath
        }).toString();

        const changeEntry = `├── v${version} (${date}) - AUTO-VERSIONED
│   ├── 🔧 CHANGES
│   │   ├── Modified files: ${files.length}
│   │   └── Files: ${files.slice(0, 3).map(f => path.basename(f)).join(', ')}${files.length > 3 ? '...' : ''}
│   ├── 📝 RECENT COMMITS
${commits.split('\n').slice(0, 3).map(c => `│   │   └── ${c}`).join('\n')}
│   └── 🤖 Auto-generated by AutoVersioning system
`;

        // Update CHANGELOG.md
        if (fs.existsSync(changelogPath)) {
            const changelog = fs.readFileSync(changelogPath, 'utf-8');
            const updatedChangelog = changelog.replace(
                '## Version History',
                `## Version History\n\n${changeEntry}`
            );
            fs.writeFileSync(changelogPath, updatedChangelog);
        }

        // Also update CLAUDE.md if it exists
        if (fs.existsSync(claudePath)) {
            const claude = fs.readFileSync(claudePath, 'utf-8');
            const updatedClaude = claude.replace(
                '## 📊 Migration Timeline',
                `${changeEntry}\n\n## 📊 Migration Timeline`
            );
            fs.writeFileSync(claudePath, updatedClaude);
        }

        console.log(`[AUTO-VERSION] Updated changelog for version ${version}`);
    }

    /**
     * Trigger DocuBot for documentation updates
     */
    private async triggerDocuBot(version: string, files: string[]): Promise<void> {
        if (this.docuBotActive) {
            console.log('[AUTO-VERSION] DocuBot already active, skipping');
            return;
        }

        this.docuBotActive = true;
        console.log(`[AUTO-VERSION] Triggering DocuBot for version ${version}`);

        try {
            // Create DocuBot workflow
            const docuWorkflow = [
                {
                    id: 'update-docs',
                    agent: 'docu',
                    description: 'Update documentation for new version'
                }
            ];

            const docuRequest = {
                prompt: `Update documentation for version ${version}.
                Changed files: ${files.join(', ')}

                Tasks:
                1. Update README.md with new version info
                2. Update API documentation if APIs changed
                3. Update instruction files if agent behavior changed
                4. Create release notes

                Focus on what's new and what changed.`,
                command: 'auto',
                context: {
                    version,
                    changedFiles: files
                }
            };

            // Execute DocuBot workflow
            await this.dispatcher.executeWorkflow(docuWorkflow, docuRequest);

            console.log('[AUTO-VERSION] DocuBot documentation update completed');
        } catch (error) {
            console.error('[AUTO-VERSION] Error triggering DocuBot:', error);
        } finally {
            this.docuBotActive = false;
        }
    }

    /**
     * Watch for file changes
     */
    public startWatching(): vscode.Disposable {
        const watcher = vscode.workspace.createFileSystemWatcher('**/*.{ts,js,py,tsx,jsx}');

        const changedFiles: Set<string> = new Set();
        let debounceTimer: NodeJS.Timeout;

        const handleChanges = () => {
            if (changedFiles.size > 0) {
                const files = Array.from(changedFiles);
                changedFiles.clear();
                this.onCodeChange(files);
            }
        };

        watcher.onDidChange(uri => {
            changedFiles.add(uri.fsPath);
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(handleChanges, 5000); // Wait 5 seconds after last change
        });

        watcher.onDidCreate(uri => {
            changedFiles.add(uri.fsPath);
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(handleChanges, 5000);
        });

        return watcher;
    }
}