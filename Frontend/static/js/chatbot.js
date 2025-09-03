document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const clearChatButton = document.getElementById('clear-chat');
    const currentKbName = document.getElementById('current-kb-name');
    const currentKbId = document.getElementById('current-kb-id');

    // Load current knowledge base name on page load
    loadCurrentKnowledgeBase();

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    // Handle send button click
    sendButton.addEventListener('click', function() {
        sendMessage();
    });

    // Handle Enter key press
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Handle clear chat button
    clearChatButton.addEventListener('click', function() {
        clearChat();
    });

    // Elements
    const configDarkToggle = document.getElementById('configDarkToggle');
    const configTriangle   = document.getElementById('configTriangle');
    const configPanelDark  = document.getElementById('configPanelDark');

    // Toggle function
    const toggleDarkPanel = () => {
      const isOpen = configPanelDark.classList.toggle('is-open');
      configTriangle.classList.toggle('is-active', isOpen);
      configDarkToggle.setAttribute('aria-expanded', String(isOpen));
      configDarkToggle.title = isOpen ? 'Скрыть панель параметров' : 'Показать панель параметров';
    };

    // Bind once to the button (covers mouse, keyboard, touch)
    configDarkToggle.addEventListener('click', toggleDarkPanel);

    // Function to load current knowledge base name
    async function loadCurrentKnowledgeBase() {
        try {
            currentKbName.textContent = 'Загрузка...';
            currentKbName.classList.add('opacity-50');
            
            const response = await fetch('/api/knowledge-bases');
            const data = await response.json();
            
            if (data.success && data.knowledge_bases && data.current_kb_id) {
                const currentKb = data.knowledge_bases.find(kb => kb.id === data.current_kb_id);
                if (currentKb) {
                    currentKbName.textContent = currentKb.name;
                    currentKbId.textContent = `(ID: ${currentKb.id})`;
                } else {
                    currentKbName.textContent = 'База знаний по умолчанию';
                    currentKbId.textContent = '(ID: default)';
                }
            } else {
                currentKbName.textContent = 'База знаний по умолчанию';
                currentKbId.textContent = '(ID: default)';
            }
            
            currentKbName.classList.remove('opacity-50');
        } catch (error) {
            console.error('Error loading knowledge base info:', error);
            currentKbName.textContent = 'База знаний по умолчанию';
            currentKbId.textContent = '(ID: default)';
            currentKbName.classList.remove('opacity-50');
        }
    }

    // Function to refresh knowledge base name (useful after KB switching)
    function refreshKnowledgeBaseName() {
        loadCurrentKnowledgeBase();
    }

    // Function to handle KB switching responses
    function handleKBSwitchResponse(response) {
        if (response && typeof response === 'string') {
            // Check if this is a KB switch response
            if (response.includes('Переключение на базу знаний') || 
                response.includes('✅') || 
                response.includes('база знаний')) {
                
                // Show a temporary success indicator
                const originalText = currentKbName.textContent;
                currentKbName.textContent = 'Обновление...';
                currentKbName.style.color = '#10B981'; // Green color for success
                
                // Refresh the KB name after a short delay
                setTimeout(() => {
                    refreshKnowledgeBaseName();
                    // Reset color after refresh
                    setTimeout(() => {
                        currentKbName.style.color = '';
                    }, 1000);
                }, 800);
            }
        }
    }

    // Set up periodic refresh of KB name (every 30 seconds)
    setInterval(refreshKnowledgeBaseName, 30000);

    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Disable input and button
        chatInput.disabled = true;
        sendButton.disabled = true;
        sendButton.classList.add('loading');

        // Add user message
        addMessage(message, 'user');

        // Clear input
        chatInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        // Send message to API
        fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        })
        .then(response => {
            if (response.status === 503) {
                // Chatbot is stopped
                return response.json().then(data => {
                    removeTypingIndicator();
                    if (data.chatbot_stopped) {
                        addMessage(data.error || 'Чатбот временно недоступен', 'bot');
                    } else {
                        addMessage('Извините, произошла ошибка: ' + (data.error || 'Неизвестная ошибка'), 'bot');
                    }
                });
            }
            return response.json().then(data => {
                // Remove typing indicator
                removeTypingIndicator();
                
                if (data.success) {
                    // Add bot response
                    addMessage(data.response, 'bot');
                    
                    // Handle KB switching responses
                    handleKBSwitchResponse(data.response);
                } else {
                    // Add error message
                    addMessage('Извините, произошла ошибка: ' + (data.error || 'Неизвестная ошибка'), 'bot');
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('Извините, произошла ошибка при отправке сообщения. Попробуйте еще раз.', 'bot');
        })
        .finally(() => {
            // Re-enable input and button
            chatInput.disabled = false;
            sendButton.disabled = false;
            sendButton.classList.remove('loading');
            chatInput.focus();
        });
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start space-x-3 message-enter ${sender === 'user' ? 'justify-end' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="user-message rounded-lg p-3 max-w-xs lg:max-w-md">
                    <p class="text-white">${escapeHtml(text)}</p>
                    <span class="text-xs text-white opacity-70 mt-1 block">${timestamp}</span>
                </div>
                <div class="w-8 h-8 bg-[#DC4918] rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-[#DC4918] rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                    </svg>
                </div>
                <div class="bot-message rounded-lg p-3 max-w-xs lg:max-w-md">
                    <p class="text-white">${escapeHtml(text)}</p>
                    <span class="text-xs text-[#718096] mt-1 block">${timestamp}</span>
                </div>
            `;
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-3';
        typingDiv.innerHTML = `
            <div class="w-8 h-8 bg-[#DC4918] rounded-full flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
            </div>
            <div class="bg-[#1E2328] rounded-lg p-3 border border-[#2D3446]">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function clearChat() {
        // Clear messages from UI
        chatMessages.innerHTML = `
            <!-- Welcome Message -->
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 bg-[#DC4918] rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                    </svg>
                </div>
                <div class="bot-message rounded-lg p-3 max-w-xs lg:max-w-md">
                    <p class="text-white">Привет! Я NeuroBot Assistant. Чем могу помочь?</p>
                    <span class="text-xs text-[#718096] mt-1 block">Сейчас</span>
                </div>
            </div>
        `;
        
        // Clear conversation history on server
        fetch('/api/chatbot/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Chat history cleared');
                refreshKnowledgeBaseName(); // Refresh KB name after clearing chat
            } else {
                console.error('Error clearing chat history:', data.error);
            }
        })
        .catch(error => {
            console.error('Error clearing chat history:', error);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Focus input on page load
    chatInput.focus();
}); 