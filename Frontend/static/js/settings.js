document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('settings-form');
    const messageDiv = document.getElementById('message');
    const messageContent = document.getElementById('message-content');
    const kbSelector = document.getElementById('settings-kb-selector');
    const kbDetailsBtn = document.getElementById('settings-kb-details-btn');
    const kbDetailsModal = document.getElementById('settings-kb-details-modal');
    const closeKbDetailsModal = document.getElementById('close-settings-kb-details-modal');
    const closeKbDetails = document.getElementById('close-settings-kb-details');
    const stopChatbotBtn = document.getElementById('stop-chatbot-btn');
    const startChatbotBtn = document.getElementById('start-chatbot-btn');
    const chatbotStatus = document.getElementById('chatbot-status');
    const chatbotStatusDetails = document.getElementById('chatbot-status-details');
    const chatbotStopTime = document.getElementById('chatbot-stop-time');
    const chatbotStopMessage = document.getElementById('chatbot-stop-message');
    const currentModel = document.getElementById('current-model');
    const modelSelector = document.getElementById('model-selector');
    const saveModelBtn = document.getElementById('save-model-btn');
    const deleteSettingsKbBtn = document.getElementById('delete-settings-kb-btn');

    let currentKbId = null;
    let knowledgeBases = [];
    let modelConfig = null;

    // Initialize settings page
    initSettingsPage();

    function initSettingsPage() {
        // Set initial state
        kbSelector.innerHTML = '<option value="">Загрузка...</option>';
        
        loadKnowledgeBases();
        loadChatbotStatus();
        loadModelConfig();
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
                // Set currentKbId to the actual current KB from backend session
                if (data.current_kb_id) {
                    currentKbId = data.current_kb_id;
                } else if (knowledgeBases.length > 0) {
                    currentKbId = knowledgeBases[0].id;
                }

                updateKbSelector();

                // Load settings for the current KB
                if (currentKbId) {
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
            option.style.backgroundColor = '#242A36';
            option.style.color = 'white';
            kbSelector.appendChild(option);
            return;
        }

        knowledgeBases.forEach(kb => {
            const option = document.createElement('option');
            option.value = kb.id;
            option.textContent = kb.name;
            option.style.backgroundColor = '#242A36';
            option.style.color = 'white';
            if (kb.id === currentKbId) {
                option.selected = true;
            }
            kbSelector.appendChild(option);
        });
    }

    function setupEventListeners() {
        // KB Selector change
        kbSelector.addEventListener('change', async (e) => {
            const selectedKbId = e.target.value;
            if (selectedKbId && selectedKbId !== currentKbId) {
                await switchToKb(selectedKbId);
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

        // Chatbot control buttons
        stopChatbotBtn.addEventListener('click', stopChatbot);
        startChatbotBtn.addEventListener('click', startChatbot);

        // Model selection
        saveModelBtn.addEventListener('click', saveModel);

        // KB delete button - use event delegation since button is in modal
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'delete-settings-kb-btn') {
                e.preventDefault();
                e.stopPropagation();
                deleteCurrentKb();
            }
        });
    }

    function loadChatbotStatus() {
        fetch('/api/chatbot/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateChatbotStatusDisplay(data.status);
            } else {
                console.error('Failed to load chatbot status:', data.error);
                chatbotStatus.textContent = 'Ошибка загрузки статуса';
            }
        })
        .catch(error => {
            console.error('Error loading chatbot status:', error);
            chatbotStatus.textContent = 'Ошибка загрузки статуса';
        });
    }

    function updateChatbotStatusDisplay(status) {
        if (status.stopped) {
            chatbotStatus.textContent = 'Остановлен';
            chatbotStatus.className = 'text-red-400 font-medium';
            stopChatbotBtn.classList.add('hidden');
            
            // Check if stopped by admin
            if (status.stopped_by === 'admin') {
                startChatbotBtn.classList.add('hidden');
                chatbotStatus.textContent = 'Остановлен админом';
                chatbotStatus.className = 'text-red-500 font-medium';
            } else {
                startChatbotBtn.classList.remove('hidden');
            }
            
            // Show stop details
            chatbotStatusDetails.classList.remove('hidden');
            if (status.stopped_at) {
                const stopDate = new Date(status.stopped_at);
                chatbotStopTime.textContent = `Остановлен: ${stopDate.toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' })}`;
            }
            if (status.message) {
                chatbotStopMessage.textContent = `Сообщение: ${status.message}`;
            }
        } else {
            chatbotStatus.textContent = 'Работает';
            chatbotStatus.className = 'text-green-400 font-medium';
            stopChatbotBtn.classList.remove('hidden');
            startChatbotBtn.classList.add('hidden');
            chatbotStatusDetails.classList.add('hidden');
        }
    }

    function stopChatbot() {
        if (!confirm('Вы уверены, что хотите остановить чатбот? Все чатботы для вашего аккаунта будут недоступны.')) {
            return;
        }

        const message = prompt('Введите сообщение для пользователей (необязательно):', 'Чатбот временно остановлен');
        
        fetch('/api/chatbot/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message || 'Чатбот временно остановлен'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Чатботы успешно остановлены', 'success');
                loadChatbotStatus(); // Reload status
            } else {
                showMessage(data.error || 'Ошибка при остановке чатботов', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Ошибка при остановке чатботов', 'error');
        });
    }

    function startChatbot() {
        fetch('/api/chatbot/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Чатботы успешно запущены', 'success');
                loadChatbotStatus(); // Reload status
            } else {
                // Check if bots were stopped by admin
                if (data.admin_stopped) {
                    showMessage('Все ваши боты приостановлены админом', 'error');
                } else {
                    showMessage(data.error || 'Ошибка при запуске чатботов', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Ошибка при запуске чатботов', 'error');
        });
    }

    function loadModelConfig() {
        fetch('/api/model/config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modelConfig = data.config;
                updateModelDisplay();
            } else {
                console.error('Failed to load model config:', data.error);
                currentModel.textContent = 'Ошибка загрузки';
            }
        })
        .catch(error => {
            console.error('Error loading model config:', error);
            currentModel.textContent = 'Ошибка загрузки';
        });
    }

    function updateModelDisplay() {
        if (!modelConfig) return;

        // Update current model display
        currentModel.textContent = modelConfig.current_model_name;

        // Update model selector
        modelSelector.innerHTML = '';
        Object.entries(modelConfig.available_models).forEach(([modelId, modelName]) => {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = modelName;
            option.style.backgroundColor = '#242A36';
            option.style.color = 'white';
            if (modelId === modelConfig.model) {
                option.selected = true;
            }
            modelSelector.appendChild(option);
        });
    }

    function saveModel() {
        const selectedModel = modelSelector.value;
        if (!selectedModel) {
            showMessage('Пожалуйста, выберите модель', 'error');
            return;
        }

        fetch('/api/model/set', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: selectedModel
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                modelConfig = data.config;
                updateModelDisplay();
            } else {
                showMessage(data.error || 'Ошибка при изменении модели', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Ошибка при изменении модели', 'error');
        });
    }

    function deleteCurrentKb() {
        if (!currentKbId) {
            showMessage('Сначала выберите базу знаний.', 'error');
            return;
        }

        // Check if trying to delete the default KB
        if (currentKbId === 'default') {
            showMessage('Базу знаний по умолчанию нельзя удалить', 'error');
            return;
        }

        // Get KB name for confirmation
        const kbName = knowledgeBases.find(kb => kb.id === currentKbId)?.name || currentKbId;
        
        // Proceed with deletion (backend will handle switching to default if needed)
        proceedWithDeletion(kbName);
    }

    function proceedWithDeletion(kbName) {
        if (!confirm(`Вы уверены, что хотите удалить базу знаний "${kbName}"?\n\nЭто действие нельзя отменить. Все данные будут потеряны.`)) {
            return;
        }

        fetch(`/api/knowledge-bases/${currentKbId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let message = `База знаний "${kbName}" успешно удалена`;
                if (data.switched_to_default) {
                    message += '. Переключились на базу знаний по умолчанию.';
                }
                showMessage(message, 'success');
                hideKbDetailsModal();
                loadKnowledgeBases(); // Reload KB list
            } else {
                showMessage(data.error || 'Ошибка при удалении базы знаний', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Ошибка при удалении базы знаний', 'error');
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
                document.getElementById('settings-kb-details-created').textContent = new Date(data.created_at).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' });
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
        
        // Always scroll to the message element, regardless of modal state
        setTimeout(() => {
            messageDiv.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
        }, 100); // Small delay to ensure the message is rendered
        
        // Hide message after 5 seconds
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }

    // Resizable textarea functionality
    function initResizableTextarea() {
        const textarea = document.getElementById('additional-prompt');
        const handle = document.querySelector('.resize-handle');
        
        if (!textarea || !handle) return;

        let isResizing = false;
        let startY = 0;
        let startHeight = 0;

        // Mouse events for the handle
        handle.addEventListener('mousedown', function(e) {
            isResizing = true;
            startY = e.clientY;
            startHeight = textarea.offsetHeight;
            
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            
            e.preventDefault();
        });

        function onMouseMove(e) {
            if (!isResizing) return;
            
            const deltaY = e.clientY - startY;
            const newHeight = Math.max(100, Math.min(600, startHeight + deltaY)); // Min 100px, Max 600px
            
            textarea.style.height = newHeight + 'px';
        }

        function onMouseUp() {
            isResizing = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        // Touch events for mobile devices
        handle.addEventListener('touchstart', function(e) {
            isResizing = true;
            startY = e.touches[0].clientY;
            startHeight = textarea.offsetHeight;
            
            document.addEventListener('touchmove', onTouchMove);
            document.addEventListener('touchend', onTouchEnd);
            
            e.preventDefault();
        });

        function onTouchMove(e) {
            if (!isResizing) return;
            
            const deltaY = e.touches[0].clientY - startY;
            const newHeight = Math.max(100, Math.min(600, startHeight + deltaY));
            
            textarea.style.height = newHeight + 'px';
        }

        function onTouchEnd() {
            isResizing = false;
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchend', onTouchEnd);
        }

        // Auto-resize on input (optional enhancement)
        textarea.addEventListener('input', function() {
            if (!isResizing) {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 600) + 'px';
            }
        });
    }

    // Function to automatically switch to default KB
    async function switchToDefaultKB() {
        try {
            const response = await fetch('/api/knowledge-bases/default', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                console.log('Successfully switched to default KB');
            } else {
                console.error('Failed to switch to default KB:', data.error);
            }
        } catch (error) {
            console.error('Error switching to default KB:', error);
        }
    }

    // Function to switch to a KB with password protection
    async function switchToKb(kbId) {
        try {
            // Check if KB requires password (not default KB)
            if (kbId !== 'default') {
                // Get KB details to check if it has a password
                const kbDetailsResponse = await fetch(`/api/knowledge-bases/${kbId}`);
                const kbDetails = await kbDetailsResponse.json();
                
                if (kbDetails.success && kbDetails.has_password) {
                    // Show password prompt
                    const password = await showPasswordPrompt(kbDetails.name);
                    if (password === null) {
                        // User cancelled, revert selector
                        kbSelector.value = currentKbId;
                        return;
                    }
                    
                    // Try to switch with password
                    const response = await fetch(`/api/knowledge-bases/${kbId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ password: password })
                    });

                    const data = await response.json();

                    if (data.success) {
                        currentKbId = kbId;
                        loadSettingsForKb(currentKbId);
                        showMessage(`Переключено на базу знаний "${kbDetails.name}"`, 'success');
                    } else {
                        console.error('Failed to switch knowledge base:', data.error);
                        showMessage(data.error || 'Ошибка при переключении базы знаний.', 'error');
                        // Revert selector
                        kbSelector.value = currentKbId;
                    }
                } else {
                    // KB doesn't have password, switch directly
                    const response = await fetch(`/api/knowledge-bases/${kbId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    const data = await response.json();

                    if (data.success) {
                        currentKbId = kbId;
                        loadSettingsForKb(currentKbId);
                        const kbName = (knowledgeBases.find(k => k.id === kbId) || {}).name || kbId;
                        showMessage(`Переключено на базу знаний "${kbName}"`, 'success');
                    } else {
                        console.error('Failed to switch knowledge base:', data.error);
                        showMessage('Ошибка при переключении базы знаний.', 'error');
                        // Revert selector
                        kbSelector.value = currentKbId;
                    }
                }
            } else {
                // Default KB, switch directly
                const response = await fetch(`/api/knowledge-bases/${kbId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                const data = await response.json();

                if (data.success) {
                    currentKbId = kbId;
                    loadSettingsForKb(currentKbId);
                    showMessage('Переключено на базу знаний по умолчанию', 'success');
                } else {
                    console.error('Failed to switch knowledge base:', data.error);
                    showMessage('Ошибка при переключении базы знаний.', 'error');
                    // Revert selector
                    kbSelector.value = currentKbId;
                }
            }
        } catch (error) {
            console.error('Error switching knowledge base:', error);
            showMessage('Ошибка при переключении базы знаний.', 'error');
            // Revert selector
            kbSelector.value = currentKbId;
        }
    }

    // Function to show password prompt modal
    function showPasswordPrompt(kbName) {
        return new Promise((resolve) => {
            const modal = document.getElementById('settings-kb-password-modal');
            const passwordInput = document.getElementById('settings-kb-password-input');
            const passwordName = document.getElementById('settings-kb-password-name');
            const errorDiv = document.getElementById('settings-kb-password-error');
            const form = document.getElementById('settings-kb-password-form');
            const closeBtn = document.getElementById('close-settings-kb-password-modal');
            const cancelBtn = document.getElementById('cancel-settings-kb-password');

            // Set KB name
            passwordName.textContent = kbName;
            
            // Clear previous values
            passwordInput.value = '';
            errorDiv.textContent = '';
            
            // Show modal
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            
            // Focus on password input
            setTimeout(() => passwordInput.focus(), 100);

            // Handle form submission
            const handleSubmit = (e) => {
                e.preventDefault();
                const password = passwordInput.value.trim();
                
                if (!password) {
                    errorDiv.textContent = 'Пожалуйста, введите пароль';
                    return;
                }
                
                // Clean up event listeners
                form.removeEventListener('submit', handleSubmit);
                closeBtn.removeEventListener('click', handleCancel);
                cancelBtn.removeEventListener('click', handleCancel);
                modal.removeEventListener('click', handleModalClick);
                
                // Hide modal
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                
                // Resolve with password
                resolve(password);
            };

            // Handle cancel
            const handleCancel = () => {
                // Clean up event listeners
                form.removeEventListener('submit', handleSubmit);
                closeBtn.removeEventListener('click', handleCancel);
                cancelBtn.removeEventListener('click', handleCancel);
                modal.removeEventListener('click', handleModalClick);
                
                // Hide modal
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                
                // Resolve with null (cancelled)
                resolve(null);
            };

            // Handle modal click outside
            const handleModalClick = (e) => {
                if (e.target === modal) {
                    handleCancel();
                }
            };

            // Add event listeners
            form.addEventListener('submit', handleSubmit);
            closeBtn.addEventListener('click', handleCancel);
            cancelBtn.addEventListener('click', handleCancel);
            modal.addEventListener('click', handleModalClick);
        });
    }

    // Initialize resizable textarea
    initResizableTextarea();
}); 