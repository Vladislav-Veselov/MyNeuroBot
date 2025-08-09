// Admin panel functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin panel
    initAdminPanel();
    
    // Initialize logout functionality
    initLogout();
});

function initAdminPanel() {
    loadUserBalances();
    loadUsers();
}

function initLogout() {
    // Get logout button and user account elements
    const logoutBtn = document.getElementById('logout-btn');
    const userAccountBtn = document.getElementById('user-account-btn');
    const userDropdown = document.getElementById('user-dropdown');
    const usernameDisplay = document.getElementById('username-display');
    
    // Set admin username
    usernameDisplay.textContent = 'Админ';
    
    // Toggle dropdown on click
    if (userAccountBtn) {
        userAccountBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('hidden');
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (userAccountBtn && userDropdown && !userAccountBtn.contains(e.target) && !userDropdown.contains(e.target)) {
            userDropdown.classList.add('hidden');
        }
    });
    
    // Logout functionality
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/api/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Clear localStorage
                    localStorage.removeItem('username');
                    // Redirect to login page
                    window.location.href = '/login';
                } else {
                    console.error('Logout failed:', data.error);
                    // Still redirect to login page
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Logout error:', error);
                // Still redirect to login page
                window.location.href = '/login';
            }
        });
    }
}

function loadUserBalances() {
    fetch('/api/admin/balances')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateUserBalancesDisplay(data.balances);
        } else {
            console.error('Error loading balances:', data.error);
            showError('Ошибка загрузки балансов');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Ошибка загрузки балансов');
    });
}

function updateUserBalancesDisplay(balances) {
    const userBalancesDiv = document.getElementById('user-balances');
    
    if (!balances || Object.keys(balances).length === 0) {
        userBalancesDiv.innerHTML = `
            <div class="text-center text-[#718096] py-4">
                <p>Нет пользователей</p>
            </div>
        `;
        return;
    }
    
    const balancesHtml = Object.entries(balances).map(([username, balance]) => {
        const balanceRub = balance.balance_rub || 0;
        const totalCostRub = balance.total_cost_rub || 0;
        const totalTokens = (balance.total_input_tokens || 0) + (balance.total_output_tokens || 0);
        
        let balanceColor = 'text-green-400';
        if (balanceRub < 0) balanceColor = 'text-red-400';
        else if (balanceRub === 0) balanceColor = 'text-yellow-400';
        
        return `
            <div class="bg-[#242A36] rounded-lg p-4 border-l-4 border-[#DC4918]">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h4 class="text-white font-medium">${username}</h4>
                        <p class="text-sm text-[#A0AEC0]">Модель: ${balance.current_model || 'gpt-4o-mini'}</p>
                    </div>
                    <div class="text-right">
                        <p class="${balanceColor} font-mono font-bold">₽${balanceRub.toFixed(2)}</p>
                        <p class="text-xs text-[#718096]">Общие расходы: ₽${totalCostRub.toFixed(2)}</p>
                    </div>
                </div>
                <div class="flex justify-between text-xs text-[#718096]">
                    <span>Токенов: ${totalTokens.toLocaleString()}</span>
                    <span>Обновлено: ${formatDate(balance.last_updated)}</span>
                </div>
            </div>
        `;
    }).join('');
    
    userBalancesDiv.innerHTML = balancesHtml;
}

function loadUsers() {
    fetch('/api/admin/users')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateUsersSelect(data.users);
        } else {
            console.error('Error loading users:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateUsersSelect(users) {
    const userSelect = document.getElementById('username');
    
    // Clear existing options except the first one
    userSelect.innerHTML = '<option value="" style="background-color: #242A36; color: white;">Выберите пользователя</option>';
    
    Object.keys(users).forEach(username => {
        if (username !== 'admin') { // Don't show admin in the list
            const option = document.createElement('option');
            option.value = username;
            option.textContent = username;
            option.style.backgroundColor = '#242A36';
            option.style.color = 'white';
            userSelect.appendChild(option);
        }
    });
}

// Balance increase form handling
document.getElementById('balance-increase-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const amount = parseFloat(document.getElementById('amount').value);
    const reason = document.getElementById('reason').value || 'Manual balance increase';
    
    if (!username) {
        showFormMessage('error', 'Выберите пользователя');
        return;
    }
    
    if (!amount || amount <= 0) {
        showFormMessage('error', 'Введите корректную сумму');
        return;
    }
    
    try {
        const response = await fetch('/api/admin/balance/increase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, amount_rub: amount, reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showFormMessage('success', `Баланс пользователя ${username} увеличен на ₽${amount.toFixed(2)}`);
            // Reset form
            document.getElementById('balance-increase-form').reset();
            // Reload balances
            loadUserBalances();
        } else {
            showFormMessage('error', data.error || 'Ошибка при пополнении баланса');
        }
    } catch (error) {
        showFormMessage('error', 'Произошла ошибка. Попробуйте еще раз.');
    }
});

function showFormMessage(type, message) {
    const messageDiv = document.getElementById('form-message');
    messageDiv.textContent = message;
    messageDiv.className = `mt-4 p-3 rounded-md ${
        type === 'success' 
            ? 'bg-green-600 text-white' 
            : 'bg-red-600 text-white'
    }`;
    
    // Clear message after 5 seconds
    setTimeout(() => {
        messageDiv.textContent = '';
        messageDiv.className = '';
    }, 5000);
}

function showError(message) {
    const userBalancesDiv = document.getElementById('user-balances');
    userBalancesDiv.innerHTML = `
        <div class="text-center text-red-400 py-4">
            <p>${message}</p>
        </div>
    `;
}

function formatDate(dateString) {
    if (!dateString) return 'Неизвестно';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return 'Неизвестно';
    }
} 