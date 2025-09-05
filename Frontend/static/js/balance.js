// Balance page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize balance page
    initBalancePage();
});

function initBalancePage() {
    loadBalanceData();
    loadTransactions();
}

function loadBalanceData() {
    fetch('/api/balance')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateBalanceDisplay(data.balance);
        } else {
            console.error('Error loading balance:', data.error);
            showError('Ошибка загрузки баланса');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Ошибка загрузки баланса');
    });
}

function updateBalanceDisplay(balanceData) {
    // Update balance display
    const balanceDisplay = document.getElementById('balance-display');
    const balanceStatus = document.getElementById('balance-status');
    
    const balanceRub = balanceData.balance_rub || 0;
    balanceDisplay.textContent = `₽${balanceRub.toFixed(2)}`;
    
    // Set balance status color
    if (balanceRub < 0) {
        balanceDisplay.classList.add('text-red-500');
        balanceDisplay.classList.remove('text-white');
        balanceStatus.textContent = 'Отрицательный баланс';
        balanceStatus.className = 'text-sm mt-2 text-red-400';
    } else if (balanceRub === 0) {
        balanceDisplay.classList.remove('text-red-500', 'text-green-500');
        balanceDisplay.classList.add('text-white');
        balanceStatus.textContent = 'Нулевой баланс';
        balanceStatus.className = 'text-sm mt-2 text-yellow-400';
    } else {
        balanceDisplay.classList.add('text-green-500');
        balanceDisplay.classList.remove('text-white', 'text-red-500');
        balanceStatus.textContent = 'Положительный баланс';
        balanceStatus.className = 'text-sm mt-2 text-green-400';
    }
    
    // Update current model
    const currentModelDisplay = document.getElementById('current-model-display');
    const modelDescription = document.getElementById('model-description');
    
    const currentModel = balanceData.current_model || 'gpt-4o-mini';
    currentModelDisplay.textContent = getModelDisplayName(currentModel);
    modelDescription.textContent = getModelDescription(currentModel);
    
    // Update token statistics
    const totalInputTokens = document.getElementById('total-input-tokens');
    const totalOutputTokens = document.getElementById('total-output-tokens');
    const totalTokens = document.getElementById('total-tokens');
    
    const inputTokens = balanceData.total_input_tokens || 0;
    const outputTokens = balanceData.total_output_tokens || 0;
    const totalTokenCount = inputTokens + outputTokens;
    
    totalInputTokens.textContent = inputTokens.toLocaleString();
    totalOutputTokens.textContent = outputTokens.toLocaleString();
    totalTokens.textContent = totalTokenCount.toLocaleString();
    
    // Update cost statistics
    const totalCostRub = document.getElementById('total-cost-rub');
    
    const costRub = balanceData.total_cost_rub || 0;
    
    totalCostRub.textContent = `₽${costRub.toFixed(2)}`;
}

function getModelDisplayName(modelId) {
    const modelNames = {
        'gpt-4o': 'PRO',
        'gpt-4o-mini': 'LITE'
    };
    return modelNames[modelId] || modelId;
}

function getModelDescription(modelId) {
    const descriptions = {
        'gpt-4o': '(более мощный и точный)',
        'gpt-4o-mini': '(быстрый и экономичный)'
    };
    return descriptions[modelId] || '';
}

function loadTransactions() {
    fetch('/api/balance/transactions')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateTransactionsList(data.transactions);
        } else {
            console.error('Error loading transactions:', data.error);
            showTransactionsError('Ошибка загрузки транзакций');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTransactionsError('Ошибка загрузки транзакций');
    });
}

function updateTransactionsList(transactions) {
    const transactionsList = document.getElementById('transactions-list');
    
    if (!transactions || transactions.length === 0) {
        transactionsList.innerHTML = `
            <div class="text-center text-[#718096] py-4">
                <p>Нет транзакций</p>
            </div>
        `;
        return;
    }
    
    // Sort transactions by timestamp (newest first)
    transactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    const transactionsHtml = transactions.map(transaction => {
        const date = new Date(transaction.timestamp);
        const formattedDate = date.toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Europe/Moscow'
        });
        
        const activityType = getActivityTypeDisplay(transaction.activity_type);
        const modelName = getModelDisplayName(transaction.model);
        const costRub = transaction.cost_rub.toFixed(2);
        const inputTokens = transaction.input_tokens.toLocaleString();
        const outputTokens = transaction.output_tokens.toLocaleString();
        
        // Check if this is a credit transaction (balance increase)
        const isCredit = transaction.is_credit || transaction.activity_type === 'balance_increase';
        
        // Determine the color and sign based on transaction type
        let amountColor = 'text-red-400';
        let amountSign = '-₽';
        let borderColor = 'border-[#DC4918]';
        
        if (isCredit) {
            amountColor = 'text-green-400';
            amountSign = '+₽';
            borderColor = 'border-green-500';
        }
        
        return `
            <div class="bg-[#1E2328] rounded-lg p-4 border-l-4 ${borderColor}">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h4 class="text-white font-medium">${activityType}</h4>
                        <p class="text-sm text-[#A0AEC0]">${modelName}</p>
                    </div>
                    <div class="text-right">
                        <p class="${amountColor} font-mono">${amountSign}${costRub}</p>
                        <p class="text-xs text-[#718096]">${formattedDate}</p>
                    </div>
                </div>
                <div class="flex justify-between text-xs text-[#718096]">
                    <span>Входные: ${inputTokens}</span>
                    <span>Выходные: ${outputTokens}</span>
                </div>
            </div>
        `;
    }).join('');
    
    transactionsList.innerHTML = transactionsHtml;
}

function getActivityTypeDisplay(activityType) {
    const activityNames = {
        'chatbot': 'Чат с ботом',
        'client_analysis': 'Анализ клиентов',
        'qa_generation': 'Генерация Q&A',
        'knowledge_processing': 'Обработка знаний',
        'balance_increase': 'Пополнение баланса'
    };
    return activityNames[activityType] || activityType;
}

function showError(message) {
    const balanceDisplay = document.getElementById('balance-display');
    balanceDisplay.textContent = 'Ошибка';
    balanceDisplay.className = 'text-6xl font-bold text-red-500 mb-4';
    
    const balanceStatus = document.getElementById('balance-status');
    balanceStatus.textContent = message;
    balanceStatus.className = 'text-sm mt-2 text-red-400';
}

function showTransactionsError(message) {
    const transactionsList = document.getElementById('transactions-list');
    transactionsList.innerHTML = `
        <div class="text-center text-red-400 py-4">
            <p>${message}</p>
        </div>
    `;
} 