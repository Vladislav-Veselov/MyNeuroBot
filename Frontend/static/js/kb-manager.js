// Knowledge Base Management
class KnowledgeBaseManager {
    constructor() {
        this.currentKbId = null;
        this.knowledgeBases = [];
        this.init();
    }

    async init() {
        await this.loadKnowledgeBases();
        this.setupEventListeners();
    }

    async loadKnowledgeBases() {
        try {
            const response = await fetch('/api/knowledge-bases');
            
            // Check if user is not authenticated
            if (response.status === 401) {
                console.log('User not authenticated, redirecting to login');
                window.location.href = '/login';
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.knowledgeBases = data.knowledge_bases;
                this.currentKbId = data.current_kb_id;
                this.updateKbSelector();
            } else {
                console.error('Failed to load knowledge bases:', data.error);
                this.showFallbackOption();
            }
        } catch (error) {
            console.error('Error loading knowledge bases:', error);
            this.showFallbackOption();
        }
    }

    showFallbackOption() {
        const selector = document.getElementById('kb-selector');
        if (selector) {
            selector.innerHTML = '';
            const option = document.createElement('option');
            option.value = 'default';
            option.textContent = 'Основная база знаний';
            option.selected = true;
            selector.appendChild(option);
        }
    }

    updateKbSelector() {
        const selector = document.getElementById('kb-selector');
        
        if (!selector) {
            console.error('KB selector element not found!');
            return;
        }
        
        // Show loading state
        selector.innerHTML = '<option value="">Загрузка...</option>';
        
        if (this.knowledgeBases.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Нет баз знаний';
            selector.innerHTML = '';
            selector.appendChild(option);
            return;
        }

        // Clear and populate with knowledge bases
        selector.innerHTML = '';
        this.knowledgeBases.forEach(kb => {
            const option = document.createElement('option');
            option.value = kb.id;
            option.textContent = kb.name;
            if (kb.id === this.currentKbId) {
                option.selected = true;
            }
            selector.appendChild(option);
        });
    }

    setupEventListeners() {
        // KB Selector change
        const kbSelector = document.getElementById('kb-selector');
        kbSelector.addEventListener('change', (e) => {
            const selectedKbId = e.target.value;
            if (selectedKbId && selectedKbId !== this.currentKbId) {
                this.switchKnowledgeBase(selectedKbId);
            }
        });

        // Create KB button
        const createKbBtn = document.getElementById('create-kb-btn');
        createKbBtn.addEventListener('click', () => {
            this.showCreateKbModal();
        });

        // KB Details button
        const kbDetailsBtn = document.getElementById('kb-details-btn');
        kbDetailsBtn.addEventListener('click', () => {
            this.showKbDetailsModal();
        });

        // Create KB modal
        const createKbModal = document.getElementById('create-kb-modal');
        const closeCreateKbModal = document.getElementById('close-create-kb-modal');
        const cancelCreateKb = document.getElementById('cancel-create-kb');
        const createKbForm = document.getElementById('create-kb-form');

        closeCreateKbModal.addEventListener('click', () => {
            this.hideCreateKbModal();
        });

        cancelCreateKb.addEventListener('click', () => {
            this.hideCreateKbModal();
        });

        createKbForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createKnowledgeBase();
        });

        // Close modal when clicking outside
        createKbModal.addEventListener('click', (e) => {
            if (e.target === createKbModal) {
                this.hideCreateKbModal();
            }
        });

        // KB Details modal
        const kbDetailsModal = document.getElementById('kb-details-modal');
        const closeKbDetailsModal = document.getElementById('close-kb-details-modal');
        const closeKbDetails = document.getElementById('close-kb-details');
        const changeKbPasswordBtn = document.getElementById('change-kb-password-btn');

        closeKbDetailsModal.addEventListener('click', () => {
            this.hideKbDetailsModal();
        });

        closeKbDetails.addEventListener('click', () => {
            this.hideKbDetailsModal();
        });

        changeKbPasswordBtn.addEventListener('click', () => {
            this.showChangePasswordModal();
        });

        // Close KB details modal when clicking outside
        kbDetailsModal.addEventListener('click', (e) => {
            if (e.target === kbDetailsModal) {
                this.hideKbDetailsModal();
            }
        });

        // Change Password modal
        const changePasswordModal = document.getElementById('change-kb-password-modal');
        const closeChangePasswordModal = document.getElementById('close-change-password-modal');
        const cancelChangePassword = document.getElementById('cancel-change-password');
        const changePasswordForm = document.getElementById('change-kb-password-form');

        closeChangePasswordModal.addEventListener('click', () => {
            this.hideChangePasswordModal();
        });

        cancelChangePassword.addEventListener('click', () => {
            this.hideChangePasswordModal();
        });

        changePasswordForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.changeKbPassword();
        });

        // Close change password modal when clicking outside
        changePasswordModal.addEventListener('click', (e) => {
            if (e.target === changePasswordModal) {
                this.hideChangePasswordModal();
            }
        });

        // Toggle Analyze Clients button
        const toggleAnalyzeClientsBtn = document.getElementById('toggle-analyze-clients-btn');
        toggleAnalyzeClientsBtn.addEventListener('click', () => {
            this.showChangeAnalyzeClientsModal();
        });

        // Change Analyze Clients modal
        const changeAnalyzeClientsModal = document.getElementById('change-kb-analyze-clients-modal');
        const closeChangeAnalyzeClientsModal = document.getElementById('close-change-analyze-clients-modal');
        const cancelChangeAnalyzeClients = document.getElementById('cancel-change-analyze-clients');
        const changeAnalyzeClientsForm = document.getElementById('change-kb-analyze-clients-form');

        closeChangeAnalyzeClientsModal.addEventListener('click', () => {
            this.hideChangeAnalyzeClientsModal();
        });

        cancelChangeAnalyzeClients.addEventListener('click', () => {
            this.hideChangeAnalyzeClientsModal();
        });

        changeAnalyzeClientsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.changeKbAnalyzeClients();
        });

        // Close change analyze clients modal when clicking outside
        changeAnalyzeClientsModal.addEventListener('click', (e) => {
            if (e.target === changeAnalyzeClientsModal) {
                this.hideChangeAnalyzeClientsModal();
            }
        });

        // Toggle dot event listeners for KB creation
        const analyzeClientsYes = document.getElementById('kb-analyze-clients-yes');
        const analyzeClientsNo = document.getElementById('kb-analyze-clients-no');
        
        if (analyzeClientsYes && analyzeClientsNo) {
            analyzeClientsYes.addEventListener('click', () => {
                this.setAnalyzeClientsToggle('true');
            });
            
            analyzeClientsNo.addEventListener('click', () => {
                this.setAnalyzeClientsToggle('false');
            });
        }

        // Toggle dot event listeners for change modal
        const newAnalyzeClientsYes = document.getElementById('new-kb-analyze-clients-yes');
        const newAnalyzeClientsNo = document.getElementById('new-kb-analyze-clients-no');
        
        if (newAnalyzeClientsYes && newAnalyzeClientsNo) {
            newAnalyzeClientsYes.addEventListener('click', () => {
                this.setNewAnalyzeClientsToggle('true');
            });
            
            newAnalyzeClientsNo.addEventListener('click', () => {
                this.setNewAnalyzeClientsToggle('false');
            });
        }
    }

    showCreateKbModal() {
        const modal = document.getElementById('create-kb-modal');
        const input = document.getElementById('kb-name');
        const passwordInput = document.getElementById('kb-password');
        const error = document.getElementById('create-kb-error');
        
        input.value = '';
        passwordInput.value = '';
        this.setAnalyzeClientsToggle('true'); // Default to Yes
        error.textContent = '';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        input.focus();
    }

    hideCreateKbModal() {
        const modal = document.getElementById('create-kb-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    showKbDetailsModal() {
        if (!this.currentKbId) {
            this.showNotification('Сначала выберите базу знаний.', 'error');
            return;
        }
        
        this.loadKbDetails();
        const modal = document.getElementById('kb-details-modal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    hideKbDetailsModal() {
        const modal = document.getElementById('kb-details-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    async loadKbDetails() {
        try {
            const response = await fetch(`/api/knowledge-bases/${this.currentKbId}`);
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('kb-details-name').textContent = data.name;
                document.getElementById('kb-details-id').textContent = data.kb_id;
                document.getElementById('kb-details-created').textContent = new Date(data.created_at).toLocaleString('ru-RU');
                document.getElementById('kb-details-docs').textContent = data.document_count;
                
                // Display the actual password
                const passwordElement = document.getElementById('kb-details-password');
                if (data.password) {
                    passwordElement.textContent = data.password;
                    passwordElement.className = 'text-white font-mono';
                } else {
                    passwordElement.textContent = 'Не установлен';
                    passwordElement.className = 'text-[#718096] italic';
                }
                
                // Display analyze_clients setting
                const analyzeClientsElement = document.getElementById('kb-details-analyze-clients');
                if (data.analyze_clients !== undefined) {
                    analyzeClientsElement.textContent = data.analyze_clients ? 'Включен' : 'Отключен';
                    analyzeClientsElement.className = data.analyze_clients ? 'text-green-400' : 'text-red-400';
                } else {
                    analyzeClientsElement.textContent = 'Включен (по умолчанию)';
                    analyzeClientsElement.className = 'text-green-400';
                }
            } else {
                this.showNotification('Ошибка при загрузке деталей базы знаний.', 'error');
            }
        } catch (error) {
            console.error('Error loading KB details:', error);
            this.showNotification('Ошибка при загрузке деталей базы знаний.', 'error');
        }
    }

    showChangePasswordModal() {
        const modal = document.getElementById('change-kb-password-modal');
        const input = document.getElementById('new-kb-password');
        const error = document.getElementById('change-password-error');
        
        input.value = '';
        error.textContent = '';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        input.focus();
    }

    hideChangePasswordModal() {
        const modal = document.getElementById('change-kb-password-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    async changeKbPassword() {
        const input = document.getElementById('new-kb-password');
        const error = document.getElementById('change-password-error');
        const password = input.value.trim();

        if (!password) {
            error.textContent = 'Пожалуйста, введите новый пароль.';
            return;
        }

        try {
            const response = await fetch(`/api/knowledge-bases/${this.currentKbId}/password`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password })
            });

            const data = await response.json();

            if (data.success) {
                this.hideChangePasswordModal();
                this.hideKbDetailsModal();
                this.showNotification('Пароль базы знаний успешно изменен!', 'success');
            } else {
                error.textContent = data.error || 'Ошибка при изменении пароля.';
            }
        } catch (error) {
            console.error('Error changing KB password:', error);
            error.textContent = 'Ошибка при изменении пароля.';
        }
    }

    showChangeAnalyzeClientsModal() {
        const modal = document.getElementById('change-kb-analyze-clients-modal');
        const error = document.getElementById('change-analyze-clients-error');
        
        // Set current value
        const currentAnalyzeClientsElement = document.getElementById('kb-details-analyze-clients');
        const currentValue = currentAnalyzeClientsElement.textContent.includes('Включен') ? 'true' : 'false';
        this.setNewAnalyzeClientsToggle(currentValue);
        
        error.textContent = '';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    hideChangeAnalyzeClientsModal() {
        const modal = document.getElementById('change-kb-analyze-clients-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    async changeKbAnalyzeClients() {
        const error = document.getElementById('change-analyze-clients-error');
        const analyzeClients = this.getNewAnalyzeClientsToggleValue();

        try {
            const response = await fetch(`/api/knowledge-bases/${this.currentKbId}/analyze-clients`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ analyze_clients: analyzeClients })
            });

            const data = await response.json();

            if (data.success) {
                this.hideChangeAnalyzeClientsModal();
                this.hideKbDetailsModal();
                this.showNotification('Настройка анализа клиентов успешно изменена!', 'success');
            } else {
                error.textContent = data.error || 'Ошибка при изменении настройки.';
            }
        } catch (error) {
            console.error('Error changing KB analyze clients setting:', error);
            error.textContent = 'Ошибка при изменении настройки.';
        }
    }

    setAnalyzeClientsToggle(value) {
        const yesBtn = document.getElementById('kb-analyze-clients-yes');
        const noBtn = document.getElementById('kb-analyze-clients-no');
        
        if (yesBtn && noBtn) {
            yesBtn.classList.remove('active');
            noBtn.classList.remove('active');
            
            if (value === 'true') {
                yesBtn.classList.add('active');
            } else {
                noBtn.classList.add('active');
            }
        }
    }

    getAnalyzeClientsToggleValue() {
        const yesBtn = document.getElementById('kb-analyze-clients-yes');
        return yesBtn && yesBtn.classList.contains('active');
    }

    setNewAnalyzeClientsToggle(value) {
        const yesBtn = document.getElementById('new-kb-analyze-clients-yes');
        const noBtn = document.getElementById('new-kb-analyze-clients-no');
        
        if (yesBtn && noBtn) {
            yesBtn.classList.remove('active');
            noBtn.classList.remove('active');
            
            if (value === 'true') {
                yesBtn.classList.add('active');
            } else {
                noBtn.classList.add('active');
            }
        }
    }

    getNewAnalyzeClientsToggleValue() {
        const yesBtn = document.getElementById('new-kb-analyze-clients-yes');
        return yesBtn && yesBtn.classList.contains('active');
    }

    async createKnowledgeBase() {
        const input = document.getElementById('kb-name');
        const passwordInput = document.getElementById('kb-password');
        const error = document.getElementById('create-kb-error');
        const name = input.value.trim();
        const password = passwordInput.value.trim();
        const analyzeClients = this.getAnalyzeClientsToggleValue();

        if (!name) {
            error.textContent = 'Пожалуйста, введите название базы знаний.';
            return;
        }

        if (!password) {
            error.textContent = 'Пожалуйста, введите пароль для базы знаний.';
            return;
        }

        try {
            const response = await fetch('/api/knowledge-bases', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, password, analyze_clients: analyzeClients })
            });

            const data = await response.json();

            if (data.success) {
                this.hideCreateKbModal();
                await this.loadKnowledgeBases();
                this.switchKnowledgeBase(data.kb_id);
                
                // Show success message
                this.showNotification('База знаний успешно создана!', 'success');
            } else {
                error.textContent = data.error || 'Ошибка при создании базы знаний.';
            }
        } catch (error) {
            console.error('Error creating knowledge base:', error);
            error.textContent = 'Ошибка при создании базы знаний.';
        }
    }

    async switchKnowledgeBase(kbId) {
        try {
            const response = await fetch(`/api/knowledge-bases/${kbId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                this.currentKbId = kbId;
                this.updateKbSelector();
                
                // Reload the page to refresh the knowledge base content
                window.location.reload();
            } else {
                console.error('Failed to switch knowledge base:', data.error);
                this.showNotification('Ошибка при переключении базы знаний.', 'error');
            }
        } catch (error) {
            console.error('Error switching knowledge base:', error);
            this.showNotification('Ошибка при переключении базы знаний.', 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-600' : 
            type === 'error' ? 'bg-red-600' : 'bg-blue-600'
        } text-white`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Initialize KB Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const selector = document.getElementById('kb-selector');
    if (selector) {
        window.kbManager = new KnowledgeBaseManager();
    } else {
        console.error('KB selector not found');
    }
}); 