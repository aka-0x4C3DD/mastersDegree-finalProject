// ClinicalGPT Medical Assistant - Client-side JavaScript

// Global variables
const API_URL = window.location.origin;
let chatHistory = [];
let currentChatId = generateChatId();

// Include Marked.js library for Markdown parsing
const markedScript = document.createElement('script');
markedScript.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
document.head.appendChild(markedScript);

// Initialize marked options once the script is loaded
markedScript.onload = function() {
    marked.setOptions({
        breaks: true,        // Convert \n to <br>
        sanitize: false,     // Allow HTML in the markdown
        mangle: false,       // Don't mangle email addresses
        headerIds: false     // Don't add ids to headers
    });
};

// DOM Elements
const serverStatusEl = document.getElementById('server-status');
const userInputEl = document.getElementById('user-input');
const webSearchCheckEl = document.getElementById('web-search-check');
const sendMessageBtn = document.getElementById('send-message-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const clearChatBtn = document.getElementById('clear-chat-btn');
const saveChatBtn = document.getElementById('save-chat-btn');
const uploadFileBtn = document.getElementById('upload-file-btn');
const fileUploadEl = document.getElementById('file-upload');
const uploadFileSubmitBtn = document.getElementById('upload-file-submit');
const chatMessagesEl = document.getElementById('chat-messages');
const historyListEl = document.getElementById('history-list');
const noHistoryMessageEl = document.getElementById('no-history-message');
const statusMessageEl = document.getElementById('status-message');
const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
const clearHistoryBtn = document.getElementById('clear-history-btn');
const sidebarEl = document.querySelector('.sidebar');

// Medical terms for highlighting
const medicalTerms = [
    'diabetes', 'hypertension', 'cancer', 'cardiovascular', 'asthma', 
    'arthritis', 'alzheimer', 'parkinson', 'obesity', 'depression',
    'anxiety', 'schizophrenia', 'bipolar', 'adhd', 'autism',
    'influenza', 'pneumonia', 'covid', 'vaccination', 'immunization',
    'medication', 'prescription', 'diagnosis', 'prognosis', 'symptom',
    'treatment', 'therapy', 'surgery', 'chronic', 'acute'
];

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    checkServerStatus();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load history from local storage
    loadChatHistory();
    
    // Auto-resize text area
    autoResizeTextarea(userInputEl);

    // Setup sample query click handlers
    setupSampleQueries();
});

// Setup all event listeners
function setupEventListeners() {
    // Main chat interactions
    sendMessageBtn.addEventListener('click', handleSendMessage);
    userInputEl.addEventListener('keydown', handleEnterKey);
    
    // Chat management
    newChatBtn.addEventListener('click', startNewChat);
    clearChatBtn.addEventListener('click', clearCurrentChat);
    saveChatBtn.addEventListener('click', saveChat);
    
    // File upload
    uploadFileBtn.addEventListener('click', openFileUploadModal);
    uploadFileSubmitBtn.addEventListener('click', handleFileUpload);
    
    // Mobile responsiveness
    toggleSidebarBtn.addEventListener('click', toggleSidebar);
    
    // History management
    clearHistoryBtn.addEventListener('click', clearAllHistory);
}

// Auto-resize textarea as user types
function autoResizeTextarea(textarea) {
    textarea.addEventListener('input', function() {
        // Reset height to auto to get the correct scrollHeight
        this.style.height = 'auto';
        // Set new height based on scrollHeight
        this.style.height = (this.scrollHeight) + 'px';
    });
}

// Handle Enter key in textarea
function handleEnterKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
}

// Setup sample queries click handlers
function setupSampleQueries() {
    const sampleQueries = document.querySelectorAll('.sample-query');
    sampleQueries.forEach(query => {
        query.addEventListener('click', () => {
            const queryText = query.getAttribute('data-query');
            userInputEl.value = queryText;
            autoResizeTextarea(userInputEl);
            // Focus and scroll to input
            userInputEl.focus();
        });
    });
}

// Generate a unique ID for each chat
function generateChatId() {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
}

// Start a new chat
function startNewChat() {
    currentChatId = generateChatId();
    clearMessages();
    userInputEl.value = '';
    userInputEl.focus();
    
    // Show welcome message
    showWelcomeMessage();
    
    updateStatusMessage('Started new chat');
}

// Clear current chat
function clearCurrentChat() {
    if (confirm('Are you sure you want to clear the current chat?')) {
        clearMessages();
        showWelcomeMessage();
        updateStatusMessage('Chat cleared');
    }
}

// Clear all history
function clearAllHistory() {
    if (confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
        chatHistory = [];
        localStorage.removeItem('clinicalGptChatHistory');
        updateHistoryUI();
        updateStatusMessage('All history cleared');
    }
}

// Toggle sidebar for mobile view
function toggleSidebar() {
    sidebarEl.classList.toggle('show');
}

// Show welcome message
function showWelcomeMessage() {
    // The welcome message is already in the HTML
    // We just need to make sure it's visible
    const welcomeMessage = document.querySelector('.system-message');
    if (!welcomeMessage) {
        // If it's not in the DOM for some reason, add it back
        const welcomeHtml = `
            <div class="message-container system-message">
                <div class="message-content">
                    <div class="message-header">
                        <div class="message-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-sender">ClinicalGPT</div>
                    </div>
                    <div class="message-body">
                        <p>Hello! I'm ClinicalGPT, your medical assistant. You can ask me questions about medical conditions, symptoms, treatments, or upload medical files for analysis.</p>
                        <div class="sample-queries">
                            <p class="fw-bold mb-2">Try asking me:</p>
                            <div class="sample-query" data-query="What are the symptoms of type 2 diabetes?">
                                <i class="fas fa-comment-medical me-2"></i>What are the symptoms of type 2 diabetes?
                            </div>
                            <div class="sample-query" data-query="How is hypertension diagnosed?">
                                <i class="fas fa-comment-medical me-2"></i>How is hypertension diagnosed?
                            </div>
                            <div class="sample-query" data-query="What are the latest treatments for COVID-19?">
                                <i class="fas fa-comment-medical me-2"></i>What are the latest treatments for COVID-19?
                            </div>
                            <div class="sample-query" data-query="Can you explain the differences between Type 1 and Type 2 diabetes?">
                                <i class="fas fa-comment-medical me-2"></i>Can you explain the differences between Type 1 and Type 2 diabetes?
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        chatMessagesEl.innerHTML = welcomeHtml;
        setupSampleQueries();
    }
}

// Check server connection status
function checkServerStatus() {
    updateStatusMessage('Checking server connection...');
    
    fetch(`${API_URL}/api/health`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Server connection failed');
        })
        .then(data => {
            serverStatusEl.innerHTML = '<i class="fas fa-circle text-success me-1"></i> Server Connected';
            updateStatusMessage('Connected to server');
        })
        .catch(error => {
            console.error('Server status check failed:', error);
            serverStatusEl.innerHTML = '<i class="fas fa-circle text-danger me-1"></i> Server Disconnected';
            updateStatusMessage('Error: Could not connect to server', true);
        });
}

// Send a message to the API
function handleSendMessage() {
    const message = userInputEl.value.trim();
    if (!message) {
        return;
    }
    
    // Add user message to the chat
    addMessage('user', message);
    
    // Clear input and reset height
    userInputEl.value = '';
    userInputEl.style.height = 'auto';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to API
    const requestData = {
        query: message,
        search_web: webSearchCheckEl.checked
    };
    
    updateStatusMessage('Processing query...');
    
    fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Remove typing indicator
        removeTypingIndicator();
        
        // Process and display response
        processResponse(data, message);
        
        // Save to chat history
        saveChatToHistory();
        
        updateStatusMessage('Ready');
    })
    .catch(error => {
        // Remove typing indicator
        removeTypingIndicator();
        
        // Show error message
        addErrorMessage(`Error: ${error.message}`);
        updateStatusMessage('Error occurred', true);
    });
}

// Show typing indicator
function showTypingIndicator() {
    const typingHtml = `
        <div class="message-container ai-message" id="typing-indicator">
            <div class="message-content">
                <div class="message-header">
                    <div class="message-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-sender">ClinicalGPT</div>
                </div>
                <div class="message-body">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        </div>
    `;
    chatMessagesEl.insertAdjacentHTML('beforeend', typingHtml);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Add a message to the chat
function addMessage(type, content, timestamp = new Date()) {
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message-container ${type}-message`;
    
    // Format timestamp
    const formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Set different icon and styling based on message type
    let iconClass, senderName;
    if (type === 'user') {
        iconClass = 'fas fa-user';
        senderName = 'You';
    } else if (type === 'ai') {
        iconClass = 'fas fa-robot';
        senderName = 'ClinicalGPT';
    } else {
        iconClass = 'fas fa-info-circle';
        senderName = 'System';
    }
    
    // If first message in a new chat, clear welcome message
    if (chatMessagesEl.querySelectorAll('.message-container').length === 1 && 
        chatMessagesEl.querySelector('.system-message')) {
        chatMessagesEl.innerHTML = '';
    }
    
    // Create message HTML
    let messageContent = content;
    
    // If it's AI message, process/format the content
    if (type === 'ai' && typeof content === 'object') {
        messageContent = formatAIResponse(content);
    }
    
    messageEl.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <div class="message-icon">
                    <i class="${iconClass}"></i>
                </div>
                <div class="message-sender">${senderName}</div>
                <div class="message-timestamp">${formattedTime}</div>
            </div>
            <div class="message-body">
                ${type === 'user' ? `<p>${escapeHtml(messageContent)}</p>` : messageContent}
            </div>
        </div>
    `;
    
    // Add to chat
    chatMessagesEl.appendChild(messageEl);
    scrollToBottom();
}

// Process API response and add to chat
function processResponse(data, originalQuery) {
    removeTypingIndicator();
    
    if (data.error) {
        addErrorMessage(data.error);
        updateStatusMessage('Error in response', true);
        return;
    }
    
    // Format and add the AI's response
    const responseHtml = formatAIResponse(data);
    addMessage('ai', responseHtml);
    
    // Save this conversation to history if it's not already there
    const currentChatExists = chatHistory.some(chat => chat.id === currentChatId);
    if (!currentChatExists) {
        saveChatToHistory();
    }
    
    updateStatusMessage('Response received');
    scrollToBottom();
}

// Format AI response
function formatAIResponse(data) {
    let html = '';
    
    // Handle any error responses
    if (data.error) {
        return `<div class="error-message">${data.error}</div>`;
    }
    
    // Add model information
    html += `<div class="model-info">Generated by <span class="model-name">${data.model_name || 'ClinicalGPT'}</span> on ${data.device_used || 'device'}</div>`;
    
    // Process the response text with markdown
    const responseHtml = typeof marked !== 'undefined' ? 
        marked.parse(data.response) : 
        data.response;
    
    // Add the markdown-rendered response
    html += `<div class="markdown-content">${responseHtml}</div>`;
    
    // Add web search results if available
    if (data.web_results && data.web_results.length > 0) {
        html += '<div class="web-results">';
        html += '<h4>Sources:</h4>';
        html += '<ul>';
        
        data.web_results.forEach(result => {
            const title = result.title || 'Medical Source';
            html += `<li><a href="${result.source}" target="_blank" rel="noopener noreferrer">${title}</a></li>`;
        });
        
        html += '</ul></div>';
    }
    
    return html;
}

// Highlight medical terms in text
function highlightMedicalTerms(text) {
    if (!text) return '';
    
    // Create a regex pattern for all medical terms
    const medicalTermPattern = new RegExp('\\b(' + medicalTerms.join('|') + ')\\b', 'gi');
    
    // Replace medical terms with highlighted version
    return text.replace(medicalTermPattern, '<span class="medical-term">$1</span>');
}

// Add error message to chat
function addErrorMessage(message) {
    const errorHtml = `<div class="error-message">${message}</div>`;
    addMessage('ai', errorHtml);
}

// Clear all messages
function clearMessages() {
    chatMessagesEl.innerHTML = '';
}

// Scroll chat to bottom
function scrollToBottom() {
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

// Update status message
function updateStatusMessage(message, isError = false) {
    statusMessageEl.textContent = message;
    if (isError) {
        statusMessageEl.classList.add('text-danger');
    } else {
        statusMessageEl.classList.remove('text-danger');
    }
}

// Save current chat to history
function saveChatToHistory() {
    const messages = chatMessagesEl.querySelectorAll('.message-container:not(.system-message)');
    if (messages.length === 0) return;
    
    // Get first user message as title
    const firstUserMessage = Array.from(messages).find(el => el.classList.contains('user-message'));
    let chatTitle = 'Untitled Chat';
    
    if (firstUserMessage) {
        const messageText = firstUserMessage.querySelector('.message-body').textContent.trim();
        chatTitle = messageText.substring(0, 30) + (messageText.length > 30 ? '...' : '');
    }
    
    // Create chat object
    const chat = {
        id: currentChatId,
        title: chatTitle,
        timestamp: new Date().toISOString(),
        messages: Array.from(messages).map(el => {
            return {
                type: el.classList.contains('user-message') ? 'user' : 'ai',
                content: el.querySelector('.message-body').innerHTML,
                timestamp: el.querySelector('.message-timestamp').textContent
            };
        })
    };
    
    // Check if this chat already exists in history
    const existingChatIndex = chatHistory.findIndex(item => item.id === currentChatId);
    if (existingChatIndex !== -1) {
        // Update existing chat
        chatHistory[existingChatIndex] = chat;
    } else {
        // Add new chat to history
        chatHistory.unshift(chat);
        
        // Limit history to 20 items
        if (chatHistory.length > 20) {
            chatHistory.pop();
        }
    }
    
    // Save to local storage
    localStorage.setItem('clinicalGptChatHistory', JSON.stringify(chatHistory));
    
    // Update history UI
    updateHistoryUI();
}

// Load chat history from local storage
function loadChatHistory() {
    const savedHistory = localStorage.getItem('clinicalGptChatHistory');
    if (savedHistory) {
        try {
            chatHistory = JSON.parse(savedHistory);
            updateHistoryUI();
        } catch (e) {
            console.error('Error parsing chat history:', e);
        }
    }
}

// Update the history list in the UI
function updateHistoryUI() {
    // Clear existing history items
    const historyItems = historyListEl.querySelectorAll('.history-item');
    historyItems.forEach(item => item.remove());
    
    // Show/hide no history message
    if (chatHistory.length === 0) {
        noHistoryMessageEl.classList.remove('d-none');
    } else {
        noHistoryMessageEl.classList.add('d-none');
        
        // Add history items
        chatHistory.forEach(chat => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            if (chat.id === currentChatId) {
                historyItem.classList.add('active');
            }
            
            // Format the date
            const date = new Date(chat.timestamp);
            const formattedDate = date.toLocaleDateString();
            
            historyItem.innerHTML = `
                <i class="fas fa-comment-medical"></i>
                <div class="history-item-content">
                    <div class="history-item-title">${escapeHtml(chat.title)}</div>
                    <div class="history-item-date">${formattedDate}</div>
                </div>
            `;
            
            // Add click listener
            historyItem.addEventListener('click', () => {
                loadChat(chat.id);
            });
            
            historyListEl.appendChild(historyItem);
        });
    }
}

// Load a chat from history
function loadChat(chatId) {
    const chat = chatHistory.find(item => item.id === chatId);
    if (!chat) return;
    
    // Update current chat ID
    currentChatId = chatId;
    
    // Clear current messages
    clearMessages();
    
    // Add messages from history
    chat.messages.forEach(msg => {
        const messageEl = document.createElement('div');
        messageEl.className = `message-container ${msg.type}-message`;
        
        messageEl.innerHTML = `
            <div class="message-content">
                <div class="message-header">
                    <div class="message-icon">
                        <i class="${msg.type === 'user' ? 'fas fa-user' : 'fas fa-robot'}"></i>
                    </div>
                    <div class="message-sender">${msg.type === 'user' ? 'You' : 'ClinicalGPT'}</div>
                    <div class="message-timestamp">${msg.timestamp || ''}</div>
                </div>
                <div class="message-body">
                    ${msg.content}
                </div>
            </div>
        `;
        
        chatMessagesEl.appendChild(messageEl);
    });
    
    // Update UI
    scrollToBottom();
    updateStatusMessage(`Loaded chat: ${chat.title}`);
    updateHistoryUI();
    
    // Close sidebar on mobile
    if (window.innerWidth < 768) {
        sidebarEl.classList.remove('show');
    }
}

// Open file upload modal
function openFileUploadModal() {
    const fileModal = new bootstrap.Modal(document.getElementById('fileUploadModal'));
    fileModal.show();
}

// Handle file upload
function handleFileUpload() {
    const file = fileUploadEl.files[0];
    if (!file) {
        alert('Please select a file first');
        return;
    }
    
    // Hide modal
    const fileModal = bootstrap.Modal.getInstance(document.getElementById('fileUploadModal'));
    fileModal.hide();
    
    // Add message about file upload
    addMessage('user', `Uploading file: ${file.name}`);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Upload file
    const formData = new FormData();
    formData.append('file', file);
    
    updateStatusMessage('Uploading and processing file...');
    
    fetch(`${API_URL}/api/process-file`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add file name to the data
        data.file_name = file.name;
        
        // Process and display response
        addMessage('ai', data);
        
        // Save to chat history
        saveChatToHistory();
        
        // Clear file input
        fileUploadEl.value = '';
        
        updateStatusMessage('File processed successfully');
    })
    .catch(error => {
        // Remove typing indicator
        removeTypingIndicator();
        
        // Show error message
        addErrorMessage(`Error processing file: ${error.message}`);
        
        // Clear file input
        fileUploadEl.value = '';
        
        updateStatusMessage('Error processing file', true);
    });
}

// Save chat to a text file
function saveChat() {
    const messages = chatMessagesEl.querySelectorAll('.message-container');
    if (messages.length === 0) {
        alert('No messages to save');
        return;
    }
    
    let chatText = 'ClinicalGPT Chat Transcript\n';
    chatText += '========================\n\n';
    
    messages.forEach(msg => {
        const isUser = msg.classList.contains('user-message');
        const sender = isUser ? 'You' : 'ClinicalGPT';
        const timestamp = msg.querySelector('.message-timestamp')?.textContent || '';
        const content = msg.querySelector('.message-body').textContent.trim();
        
        chatText += `[${timestamp}] ${sender}:\n${content}\n\n`;
    });
    
    // Create and download the file
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clinicalgpt-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    updateStatusMessage('Chat saved to file');
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}