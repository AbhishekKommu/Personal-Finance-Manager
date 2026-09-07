document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.getElementById('authForm');
    const txForm = document.getElementById('txForm');

    // Login / Register Form Handling
    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const isLogin = authForm.dataset.type === 'login';
            const endpoint = isLogin ? '/api/login' : '/api/register';

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();
            if (res.ok) {
                window.location.href = isLogin ? '/dashboard' : '/login';
            } else {
                alert(data.error || 'Operation failed');
            }
        });
    }

    // Dashboard Transaction Operations
    if (txForm) {
        loadTransactions();

        txForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('title').value;
            const amount = document.getElementById('amount').value;
            const type = document.getElementById('type').value;
            const category = document.getElementById('category').value;

            const res = await fetch('/api/transactions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, amount, type, category })
            });

            if (res.ok) {
                txForm.reset();
                loadTransactions();
            }
        });

        document.getElementById('logoutBtn').addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        });
    }
});

async function loadTransactions() {
    const res = await fetch('/api/transactions');
    const data = await res.json();

    // Update Summary Cards
    document.getElementById('totalBalance').textContent = `$${data.summary.balance.toFixed(2)}`;
    document.getElementById('totalIncome').textContent = `+$${data.summary.income.toFixed(2)}`;
    document.getElementById('totalExpense').textContent = `-$${data.summary.expense.toFixed(2)}`;

    // Render Transaction List
    const list = document.getElementById('txList');
    list.innerHTML = '';

    data.transactions.forEach(tx => {
        const li = document.createElement('li');
        li.className = 'tx-item';
        li.innerHTML = `
            <div class="tx-details">
                <strong>${escapeHTML(tx.title)}</strong>
                <span class="tx-category">${escapeHTML(tx.category)} • ${tx.date}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="tx-amount ${tx.type}">
                    ${tx.type === 'income' ? '+' : '-'}$${tx.amount.toFixed(2)}
                </span>
                <button class="btn btn-danger" onclick="deleteTx(${tx.id})">×</button>
            </div>
        `;
        list.appendChild(li);
    });
}

async function deleteTx(id) {
    await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
    loadTransactions();
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag));
}