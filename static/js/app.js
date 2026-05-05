// AI Hardware Architect - Frontend Application

const socket = io();
let currentChatId = null;
let isWaitingForResponse = false;
let selectedChats = new Set();

// DOM Elements
const sidebar = document.getElementById('sidebar');
const chatList = document.getElementById('chatList');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const chatTitle = document.getElementById('chatTitle');
const deleteChatBtn = document.getElementById('deleteChatBtn');
const approvalModal = document.getElementById('approvalModal');
const approveBtn = document.getElementById('approveBtn');
const rejectBtn = document.getElementById('rejectBtn');
const bulkActions = document.getElementById('bulkActions');
const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
const selectedCount = document.getElementById('selectedCount');
const themeToggleBtn = document.getElementById('themeToggleBtn');
const agentWorkflow = document.getElementById('agentWorkflow');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const shareBtn = document.getElementById('shareBtn');

let currentBuildData = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadChats();
    createNewChat();
    setupEventListeners();
    setupSocketListeners();
    loadTheme();
});

// Event Listeners
function setupEventListeners() {
    // New chat
    newChatBtn.addEventListener('click', createNewChat);
    
    // Toggle sidebar
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('hidden');
    });
    
    mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('hidden');
    });
    
    // Theme toggle
    themeToggleBtn.addEventListener('click', toggleTheme);
    
    // Message input
    messageInput.addEventListener('input', () => {
        autoResizeTextarea();
        sendBtn.disabled = !messageInput.value.trim() || isWaitingForResponse;
    });
    
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                sendMessage();
            }
        }
    });
    
    // Send button
    sendBtn.addEventListener('click', sendMessage);
    
    // Delete chat
    deleteChatBtn.addEventListener('click', deleteCurrentChat);
    
    // Bulk delete
    bulkDeleteBtn.addEventListener('click', bulkDeleteChats);
    
    // Approval buttons
    approveBtn.addEventListener('click', () => approveBuild());
    rejectBtn.addEventListener('click', () => rejectBuild());
    
    // Export and share buttons
    exportJsonBtn.addEventListener('click', exportBuildJson);
    shareBtn.addEventListener('click', shareBuild);
    
    // Example prompts
    document.querySelectorAll('.example-prompt').forEach(btn => {
        btn.addEventListener('click', () => {
            messageInput.value = btn.dataset.prompt;
            autoResizeTextarea();
            sendBtn.disabled = false;
            messageInput.focus();
        });
    });
}

// Socket Listeners
function setupSocketListeners() {
    socket.on('message', (data) => {
        addMessage(data.role, data.content);
        isWaitingForResponse = false;
        sendBtn.disabled = !messageInput.value.trim();
    });
    
    socket.on('agent_status', (data) => {
        updateThinkingIndicator(data.stage, data.status, data.message, data.data);
    });
    
    socket.on('approval_needed', (data) => {
        currentBuildData = data.build_data;
        showApprovalModal();
    });
    
    socket.on('discord_sent', (data) => {
        if (data.success) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message, 'error');
        }
    });
    
    socket.on('error', (data) => {
        alert('Error: ' + data.error);
        isWaitingForResponse = false;
        sendBtn.disabled = !messageInput.value.trim();
        hideAgentWorkflow();
    });
}

// Theme management
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    } else if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
    } else {
        // Auto-detect
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('dark-mode');
        }
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Create new chat
async function createNewChat() {
    try {
        const response = await fetch('/api/chat/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        currentChatId = data.chat_id;
        
        // Clear messages
        messagesContainer.innerHTML = '';
        welcomeScreen.style.display = 'flex';
        
        // Update title
        chatTitle.textContent = 'New Chat';
        
        // Reload chat list
        loadChats();
        
        // Focus input
        messageInput.focus();
        
    } catch (error) {
        console.error('Error creating new chat:', error);
        alert('Error creating new chat');
    }
}

// Load chats
async function loadChats() {
    try {
        const response = await fetch('/api/chats');
        const data = await response.json();
        
        chatList.innerHTML = '';
        
        data.chats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            if (chat.id === currentChatId) {
                chatItem.classList.add('active');
            }
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'chat-item-checkbox';
            checkbox.checked = selectedChats.has(chat.id);
            checkbox.onclick = (e) => {
                e.stopPropagation();
                toggleChatSelection(chat.id, checkbox.checked);
            };
            
            const titleDiv = document.createElement('div');
            titleDiv.className = 'chat-item-title';
            titleDiv.textContent = chat.title;
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-item-delete';
            deleteBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            `;
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteChat(chat.id);
            };
            
            chatItem.appendChild(checkbox);
            chatItem.appendChild(titleDiv);
            chatItem.appendChild(deleteBtn);
            
            chatItem.addEventListener('click', () => {
                loadChat(chat.id);
            });
            
            chatList.appendChild(chatItem);
        });
        
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

// Toggle chat selection
function toggleChatSelection(chatId, isSelected) {
    if (isSelected) {
        selectedChats.add(chatId);
    } else {
        selectedChats.delete(chatId);
    }
    
    updateBulkActions();
}

// Update bulk actions visibility
function updateBulkActions() {
    if (selectedChats.size > 0) {
        bulkActions.style.display = 'block';
        selectedCount.textContent = selectedChats.size;
    } else {
        bulkActions.style.display = 'none';
    }
}

// Bulk delete chats
async function bulkDeleteChats() {
    if (selectedChats.size === 0) return;
    
    if (!confirm(`Delete ${selectedChats.size} chat(s)?`)) return;
    
    try {
        const deletePromises = Array.from(selectedChats).map(chatId => 
            fetch(`/api/chat/${chatId}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        
        // If current chat was deleted, create new one
        if (selectedChats.has(currentChatId)) {
            createNewChat();
        } else {
            loadChats();
        }
        
        selectedChats.clear();
        updateBulkActions();
        
    } catch (error) {
        console.error('Error deleting chats:', error);
        alert('Error deleting chats');
    }
}

// Load specific chat
async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chat/${chatId}`);
        const data = await response.json();
        
        currentChatId = chatId;
        
        // Clear messages
        messagesContainer.innerHTML = '';
        welcomeScreen.style.display = 'none';
        
        // Load messages
        data.messages.forEach(msg => {
            addMessage(msg.role, msg.content, false);
        });
        
        // Update title
        chatTitle.textContent = data.messages.length > 0 
            ? (data.messages[0].content.substring(0, 40) + (data.messages[0].content.length > 40 ? '...' : ''))
            : 'Chat';
        
        // Reload chat list to update active state
        loadChats();
        
        // Scroll to bottom
        scrollToBottom();
        
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

// Send message
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isWaitingForResponse) return;
    
    // Hide welcome screen
    welcomeScreen.style.display = 'none';
    
    // Add user message
    addMessage('user', message);
    
    // Show thinking indicator immediately
    showThinkingIndicator();
    
    // Send to server
    socket.emit('send_message', {
        chat_id: currentChatId,
        message: message
    });
    
    // Clear input
    messageInput.value = '';
    autoResizeTextarea();
    sendBtn.disabled = true;
    isWaitingForResponse = true;
    
    // Update title if first message
    if (chatTitle.textContent === 'New Chat') {
        chatTitle.textContent = message.substring(0, 40) + (message.length > 40 ? '...' : '');
    }
}

// Add message to UI
function addMessage(role, content, scroll = true) {
    // Remove thinking indicator if exists
    const thinkingIndicator = document.querySelector('.thinking-indicator');
    if (thinkingIndicator) {
        thinkingIndicator.parentElement.parentElement.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🤖';
    
    // Parse markdown
    const htmlContent = marked.parse(content);
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${htmlContent}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    
    if (scroll) {
        scrollToBottom();
    }
}

// Show thinking indicator with agent details
function showThinkingIndicator(stage = 'processing', message = 'Processing...') {
    // Remove existing thinking indicator
    const existing = document.querySelector('.thinking-indicator-container');
    if (existing) {
        existing.remove();
    }
    
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant';
    thinkingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="thinking-indicator-container">
                <div class="agent-workflow-status">
                    <div class="workflow-stage">${message}</div>
                    <div class="thinking-indicator">
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                        <div class="thinking-dot"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(thinkingDiv);
    scrollToBottom();
}

// Update thinking indicator with agent progress
function updateThinkingIndicator(stage, status, message, data = null) {
    const container = document.querySelector('.thinking-indicator-container');
    if (!container) {
        showThinkingIndicator(stage, message);
        return;
    }
    
    const statusDiv = container.querySelector('.agent-workflow-status');
    if (!statusDiv) return;
    
    // Create status icon based on stage and status
    let icon = '⏳';
    if (status === 'completed') icon = '✅';
    else if (status === 'error') icon = '❌';
    else if (status === 'processing') icon = '⚙️';
    else if (status === 'waiting') icon = '⏸️';
    
    // Add stage-specific icons
    const stageIcons = {
        'architect': '🏗️',
        'procurement': '🛒',
        'approval': '👤',
        'discord': '📤',
        'complete': '🎉'
    };
    
    const stageIcon = stageIcons[stage] || '⚙️';
    
    // Build detailed message with data if available
    let detailsHTML = '';
    if (data && status === 'completed') {
        if (stage === 'architect') {
            detailsHTML = `
                <div class="agent-details">
                    <div class="detail-item">💰 Budget: ${data.budget?.toLocaleString() || 'N/A'} MAD</div>
                    <div class="detail-item">🎯 Use Case: ${data.use_case || 'N/A'}</div>
                    <div class="detail-item">⚡ Performance: ${data.performance_level || 'N/A'}</div>
                </div>
            `;
        } else if (stage === 'procurement') {
            const components = data.selected_components || {};
            const componentCount = Object.keys(components).length;
            detailsHTML = `
                <div class="agent-details">
                    <div class="detail-item">🔧 Components: ${componentCount} selected</div>
                    <div class="detail-item">💵 Total: ${data.total_price?.toLocaleString() || 'N/A'} MAD</div>
                    <div class="detail-item">📊 Compatibility: Verified</div>
                </div>
            `;
        }
    }
    
    statusDiv.innerHTML = `
        <div class="workflow-stage-header">
            <span class="stage-icon">${stageIcon}</span>
            <span class="stage-name">${stage.charAt(0).toUpperCase() + stage.slice(1)} Agent</span>
            <span class="status-icon">${icon}</span>
        </div>
        <div class="workflow-message">${message}</div>
        ${detailsHTML}
        ${status === 'processing' ? '<div class="thinking-indicator"><div class="thinking-dot"></div><div class="thinking-dot"></div><div class="thinking-dot"></div></div>' : ''}
    `;
}

// Show approval modal
function showApprovalModal() {
    approvalModal.style.display = 'block';
}

// Hide approval modal
function hideApprovalModal() {
    approvalModal.style.display = 'none';
}

// Approve build
function approveBuild() {
    socket.emit('approve_build', {
        chat_id: currentChatId,
        feedback: '',
        build_data: currentBuildData  // Send the build data for Discord
    });
    hideApprovalModal();
    showThinkingIndicator();
}

// Reject build
function rejectBuild() {
    socket.emit('reject_build', {
        chat_id: currentChatId,
        feedback: ''
    });
    hideApprovalModal();
    showThinkingIndicator();
}

// Delete current chat
async function deleteCurrentChat() {
    if (!currentChatId) return;
    
    if (!confirm('Are you sure you want to delete this chat?')) return;
    
    try {
        const response = await fetch(`/api/chat/${currentChatId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            createNewChat();
        } else {
            alert('Error deleting chat: ' + data.error);
        }
        
    } catch (error) {
        console.error('Error deleting chat:', error);
        alert('Error deleting chat');
    }
}

// Delete specific chat
async function deleteChat(chatId) {
    if (!confirm('Delete this chat?')) return;
    
    try {
        const response = await fetch(`/api/chat/${chatId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (chatId === currentChatId) {
                createNewChat();
            } else {
                loadChats();
            }
        } else {
            alert('Error deleting chat: ' + data.error);
        }
        
    } catch (error) {
        console.error('Error deleting chat:', error);
        alert('Error deleting chat');
    }
}

// Auto-resize textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


// Show approval modal
function showApprovalModal() {
    approvalModal.style.display = 'block';
}

// Hide approval modal
function hideApprovalModal() {
    approvalModal.style.display = 'none';
}

// Export build as JSON
function exportBuildJson() {
    if (!currentBuildData) {
        alert('No build data available');
        return;
    }
    
    const dataStr = JSON.stringify(currentBuildData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pc-build-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    showNotification('📥 Build exported as JSON', 'success');
}

// Share build
function shareBuild() {
    if (!currentBuildData) {
        alert('No build data available');
        return;
    }
    
    const components = currentBuildData.selected_components || {};
    const total = currentBuildData.total_price || 0;
    
    let shareText = `🖥️ My PC Build (${total.toLocaleString()} MAD)\n\n`;
    
    for (const [category, component] of Object.entries(components)) {
        shareText += `${category}: ${component.Brand} ${component.Model}\n`;
    }
    
    shareText += `\nBuilt with AI Hardware Architect`;
    
    if (navigator.share) {
        navigator.share({
            title: 'My PC Build',
            text: shareText
        }).then(() => {
            showNotification('✅ Build shared!', 'success');
        }).catch(err => {
            copyToClipboard(shareText);
        });
    } else {
        copyToClipboard(shareText);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('📋 Build copied to clipboard!', 'success');
    }).catch(err => {
        alert('Failed to copy to clipboard');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 12px 20px;
        background-color: ${type === 'success' ? 'var(--accent-color)' : 'var(--danger-color)'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
