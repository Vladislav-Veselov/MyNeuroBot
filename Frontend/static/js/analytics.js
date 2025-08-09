// Analytics page functionality
class AnalyticsManager {
    constructor() {
        this.currentSessionId = null;
        this.allSessions = []; // Store all sessions for filtering
        this.selectedKbId = 'all'; // Track selected KB
        this.init();
    }

    init() {
        this.analyzeUnreadSessions();
        this.loadStatistics();
        this.loadKnowledgeBases();
        this.loadSessions();
        this.bindEvents();
    }

    bindEvents() {
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.analyzeUnreadSessions();
            this.loadStatistics();
            this.loadKnowledgeBases();
        });

        // Clear all button
        document.getElementById('clear-all-btn').addEventListener('click', () => {
            this.clearAllSessions();
        });

        // KB selector change
        document.getElementById('kb-selector').addEventListener('change', (e) => {
            this.selectedKbId = e.target.value;
            this.filterSessions();
        });

        // Modal close button
        document.getElementById('close-modal').addEventListener('click', () => {
            this.closeModal();
        });

        // Delete session button
        document.getElementById('delete-session').addEventListener('click', () => {
            this.deleteCurrentSession();
        });

        // Close modal on backdrop click
        document.getElementById('dialogue-modal').addEventListener('click', (e) => {
            if (e.target.id === 'dialogue-modal') {
                this.closeModal();
            }
        });

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // Scroll to top button
        document.getElementById('scroll-to-top').addEventListener('click', () => {
            this.scrollToTop();
        });

        // Toggle potential client button (delegated event)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-potential-client-btn')) {
                e.stopPropagation(); // Prevent session card click
                this.togglePotentialClient(e.target.dataset.sessionId, e.target.dataset.currentStatus === 'true');
            }
        });

        // Download session button (delegated event)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('download-session-btn') || e.target.closest('.download-session-btn')) {
                e.stopPropagation(); // Prevent session card click
                const button = e.target.classList.contains('download-session-btn') ? e.target : e.target.closest('.download-session-btn');
                this.downloadSession(button.dataset.sessionId);
            }
        });
    }

    async analyzeUnreadSessions() {
        try {
            console.log('Analyzing unread sessions for potential clients...');
            
            const response = await fetch('/api/analyze-unread-sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                console.log('Analysis completed:', data.stats);
                if (data.stats.analyzed > 0) {
                    // Show a notification about the analysis results
                    this.showAnalysisNotification(data.stats);
                }
                // Always refresh sessions to show updated potential client status
                this.loadSessions();
                this.filterSessions();
            } else {
                console.error('Failed to analyze sessions:', data.error);
                // Still refresh sessions even if analysis failed
                this.loadSessions();
                this.filterSessions();
            }
        } catch (error) {
            console.error('Error analyzing sessions:', error);
        }
    }

    showAnalysisNotification(stats) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.className = 'analysis-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <h4>Анализ завершен</h4>
                <p>Проанализировано сессий: ${stats.analyzed}</p>
                <p>Потенциальных клиентов: ${stats.potential_clients}</p>
                <p>Не клиентов: ${stats.not_potential}</p>
                <button onclick="this.parentElement.parentElement.remove()">✕</button>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1E2328;
            border: 1px solid #2D3446;
            border-radius: 8px;
            padding: 16px;
            color: white;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            max-width: 300px;
        `;
        
        notification.querySelector('.notification-content').style.cssText = `
            position: relative;
        `;
        
        notification.querySelector('h4').style.cssText = `
            margin: 0 0 8px 0;
            color: #DC4918;
            font-size: 16px;
        `;
        
        notification.querySelector('p').style.cssText = `
            margin: 4px 0;
            font-size: 14px;
            color: #A0AEC0;
        `;
        
        notification.querySelector('button').style.cssText = `
            position: absolute;
            top: 0;
            right: 0;
            background: none;
            border: none;
            color: #A0AEC0;
            cursor: pointer;
            font-size: 16px;
            padding: 0;
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    async loadStatistics() {
        try {
            const response = await fetch('/api/dialogues/stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateStatistics(data.stats);
            } else {
                console.error('Failed to load statistics:', data.error);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    updateStatistics(stats) {
        document.getElementById('total-sessions').textContent = stats.total_sessions || 0;
        document.getElementById('total-messages').textContent = stats.total_messages || 0;
        document.getElementById('storage-created').textContent = this.formatDate(stats.last_updated);
        document.getElementById('file-size').textContent = `${stats.file_size_mb || 0} МБ`;
    }

    async loadKnowledgeBases() {
        try {
            const response = await fetch('/api/knowledge-bases');
            const data = await response.json();
            
            if (data.success) {
                this.populateKbSelector(data.knowledge_bases);
            } else {
                console.error('Failed to load knowledge bases:', data.error);
            }
        } catch (error) {
            console.error('Error loading knowledge bases:', error);
        }
    }

    populateKbSelector(knowledgeBases) {
        const selector = document.getElementById('kb-selector');
        const currentValue = selector.value; // Preserve current selection
        
        // Clear existing options except "all"
        selector.innerHTML = '<option value="all">Все базы знаний</option>';
        
        // Add KB options
        knowledgeBases.forEach(kb => {
            const option = document.createElement('option');
            option.value = kb.id; // Use kb.id instead of kb.kb_id
            option.textContent = kb.name || kb.id;
            selector.appendChild(option);
        });
        
        // Restore selection if it was valid
        if (currentValue && currentValue !== 'all') {
            const option = selector.querySelector(`option[value="${currentValue}"]`);
            if (option) {
                selector.value = currentValue;
                this.selectedKbId = currentValue;
            }
        }
        
        // Update KB session counts
        this.updateKbSessionCounts();
    }

    updateKbSessionCounts() {
        // Count sessions per KB
        const kbCounts = {};
        this.allSessions.forEach(session => {
            const kbId = session.kb_id || 'unknown';
            kbCounts[kbId] = (kbCounts[kbId] || 0) + 1;
        });
        
        // Update option text to show session counts
        const selector = document.getElementById('kb-selector');
        selector.querySelectorAll('option').forEach(option => {
            if (option.value === 'all') {
                const totalSessions = this.allSessions.length;
                option.textContent = `Все базы знаний (${totalSessions})`;
            } else {
                const count = kbCounts[option.value] || 0;
                const originalText = option.textContent.split(' (')[0]; // Remove existing count if any
                option.textContent = `${originalText} (${count})`;
            }
        });
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/dialogues');
            const data = await response.json();
            
            if (data.success) {
                this.allSessions = data.sessions; // Store all sessions
                this.updateKbSessionCounts(); // Update KB session counts
                this.filterSessions(); // Apply current filter
            } else {
                console.error('Failed to load sessions:', data.error);
                this.showEmptyState('Ошибка загрузки диалогов');
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showEmptyState('Ошибка загрузки диалогов');
        }
    }

    filterSessions() {
        let filteredSessions = this.allSessions;
        
        // Filter by selected KB
        if (this.selectedKbId !== 'all') {
            filteredSessions = this.allSessions.filter(session => 
                session.kb_id === this.selectedKbId
            );
        }
        
        this.renderSessions(filteredSessions);
    }

    renderSessions(sessions) {
        const container = document.getElementById('sessions-container');
        
        if (!sessions || sessions.length === 0) {
            if (this.selectedKbId !== 'all') {
                // Get the KB name for the selected KB
                const selector = document.getElementById('kb-selector');
                const selectedOption = selector.querySelector(`option[value="${this.selectedKbId}"]`);
                const kbName = selectedOption ? selectedOption.textContent : this.selectedKbId;
                this.showEmptyState(`Нет диалогов для базы знаний "${kbName}"`);
            } else {
                this.showEmptyState('Нет диалогов');
            }
            return;
        }

        container.innerHTML = sessions.map(session => this.createSessionCard(session)).join('');
        
        // Add click event listeners to session cards
        container.querySelectorAll('.session-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't open session if clicking on the toggle button
                if (!e.target.classList.contains('toggle-potential-client-btn')) {
                    this.openSession(card.dataset.sessionId);
                }
            });
        });
    }

    createSessionCard(session) {
        const lastUpdated = this.formatDate(session.last_updated);
        const preview = session.first_message || 'Нет сообщений';
        const isUnread = session.unread || false;
        const isPotentialClient = session.potential_client === true;
        const ipAddress = session.ip_address || 'Неизвестно';
        const kbName = session.kb_name || session.kb_id || 'База знаний по умолчанию';
        
        // Add CSS classes for styling
        let cardClasses = 'session-card';
        if (isUnread) cardClasses += ' unread';
        if (isPotentialClient) cardClasses += ' potential-client';
        
        return `
            <div class="${cardClasses}" data-session-id="${session.session_id}">
                <div class="session-header">
                    <div class="session-id">
                        ${session.session_id.substring(0, 8)}...
                        ${isUnread ? '<span class="unread-indicator"></span>' : ''}
                        ${isPotentialClient ? '<span class="potential-client-indicator">👤</span>' : ''}
                    </div>
                    <div class="session-time">${lastUpdated}</div>
                </div>
                <div class="session-content">
                    <div class="session-preview">${this.escapeHtml(preview)}</div>
                </div>
                <div class="session-meta">
                    <div class="session-kb">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                        </svg>
                        ${kbName}
                    </div>
                    <div class="session-messages">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                        </svg>
                        ${session.total_messages} сообщений
                    </div>
                    <div class="session-ip">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                        </svg>
                        ${ipAddress}
                    </div>
                </div>
                <div class="session-actions">
                    <button class="toggle-potential-client-btn" data-session-id="${session.session_id}" data-current-status="${isPotentialClient}">
                        ${isPotentialClient ? 'Убрать клиента' : 'Отметить клиентом'}
                    </button>
                    <button class="download-session-btn" data-session-id="${session.session_id}">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        Скачать
                    </button>
                </div>
            </div>
        `;
    }

    showEmptyState(message) {
        const container = document.getElementById('sessions-container');
        container.innerHTML = `
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>
                <p>${message}</p>
            </div>
        `;
    }

    async openSession(sessionId) {
        try {
            const response = await fetch(`/api/dialogues/${sessionId}`);
            const data = await response.json();
            
            if (data.session_id) {
                this.currentSessionId = sessionId;
                this.renderDialogue(data);
                this.openModal();
                
                            // Refresh sessions to update unread status immediately
            this.loadSessions();
            this.filterSessions();
            } else {
                console.error('Failed to load session:', data.error);
                alert('Ошибка загрузки диалога');
            }
        } catch (error) {
            console.error('Error loading session:', error);
            alert('Ошибка загрузки диалога');
        }
    }

    renderDialogue(session) {
        const container = document.getElementById('dialogue-messages');
        const info = document.getElementById('dialogue-info');
        const scrollButton = document.getElementById('scroll-to-top');
        
        // Update session info - handle both old and new data structures
        const lastUpdated = session.metadata ? session.metadata.last_updated : session.last_updated;
        info.textContent = `Сессия: ${session.session_id.substring(0, 8)}... | Обновлено: ${this.formatDate(lastUpdated)}`;
        
        // Render messages
        if (!session.messages || session.messages.length === 0) {
            container.innerHTML = `
                <div class="text-center text-[#A0AEC0] py-8">
                    <p>Нет сообщений в этой сессии</p>
                </div>
            `;
            return;
        }

        container.innerHTML = session.messages.map(message => this.createMessageElement(message)).join('');
        
        // Remove existing scroll event listener to prevent duplicates
        container.removeEventListener('scroll', this.handleScroll);
        
        // Add scroll event listener for scroll-to-top button
        this.handleScroll = () => {
            if (container.scrollTop > 300) {
                scrollButton.classList.remove('opacity-0', 'pointer-events-none');
                scrollButton.classList.add('opacity-100');
            } else {
                scrollButton.classList.add('opacity-0', 'pointer-events-none');
                scrollButton.classList.remove('opacity-100');
            }
        };
        
        container.addEventListener('scroll', this.handleScroll);
        
        // Ensure container has proper height and scrolling
        container.style.height = '100%';
        container.style.overflowY = 'auto';
        container.style.overflowX = 'hidden';
        container.style.maxHeight = '100%';
        
        // Force recalculation of layout
        container.offsetHeight;
        
        // Scroll to bottom after a short delay to ensure content is rendered
        setTimeout(() => {
            container.scrollTop = container.scrollHeight;
        }, 100);
    }

    scrollToTop() {
        const container = document.getElementById('dialogue-messages');
        if (container) {
            container.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    }

    createMessageElement(message) {
        const timestamp = this.formatDate(message.timestamp);
        const isUser = message.role === 'user';
        const avatarText = isUser ? 'U' : 'B';
        const avatarClass = isUser ? 'user' : 'assistant';
        
        return `
            <div class="modal-message ${avatarClass}">
                <div class="message-avatar ${avatarClass}">${avatarText}</div>
                <div class="message-content ${avatarClass}">
                    <div class="message-bubble">${this.escapeHtml(message.content)}</div>
                    <div class="message-timestamp ${avatarClass}">${timestamp}</div>
                </div>
            </div>
        `;
    }

    openModal() {
        const modal = document.getElementById('dialogue-modal');
        modal.classList.remove('hidden');
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        const modal = document.getElementById('dialogue-modal');
        modal.classList.add('hidden');
        modal.classList.remove('show');
        document.body.style.overflow = '';
        this.currentSessionId = null;
        
        // Refresh sessions to update unread status
        this.loadSessions();
        this.filterSessions();
    }

    async deleteCurrentSession() {
        if (!this.currentSessionId) return;
        
        if (!confirm('Вы уверены, что хотите удалить эту сессию?')) return;
        
        try {
            const response = await fetch(`/api/dialogues/${this.currentSessionId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                this.closeModal();
                this.loadStatistics();
                this.loadSessions();
                this.filterSessions();
            } else {
                console.error('Failed to delete session:', data.error);
                alert('Ошибка удаления сессии');
            }
        } catch (error) {
            console.error('Error deleting session:', error);
            alert('Ошибка удаления сессии');
        }
    }

    async clearAllSessions() {
        if (!confirm('Вы уверены, что хотите удалить ВСЕ сессии? Это действие нельзя отменить.')) return;
        
        try {
            const response = await fetch('/api/dialogues/clear-all', {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                this.closeModal();
                this.loadStatistics();
                this.loadSessions();
                this.filterSessions();
            } else {
                console.error('Failed to clear sessions:', data.error);
                alert('Ошибка очистки сессий');
            }
        } catch (error) {
            console.error('Error clearing sessions:', error);
            alert('Ошибка очистки сессий');
        }
    }

    async togglePotentialClient(sessionId, currentStatus) {
        try {
            const newStatus = !currentStatus;
            const response = await fetch(`/api/dialogues/${sessionId}/potential-client`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    potential_client: newStatus
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Refresh sessions to show updated status
                this.loadSessions();
                this.filterSessions();
            } else {
                console.error('Failed to toggle potential client:', data.error);
                alert('Ошибка при изменении статуса клиента');
            }
        } catch (error) {
            console.error('Error toggling potential client:', error);
            alert('Ошибка при изменении статуса клиента');
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'Неизвестно';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return date.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } else if (diffDays === 1) {
            return 'Вчера';
        } else if (diffDays < 7) {
            return `${diffDays} дней назад`;
        } else {
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async downloadSession(sessionId) {
        try {
            // Create a temporary link element to trigger the download
            const link = document.createElement('a');
            link.href = `/api/dialogues/${sessionId}/download`;
            link.download = `dialogue_${sessionId.substring(0, 8)}.txt`;
            link.style.display = 'none';
            
            // Add the link to the document, click it, and remove it
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error downloading session:', error);
            alert('Ошибка при скачивании диалога');
        }
    }
}

// Initialize analytics when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AnalyticsManager();
}); 