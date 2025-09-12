/**
 * Chat Interface JavaScript
 * Handles all interactions in the KI AutoAgent chat webview
 */

(function() {
    // VS Code API
    const vscode = acquireVsCodeApi();
    
    // DOM Elements
    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const clearBtn = document.getElementById('clear-btn');
    const agentDropdown = document.getElementById('agent-dropdown');
    const modeBtns = document.querySelectorAll('.mode-btn');
    const quickActions = document.querySelectorAll('.quick-action');
    
    // State
    let currentMode = 'auto';
    let currentAgent = 'orchestrator';
    let isTyping = false;
    let messageHistory = [];
    let historyIndex = -1;
    
    // Initialize
    function init() {
        setupEventListeners();
        restoreState();
        focusInput();
    }
    
    // Event Listeners
    function setupEventListeners() {
        // Send button
        sendBtn.addEventListener('click', sendMessage);
        
        // Clear button
        clearBtn.addEventListener('click', clearChat);
        
        // Message input
        messageInput.addEventListener('keydown', handleInputKeydown);
        messageInput.addEventListener('input', autoResizeTextarea);
        
        // Agent dropdown
        agentDropdown.addEventListener('change', (e) => {
            currentAgent = e.target.value;
            vscode.postMessage({
                command: 'changeAgent',
                agent: currentAgent
            });
            saveState();
        });
        
        // Mode buttons
        modeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                modeBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentMode = btn.dataset.mode;
                vscode.postMessage({
                    command: 'changeMode',
                    mode: currentMode
                });
                
                // Update agent dropdown based on mode
                if (currentMode === 'auto') {
                    agentDropdown.value = 'orchestrator';
                    currentAgent = 'orchestrator';
                    agentDropdown.disabled = true;
                } else {
                    agentDropdown.disabled = false;
                }
                
                saveState();
            });
        });
        
        // Quick action buttons
        quickActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                vscode.postMessage({
                    command: 'quickAction',
                    action: action
                });
                
                // Hide welcome message after action
                const welcomeMsg = document.querySelector('.welcome-message');
                if (welcomeMsg) {
                    welcomeMsg.style.display = 'none';
                }
            });
        });
    }
    
    // Handle input keyboard events
    function handleInputKeydown(e) {
        // Send on Enter (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
        
        // History navigation with up/down arrows
        if (e.key === 'ArrowUp' && messageInput.value === '') {
            e.preventDefault();
            navigateHistory('up');
        } else if (e.key === 'ArrowDown' && historyIndex >= 0) {
            e.preventDefault();
            navigateHistory('down');
        }
    }
    
    // Send message
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text || isTyping) return;
        
        // Hide welcome message
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'none';
        }
        
        // Add to history
        messageHistory.push(text);
        historyIndex = messageHistory.length;
        
        // Send to extension
        vscode.postMessage({
            command: 'sendMessage',
            text: text,
            agent: currentAgent,
            mode: currentMode
        });
        
        // Clear input
        messageInput.value = '';
        autoResizeTextarea();
        focusInput();
        
        // Save state
        saveState();
    }
    
    // Clear chat
    function clearChat() {
        if (confirm('Clear all messages?')) {
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <h2>👋 Welcome to KI AutoAgent Chat</h2>
                    <p>Select an agent above or use Auto mode for intelligent routing.</p>
                    <div class="quick-actions">
                        <button class="quick-action" data-action="help">📚 Help</button>
                        <button class="quick-action" data-action="examples">💡 Examples</button>
                        <button class="quick-action" data-action="agents">🤖 View Agents</button>
                    </div>
                </div>
            `;
            
            // Re-attach quick action listeners
            document.querySelectorAll('.quick-action').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = btn.dataset.action;
                    vscode.postMessage({
                        command: 'quickAction',
                        action: action
                    });
                });
            });
            
            vscode.postMessage({
                command: 'clearChat'
            });
        }
    }
    
    // Add message to chat
    function addMessage(message) {
        // Hide welcome message if it exists
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'none';
        }
        
        // Remove typing indicator if present
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        
        // Add special class for agent-to-agent messages
        if (message.role === 'agent-to-agent') {
            messageDiv.classList.add('agent-to-agent');
        }
        
        // Build message content
        let html = '';
        
        if (message.agent && message.role !== 'user') {
            html += `
                <div class="message-header">
                    <span class="agent-name">${getAgentIcon(message.agent)} ${message.agent}</span>
                    <span class="timestamp">${formatTimestamp(message.timestamp)}</span>
                </div>
            `;
        }
        
        html += `<div class="message-content">${formatMessageContent(message.content)}</div>`;
        
        if (message.role === 'user') {
            html += `<div class="timestamp">${formatTimestamp(message.timestamp)}</div>`;
        }
        
        messageDiv.innerHTML = html;
        
        // Check if message should be collapsible
        if (message.isCollapsible || (message.content.length > 500 && message.role === 'agent-to-agent')) {
            makeCollapsible(messageDiv);
        }
        
        // Add to container
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Make message collapsible
    function makeCollapsible(messageDiv) {
        messageDiv.classList.add('collapsed');
        
        const expandBtn = document.createElement('div');
        expandBtn.className = 'expand-btn';
        expandBtn.textContent = 'Show more';
        expandBtn.onclick = () => {
            messageDiv.classList.toggle('collapsed');
            expandBtn.textContent = messageDiv.classList.contains('collapsed') ? 'Show more' : 'Show less';
        };
        
        messageDiv.appendChild(expandBtn);
    }
    
    // Show typing indicator
    function showTypingIndicator(agent) {
        // Remove existing typing indicator
        const existing = document.querySelector('.typing-indicator');
        if (existing) {
            existing.remove();
        }
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <span class="agent-name">${getAgentIcon(agent)} ${agent}</span>
            <div class="typing-dots">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        scrollToBottom();
        isTyping = true;
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        isTyping = false;
    }
    
    // Format message content (basic markdown support)
    function formatMessageContent(content) {
        // Escape HTML
        content = escapeHtml(content);
        
        // Convert markdown-style formatting
        // Bold
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Code blocks
        content = content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Headers
        content = content.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        content = content.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        content = content.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        
        // Lists
        content = content.replace(/^- (.*?)$/gm, '<li>$1</li>');
        content = content.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }
    
    // Escape HTML
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    // Get agent icon
    function getAgentIcon(agent) {
        const icons = {
            'orchestrator': '🤖',
            'architect': '🏗️',
            'codesmith': '💻',
            'tradestrat': '📈',
            'research': '🔍',
            'richter': '⚖️',
            'docu': '📝',
            'reviewer': '👁️',
            'fixer': '🔧',
            'system': 'ℹ️'
        };
        return icons[agent.toLowerCase()] || '🤖';
    }
    
    // Format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Auto-resize textarea
    function autoResizeTextarea() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }
    
    // Navigate message history
    function navigateHistory(direction) {
        if (direction === 'up' && historyIndex > 0) {
            historyIndex--;
            messageInput.value = messageHistory[historyIndex];
            autoResizeTextarea();
        } else if (direction === 'down') {
            if (historyIndex < messageHistory.length - 1) {
                historyIndex++;
                messageInput.value = messageHistory[historyIndex];
            } else {
                historyIndex = messageHistory.length;
                messageInput.value = '';
            }
            autoResizeTextarea();
        }
    }
    
    // Scroll to bottom of messages
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Focus input
    function focusInput() {
        messageInput.focus();
    }
    
    // Save state
    function saveState() {
        const state = {
            currentMode,
            currentAgent,
            messageHistory
        };
        vscode.setState(state);
    }
    
    // Restore state
    function restoreState() {
        const state = vscode.getState();
        if (state) {
            currentMode = state.currentMode || 'auto';
            currentAgent = state.currentAgent || 'orchestrator';
            messageHistory = state.messageHistory || [];
            historyIndex = messageHistory.length;
            
            // Update UI
            agentDropdown.value = currentAgent;
            modeBtns.forEach(btn => {
                if (btn.dataset.mode === currentMode) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // Update agent dropdown state
            if (currentMode === 'auto') {
                agentDropdown.disabled = true;
            }
        }
    }
    
    // Handle messages from extension
    window.addEventListener('message', event => {
        const message = event.data;
        
        switch (message.type) {
            case 'addMessage':
                addMessage(message.message);
                break;
                
            case 'showTyping':
                showTypingIndicator(message.agent);
                break;
                
            case 'hideTyping':
                hideTypingIndicator();
                break;
                
            case 'updateState':
                if (message.state) {
                    currentMode = message.state.mode || currentMode;
                    currentAgent = message.state.agent || currentAgent;
                    saveState();
                }
                break;
        }
    });
    
    // Initialize on load
    init();
})();