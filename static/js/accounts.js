// static/js/accounts.js

class AccountManager {
    constructor() {
        this.accounts = [];
        this.editingAccount = null;
        this.currentAccountId = null;
        this.currentAccountData = null;
        // It's a good practice to define the base URL in a configurable way
        this.baseUrl = 'http://127.0.0.1:8000'; 
        this.init();
    }

    init() {
        // This runs when the page loads. It binds all the event listeners.
        this.bindEvents();
        
        // Load initial accounts if we are on the accounts index page.
        if (document.getElementById('accountsTableBody')) {
            this.loadAccounts();
        }
        
        // Initialize detail page specific functionality
        this.initializeNoteTagModal();
    }

    bindEvents() {
        // Safely add event listeners to elements that might not exist on every page.
        const addEventListenerSafe = (id, event, handler) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener(event, handler.bind(this));
            }
        };

        // --- Event bindings for the Accounts Index Page ---
        addEventListenerSafe('searchInput', 'input', this.debounce(() => this.loadAccounts(), 300));
        addEventListenerSafe('typeFilter', 'change', () => this.loadAccounts());
        addEventListenerSafe('statusFilter', 'change', () => this.loadAccounts());
        addEventListenerSafe('activeFilter', 'change', () => this.loadAccounts());
        addEventListenerSafe('resetFilters', 'click', this.resetFilters);
        
        // --- Event bindings for Modals (e.g., Add Account) ---
        addEventListenerSafe('addAccountBtn', 'click', this.openAddModal);
        addEventListenerSafe('closeModal', 'click', this.closeModal);
        addEventListenerSafe('cancelBtn', 'click', this.closeModal);
        addEventListenerSafe('accountForm', 'submit', this.handleSubmit);

        // Add event listener to close modal on overlay click
        const modal = document.getElementById('accountModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                // If the click is on the dark background, close the modal
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }
    }
    
    initializeNoteTagModal() {
        const noteTagModal = document.getElementById('noteTagModal');
        if (!noteTagModal) return; // Only run this code on the detail page

        const modalTitle = document.getElementById('modalTitle');
        const noteTagForm = document.getElementById('noteTagForm');
        const formType = document.getElementById('formType');
        
        const tagInputContainer = document.getElementById('tagInputContainer');
        const noteInputContainer = document.getElementById('noteInputContainer');

        const addNoteBtn = document.getElementById('addNoteBtn');
        const addTagBtn = document.getElementById('addTagBtn');
        
        const cancelModalBtn = document.getElementById('cancelModal');
        
        const openModal = (type) => {
            if (!noteTagModal || !modalTitle || !tagInputContainer || !noteInputContainer || !formType) return;
            formType.value = type;
            if (type === 'note') {
                modalTitle.textContent = 'Add Note';
                noteInputContainer.style.display = 'block';
                tagInputContainer.style.display = 'none';
            } else {
                modalTitle.textContent = 'Add Tag';
                noteInputContainer.style.display = 'none';
                tagInputContainer.style.display = 'block';
            }
            noteTagModal.classList.remove('hidden');
        }

        const closeModal = () => {
            if (!noteTagModal) return;
            noteTagModal.classList.add('hidden');
            if (noteTagForm) noteTagForm.reset();
        }

        if (addNoteBtn) {
            addNoteBtn.addEventListener('click', () => openModal('note'));
        }

        if (addTagBtn) {
            addTagBtn.addEventListener('click', () => openModal('tag'));
        }

        if (cancelModalBtn) {
            cancelModalBtn.addEventListener('click', closeModal);
        }
        
        noteTagModal.addEventListener('click', (e) => {
            if (e.target === noteTagModal) {
                closeModal();
            }
        });

        if(noteTagForm){
            noteTagForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                const type = formType.value;
                const contentEl = type === 'note' ? document.getElementById('noteContent') : document.getElementById('tagContent');
                const content = contentEl ? contentEl.value : '';

                if (!content.trim()) {
                    alert('Content cannot be empty.');
                    return;
                }
                
                alert(`Saving ${type}: "${content}" (Backend API call needs to be implemented)`);
                console.log(`Submitting ${type} to backend is not yet implemented.`);
                closeModal();
            });
        }
    }


    // --- UTILITY METHODS ---

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    showLoading(isLoading) {
        const spinner = document.getElementById('loadingSpinner');
        const table = document.getElementById('accountsTable');
        if (spinner && table) {
            spinner.classList.toggle('hidden', !isLoading);
            table.classList.toggle('hidden', isLoading);
        }
    }

    // --- API REQUEST HANDLING ---

    async apiRequest(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/frontend/login.html'; 
            throw new Error('No authentication token found.');
        }

        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            ...options,
        };
        
        if (config.body && typeof config.body !== 'string') {
            config.body = JSON.stringify(config.body);
        }

        const response = await fetch(`${this.baseUrl}/api${endpoint}`, config);

        if (response.status === 401) {
            localStorage.clear();
            window.location.href = '/frontend/login.html';
            throw new Error('Session expired. Please log in again.');
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API request failed with status: ${response.statusText}`);
        }
        
        return response.json();
    }

    // --- DATA LOADING AND RENDERING (Accounts Index Page) ---

    async loadAccounts() {
        this.showLoading(true);
        try {
            const params = new URLSearchParams();
            
            const searchValue = document.getElementById('searchInput')?.value?.trim();
            if (searchValue) params.append('search', searchValue);
            
            const typeValue = document.getElementById('typeFilter')?.value;
            if (typeValue) params.append('account_type', typeValue);
            
            const statusValue = document.getElementById('statusFilter')?.value;
            if (statusValue) params.append('status', statusValue);
            
            const activeValue = document.getElementById('activeFilter')?.value;
            if (activeValue) params.append('is_active', activeValue);

            params.append('skip', '0');
            params.append('limit', '100');

            const queryString = params.toString();
            const endpoint = `/accounts/${queryString ? '?' + queryString : ''}`;
            
            const response = await this.apiRequest(endpoint);
            this.accounts = response.items || [];
            this.renderAccounts();

        } catch (error) {
            console.error('Error loading accounts:', error);
            this.showError('Failed to load accounts: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    renderAccounts() {
        const tbody = document.getElementById('accountsTableBody');
        const accountsTable = document.getElementById('accountsTable');
        const emptyState = document.getElementById('emptyState');

        if (!tbody) return;

        tbody.innerHTML = '';

        if (!this.accounts || this.accounts.length === 0) {
            if (accountsTable) accountsTable.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }
        
        if (accountsTable) accountsTable.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        
        this.accounts.forEach(account => {
            const row = document.createElement('tr');
            row.className = "hover:bg-gray-50 cursor-pointer";
            row.innerHTML = `
                <td class="table-cell">${this.escapeHtml(account.account_number || '')}</td>
                <td class="table-cell font-medium text-gray-900">
                    <a href="/accounts/${account.id}" class="text-blue-600 hover:text-blue-800 hover:underline">
                        ${this.escapeHtml(account.account_name || '')}
                    </a>
                </td>
                <td class="table-cell">${this.escapeHtml(account.account_type || '')}</td>
                <td class="table-cell">${this.escapeHtml(account.primary_email || '')}</td>
                <td class="table-cell">${this.escapeHtml(account.home_phone || '')}</td>
                <td class="table-cell"><span class="badge ${this.getStatusBadgeClass(account.status)}">${this.escapeHtml(account.status || '')}</span></td>
                <td class="table-cell">
                    <div class="flex space-x-2">
                        <a href="/accounts/${account.id}/edit" class="text-green-600 hover:text-green-800" title="Edit">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        </a>
                        <button class="text-red-600 hover:text-red-800" onclick="window.deleteAccount(${account.id})" title="Delete">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                        </button>
                    </div>
                </td>
            `;
            
            row.addEventListener('click', (e) => {
                if (!e.target.closest('button') && !e.target.closest('a')) {
                    window.location.href = `/accounts/${account.id}`;
                }
            });
            
            tbody.appendChild(row);
        });
    }

    // --- MODAL AND FORM HANDLING ---
    
    openAddModal() {
        this.editingAccount = null;
        this.clearForm();
        document.getElementById('modalTitle').textContent = 'Add New Account';
        document.getElementById('saveText').textContent = 'Save Account';
        document.getElementById('accountModal').classList.remove('hidden');
    }
    
    clearForm() {
        const form = document.getElementById('accountForm');
        if (form) form.reset();
    }

    closeModal() {
        document.getElementById('accountModal').classList.add('hidden');
        this.editingAccount = null;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const saveBtn = document.getElementById('saveBtn');
        const saveText = document.getElementById('saveText');
        const savingText = document.getElementById('savingText');
        
        if (saveBtn) saveBtn.disabled = true;
        if (saveText) saveText.classList.add('hidden');
        if (savingText) savingText.classList.remove('hidden');

        try {
            const formData = new FormData(e.target);
            const accountData = {};
            for (let [key, value] of formData.entries()) {
                accountData[key] = value || null;
            }

            const response = await this.apiRequest('/accounts/', {
                method: 'POST',
                body: accountData
            });

            this.closeModal();
            await this.loadAccounts();
            this.showSuccess('Account created successfully!');

        } catch (error) {
            console.error('Error saving account:', error);
            this.showError('Failed to save account: ' + error.message);
        } finally {
            if (saveBtn) saveBtn.disabled = false;
            if (saveText) saveText.classList.remove('hidden');
            if (savingText) savingText.classList.add('hidden');
        }
    }
    
    resetFilters() {
        const filterIds = ['searchInput', 'typeFilter', 'statusFilter', 'activeFilter'];
        filterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });
        this.loadAccounts();
    }

    // --- HELPER FUNCTIONS ---

    getStatusBadgeClass(status) {
        const s = (status || '').toLowerCase();
        if (s === 'active') return 'badge-success';
        if (s === 'inactive') return 'badge-secondary';
        if (s === 'pending') return 'badge-warning';
        return 'badge-secondary';
    }

    escapeHtml(text) {
        if (text === null || typeof text === 'undefined') return '';
        return text.toString().replace(/[&<>"']/g, m => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        })[m]);
    }
    
    showError(message) { 
        console.error(message);
        alert(`Error: ${message}`); 
    }

    showSuccess(message) {
        alert(message);
    }
}

// --- GLOBAL FUNCTIONS ---

window.deleteAccount = async function(accountId) {
    if (!confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            alert('Authentication error. Please log in again.');
            return;
        }
        
        const response = await fetch(`http://127.0.0.1:8000/api/accounts/${accountId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            alert('Account deleted successfully!');
            if (window.accountManager) {
                window.accountManager.loadAccounts();
            }
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to delete account.');
        }
    } catch (error) {
        console.error('Error deleting account:', error);
        alert('Failed to delete account. ' + error.message);
    }
};

function openAddAccountModal() {
    if (window.accountManager) {
        window.accountManager.openAddModal();
    }
}

// --- INITIALIZATION ---

document.addEventListener('DOMContentLoaded', () => {
    window.accountManager = new AccountManager();
});
