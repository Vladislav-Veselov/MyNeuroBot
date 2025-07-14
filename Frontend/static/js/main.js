document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query-input');
    const loadingIndicator = document.getElementById('loading');

    // Function to add a message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        if (typeof content === 'string') {
            messageDiv.textContent = content;
        } else {
            // For bot messages with structured content
            const answerDiv = document.createElement('div');
            answerDiv.className = 'answer-content';
            answerDiv.textContent = content.answer;
            messageDiv.appendChild(answerDiv);

            if (content.sources && content.sources.length > 0) {
                const sourcesHeader = document.createElement('div');
                sourcesHeader.className = 'sources-header mt-4 text-sm text-gray-600';
                sourcesHeader.textContent = 'Supporting Sources:';
                messageDiv.appendChild(sourcesHeader);

                content.sources.forEach(source => {
                    messageDiv.appendChild(addResultCard(source));
                });
            }
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Function to add a result card
    function addResultCard(result) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        const score = document.createElement('div');
        score.className = 'result-score';
        score.textContent = `Relevance Score: ${(1 - result.score).toFixed(3)}`;
        
        const content = document.createElement('div');
        content.className = 'result-content';
        content.textContent = result.content;
        
        card.appendChild(score);
        card.appendChild(content);
        
        if (result.metadata && Object.keys(result.metadata).length > 0) {
            const metadata = document.createElement('div');
            metadata.className = 'result-metadata';
            metadata.textContent = `Metadata: ${JSON.stringify(result.metadata)}`;
            card.appendChild(metadata);
        }
        
        return card;
    }

    // Handle form submission
    queryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;

        // Add user message
        addMessage(query, true);
        queryInput.value = '';
        
        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });

            const data = await response.json();
            
            if (response.ok) {
                // Add bot message with the generated answer and sources
                addMessage(data);
            } else {
                addMessage(`Error: ${data.error}`, false);
            }
        } catch (error) {
            addMessage('Sorry, there was an error processing your request.', false);
            console.error('Error:', error);
        } finally {
            loadingIndicator.classList.add('hidden');
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    // Focus input on load
    queryInput.focus();
}); 