/**
 * ChatWidget - Status bar widget for KI AutoAgent Chat
 * Provides quick access to the chat panel from VS Code status bar
 */
import * as vscode from 'vscode';
import { MultiAgentChatPanel } from './MultiAgentChatPanel';

export class ChatWidget {
    private statusBarItem: vscode.StatusBarItem;
    private unreadCount: number = 0;
    private lastMessage: string = '';
    private pulseInterval: NodeJS.Timeout | undefined;
    
    constructor(private context: vscode.ExtensionContext, private dispatcher?: any) {
        // Create status bar item (right side, high priority)
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            1000 // High priority to appear on the right
        );
        
        this.updateStatusBar();
        this.statusBarItem.show();
        
        // Register commands
        this.registerCommands();
        
        // Add to subscriptions
        context.subscriptions.push(this.statusBarItem);
    }
    
    private registerCommands() {
        // Toggle chat command
        const toggleCommand = vscode.commands.registerCommand(
            'ki-autoagent.toggleChat',
            () => this.toggleChat()
        );
        
        // Quick chat command (opens quick input)
        const quickChatCommand = vscode.commands.registerCommand(
            'ki-autoagent.quickChat',
            () => this.showQuickChat()
        );
        
        // Clear unread command
        const clearUnreadCommand = vscode.commands.registerCommand(
            'ki-autoagent.clearUnread',
            () => this.clearUnreadCount()
        );
        
        this.context.subscriptions.push(
            toggleCommand,
            quickChatCommand,
            clearUnreadCommand
        );
    }
    
    private updateStatusBar() {
        // Build status bar text
        let text = '$(comment-discussion) KI Chat';
        
        if (this.unreadCount > 0) {
            text = `$(comment-discussion) KI Chat (${this.unreadCount})`;
            
            // Add warning background for unread messages
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            
            // Start pulse animation
            if (!this.pulseInterval) {
                this.startPulseAnimation();
            }
        } else {
            // Clear background when no unread
            this.statusBarItem.backgroundColor = undefined;
            
            // Stop pulse animation
            if (this.pulseInterval) {
                this.stopPulseAnimation();
            }
        }
        
        this.statusBarItem.text = text;
        this.statusBarItem.command = 'ki-autoagent.toggleChat';
        
        // Update tooltip
        if (this.lastMessage) {
            this.statusBarItem.tooltip = new vscode.MarkdownString(
                `**KI AutoAgent Chat**\n\n` +
                `Last message: _${this.truncateMessage(this.lastMessage)}_\n\n` +
                `Click to open chat • Right-click for options`
            );
        } else {
            this.statusBarItem.tooltip = new vscode.MarkdownString(
                `**KI AutoAgent Chat**\n\n` +
                `Click to open multi-agent chat interface\n\n` +
                `Features:\n` +
                `• Chat with specialized AI agents\n` +
                `• Auto-routing to best agent\n` +
                `• Multi-agent workflows\n\n` +
                `Click to open • Right-click for options`
            );
        }
    }
    
    private startPulseAnimation() {
        let isPulsing = false;
        this.pulseInterval = setInterval(() => {
            if (isPulsing) {
                this.statusBarItem.text = this.statusBarItem.text.replace('🔴', '$(comment-discussion)');
            } else {
                this.statusBarItem.text = this.statusBarItem.text.replace('$(comment-discussion)', '🔴');
            }
            isPulsing = !isPulsing;
        }, 1000);
    }
    
    private stopPulseAnimation() {
        if (this.pulseInterval) {
            clearInterval(this.pulseInterval);
            this.pulseInterval = undefined;
            this.updateStatusBar();
        }
    }
    
    private toggleChat() {
        const panel = MultiAgentChatPanel.createOrShow(this.context.extensionUri, this.dispatcher);
        this.clearUnreadCount();
        return panel;
    }
    
    private async showQuickChat() {
        // Show quick input for fast message sending
        const message = await vscode.window.showInputBox({
            placeHolder: 'Type your message for KI AutoAgent...',
            prompt: 'Send a quick message to the AI agents',
            ignoreFocusOut: false
        });
        
        if (message) {
            // Open chat and send message
            const panel = this.toggleChat();
            if (panel) {
                // Send message to panel
                panel.addMessage({
                    role: 'user',
                    content: message,
                    timestamp: new Date().toISOString()
                });
                
                // Process the message (this would normally go through the dispatcher)
                setTimeout(() => {
                    panel.addMessage({
                        role: 'assistant',
                        content: 'Processing your request...',
                        agent: 'orchestrator',
                        timestamp: new Date().toISOString()
                    });
                }, 100);
            }
        }
    }
    
    public updateUnreadCount(count: number) {
        this.unreadCount = count;
        this.updateStatusBar();
    }
    
    public incrementUnread() {
        this.unreadCount++;
        this.updateStatusBar();
    }
    
    public clearUnreadCount() {
        this.unreadCount = 0;
        this.updateStatusBar();
    }
    
    public setLastMessage(message: string, agent?: string) {
        this.lastMessage = agent ? `[${agent}] ${message}` : message;
        this.updateStatusBar();
    }
    
    private truncateMessage(message: string, maxLength: number = 50): string {
        if (message.length <= maxLength) {
            return message;
        }
        return message.substring(0, maxLength) + '...';
    }
    
    public showNotification(message: string, agent: string) {
        // Show notification when chat is not open
        if (!MultiAgentChatPanel.currentPanel) {
            vscode.window.showInformationMessage(
                `KI Agent ${agent}: ${this.truncateMessage(message, 100)}`,
                'Open Chat',
                'Dismiss'
            ).then(selection => {
                if (selection === 'Open Chat') {
                    this.toggleChat();
                }
            });
            
            // Increment unread count
            this.incrementUnread();
            this.setLastMessage(message, agent);
        }
    }
    
    public dispose() {
        if (this.pulseInterval) {
            clearInterval(this.pulseInterval);
        }
        this.statusBarItem.dispose();
    }
}