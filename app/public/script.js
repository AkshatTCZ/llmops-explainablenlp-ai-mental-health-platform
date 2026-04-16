// API Configuration
const FASTAPI_BASE_URL = 'http://127.0.0.1:8000';
const PREDICT_ENDPOINT = `${FASTAPI_BASE_URL}/predict`;
const EXPLAIN_ENDPOINT = `${FASTAPI_BASE_URL}/explain`;

// State
// Load sessionId from localStorage or create a new one
let sessionId = localStorage.getItem('chatSessionId') || `session_${Date.now()}`;
if (!localStorage.getItem('chatSessionId')) {
    localStorage.setItem('chatSessionId', sessionId);
}
let isProcessing = false;
let explainRequests = new Set();
let chatHistory = [];
let adviceGiven = false;

const HISTORY_LIMIT = 8;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const typingIndicator = document.getElementById('typingIndicator');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const statusDot = statusIndicator.querySelector('.status-dot');
const emotionDisplay = document.getElementById('emotionDisplay');
const charCount = document.getElementById('charCount');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
    updateCharCount();
    
    // Try to restore previous conversation
    const restored = restoreMessagesFromStorage();
    if (restored) {
        console.log('Previous conversation restored');
    }
});

// Event Listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSend);
    resetBtn.addEventListener('click', handleReset);
    
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    messageInput.addEventListener('input', () => {
        updateCharCount();
        autoResizeTextarea();
    });
}

// Auto-resize textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 120)}px`;
}

// Update character count
function updateCharCount() {
    const count = messageInput.value.length;
    charCount.textContent = `${count} / 1000`;
    
    if (count > 900) {
        charCount.style.color = 'var(--warning)';
    } else if (count > 750) {
        charCount.style.color = 'var(--text-muted)';
    } else {
        charCount.style.color = 'var(--text-muted)';
    }
}

// Handle Send
async function handleSend() {
    const message = messageInput.value.trim();
    
    if (!message || isProcessing) {
        return;
    }
    
    // Track short-term memory separately from the UI so the backend gets recent context.
    appendToChatHistory('user', message);

    // Add user message to chat
    addMessage('user', message);
    
    // Clear input
    messageInput.value = '';
    updateCharCount();
    autoResizeTextarea();
    
    // Disable input
    setProcessing(true);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Create abort controller for timeout (6 minutes)
    const controller = new AbortController();
    let timeoutId = setTimeout(() => controller.abort(), 360000); // 6 minutes
    
    try {
        const response = await fetch(PREDICT_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: message,
                advice_given: adviceGiven,
                history: getRecentHistory()
            }),
            signal: controller.signal
        });
        
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Add assistant response and preserve originating user text for explainability.
        appendToChatHistory('assistant', data.response);
        adviceGiven = true;
        addMessage('assistant', data.response, data.emotion, message);

        // Persist most recent signal for the Book page (single-book UI).
        if (Array.isArray(data.important_words)) {
            localStorage.setItem(`lastImportantWords_${sessionId}`, JSON.stringify(data.important_words));
        }
        if (typeof data.emotion === 'string' && data.emotion.trim()) {
            localStorage.setItem(`lastEmotion_${sessionId}`, data.emotion);
        }
        
        // Update emotion display
        if (data.emotion) {
            updateEmotionDisplay(data.emotion);
        }
        
        updateStatus('ready', 'Ready');
        
    } catch (error) {
        if (timeoutId) {
            clearTimeout(timeoutId);
            timeoutId = null;
        }
        console.error('Error:', error);
        let errorMessage = error.message;
        if (error.name === 'AbortError' || error.message.includes('timeout') || error.message.includes('timed out')) {
            errorMessage = "The response is taking longer than expected (over 6 minutes). This might be because: 1) The model is loading for the first time, 2) Your system is slower, or 3) Ollama is processing other requests. Please wait a moment and try again, or check if Ollama is running properly.";
        }
        addMessage('assistant', `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`, null);
        updateStatus('error', 'Error');
    } finally {
        setProcessing(false);
        hideTypingIndicator();
    }
}

// Handle Reset
async function handleReset() {
    if (!confirm('Are you sure you want to start a new conversation? This will clear your chat history.')) {
        return;
    }
    
    // Clear chat messages
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🌟</div>
            <h2>Welcome to Your Mental Health Support Chat</h2>
            <p>I'm here to listen and support you. Share what's on your mind, and I'll respond with understanding and care.</p>
            <div class="emotion-badges">
                <span class="badge">😊 Joy</span>
                <span class="badge">😢 Sadness</span>
                <span class="badge">😰 Fear</span>
                <span class="badge">😠 Anger</span>
                <span class="badge">😐 Neutral</span>
            </div>
        </div>
    `;
    
    // Clear old session messages from localStorage
    localStorage.removeItem(`chatMessages_${sessionId}`);
    
    // Create new session and store it
    const oldSessionId = sessionId;
    sessionId = `session_${Date.now()}`;
    localStorage.setItem('chatSessionId', sessionId);
    chatHistory = [];
    adviceGiven = false;
    
    emotionDisplay.textContent = '';
    updateStatus('ready', 'Ready');
    
    // No backend reset needed; inference is stateless in FastAPI endpoints.
}

// Save messages to localStorage
function saveMessagesToStorage() {
    const messages = [];
    const messageElements = chatMessages.querySelectorAll('.message');
    
    messageElements.forEach(msg => {
        const role = msg.classList.contains('user') ? 'user' : 'assistant';
        const text = msg.querySelector('.message-text')?.textContent || '';
        const emotionTag = msg.querySelector('.emotion-tag');
        const emotion = emotionTag ? emotionTag.textContent.replace('Detected: ', '') : null;
        const sourceText = msg.dataset.sourceText || null;
        const explanationText = msg.querySelector('.explain-result')?.textContent || null;

        messages.push({ role, text, emotion, sourceText, explanationText });
    });
    
    localStorage.setItem(`chatMessages_${sessionId}`, JSON.stringify(messages));
}

// Restore messages from localStorage
function restoreMessagesFromStorage() {
    const savedMessages = localStorage.getItem(`chatMessages_${sessionId}`);
    
    if (savedMessages) {
        try {
            const messages = JSON.parse(savedMessages);
            
            // Clear welcome message
            const welcomeMessage = chatMessages.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            // Restore all messages
            messages.forEach(msg => {
                addMessageToDOM(msg.role, msg.text, msg.emotion, false, msg.sourceText, msg.explanationText); // false = don't save again
            });

            chatHistory = messages
                .filter(msg => (msg.role === 'user' || msg.role === 'assistant') && typeof msg.text === 'string' && msg.text.trim())
                .map(msg => ({ role: msg.role, content: msg.text }));
            adviceGiven = chatHistory.some(msg => msg.role === 'assistant');

            // Best-effort restore for Book page (may be missing for old sessions).
            // Important words are stored per-session when responses arrive.
            
            scrollToBottom();
            return true;
        } catch (error) {
            console.error('Error restoring messages:', error);
            return false;
        }
    }
    return false;
}

// Add message to DOM (internal function)
function addMessageToDOM(role, text, emotion = null, saveToStorage = true, sourceText = null, explanationText = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    if (sourceText) {
        messageDiv.dataset.messageId = `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        messageDiv.dataset.sourceText = sourceText;
    }
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageHeader = document.createElement('div');
    messageHeader.className = 'message-header';
    
    if (role === 'user') {
        messageHeader.innerHTML = '<span>You</span>';
    } else {
        messageHeader.innerHTML = '<span>AI Assistant</span>';
        if (emotion) {
            const emotionTag = document.createElement('span');
            emotionTag.className = `emotion-tag emotion-${emotion.toLowerCase()}`;
            emotionTag.textContent = `Detected: ${emotion}`;
            messageHeader.appendChild(emotionTag);
        }
    }
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    messageContent.appendChild(messageHeader);
    messageContent.appendChild(messageText);

    if (role === 'assistant' && sourceText) {
        const explainWrap = document.createElement('div');
        explainWrap.className = 'explain-wrap';

        const explainBtn = document.createElement('button');
        explainBtn.className = explanationText ? 'explain-btn explain-btn--done' : 'explain-btn';
        explainBtn.type = 'button';
        explainBtn.textContent = explanationText ? 'Explained' : 'Technical explanation';
        explainBtn.setAttribute('aria-label', 'Show technical explanation for this reply');
        explainBtn.disabled = !!explanationText;
        explainBtn.addEventListener('click', () => handleExplainClick(messageDiv, explainBtn));

        const explainResult = document.createElement('div');
        explainResult.className = 'explain-result';
        if (explanationText) {
            explainResult.textContent = explanationText;
        }

        explainWrap.appendChild(explainBtn);
        explainWrap.appendChild(explainResult);
        messageContent.appendChild(explainWrap);
    }

    messageDiv.appendChild(messageContent);
    
    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    // Save to localStorage if requested
    if (saveToStorage) {
        saveMessagesToStorage();
    }
}

// Add Message to Chat (public function)
function addMessage(role, text, emotion = null, sourceText = null) {
    addMessageToDOM(role, text, emotion, true, sourceText);
}

function appendToChatHistory(role, content) {
    if (!content || (role !== 'user' && role !== 'assistant')) {
        return;
    }

    chatHistory.push({ role, content });
}

function getRecentHistory(limit = HISTORY_LIMIT) {
    return chatHistory.slice(-limit);
}

// Scroll to Bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show/Hide Typing Indicator
function showTypingIndicator() {
    typingIndicator.classList.add('active');
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
}

// Set Processing State
function setProcessing(processing) {
    isProcessing = processing;
    sendBtn.disabled = processing;
    messageInput.disabled = processing;
    
    if (processing) {
        sendBtn.style.opacity = '0.5';
        updateStatus('processing', 'Processing...');
    } else {
        sendBtn.style.opacity = '1';
        messageInput.focus();
    }
}

// Update Status
function updateStatus(type, text) {
    statusText.textContent = text;
    
    // Remove all status classes
    statusDot.classList.remove('ready', 'processing', 'error');
    
    // Add the appropriate class
    statusDot.classList.add(type);
}

// Update Emotion Display
function updateEmotionDisplay(emotion) {
    if (!emotion) {
        emotionDisplay.textContent = '';
        return;
    }
    
    const emotionEmojis = {
        'joy': '😊',
        'sadness': '😢',
        'fear': '😰',
        'anger': '😠',
        'neutral': '😐'
    };
    
    const emoji = emotionEmojis[emotion.toLowerCase()] || '😐';
    emotionDisplay.textContent = `${emoji} ${emotion}`;
    emotionDisplay.className = `emotion-display emotion-${emotion.toLowerCase()}`;
}

// Check Health
async function checkHealth() {
    try {
        const response = await fetch(`${FASTAPI_BASE_URL}/`);
        if (response.ok) {
            updateStatus('ready', 'Ready');
        } else {
            updateStatus('error', 'Server Error');
        }
    } catch (error) {
        updateStatus('error', 'Connection Error');
        console.error('Health check failed:', error);
    }
}

async function handleExplainClick(messageDiv, explainBtn) {
    const sourceText = messageDiv.dataset.sourceText;
    if (!sourceText) {
        return;
    }

    const explainResult = messageDiv.querySelector('.explain-result');
    if (!explainResult || explainResult.textContent.trim()) {
        return; // Explanation already fetched and shown.
    }

    const explainKey = messageDiv.dataset.messageId || `${sessionId}:${sourceText}`;
    if (explainRequests.has(explainKey)) {
        return; // Prevent duplicate in-flight API calls.
    }

    explainRequests.add(explainKey);
    explainBtn.disabled = true;
    explainBtn.textContent = 'Loading…';
    explainBtn.classList.remove('explain-btn--done');

    try {
        const response = await fetch(EXPLAIN_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: sourceText
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        explainResult.textContent = data.explanation || 'No explanation available.';
        explainBtn.textContent = 'Explained';
        explainBtn.disabled = true;
        explainBtn.classList.add('explain-btn--done');
        saveMessagesToStorage();
    } catch (error) {
        console.error('Explain error:', error);
        explainBtn.disabled = false;
        explainBtn.textContent = 'Technical explanation';
        explainResult.textContent = 'Failed to load explanation. Please try again.';
    } finally {
        explainRequests.delete(explainKey);
        scrollToBottom();
    }
}

// Auto-focus input on load
window.addEventListener('load', () => {
    messageInput.focus();
});

