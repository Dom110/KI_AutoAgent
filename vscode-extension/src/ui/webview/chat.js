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
    const thinkingIntensitySelect = document.getElementById('thinking-intensity');
    const stopBtn = document.getElementById('stop-btn');
    const settingsBtn = document.getElementById('settings-btn');
    const modeOptions = document.querySelectorAll('.mode-option');
    
    // State
    let currentAgent = 'auto';
    let isTyping = false;
    let messageHistory = [];
    let historyIndex = -1;
    let thinkingMode = false;
    let thinkingIntensity = 'normal';
    let isProcessing = false;
    
    // Initialize
    function init() {
        setupEventListeners();
        restoreState();
        focusInput();
        initializeTokenCounter();
    }
    
    // Event Listeners
    function setupEventListeners() {
        // Send button
        sendBtn.addEventListener('click', sendMessage);

        // Export chat button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportChat);
        }

        // Attach file button
        const attachBtn = document.getElementById('attach-btn');
        if (attachBtn) {
            attachBtn.addEventListener('click', attachFile);
        }
        
        // Plan First button
        if (planFirstBtn) {
            planFirstBtn.addEventListener('click', sendPlanFirstMessage);
        }
        
        // Thinking Mode toggle
        if (thinkingModeBtn) {
            thinkingModeBtn.addEventListener('click', toggleThinkingMode);
        }

        // Thinking Intensity selector
        if (thinkingIntensitySelect) {
            thinkingIntensitySelect.addEventListener('change', (e) => {
                thinkingIntensity = e.target.value;
                vscode.postMessage({
                    command: 'setThinkingIntensity',
                    intensity: thinkingIntensity
                });
            });
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

        // History button
        const historyBtn = document.getElementById('history-btn');
        if (historyBtn) {
            historyBtn.addEventListener('click', () => {
                vscode.postMessage({ command: 'showHistory' });
            });
        }

        // Message input
        messageInput.addEventListener('keydown', handleInputKeydown);
        messageInput.addEventListener('input', autoResizeTextarea);

        // Add click handler for compact mode message expansion
        document.addEventListener('click', (e) => {
            if (!isCompactMode) return;

            const messageBubble = e.target.closest('.message-bubble');
            if (messageBubble && !messageBubble.classList.contains('system')
                && !messageBubble.classList.contains('tool-notification')) {
                messageBubble.classList.toggle('expanded');
            }
        });
        
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
            thinkingMode: thinkingMode,
            thinkingIntensity: thinkingIntensity
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
        // Add agent-specific class if agent is specified
        if (message.agent) {
            messageWrapper.className = `message-wrapper ${message.role} ${message.agent} streaming`;
        } else {
            messageWrapper.className = `message-wrapper ${message.role} streaming`;
        }
        messageWrapper.dataset.messageId = message.metadata?.messageId;

        // Create message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';

        // Add agent badge for assistant messages
        if (message.role === 'assistant' && message.agent) {
            const agentBadge = document.createElement('div');
            agentBadge.className = 'agent-badge';
            agentBadge.textContent = getAgentDisplayName(message.agent);
            agentBadge.style.color = getAgentColor(message.agent);
            messageBubble.appendChild(agentBadge);
        }

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
    function finalizeStreamingMessage(messageId, fullContent, metadata, agent) {
        const messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageWrapper) {
            // Remove streaming class
            messageWrapper.classList.remove('streaming');

            // Update agent if provided (for workflow results)
            if (agent && agent !== messageWrapper.dataset.agent) {
                // Update wrapper class
                messageWrapper.classList.remove(messageWrapper.dataset.agent);
                messageWrapper.classList.add(agent);
                messageWrapper.dataset.agent = agent;

                // Update or add agent badge
                const messageBubble = messageWrapper.querySelector('.message-bubble');
                let agentBadge = messageBubble.querySelector('.agent-badge');
                if (!agentBadge) {
                    agentBadge = document.createElement('div');
                    agentBadge.className = 'agent-badge';
                    messageBubble.insertBefore(agentBadge, messageBubble.firstChild);
                }
                agentBadge.textContent = getAgentDisplayName(agent);
                agentBadge.style.color = getAgentColor(agent);
            }

            const messageContent = messageWrapper.querySelector('.message-content');
            if (messageContent) {
                // Set final content without cursor
                messageContent.innerHTML = formatMessageContent(fullContent);

                // Check if content should have expand/collapse
                const contentLength = fullContent?.length || 0;
                const shouldTruncate = contentLength > 500;

                if (shouldTruncate && !messageWrapper.querySelector('.expand-button')) {
                    messageContent.classList.add('truncated');

                    const expandButton = document.createElement('button');
                    expandButton.className = 'expand-button';
                    expandButton.textContent = '...';
                    expandButton.title = 'Expand';
                    expandButton.setAttribute('type', 'button');
                    expandButton.addEventListener('click', function(e) {
                        e.stopPropagation();
                        e.preventDefault();
                        toggleMessageExpansion(messageWrapper.querySelector('.message-bubble'));
                    });
                    messageWrapper.querySelector('.message-bubble').appendChild(expandButton);
                }

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
    
    // Clear all messages
    function clearMessages() {
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to KI AutoAgent</h2>
                <p>Start a conversation with our AI agents</p>
            </div>
        `;
    }

    // Add a system message
    function addSystemMessage(content) {
        const message = {
            role: 'system',
            content: content,
            timestamp: new Date().toISOString(),
            metadata: { isSystemNotification: true }
        };
        addMessage(message);
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
        // Add agent-specific class if agent is specified
        if (message.agent) {
            messageWrapper.className = `message-wrapper ${message.role} ${message.agent}`;
        } else {
            messageWrapper.className = `message-wrapper ${message.role}`;
        }

        // Store message ID for action buttons
        const messageId = message.metadata?.messageId || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        messageWrapper.dataset.messageId = messageId;

        // Create message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';

        // Handle tool notifications with agent-specific colors
        if (message.metadata?.isToolNotification && message.metadata?.agentColor) {
            // Tool notification - use agent color
            messageBubble.style.backgroundColor = message.metadata.agentColor;
            messageBubble.style.opacity = '0.85';
            messageBubble.classList.add('tool-notification');

            // Add agent badge for tool notification
            if (message.metadata.agentEmoji && message.metadata.agentName) {
                const toolBadge = document.createElement('div');
                toolBadge.className = 'tool-agent-badge';
                toolBadge.innerHTML = `${message.metadata.agentEmoji} ${getAgentDisplayName(message.metadata.agentName)}`;
                messageBubble.appendChild(toolBadge);
            }
        }
        // Add agent badge for assistant messages
        else if (message.role === 'assistant' && message.agent) {
            const agentBadge = document.createElement('div');
            agentBadge.className = 'agent-badge';
            agentBadge.textContent = getAgentDisplayName(message.agent);
            agentBadge.style.color = getAgentColor(message.agent);
            messageBubble.appendChild(agentBadge);
        }

        // Add message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        // Check if content should be truncated (collapsible)
        const contentLength = message.content?.length || 0;
        const shouldTruncate = message.isCollapsible || contentLength > 500;

        if (shouldTruncate) {
            messageContent.classList.add('truncated');
            // Add unique ID for toggle functionality
            const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            messageContent.setAttribute('data-message-id', messageId);
            messageBubble.setAttribute('data-message-id', messageId);
        }

        messageContent.innerHTML = formatMessageContent(message.content);
        messageBubble.appendChild(messageContent);

        // Add expand button if content is truncated
        if (shouldTruncate) {
            const expandButton = document.createElement('button');
            expandButton.className = 'expand-button';
            expandButton.textContent = '...';
            expandButton.title = 'Expand';
            expandButton.setAttribute('type', 'button');
            // Use addEventListener instead of onclick for better compatibility
            expandButton.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                toggleMessageExpansion(messageBubble);
            });
            messageBubble.appendChild(expandButton);
        }

        // Add metadata (timestamp on hover)
        if (message.timestamp) {
            const messageMeta = document.createElement('div');
            messageMeta.className = 'message-meta';
            messageMeta.innerHTML = `<span class="timestamp">${formatTimestamp(message.timestamp)}</span>`;
            messageBubble.appendChild(messageMeta);
        }

        // Add action buttons for user and assistant messages
        if ((message.role === 'user' || message.role === 'assistant') && !message.metadata?.isSystemNotification) {
            const messageActions = document.createElement('div');
            messageActions.className = 'message-actions';

            // Copy button
            const copyBtn = document.createElement('button');
            copyBtn.className = 'message-action-btn';
            copyBtn.innerHTML = '📋';
            copyBtn.title = 'Copy message';
            copyBtn.onclick = () => copyMessageToClipboard(message.content);
            messageActions.appendChild(copyBtn);

            // Regenerate button (for assistant messages)
            if (message.role === 'assistant') {
                const regenerateBtn = document.createElement('button');
                regenerateBtn.className = 'message-action-btn';
                regenerateBtn.innerHTML = '🔄';
                regenerateBtn.title = 'Regenerate response';
                regenerateBtn.onclick = () => regenerateResponse(messageId, message.agent);
                messageActions.appendChild(regenerateBtn);
            }

            // Edit button (for user messages)
            if (message.role === 'user') {
                const editBtn = document.createElement('button');
                editBtn.className = 'message-action-btn';
                editBtn.innerHTML = '✏️';
                editBtn.title = 'Edit message';
                editBtn.onclick = () => editMessage(messageId, message.content);
                messageActions.appendChild(editBtn);
            }

            messageBubble.appendChild(messageActions);
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
    
    // Toggle message expansion/collapse
    function toggleMessageExpansion(messageBubble) {
        const contentEl = messageBubble.querySelector('.message-content');
        const expandBtn = messageBubble.querySelector('.expand-button');

        if (contentEl && expandBtn) {
            if (contentEl.classList.contains('truncated')) {
                contentEl.classList.remove('truncated');
                expandBtn.textContent = '▲';
                expandBtn.title = 'Collapse';
            } else {
                contentEl.classList.add('truncated');
                expandBtn.textContent = '...';
                expandBtn.title = 'Expand';
            }
        }
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

            // Show/hide thinking intensity selector
            if (thinkingIntensitySelect) {
                thinkingIntensitySelect.style.display = thinkingMode ? 'inline-block' : 'none';
            }

            vscode.postMessage({
                command: 'toggleThinkingMode',
                enabled: thinkingMode,
                intensity: thinkingIntensity
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
    
    // Get agent display name with emoji
    function getAgentDisplayName(agent) {
        const names = {
            'orchestrator': '🎭 Orchestrator',
            'architect': '🏗️ Architect',
            'codesmith': '💻 CodeSmith',
            'tradestrat': '📈 TradeStrat',
            'research': '🔍 Research',
            'opus-arbitrator': '⚖️ Arbitrator'
        };
        return names[agent] || agent;
    }

    // Get agent-specific color
    function getAgentColor(agent) {
        const colors = {
            'orchestrator': '#8B5CF6',     // Purple
            'architect': '#10B981',        // Emerald Green (changed from blue to avoid conflict)
            'codesmith': '#F97316',        // Orange
            'tradestrat': '#14B8A6',       // Turquoise
            'research': '#EAB308',         // Gold
            'opus-arbitrator': '#DC2626',  // Crimson
            'docubot': '#6366F1',          // Indigo
            'reviewer': '#EC4899',         // Pink
            'fixer': '#8B5CF6'             // Purple
        };
        return colors[agent.toLowerCase()] || '#666';
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
    
    // Workflow management
    let activeWorkflows = new Map();

    function createWorkflowContainer(messageId) {
        const container = document.createElement('div');
        container.className = 'workflow-container';
        container.dataset.messageId = messageId;
        container.innerHTML = `
            <div class="workflow-header" onclick="toggleWorkflow('${messageId}')">
                <span class="workflow-icon">🎯</span>
                <span class="workflow-title">Multi-Agent Workflow</span>
                <span class="workflow-toggle">▼</span>
            </div>
            <div class="workflow-steps" id="workflow-steps-${messageId}"></div>
        `;
        messagesContainer.appendChild(container);
        return container;
    }

    function addWorkflowStep(messageId, stepData) {
        let container = document.querySelector(`[data-message-id="${messageId}"]`);
        if (!container) {
            container = createWorkflowContainer(messageId);
        }

        const stepsContainer = container.querySelector('.workflow-steps');
        const stepElement = document.createElement('div');
        stepElement.className = 'workflow-step';
        stepElement.dataset.stepNumber = stepData.step;
        stepElement.innerHTML = `
            <div class="step-header" onclick="toggleStepContent('${messageId}-${stepData.step}')">
                <span class="step-status">${stepData.status === 'completed' ? '✅' : '🔄'}</span>
                <span class="step-info">Step ${stepData.step}/${stepData.total}: @${stepData.agent}</span>
                <span class="step-description">${stepData.description}</span>
                <span class="step-toggle">▼</span>
            </div>
            <div class="step-content collapsed" id="step-content-${messageId}-${stepData.step}">
                <div class="step-result">${stepData.result || 'Processing...'}</div>
            </div>
        `;

        const existingStep = stepsContainer.querySelector(`[data-step-number="${stepData.step}"]`);
        if (existingStep) {
            existingStep.replaceWith(stepElement);
        } else {
            stepsContainer.appendChild(stepElement);
        }
    }

    window.toggleStepContent = function(stepId) {
        const content = document.getElementById(`step-content-${stepId}`);
        const header = content.previousElementSibling;
        const toggle = header.querySelector('.step-toggle');

        if (content.classList.contains('collapsed')) {
            content.classList.remove('collapsed');
            toggle.textContent = '▲';
        } else {
            content.classList.add('collapsed');
            toggle.textContent = '▼';
        }
    }

    window.toggleWorkflow = function(messageId) {
        const container = document.querySelector(`[data-message-id="${messageId}"]`);
        const stepsContainer = container.querySelector('.workflow-steps');
        const toggle = container.querySelector('.workflow-toggle');

        if (stepsContainer.style.display === 'none') {
            stepsContainer.style.display = 'block';
            toggle.textContent = '▼';
        } else {
            stepsContainer.style.display = 'none';
            toggle.textContent = '▶';
        }
    }

    function addFinalResultBubble(message) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper assistant final-result-wrapper';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble assistant-bubble final-result';
        bubble.innerHTML = `
            <div class="final-result-header">✨ Final Result</div>
            <div class="message-content">${formatMessageContent(message.content)}</div>
            <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
        `;

        wrapper.appendChild(bubble);
        messagesContainer.appendChild(wrapper);
        scrollToBottom();
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
                finalizeStreamingMessage(message.messageId, message.fullContent, message.metadata, message.agent);
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

            case 'initWorkflow':
                console.log('[CHAT] Initializing workflow:', message.messageId);
                createWorkflowContainer(message.messageId);
                break;

            case 'updateWorkflowStep':
                console.log('[CHAT] Updating workflow step:', message.stepData);
                addWorkflowStep(message.messageId, message.stepData);
                break;

            case 'completeWorkflowStep':
                console.log('[CHAT] Completing workflow step:', message.stepData);
                addWorkflowStep(message.messageId, message.stepData);
                break;

            case 'addFinalResult':
                console.log('[CHAT] Adding final result:', message.message);
                addFinalResultBubble(message.message);
                break;
        }
    });
    
    // Copy message to clipboard
    function copyMessageToClipboard(content) {
        // Remove markdown formatting for plain text
        const plainText = content.replace(/[*_~`#]/g, '');
        navigator.clipboard.writeText(plainText).then(() => {
            showToast('✅ Message copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('❌ Failed to copy message');
        });
    }

    // Regenerate response from agent
    function regenerateResponse(messageId, agent) {
        // Find the previous user message
        const messages = document.querySelectorAll('.message-wrapper');
        let lastUserMessage = null;
        let foundTarget = false;

        for (let i = messages.length - 1; i >= 0; i--) {
            const wrapper = messages[i];
            if (wrapper.dataset.messageId === messageId) {
                foundTarget = true;
            }
            if (foundTarget && wrapper.classList.contains('user')) {
                const content = wrapper.querySelector('.message-content');
                if (content) {
                    lastUserMessage = content.textContent;
                    break;
                }
            }
        }

        if (lastUserMessage) {
            // Remove the old response
            const oldMessage = document.querySelector(`[data-message-id="${messageId}"]`);
            if (oldMessage) {
                oldMessage.remove();
            }

            // Send regenerate command
            vscode.postMessage({
                command: 'regenerate',
                text: lastUserMessage,
                agent: agent || currentAgent,
                mode: 'single'
            });
        }
    }

    // Edit user message
    function editMessage(messageId, originalContent) {
        const messageWrapper = document.querySelector(`[data-message-id="${messageId}"]`);
        if (!messageWrapper) return;

        const messageContent = messageWrapper.querySelector('.message-content');
        if (!messageContent) return;

        // Create edit textarea
        const editArea = document.createElement('textarea');
        editArea.className = 'message-edit-area';
        editArea.value = originalContent;
        editArea.rows = 3;

        // Create button container
        const editButtons = document.createElement('div');
        editButtons.className = 'message-edit-buttons';

        // Save button
        const saveBtn = document.createElement('button');
        saveBtn.className = 'edit-save-btn';
        saveBtn.textContent = 'Save & Send';
        saveBtn.onclick = () => {
            const newContent = editArea.value;
            if (newContent.trim()) {
                // Remove all messages after this one
                const allMessages = Array.from(document.querySelectorAll('.message-wrapper'));
                const currentIndex = allMessages.findIndex(m => m.dataset.messageId === messageId);
                for (let i = currentIndex + 1; i < allMessages.length; i++) {
                    allMessages[i].remove();
                }

                // Update the message content
                messageContent.innerHTML = formatMessageContent(newContent);
                messageWrapper.classList.remove('editing');

                // Send the edited message
                vscode.postMessage({
                    command: 'sendMessage',
                    text: newContent,
                    agent: currentAgent,
                    mode: 'auto'
                });
            }
        };

        // Cancel button
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'edit-cancel-btn';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.onclick = () => {
            messageContent.innerHTML = formatMessageContent(originalContent);
            messageWrapper.classList.remove('editing');
        };

        editButtons.appendChild(saveBtn);
        editButtons.appendChild(cancelBtn);

        // Replace content with edit area
        messageContent.innerHTML = '';
        messageContent.appendChild(editArea);
        messageContent.appendChild(editButtons);
        messageWrapper.classList.add('editing');
        editArea.focus();
    }

    // Export chat to markdown
    function exportChat() {
        const messages = document.querySelectorAll('.message-wrapper');
        let markdown = '# KI AutoAgent Chat Export\n';
        markdown += `Date: ${new Date().toLocaleString()}\n\n`;

        messages.forEach(wrapper => {
            const role = wrapper.classList.contains('user') ? 'User' :
                        wrapper.classList.contains('assistant') ? 'Assistant' : 'System';
            const content = wrapper.querySelector('.message-content')?.textContent || '';
            const agent = wrapper.dataset.agent || '';

            if (content) {
                markdown += `## ${role}${agent ? ` (${agent})` : ''}\n\n`;
                markdown += `${content}\n\n`;
                markdown += '---\n\n';
            }
        });

        vscode.postMessage({
            command: 'exportChat',
            content: markdown
        });
    }

    // Attach file to conversation
    function attachFile() {
        vscode.postMessage({
            command: 'attachFile'
        });
    }

    // Initialize token counter
    function initializeTokenCounter() {
        const tokenDisplay = document.createElement('div');
        tokenDisplay.id = 'token-counter';
        tokenDisplay.className = 'token-counter';
        tokenDisplay.innerHTML = '🤖 Tokens: <span id="token-count">0</span>';

        const header = document.getElementById('chat-header');
        if (header) {
            header.appendChild(tokenDisplay);
        }
    }

    // Update token count
    function updateTokenCount(count) {
        const tokenCount = document.getElementById('token-count');
        if (tokenCount) {
            tokenCount.textContent = count.toLocaleString();
        }
    }

    // Show toast notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    // Initialize on load
    init();
})();