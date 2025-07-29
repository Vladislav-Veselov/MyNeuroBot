document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settings-form');
    const messageDiv = document.getElementById('message');
    const messageContent = document.getElementById('message-content');
    const kbSelector = document.getElementById('settings-kb-selector');
    const kbDetailsBtn = document.getElementById('settings-kb-details-btn');
    const kbDetailsModal = document.getElementById('settings-kb-details-modal');
    const closeKbDetailsModal = document.getElementById('close-settings-kb-details-modal');
    const closeKbDetails = document.getElementById('close-settings-kb-details');

    let currentKbId = null;
    let knowledgeBases = [];

    // Initialize settings page
    initSettingsPage();

    function initSettingsPage() {
        // Set initial state
        kbSelector.innerHTML = '<option value="">Загрузка...</option>';
        
        loadKnowledgeBases();
        setupEventListeners();
    }

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const settings = {
            tone: parseInt(formData.get('tone')),
            humor: parseInt(formData.get('humor')),
            brevity: parseInt(formData.get('brevity')),
            additional_prompt: formData.get('additional_prompt')
        };

        // Validate tone selection
        if (settings.tone === null || settings.tone === undefined || isNaN(settings.tone)) {
            showMessage('Пожалуйста, выберите тон общения', 'error');
            return;
        }

        // Save settings for specific KB
        if (!currentKbId) {
            showMessage('Пожалуйста, выберите базу знаний.', 'error');
            return;
        }

        fetch(`/api/save_settings/${currentKbId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Настройки успешно сохранены!', 'success');
            } else {
                showMessage(data.error || 'Ошибка при сохранении настроек', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Ошибка при сохранении настроек', 'error');
        });
    });

    function loadKnowledgeBases() {
        fetch('/api/knowledge-bases')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                knowledgeBases = data.knowledge_bases || []; // Ensure it's an array
                updateKbSelector();
                
                // Load settings for the first KB or current KB
                if (knowledgeBases.length > 0) {
                    currentKbId = knowledgeBases[0].id;
                    loadSettingsForKb(currentKbId);
                } else {
                    // No KBs available
                    kbSelector.innerHTML = '<option value="">Нет баз знаний</option>';
                }
            } else {
                console.error('Failed to load knowledge bases:', data.error);
                // Show error in selector
                kbSelector.innerHTML = '<option value="">Ошибка загрузки</option>';
            }
        })
        .catch(error => {
            console.error('Error loading knowledge bases:', error);
            // Show error in selector
            kbSelector.innerHTML = '<option value="">Ошибка загрузки</option>';
        });
    }

    function updateKbSelector() {
        kbSelector.innerHTML = '';
        
        if (knowledgeBases.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Нет баз знаний';
            kbSelector.appendChild(option);
            return;
        }

        knowledgeBases.forEach(kb => {
            const option = document.createElement('option');
            option.value = kb.id;
            option.textContent = kb.name;
            if (kb.id === currentKbId) {
                option.selected = true;
            }
            kbSelector.appendChild(option);
        });
    }

    function setupEventListeners() {
        // KB Selector change
        kbSelector.addEventListener('change', (e) => {
            const selectedKbId = e.target.value;
            if (selectedKbId && selectedKbId !== currentKbId) {
                currentKbId = selectedKbId;
                loadSettingsForKb(currentKbId);
            }
        });

        // KB Details button
        kbDetailsBtn.addEventListener('click', () => {
            showKbDetailsModal();
        });

        // Close KB details modal
        closeKbDetailsModal.addEventListener('click', () => {
            hideKbDetailsModal();
        });

        closeKbDetails.addEventListener('click', () => {
            hideKbDetailsModal();
        });

        // Close modal when clicking outside
        kbDetailsModal.addEventListener('click', (e) => {
            if (e.target === kbDetailsModal) {
                hideKbDetailsModal();
            }
        });
    }

    function loadSettingsForKb(kbId) {
        if (!kbId) return;
        
        fetch(`/api/get_settings/${kbId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const settings = data.settings;
                
                // Set tone (now numeric 0-4)
                document.querySelector('input[name="tone"]').value = settings.tone !== undefined ? settings.tone : 2;

                // Set humor level
                document.querySelector('input[name="humor"]').value = settings.humor !== undefined ? settings.humor : 2;

                // Set brevity level
                document.querySelector('input[name="brevity"]').value = settings.brevity !== undefined ? settings.brevity : 2;

                // Set additional prompt
                document.getElementById('additional-prompt').value = settings.additional_prompt || '';
            }
        })
        .catch(error => {
            console.error('Error loading settings for KB:', error);
        });
    }

    function showKbDetailsModal() {
        if (!currentKbId) {
            showMessage('Сначала выберите базу знаний.', 'error');
            return;
        }
        
        loadKbDetails();
        kbDetailsModal.classList.remove('hidden');
        kbDetailsModal.classList.add('flex');
    }

    function hideKbDetailsModal() {
        kbDetailsModal.classList.add('hidden');
        kbDetailsModal.classList.remove('flex');
    }

    async function loadKbDetails() {
        try {
            const response = await fetch(`/api/knowledge-bases/${currentKbId}`);
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('settings-kb-details-name').textContent = data.name;
                document.getElementById('settings-kb-details-id').textContent = data.kb_id;
                document.getElementById('settings-kb-details-created').textContent = new Date(data.created_at).toLocaleString('ru-RU');
                document.getElementById('settings-kb-details-docs').textContent = data.document_count;
                
                // Display the actual password
                const passwordElement = document.getElementById('settings-kb-details-password');
                if (data.password) {
                    passwordElement.textContent = data.password;
                    passwordElement.className = 'text-white font-mono';
                } else {
                    passwordElement.textContent = 'Не установлен';
                    passwordElement.className = 'text-[#718096] italic';
                }
                
                // Display analyze_clients setting
                const analyzeClientsElement = document.getElementById('settings-kb-details-analyze-clients');
                if (data.analyze_clients !== undefined) {
                    analyzeClientsElement.textContent = data.analyze_clients ? 'Включен' : 'Отключен';
                    analyzeClientsElement.className = data.analyze_clients ? 'text-green-400' : 'text-red-400';
                } else {
                    analyzeClientsElement.textContent = 'Включен (по умолчанию)';
                    analyzeClientsElement.className = 'text-green-400';
                }
            } else {
                showMessage('Ошибка при загрузке деталей базы знаний.', 'error');
            }
        } catch (error) {
            console.error('Error loading KB details:', error);
            showMessage('Ошибка при загрузке деталей базы знаний.', 'error');
        }
    }

    function showMessage(text, type) {
        messageContent.textContent = text;
        messageDiv.className = `mt-4 p-4 rounded-lg ${type === 'success' ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`;
        messageDiv.classList.remove('hidden');
        
        // Hide message after 5 seconds
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }
}); 