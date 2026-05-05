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
    
    socket.on('thinking', () => {
        showThinkingIndicator();
    });
    
    socket.on('approval_needed', (data) => {
        showApprovalModal();
    });
    
    socket.on('error', (data) => {
        alert('Error: ' + data.error);
        isWaitingForResponse = false;
        sendBtn.disabled = !messageInput.value.trim();
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

// Show thinking indicator
function showThinkingIndicator() {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant';
    thinkingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="thinking-indicator">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(thinkingDiv);
    scrollToBottom();
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
        feedback: ''
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
