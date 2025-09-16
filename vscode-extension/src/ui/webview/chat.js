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
    const planFirstBtn = document.getElementById('plan-first-btn');
    const thinkingModeBtn = document.getElementById('thinking-mode-btn');
    const stopBtn = document.getElementById('stop-btn');
    const settingsBtn = document.getElementById('settings-btn');
    const modeOptions = document.querySelectorAll('.mode-option');
    
    // State
    let currentAgent = 'auto';
    let isTyping = false;
    let messageHistory = [];
    let historyIndex = -1;
    let thinkingMode = false;
    let isProcessing = false;
    
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
        
        // Plan First button
        if (planFirstBtn) {
            planFirstBtn.addEventListener('click', sendPlanFirstMessage);
        }
        
        // Thinking Mode toggle
        if (thinkingModeBtn) {
            thinkingModeBtn.addEventListener('click', toggleThinkingMode);
        }
        
        // Stop button
        if (stopBtn) {
            stopBtn.addEventListener('click', stopCurrentOperation);
        }
        
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
                console.log('[CHAT.JS] Agent selector clicked:');
                console.log('[CHAT.JS]   - btn.dataset.agent:', btn.dataset.agent);
                console.log('[CHAT.JS]   - currentAgent now:', currentAgent);
                
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
        
        // Note: User message will be added by backend to prevent duplicates
        
        // Determine mode
        const mode = currentAgent === 'auto' ? 'auto' : 'single';
        console.log('[CHAT.JS] Sending message with:');
        console.log('[CHAT.JS]   - text:', text.substring(0, 50) + '...');
        console.log('[CHAT.JS]   - agent:', currentAgent);
        console.log('[CHAT.JS]   - mode:', mode);
        console.log('[CHAT.JS]   - currentAgent === "auto":', currentAgent === 'auto');
        
        // Send to extension with thinking mode flag
        vscode.postMessage({
            command: 'sendMessage',
            text: text,
            agent: currentAgent,
            mode: mode,
            thinkingMode: thinkingMode
        });
        
        // Set processing state
        isProcessing = true;
        updateButtonStates();
        
        // Clear input
        messageInput.value = '';
        autoResizeTextarea();
        focusInput();
        
        // Save state
        saveState();
    }
    
    // Add streaming message to chat
    function addStreamingMessage(message) {
        console.log('[CHAT.JS] addStreamingMessage called with:', message);
        
        // Hide welcome message if it exists
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        // Create message wrapper with special streaming class
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${message.role} streaming`;
        messageWrapper.dataset.messageId = message.metadata?.messageId;
        
        // Create message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        // Add initial content (empty for streaming)
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = '<span class="streaming-cursor">▋</span>';
        messageBubble.appendChild(messageContent);
        
        // Add to wrapper
        messageWrapper.appendChild(messageBubble);
        
        // Add to container
        messagesContainer.appendChild(messageWrapper);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Update streaming message with partial content
    function updateStreamingMessage(messageId, partialContent) {
        const messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageWrapper) {
            const messageContent = messageWrapper.querySelector('.message-content');
            if (messageContent) {
                // Remove cursor if present
                const cursor = messageContent.querySelector('.streaming-cursor');
                if (cursor) {
                    cursor.remove();
                }
                
                // Append new content
                const currentContent = messageContent.innerHTML;
                messageContent.innerHTML = currentContent + formatMessageContent(partialContent) + '<span class="streaming-cursor">▋</span>';
                
                // Scroll to bottom
                scrollToBottom();
            }
        }
    }
    
    // Update existing message (for tool results)
    function updateMessage(messageId, newContent) {
        // Find message by data-message-id first
        let messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
        
        // If not found, search in system messages for content containing the messageId
        if (!messageWrapper) {
            const systemMessages = document.querySelectorAll('.message-wrapper.system');
            for (const wrapper of systemMessages) {
                const messageContent = wrapper.querySelector('.message-content');
                if (messageContent && messageContent.textContent.includes(messageId)) {
                    messageWrapper = wrapper;
                    break;
                }
            }
        }
        
        if (messageWrapper) {
            const messageContent = messageWrapper.querySelector('.message-content');
            if (messageContent) {
                // Update the content
                messageContent.innerHTML = formatMessageContent(newContent);
                // Enhance code blocks if any
                const messageBubble = messageWrapper.querySelector('.message-bubble');
                if (messageBubble) {
                    enhanceCodeBlocks(messageBubble);
                }
            }
        }
    }
    
    // Finalize streaming message
    function finalizeStreamingMessage(messageId, fullContent, metadata) {
        const messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageWrapper) {
            // Remove streaming class
            messageWrapper.classList.remove('streaming');
            
            const messageContent = messageWrapper.querySelector('.message-content');
            if (messageContent) {
                // Set final content without cursor
                messageContent.innerHTML = formatMessageContent(fullContent);
                
                // Add metadata if present
                if (metadata && !metadata.isStreaming) {
                    const messageMeta = document.createElement('div');
                    messageMeta.className = 'message-meta';
                    messageMeta.innerHTML = `<span class="timestamp">${formatTimestamp(new Date().toISOString())}</span>`;
                    messageWrapper.querySelector('.message-bubble').appendChild(messageMeta);
                }
                
                // Enhance code blocks
                enhanceCodeBlocks(messageWrapper.querySelector('.message-bubble'));
            }
        }
    }
    
    // Add message to chat - Claude Code Style
    function addMessage(message) {
        console.log('[CHAT.JS] addMessage called with:', message);
        console.log('[CHAT.JS] Message content length:', message.content?.length || 0);
        console.log('[CHAT.JS] Message role:', message.role);
        
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
    
    // Toggle thinking mode
    function toggleThinkingMode() {
        thinkingMode = !thinkingMode;
        if (thinkingModeBtn) {
            thinkingModeBtn.classList.toggle('active', thinkingMode);
            vscode.postMessage({
                command: 'toggleThinkingMode',
                enabled: thinkingMode
            });
        }
    }
    
    // Stop current operation
    function stopCurrentOperation() {
        if (isProcessing) {
            vscode.postMessage({
                command: 'stopOperation'
            });
            hideTypingIndicator();
            isProcessing = false;
            updateButtonStates();
        }
    }
    
    // Update button states based on processing status
    function updateButtonStates() {
        if (sendBtn) sendBtn.disabled = isProcessing;
        if (planFirstBtn) planFirstBtn.disabled = isProcessing;
        if (stopBtn) stopBtn.disabled = !isProcessing;
    }
    
    // Send Plan First message
    function sendPlanFirstMessage() {
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
        
        // Determine mode
        const mode = currentAgent === 'auto' ? 'auto' : 'single';
        console.log('[CHAT.JS] Sending plan first message with:');
        console.log('[CHAT.JS]   - text:', text.substring(0, 50) + '...');
        console.log('[CHAT.JS]   - agent:', currentAgent);
        console.log('[CHAT.JS]   - mode:', mode);
        
        // Send to extension with planFirst command and thinking mode
        vscode.postMessage({
            command: 'planFirst',
            text: text,
            agent: currentAgent,
            mode: mode,
            thinkingMode: thinkingMode
        });
        
        // Set processing state
        isProcessing = true;
        updateButtonStates();
        
        // Clear input
        messageInput.value = '';
        autoResizeTextarea();
        focusInput();
        
        // Save state
        saveState();
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
        console.log('[CHAT.JS] Received message from extension:', message);
        console.log('[CHAT.JS] Message type:', message.type);
        
        switch (message.type) {
            case 'addMessage':
                console.log('[CHAT.JS] Processing addMessage for:', message.message);
                addMessage(message.message);
                break;
                
            case 'addStreamingMessage':
                console.log('[CHAT.JS] Adding streaming message:', message.message);
                addStreamingMessage(message.message);
                break;
                
            case 'updateStreamingMessage':
                console.log('[CHAT.JS] Updating streaming message:', message.messageId, 'with', message.partialContent?.length, 'chars');
                updateStreamingMessage(message.messageId, message.partialContent);
                break;
                
            case 'updateMessage':
                console.log('[CHAT.JS] Updating message:', message.messageId);
                updateMessage(message.messageId, message.content);
                break;
                
            case 'finalizeStreamingMessage':
                console.log('[CHAT.JS] Finalizing streaming message:', message.messageId);
                finalizeStreamingMessage(message.messageId, message.fullContent, message.metadata);
                break;
                
            case 'showTyping':
                showTypingIndicator(message.agent);
                break;
                
            case 'hideTyping':
                hideTypingIndicator();
                isProcessing = false;
                updateButtonStates();
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

            case 'restoreMessages':
                // Clear existing messages first
                messagesContainer.innerHTML = '';
                // Add all messages back
                if (message.messages && message.messages.length > 0) {
                    message.messages.forEach(msg => {
                        addMessage(msg);
                    });
                } else {
                    // Show welcome message if no messages
                    messagesContainer.innerHTML = `
                        <div class="welcome-message">
                            <h2>Welcome to KI AutoAgent</h2>
                            <p>Start a conversation with our AI agents</p>
                        </div>
                    `;
                }
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