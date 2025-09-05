document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const documentsContainer = document.getElementById('documents-container');
    const searchInput = document.getElementById('search-input');
    const semanticSearchInput = document.getElementById('semantic-search-input');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const lastPageBtn = document.getElementById('last-page');
    const firstPageBtn = document.getElementById('first-page');
    const pageInfo = document.getElementById('page-info');
    const statsContainer = document.getElementById('stats');
    const modal = document.getElementById('document-modal');
    const modalContent = document.getElementById('modal-content');
    const closeModalBtn = document.getElementById('close-modal');
    const addQaBtn = document.getElementById('add-qa-btn');
    const addQaModal = document.getElementById('add-qa-modal');
    const closeAddQaModalBtn = document.getElementById('close-add-qa-modal');
    const addQaForm = document.getElementById('add-qa-form');
    const addQuestionInput = document.getElementById('add-question');
    const addAnswerInput = document.getElementById('add-answer');
    const addQaError = document.getElementById('add-qa-error');
    const cancelAddQaBtn = document.getElementById('cancel-add-qa');
    
    // Edit modal elements
    const editQaModal = document.getElementById('edit-qa-modal');
    const closeEditQaModalBtn = document.getElementById('close-edit-qa-modal');
    const editQaForm = document.getElementById('edit-qa-form');
    const editQuestionInput = document.getElementById('edit-question');
    const editAnswerInput = document.getElementById('edit-answer');
    const editDocumentIdInput = document.getElementById('edit-document-id');
    const editQaError = document.getElementById('edit-qa-error');
    const cancelEditQaBtn = document.getElementById('cancel-edit-qa');
    
    // Delete modal elements
    const deleteConfirmModal = document.getElementById('delete-confirm-modal');
    const closeDeleteModalBtn = document.getElementById('close-delete-modal');
    const cancelDeleteBtn = document.getElementById('cancel-delete');
    const confirmDeleteBtn = document.getElementById('confirm-delete');
    
    // Download button element
    const downloadKbBtn = document.getElementById('download-kb-btn');
    
    // State
    let currentPage = 1;
    let totalPages = 1;
    let currentSearch = '';
    let currentSemanticSearch = '';
    let isLoading = false;
    let documentToDelete = null;
    let searchMode = 'regular'; // 'regular' or 'semantic'

    // Utility functions
    function showLoading() {
        isLoading = true;
        documentsContainer.innerHTML = `
            <div class="flex justify-center items-center py-8">
                <div class="loading-spinner"></div>
            </div>
        `;
    }

    function hideLoading() {
        isLoading = false;
    }

    function highlightText(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }

    // API calls
    async function fetchDocuments(page = 1, search = '', semanticSearch = '') {
        showLoading();
        try {
            let url;
            if (semanticSearch) {
                url = `/api/semantic_search?query=${encodeURIComponent(semanticSearch)}`;
            } else {
                url = `/api/documents?page=${page}&search=${encodeURIComponent(search)}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (response.ok) {
                if (semanticSearch) {
                    // For semantic search, we don't have pagination
                    return {
                        documents: data.documents,
                        pagination: {
                            current_page: 1,
                            total_pages: 1,
                            total_documents: data.total_results,
                            items_per_page: data.documents.length
                        }
                    };
                }
                return data;
            } else {
                throw new Error(data.error || 'Failed to fetch documents');
            }
        } catch (error) {
            console.error('Error fetching documents:', error);
            documentsContainer.innerHTML = `
                <div class="text-red-500 text-center py-4">
                    Ошибка загрузки документов: ${error.message}
                </div>
            `;
            return null;
        } finally {
            hideLoading();
        }
    }

    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (response.ok) {
                return data;
            } else {
                throw new Error(data.error || 'Failed to fetch stats');
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
            return null;
        }
    }

    // UI update functions
    function updatePagination(pagination) {
        currentPage = pagination.current_page;
        totalPages = pagination.total_pages;
        
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
        lastPageBtn.disabled = currentPage === totalPages;
        firstPageBtn.disabled = currentPage === 1;
        
        pageInfo.textContent = `Страница ${currentPage} из ${totalPages} (${pagination.total_documents} вопросов)`;
    }

    function renderDocument(doc) {
        // Clean and format the text
        const question = doc.question.trim();
        const answer = doc.answer.trim();
        
        // Truncate answer for preview, preserving line breaks
        const previewAnswer = answer.length > 200 
            ? answer.split('\n')[0].substring(0, 200) + '...' 
            : answer;

        return `
            <div class="document-card bg-[#242A36] border border-[#2D3446] rounded-lg p-4 hover:shadow-md transition-shadow" data-id="${doc.id}" data-question="${encodeURIComponent(question)}" data-answer="${encodeURIComponent(answer)}">
                <div class="space-y-2">
                    <div class="flex justify-between items-start">
                        <div class="question text-lg font-semibold text-[#DC4918] flex-1">
                            ${highlightText(question, currentSearch || currentSemanticSearch)}
                        </div>
                        <div class="flex gap-2 ml-4">
                            <button class="edit-btn px-3 py-1 text-sm bg-[#2D3446] text-[#DC4918] rounded hover:bg-[#3D4456] transition-colors">
                                ✎
                            </button>
                            <button class="delete-btn px-3 py-1 text-sm bg-[#2D3446] text-red-500 rounded hover:bg-[#3D4456] transition-colors">
                                ×
                            </button>
                        </div>
                    </div>
                    <div class="answer text-[#A0AEC0] whitespace-pre-line">
                        ${highlightText(previewAnswer, currentSearch || currentSemanticSearch)}
                    </div>
                </div>
            </div>
        `;
    }

    function updateDocuments(data) {
        if (!data) return;
        
        if (data.documents.length === 0) {
            documentsContainer.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    ${currentSearch ? 'По вашему запросу ничего не найдено' : 'База знаний пуста'}
                </div>
            `;
        } else {
            documentsContainer.innerHTML = data.documents
                .map(doc => renderDocument(doc))
                .join('');
        }
        
        updatePagination(data.pagination);
    }

    function updateStats(stats) {
        if (!stats) return;

        const statsHtml = `
            <div class="stat-card bg-[#242A36] p-4 rounded-lg border border-[#2D3446]">
                <div class="stat-value text-2xl font-bold text-[#DC4918]">${stats.total_documents}</div>
                <div class="stat-label text-[#A0AEC0]">Всего вопросов</div>
            </div>
            <div class="stat-card bg-[#242A36] p-4 rounded-lg border border-[#2D3446]">
                <div class="stat-value text-2xl font-bold text-[#DC4918]">${stats.last_update}</div>
                <div class="stat-label text-[#A0AEC0]">Последнее обновление базы</div>
            </div>
            <div class="stat-card bg-[#242A36] p-4 rounded-lg border border-[#2D3446]">
                <div class="stat-value text-2xl font-bold text-[#DC4918]">${Math.round(stats.average_answer_length)}</div>
                <div class="stat-label text-[#A0AEC0]">Средняя длина ответа</div>
            </div>
        `;
        
        statsContainer.innerHTML = statsHtml;
    }

    function showDocumentModal(docId) {
        fetch(`/api/document/${docId}`)
            .then(response => response.json())
            .then(doc => {
                if (doc.error) throw new Error(doc.error);
                
                // Clean and format the text
                const question = doc.question.trim();
                const answer = doc.answer.trim();
                
                modalContent.innerHTML = `
                    <div class="space-y-6">
                        <div class="question-section">
                            <h4 class="text-lg font-semibold text-[#DC4918] mb-2">Вопрос</h4>
                            <div class="bg-[#2D3446] p-4 rounded-lg">
                                ${highlightText(question, currentSearch || currentSemanticSearch)}
                            </div>
                        </div>
                        <div class="answer-section">
                            <h4 class="text-lg font-semibold text-[#DC4918] mb-2">Ответ</h4>
                            <div class="bg-[#2D3446] p-4 rounded-lg whitespace-pre-line">
                                ${highlightText(answer, currentSearch || currentSemanticSearch)}
                            </div>
                        </div>
                    </div>
                `;
                
                modal.classList.remove('hidden');
                modal.classList.add('flex');
                
                // Ensure modal content scrolls to top after content is rendered
                setTimeout(() => {
                    modalContent.scrollTop = 0;
                    console.log('Modal opened, content height:', modalContent.scrollHeight);
                    console.log('Modal content max-height:', modalContent.style.maxHeight);
                    console.log('Modal content overflow:', modalContent.style.overflowY);
                    
                    // Debug header background
                    const modalHeader = modal.querySelector('.p-6.border-b');
                    if (modalHeader) {
                        console.log('Modal header background:', modalHeader.style.backgroundColor);
                        console.log('Modal header computed background:', window.getComputedStyle(modalHeader).backgroundColor);
                    }
                }, 100);
            })
            .catch(error => {
                console.error('Error fetching document:', error);
                modalContent.innerHTML = `
                    <div class="text-[#DC4918]">
                        Ошибка загрузки документа: ${error.message}
                    </div>
                `;
                modal.classList.remove('hidden');
                modal.classList.add('flex');
            });
    }

    function showDocumentModalFromCard(card) {
        const question = decodeURIComponent(card.dataset.question || '');
        const answer = decodeURIComponent(card.dataset.answer || '');

        modalContent.innerHTML = `
            <div class="space-y-6">
                <div class="question-section">
                    <h4 class="text-lg font-semibold text-[#DC4918] mb-2">Вопрос</h4>
                    <div class="bg-[#2D3446] p-4 rounded-lg">
                        ${highlightText(question, currentSearch || currentSemanticSearch)}
                    </div>
                </div>
                <div class="answer-section">
                    <h4 class="text-lg font-semibold text-[#DC4918] mb-2">Ответ</h4>
                    <div class="bg-[#2D3446] p-4 rounded-lg whitespace-pre-line">
                        ${highlightText(answer, currentSearch || currentSemanticSearch)}
                    </div>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Ensure modal content scrolls to top after content is rendered
        setTimeout(() => {
            modalContent.scrollTop = 0;
            console.log('Modal opened from card, content height:', modalContent.scrollHeight);
            console.log('Modal content max-height:', modalContent.style.maxHeight);
            console.log('Modal content overflow:', modalContent.style.overflowY);
            
            // Debug header background
            const modalHeader = modal.querySelector('.p-6.border-b');
            if (modalHeader) {
                console.log('Modal header background:', modalHeader.style.backgroundColor);
                console.log('Modal header computed background:', window.getComputedStyle(modalHeader).backgroundColor);
            }
        }, 100);
    }

    // Event handlers
    async function handleSearch() {
        currentSearch = searchInput.value.trim();
        currentSemanticSearch = '';  // Clear semantic search when using regular search
        searchMode = 'regular';
        currentPage = 1;
        const data = await fetchDocuments(currentPage, currentSearch);
        updateDocuments(data);
    }

    async function handleSemanticSearch() {
        currentSemanticSearch = semanticSearchInput.value.trim();
        currentSearch = '';  // Clear regular search when using semantic search
        searchMode = 'semantic';
        const data = await fetchDocuments(1, '', currentSemanticSearch);
        updateDocuments(data);
    }

    async function handlePageChange(delta) {
        if (isLoading) return;
        
        let newPage;
        if (delta === 'last') {
            newPage = totalPages;
        } else if (delta === 'first') {
            newPage = 1;
        } else {
            newPage = currentPage + delta;
        }
        
        if (newPage < 1 || newPage > totalPages) return;
        
        const data = await fetchDocuments(newPage, currentSearch);
        updateDocuments(data);
    }

    // Event listeners
    searchInput.addEventListener('input', debounce(handleSearch, 300));
    semanticSearchInput.addEventListener('input', debounce(handleSemanticSearch, 300));
    prevPageBtn.addEventListener('click', () => handlePageChange(-1));
    nextPageBtn.addEventListener('click', () => handlePageChange(1));
    lastPageBtn.addEventListener('click', () => handlePageChange('last'));
    firstPageBtn.addEventListener('click', () => handlePageChange('first'));
    closeModalBtn.addEventListener('click', () => {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    });
    
    documentsContainer.addEventListener('click', (e) => {
        const card = e.target.closest('.document-card');
        if (!card) return;

        const docId = card.dataset.id;
        
        if (e.target.classList.contains('edit-btn')) {
            e.stopPropagation(); // Prevent modal from opening
            const question = decodeURIComponent(card.dataset.question);
            const answer = decodeURIComponent(card.dataset.answer);
            openEditModal(docId, question, answer);
        } else if (e.target.classList.contains('delete-btn')) {
            e.stopPropagation(); // Prevent modal from opening
            openDeleteModal(docId);
        } else {
            showDocumentModalFromCard(card);
        }
    });

    // Add Q&A Modal logic
    function openAddQaModal() {
        addQuestionInput.value = '';
        addAnswerInput.value = '';
        addQaError.textContent = '';
        // Reset character counters
        document.getElementById('add-question-counter').textContent = '0';
        document.getElementById('add-answer-counter').textContent = '0';
        addQaModal.classList.remove('hidden');
        addQaModal.classList.add('flex');
    }
    function closeAddQaModal() {
        addQaModal.classList.remove('flex');
        addQaModal.classList.add('hidden');
    }
    addQaBtn.addEventListener('click', openAddQaModal);
    closeAddQaModalBtn.addEventListener('click', closeAddQaModal);
    cancelAddQaBtn.addEventListener('click', (e) => {
        e.preventDefault();
        closeAddQaModal();
    });
    addQaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = addQuestionInput.value.trim();
        const answer = addAnswerInput.value.trim();
        
        // Clear previous errors
        addQaError.textContent = '';
        
        // Validate question length (max 250 characters)
        if (!question) {
            addQaError.textContent = 'Пожалуйста, введите вопрос.';
            return;
        }
        if (question.length > 250) {
            addQaError.textContent = 'Вопрос слишком длинный. Максимальная длина вопроса - 250 символов.';
            return;
        }
        
        // Validate answer length (max 2500 characters)
        if (!answer) {
            addQaError.textContent = 'Пожалуйста, введите ответ.';
            return;
        }
        if (answer.length > 2500) {
            addQaError.textContent = 'Ответ слишком длинный. Максимальная длина ответа - 2500 символов.';
            return;
        }
        
        try {
            const response = await fetch('/api/add_qa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, answer })
            });
            const data = await response.json();
            if (!response.ok) {
                addQaError.textContent = data.error || 'Ошибка при добавлении.';
                return;
            }
            closeAddQaModal();
            // Refresh Q&A list
            handleSearch();
        } catch (error) {
            addQaError.textContent = 'Ошибка сети. Попробуйте еще раз.';
        }
    });

    // Edit and Delete handlers
    function openEditModal(docId, question, answer) {
        editDocumentIdInput.value = docId;
        editQuestionInput.value = question;
        editAnswerInput.value = answer;
        editQaError.textContent = '';
        // Update character counters
        document.getElementById('edit-question-counter').textContent = question.length;
        document.getElementById('edit-answer-counter').textContent = answer.length;
        editQaModal.classList.remove('hidden');
        editQaModal.classList.add('flex');
    }

    function closeEditModal() {
        editQaModal.classList.remove('flex');
        editQaModal.classList.add('hidden');
        editDocumentIdInput.value = '';
        editQuestionInput.value = '';
        editAnswerInput.value = '';
        editQaError.textContent = '';
    }

    function openDeleteModal(docId) {
        documentToDelete = docId;
        deleteConfirmModal.classList.remove('hidden');
        deleteConfirmModal.classList.add('flex');
    }

    function closeDeleteModal() {
        deleteConfirmModal.classList.remove('flex');
        deleteConfirmModal.classList.add('hidden');
        documentToDelete = null;
    }

    async function handleEdit(e) {
        e.preventDefault();
        const docId = editDocumentIdInput.value;
        const question = editQuestionInput.value.trim();
        const answer = editAnswerInput.value.trim();

        // Clear previous errors
        editQaError.textContent = '';

        // Validate question length (max 250 characters)
        if (!question) {
            editQaError.textContent = 'Пожалуйста, введите вопрос.';
            return;
        }
        if (question.length > 250) {
            editQaError.textContent = 'Вопрос слишком длинный. Максимальная длина вопроса - 250 символов.';
            return;
        }

        // Validate answer length (max 2500 characters)
        if (!answer) {
            editQaError.textContent = 'Пожалуйста, введите ответ.';
            return;
        }
        if (answer.length > 2500) {
            editQaError.textContent = 'Ответ слишком длинный. Максимальная длина ответа - 2500 символов.';
            return;
        }

        try {
            const response = await fetch(`/api/document/${docId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, answer })
            });
            const data = await response.json();
            
            if (!response.ok) {
                editQaError.textContent = data.error || 'Ошибка при редактировании.';
                return;
            }
            
            closeEditModal();
            
            // Refresh the document list and handle pagination properly
            try {
                // First, get the total count to see if current page is still valid
                const totalData = await fetchDocuments(1, currentSearch);
                const totalPages = totalData.pagination.total_pages;
                
                // If current page is now invalid, go to the last valid page
                if (currentPage > totalPages && totalPages > 0) {
                    currentPage = totalPages;
                }
                
                // Refresh with the adjusted page
                const currentData = await fetchDocuments(currentPage, currentSearch);
                updateDocuments(currentData);
                
                // Update pagination controls
                updatePagination(currentData.pagination);
            } catch (error) {
                console.error('Error refreshing after edit:', error);
                // Fallback: go to page 1
                currentPage = 1;
                const fallbackData = await fetchDocuments(1, currentSearch);
                updateDocuments(fallbackData);
                updatePagination(fallbackData.pagination);
            }
        } catch (error) {
            console.error('Error editing document:', error);
            
            // Provide more helpful error messages
            if (error.message.includes('Document not found') || error.message.includes('Документ не найден')) {
                editQaError.textContent = 'Документ был удален или перемещен. Страница будет обновлена автоматически.';
                // Auto-refresh to get current document list
                setTimeout(() => {
                    handleSearch();
                }, 1000);
            } else {
                editQaError.textContent = 'Ошибка сети. Попробуйте еще раз.';
            }
        }
    }

    async function handleDelete() {
        if (!documentToDelete) return;

        try {
            const response = await fetch(`/api/document/${documentToDelete}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Ошибка при удалении.');
            }
            
            closeDeleteModal();
            
            // Refresh the document list and handle pagination properly
            try {
                // First, get the total count to see if current page is still valid
                const totalData = await fetchDocuments(1, currentSearch);
                const totalPages = totalData.pagination.total_pages;
                
                // If current page is now invalid, go to the last valid page
                if (currentPage > totalPages && totalPages > 0) {
                    currentPage = totalPages;
                }
                
                // Refresh with the adjusted page
                const currentData = await fetchDocuments(currentPage, currentSearch);
                updateDocuments(currentData);
                
                // Update pagination controls
                updatePagination(currentData.pagination);
            } catch (error) {
                console.error('Error refreshing after deletion:', error);
                // Fallback: go to page 1
                currentPage = 1;
                const fallbackData = await fetchDocuments(1, currentSearch);
                updateDocuments(fallbackData);
                updatePagination(fallbackData.pagination);
            }
        } catch (error) {
            console.error('Error deleting document:', error);
            
            // Provide more helpful error messages
            let errorMessage = 'Ошибка при удалении: ';
            if (error.message.includes('Document not found') || error.message.includes('Документ не найден')) {
                errorMessage += 'Документ был удален или перемещен. Страница будет обновлена автоматически.';
                // Auto-refresh to get current document list
                setTimeout(() => {
                    handleSearch();
                }, 1000);
            } else {
                errorMessage += error.message;
            }
            
            alert(errorMessage);
        }
    }

    // Event listeners for edit and delete
    editQaForm.addEventListener('submit', handleEdit);
    closeEditQaModalBtn.addEventListener('click', closeEditModal);
    cancelEditQaBtn.addEventListener('click', closeEditModal);
    
    // Character counter event listeners
    addQuestionInput.addEventListener('input', function() {
        document.getElementById('add-question-counter').textContent = this.value.length;
    });
    
    addAnswerInput.addEventListener('input', function() {
        document.getElementById('add-answer-counter').textContent = this.value.length;
    });
    
    editQuestionInput.addEventListener('input', function() {
        document.getElementById('edit-question-counter').textContent = this.value.length;
    });
    
    editAnswerInput.addEventListener('input', function() {
        document.getElementById('edit-answer-counter').textContent = this.value.length;
    });
    
    closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    confirmDeleteBtn.addEventListener('click', handleDelete);

    // Download button event listener
    downloadKbBtn.addEventListener('click', handleDownloadKnowledgeFile);

    // Download knowledge file function
    async function handleDownloadKnowledgeFile() {
        try {
            // Show loading state
            const originalText = downloadKbBtn.title;
            const originalHTML = downloadKbBtn.innerHTML;
            
            downloadKbBtn.disabled = true;
            downloadKbBtn.title = 'Скачивание...';
            downloadKbBtn.innerHTML = `
                <svg class="h-5 w-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
            `;
            
            // Get current KB ID from the KB manager
            if (window.kbManager && window.kbManager.currentKbId) {
                const kbId = window.kbManager.currentKbId;
                
                // Create download link
                const downloadUrl = `/api/knowledge-bases/${kbId}/download`;
                
                // Create temporary link element and trigger download
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = '';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Show success feedback
                downloadKbBtn.innerHTML = `
                    <svg class="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                `;
                downloadKbBtn.title = 'Файл скачан!';
                
                // Reset after 2 seconds
                setTimeout(() => {
                    downloadKbBtn.disabled = false;
                    downloadKbBtn.title = originalText;
                    downloadKbBtn.innerHTML = originalHTML;
                }, 2000);
                
            } else {
                // Fallback: try to get current KB from the selector
                const kbSelector = document.getElementById('kb-selector');
                if (kbSelector && kbSelector.value) {
                    const kbId = kbSelector.value;
                    
                    // Create download link
                    const downloadUrl = `/api/knowledge-bases/${kbId}/download`;
                    
                    // Create temporary link element and trigger download
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.download = '';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // Show success feedback
                    downloadKbBtn.innerHTML = `
                        <svg class="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                    `;
                    downloadKbBtn.title = 'Файл скачан!';
                    
                    // Reset after 2 seconds
                    setTimeout(() => {
                        downloadKbBtn.disabled = false;
                        downloadKbBtn.title = originalText;
                        downloadKbBtn.innerHTML = originalHTML;
                    }, 2000);
                    
                } else {
                    alert('Не удалось определить текущую базу знаний. Пожалуйста, выберите базу знаний и попробуйте снова.');
                    
                    // Reset button state
                    downloadKbBtn.disabled = false;
                    downloadKbBtn.title = originalText;
                    downloadKbBtn.innerHTML = originalHTML;
                }
            }
        } catch (error) {
            console.error('Error downloading knowledge file:', error);
            alert('Ошибка при скачивании файла: ' + error.message);
            
            // Reset button state on error
            downloadKbBtn.disabled = false;
            downloadKbBtn.title = originalText;
            downloadKbBtn.innerHTML = originalHTML;
        }
    }

    // Initialize
    async function initialize() {
        const [documentsData, statsData] = await Promise.all([
            fetchDocuments(currentPage),
            fetchStats()
        ]);
        
        updateDocuments(documentsData);
        updateStats(statsData);
    }

    // Debounce utility
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Start the application
    initialize();

    // Clear other search when one is used
    searchInput.addEventListener('focus', () => {
        if (searchMode === 'semantic') {
            semanticSearchInput.value = '';
            currentSemanticSearch = '';
        }
    });
    
    semanticSearchInput.addEventListener('focus', () => {
        if (searchMode === 'regular') {
            searchInput.value = '';
            currentSearch = '';
        }
    });
}); 