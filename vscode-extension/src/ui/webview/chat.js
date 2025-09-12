/**
 * Chat Interface JavaScript - Claude Code Style
 * Handles all interactions in the KI AutoAgent chat webview
 */

(function() {
    // VS Code API
    const vscode = acquireVsCodeApi();
    
    // DOM Elements
    const messagesContainer = document.getElementById('messages-container');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const settingsBtn = document.getElementById('settings-btn');
    const modeOptions = document.querySelectorAll('.mode-option');
    
    // State
    let currentAgent = 'auto';
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
        
        // Settings button
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                vscode.postMessage({ command: 'openSettings' });
            });
        }
        
        // Message input
        messageInput.addEventListener('keydown', handleInputKeydown);
        messageInput.addEventListener('input', autoResizeTextarea);
        
        // Mode selector buttons
        modeOptions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active from all
                modeOptions.forEach(b => b.classList.remove('active'));
                // Add active to clicked
                btn.classList.add('active');
                // Update current agent
                currentAgent = btn.dataset.agent;
                
                vscode.postMessage({
                    command: 'changeAgent',
                    agent: currentAgent
                });
                
                saveState();
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
            welcomeMsg.remove();
        }
        
        // Add to history
        messageHistory.push(text);
        historyIndex = messageHistory.length;
        
        // Add user message immediately
        addMessage({
            role: 'user',
            content: text,
            timestamp: new Date().toISOString()
        });
        
        // Send to extension
        vscode.postMessage({
            command: 'sendMessage',
            text: text,
            agent: currentAgent,
            mode: currentAgent === 'auto' ? 'auto' : 'single'
        });
        
        // Clear input
        messageInput.value = '';
        autoResizeTextarea();
        focusInput();
        
        // Save state
        saveState();
    }
    
    // Add message to chat - Claude Code Style
    function addMessage(message) {
        // Hide welcome message if it exists
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        // Remove typing indicator if present
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Create message wrapper
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${message.role}`;
        
        // Create message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        // Add message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = formatMessageContent(message.content);
        messageBubble.appendChild(messageContent);
        
        // Add metadata (timestamp on hover)
        if (message.timestamp) {
            const messageMeta = document.createElement('div');
            messageMeta.className = 'message-meta';
            messageMeta.innerHTML = `<span class="timestamp">${formatTimestamp(message.timestamp)}</span>`;
            messageBubble.appendChild(messageMeta);
        }
        
        // Handle code blocks for copy functionality
        enhanceCodeBlocks(messageBubble);
        
        // Add to wrapper
        messageWrapper.appendChild(messageBubble);
        
        // Add to container
        messagesContainer.appendChild(messageWrapper);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Show typing indicator - Claude Style
    function showTypingIndicator(agent) {
        // Remove existing typing indicator
        const existing = document.querySelector('.typing-indicator');
        if (existing) {
            existing.remove();
        }
        
        const typingWrapper = document.createElement('div');
        typingWrapper.className = 'message-wrapper assistant';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        
        typingWrapper.appendChild(typingDiv);
        messagesContainer.appendChild(typingWrapper);
        scrollToBottom();
        isTyping = true;
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        const typingWrapper = document.querySelector('.message-wrapper:has(.typing-indicator)');
        if (typingWrapper) {
            typingWrapper.remove();
        }
        isTyping = false;
    }
    
    // Format message content (enhanced markdown support)
    function formatMessageContent(content) {
        // Escape HTML first
        content = escapeHtml(content);
        
        // Preserve code blocks temporarily
        const codeBlocks = [];
        content = content.replace(/```([\s\S]*?)```/g, (match, code) => {
            codeBlocks.push(`<pre><code>${code}</code></pre>`);
            return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
        });
        
        // Convert markdown-style formatting
        // Headers
        content = content.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        content = content.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        content = content.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        
        // Bold
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Inline code
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Lists
        content = content.replace(/^- (.*?)$/gm, '<li>$1</li>');
        content = content.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Links
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        
        // Line breaks
        content = content.replace(/\n/g, '<br>');
        
        // Restore code blocks
        codeBlocks.forEach((block, index) => {
            content = content.replace(`__CODE_BLOCK_${index}__`, 
                `<div class="code-block-wrapper">${block}<button class="copy-code-btn">Copy</button></div>`);
        });
        
        return content;
    }
    
    // Enhance code blocks with copy functionality
    function enhanceCodeBlocks(element) {
        const copyButtons = element.querySelectorAll('.copy-code-btn');
        copyButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const codeBlock = e.target.parentElement.querySelector('code');
                const text = codeBlock.textContent;
                
                navigator.clipboard.writeText(text).then(() => {
                    btn.textContent = 'Copied!';
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy:', err);
                    btn.textContent = 'Failed';
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                    }, 2000);
                });
            });
        });
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
    
    // Format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();
        
        if (isToday) {
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } else {
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
    
    // Auto-resize textarea
    function autoResizeTextarea() {
        messageInput.style.height = 'auto';
        const newHeight = Math.min(messageInput.scrollHeight, 200);
        messageInput.style.height = newHeight + 'px';
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
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }
    
    // Focus input
    function focusInput() {
        messageInput.focus();
    }
    
    // Save state
    function saveState() {
        const state = {
            currentAgent,
            messageHistory
        };
        vscode.setState(state);
    }
    
    // Restore state
    function restoreState() {
        const state = vscode.getState();
        if (state) {
            currentAgent = state.currentAgent || 'auto';
            messageHistory = state.messageHistory || [];
            historyIndex = messageHistory.length;
            
            // Update UI
            modeOptions.forEach(btn => {
                if (btn.dataset.agent === currentAgent) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
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
                
            case 'clearChat':
                messagesContainer.innerHTML = `
                    <div class="welcome-message">
                        <h2>Welcome to KI AutoAgent</h2>
                        <p>Start a conversation with our AI agents</p>
                    </div>
                `;
                messageHistory = [];
                historyIndex = -1;
                saveState();
                break;
                
            case 'updateState':
                if (message.state) {
                    currentAgent = message.state.agent || currentAgent;
                    saveState();
                }
                break;
        }
    });
    
    // Initialize on load
    init();
})();