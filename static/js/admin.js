// static/js/admin.js - Enhanced Admin functionality with sub-menu support

class AdminManager {
    constructor() {
        this.currentPage = 1;
        this.perPage = 50;
        this.currentFilters = {};
        this.editingUserId = null;
        this.availableRoles = [];
        this.currentSection = 'dashboard';
        this.sidebarCollapsed = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRoles();
        this.setupSubMenuNavigation();
        // Don't auto-load users since they're loaded server-side initially
        // Only load via AJAX when filters change
    }

    setupSubMenuNavigation() {
        // Set up sub-menu navigation
        const navItems = document.querySelectorAll('.admin-nav-item[data-section]');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');
                this.switchSection(section);
            });
        });

        // Set up sidebar toggle
        const toggleSidebar = document.getElementById('toggleSidebar');
        if (toggleSidebar) {
            toggleSidebar.addEventListener('click', () => this.toggleSidebar());
        }

        // Initialize current section based on URL or default to dashboard
        const urlPath = window.location.pathname;
        if (urlPath.includes('/users')) {
            this.currentSection = 'users';
        } else if (urlPath.includes('/filters')) {
            this.currentSection = 'filters';
        } else if (urlPath.includes('/settings')) {
            this.currentSection = 'settings';
        } else if (urlPath.includes('/logs')) {
            this.currentSection = 'logs';
        } else {
            this.currentSection = 'dashboard';
        }

        this.updateActiveNavItem();
    }

    switchSection(section) {
        // Update navigation
        this.updateActiveNavItem(section);
        
        // Navigate to section
        let url = '/admin/';
        switch(section) {
            case 'users':
                url = '/admin/users';
                break;
            case 'filters':
                url = '/admin/filters';
                break;
            case 'settings':
                url = '/admin/settings';
                break;
            case 'logs':
                url = '/admin/logs';
                break;
            default:
                url = '/admin/';
        }
        
        window.location.href = url;
    }

    updateActiveNavItem(section = null) {
        const activeSection = section || this.currentSection;
        
        // Remove active class from all nav items
        document.querySelectorAll('.admin-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current section
        const activeItem = document.querySelector(`[data-section="${activeSection}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('adminSidebar');
        const mainContent = document.getElementById('adminMainContent');
        
        this.sidebarCollapsed = !this.sidebarCollapsed;
        
        if (this.sidebarCollapsed) {
            sidebar?.classList.add('collapsed');
            mainContent?.classList.add('expanded');
        } else {
            sidebar?.classList.remove('collapsed');
            mainContent?.classList.remove('expanded');
        }
        
        // Save state
        localStorage.setItem('admin_sidebar_collapsed', this.sidebarCollapsed);
    }

    bindEvents() {
        // Add user button
        const addUserBtn = document.getElementById('addUserBtn');
        if (addUserBtn) {
            addUserBtn.addEventListener('click', () => this.openAddUserModal());
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshPage();
            });
        }
        
        // Search and filters
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.currentFilters.search = e.target.value;
                this.currentPage = 1;
                this.loadUsers();
            });
        }
        
        const roleFilter = document.getElementById('roleFilter');
        if (roleFilter) {
            roleFilter.addEventListener('change', (e) => {
                this.currentFilters.role = e.target.value;
                this.currentPage = 1;
                this.loadUsers();
            });
        }
        
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.active_only = e.target.value === 'active' ? true : 
                                                  e.target.value === 'inactive' ? false : null;
                this.currentPage = 1;
                this.loadUsers();
            });
        }
        
        const mfaFilter = document.getElementById('mfaFilter');
        if (mfaFilter) {
            mfaFilter.addEventListener('change', (e) => {
                this.currentFilters.mfa_enabled = e.target.value === 'enabled' ? true : 
                                                  e.target.value === 'disabled' ? false : null;
                this.currentPage = 1;
                this.loadUsers();
            });
        }
        
        // Reset filters
        const resetFilters = document.getElementById('resetFilters');
        if (resetFilters) {
            resetFilters.addEventListener('click', () => {
                this.resetFilters();
            });
        }
        
        // Modal events
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', () => this.closeUserModal());
        }
        
        const cancelBtn = document.getElementById('cancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeUserModal());
        }
        
        const userForm = document.getElementById('userForm');
        if (userForm) {
            userForm.addEventListener('submit', (e) => this.handleUserSubmit(e));
        }
        
        // Password modal events
        const closePasswordModal = document.getElementById('closePasswordModal');
        if (closePasswordModal) {
            closePasswordModal.addEventListener('click', () => this.closePasswordModal());
        }
        
        const cancelPasswordBtn = document.getElementById('cancelPasswordBtn');
        if (cancelPasswordBtn) {
            cancelPasswordBtn.addEventListener('click', () => this.closePasswordModal());
        }
        
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => this.handlePasswordReset(e));
        }
        
        // Close modals on outside click
        const userModal = document.getElementById('userModal');
        if (userModal) {
            userModal.addEventListener('click', (e) => {
                if (e.target.id === 'userModal') this.closeUserModal();
            });
        }
        
        const passwordModal = document.getElementById('passwordModal');
        if (passwordModal) {
            passwordModal.addEventListener('click', (e) => {
                if (e.target.id === 'passwordModal') this.closePasswordModal();
            });
        }

        // Filter management events
        this.bindFilterEvents();
    }

    bindFilterEvents() {
        // Add filter category button
        const addFilterBtn = document.getElementById('addFilterBtn');
        if (addFilterBtn) {
            addFilterBtn.addEventListener('click', () => this.openAddFilterModal());
        }

        // Filter option events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-option-toggle')) {
                const optionId = e.target.getAttribute('data-option-id');
                this.toggleFilterOption(optionId);
            }
            
            if (e.target.classList.contains('filter-option-edit')) {
                const optionId = e.target.getAttribute('data-option-id');
                this.editFilterOption(optionId);
            }
            
            if (e.target.classList.contains('filter-option-delete')) {
                const optionId = e.target.getAttribute('data-option-id');
                this.deleteFilterOption(optionId);
            }
        });
    }

    async makeRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    async loadRoles() {
        try {
            const data = await this.makeRequest('/admin/api/roles');
            this.availableRoles = data.available_roles || [];
            this.populateRoleOptions();
        } catch (error) {
            console.error('Error loading roles:', error);
            // Fallback roles
            this.availableRoles = [
                { name: 'admin', description: 'Administrator' },
                { name: 'user', description: 'Regular User' },
                { name: 'manager', description: 'Manager' }
            ];
            this.populateRoleOptions();
        }
    }

    populateRoleOptions() {
        const roleFilter = document.getElementById('roleFilter');
        const roleCheckboxes = document.querySelector('.role-checkbox-group');
        
        // Populate filter dropdown (skip if already populated)
        if (roleFilter && roleFilter.children.length <= 1) {
            this.availableRoles.forEach(role => {
                const option = document.createElement('option');
                option.value = role.name;
                option.textContent = role.name.charAt(0).toUpperCase() + role.name.slice(1);
                roleFilter.appendChild(option);
            });
        }
        
        // Populate modal checkboxes (skip if already populated)
        if (roleCheckboxes && roleCheckboxes.children.length === 0) {
            this.availableRoles.forEach(role => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <label class="flex items-center">
                        <input type="checkbox" name="roles" value="${role.name}" class="form-checkbox">
                        <span class="ml-2 text-sm text-gray-700">${role.name.charAt(0).toUpperCase() + role.name.slice(1)}</span>
                    </label>
                `;
                roleCheckboxes.appendChild(div);
            });
        }
    }

    async loadStats() {
        try {
            const stats = await this.makeRequest('/admin/api/stats');
            
            const totalUsers = document.getElementById('totalUsers');
            const activeUsers = document.getElementById('activeUsers');
            const mfaUsers = document.getElementById('mfaUsers');
            const lockedUsers = document.getElementById('lockedUsers');
            
            if (totalUsers) totalUsers.textContent = stats.total_users || 0;
            if (activeUsers) activeUsers.textContent = stats.active_users || 0;
            if (mfaUsers) mfaUsers.textContent = stats.mfa_enabled_users || 0;
            if (lockedUsers) lockedUsers.textContent = stats.locked_users || 0;
            
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async loadUsers() {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const usersTable = document.getElementById('usersTable');
        const emptyState = document.getElementById('emptyState');
        
        if (loadingSpinner) loadingSpinner.classList.remove('hidden');
        if (usersTable) usersTable.classList.add('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage
            });
            
            // Add filters
            Object.keys(this.currentFilters).forEach(key => {
                if (this.currentFilters[key] !== null && this.currentFilters[key] !== '') {
                    params.append(key, this.currentFilters[key]);
                }
            });
            
            const response = await this.makeRequest(`/admin/api/users?${params}`);
            
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
            
            if (response.users && response.users.length > 0) {
                this.renderUsers(response.users);
                this.updatePagination(response);
                if (usersTable) usersTable.classList.remove('hidden');
            } else {
                if (emptyState) emptyState.classList.remove('hidden');
            }
            
        } catch (error) {
            console.error('Error loading users:', error);
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
            this.showMessage('Error loading users: ' + error.message, 'error');
        }
    }

    renderUsers(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        const avatarColors = ['blue', 'green', 'purple', 'red', 'yellow', 'indigo'];
        
        users.forEach((user, index) => {
            const row = document.createElement('tr');
            row.className = 'admin-users-table';
            
            const avatarColor = avatarColors[index % avatarColors.length];
            const userInitial = (user.full_name || user.username).charAt(0).toUpperCase();
            
            row.innerHTML = `
                <td>
                    <div class="flex items-center">
                        <div class="user-avatar bg-${avatarColor}">
                            ${userInitial}
                        </div>
                        <div class="ml-3">
                            <div class="text-sm font-medium text-gray-900">${user.full_name || user.username}</div>
                            <div class="text-sm text-gray-500">@${user.username}</div>
                        </div>
                    </div>
                </td>
                <td class="text-sm text-gray-900">${user.email}</td>
                <td>
                    <div class="flex flex-wrap gap-1">
                        ${(user.roles || []).map(role => 
                            `<span class="role-badge ${role}">${role}</span>`
                        ).join('')}
                    </div>
                </td>
                <td>
                    <span class="user-status-badge ${user.is_active ? 'active' : 'inactive'}">
                        <span class="status-indicator ${user.is_active ? 'active' : 'inactive'}"></span>
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    ${user.is_locked ? 
                        '<span class="user-status-badge locked ml-1"><span class="status-indicator locked"></span>Locked</span>' 
                        : ''
                    }
                </td>
                <td>
                    <span class="user-status-badge ${user.mfa_enabled ? 'mfa-enabled' : 'mfa-disabled'}">
                        ${user.mfa_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </td>
                <td class="text-sm text-gray-500">
                    ${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                </td>
                <td>
                    <div class="admin-action-buttons">
                        <button onclick="adminManager.editUser(${user.id})" 
                                class="admin-action-btn edit">
                            Edit
                        </button>
                        <button onclick="adminManager.resetPassword(${user.id})" 
                                class="admin-action-btn reset-password">
                            Reset Password
                        </button>
                        <button onclick="adminManager.resetMFA(${user.id})" 
                                class="admin-action-btn reset-mfa">
                            Reset MFA
                        </button>
                        ${user.is_locked ? 
                            `<button onclick="adminManager.unlockUser(${user.id})" 
                                     class="admin-action-btn unlock">
                                Unlock
                            </button>` : ''
                        }
                        ${!user.is_active ? 
                            `<button onclick="adminManager.activateUser(${user.id})" 
                                     class="admin-action-btn activate">
                                Activate
                            </button>` : 
                            `<button onclick="adminManager.deactivateUser(${user.id})" 
                                     class="admin-action-btn deactivate">
                                Deactivate
                            </button>`
                        }
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updatePagination(response) {
        // This would update pagination controls if you add them
        // For now, just log the pagination info
        console.log('Pagination:', {
            page: response.page,
            total: response.total,
            has_next: response.has_next,
            has_prev: response.has_prev
        });
    }

    resetFilters() {
        this.currentFilters = {};
        this.currentPage = 1;
        
        const searchInput = document.getElementById('searchInput');
        const roleFilter = document.getElementById('roleFilter');
        const statusFilter = document.getElementById('statusFilter');
        const mfaFilter = document.getElementById('mfaFilter');
        
        if (searchInput) searchInput.value = '';
        if (roleFilter) roleFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        if (mfaFilter) mfaFilter.value = '';
        
        this.loadUsers();
    }

    refreshPage() {
        // Refresh the entire page to get server-side rendered data
        window.location.reload();
    }

    // Filter Management Functions
    async loadFilters() {
        try {
            const response = await this.makeRequest('/admin/api/filters/categories');
            this.renderFilters(response);
        } catch (error) {
            console.error('Error loading filters:', error);
            this.showMessage('Error loading filters: ' + error.message, 'error');
        }
    }

    renderFilters(categories) {
        const container = document.getElementById('filtersContainer');
        if (!container) return;
        
        container.innerHTML = categories.map(category => `
            <div class="bg-white rounded-lg shadow p-4 mb-4">
                <div class="flex justify-between items-start mb-3">
                    <div>
                        <h4 class="text-lg font-medium text-gray-900">${category.display_name}</h4>
                        <p class="text-sm text-gray-500">Category: <code class="bg-gray-200 px-2 py-1 rounded">${category.name}</code></p>
                        ${category.description ? `<p class="text-sm text-gray-600 mt-1">${category.description}</p>` : ''}
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${category.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${category.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <button onclick="adminManager.addFilterOption(${category.id})" class="bg-blue-50 hover:bg-blue-100 text-blue-600 text-sm px-3 py-1 rounded-md border border-blue-200">
                            Add Option
                        </button>
                    </div>
                </div>
                
                ${category.options && category.options.length > 0 ? `
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        ${category.options.map(option => `
                            <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 ${!option.is_active ? 'opacity-50' : ''}">
                                <div class="flex justify-between items-start">
                                    <div class="flex-1">
                                        <h5 class="font-medium text-gray-900">${option.display_name}</h5>
                                        <p class="text-sm text-gray-500">Value: <code class="bg-gray-100 px-1 rounded">${option.value}</code></p>
                                        ${option.color_class ? `
                                            <div class="mt-2">
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${option.color_class}">
                                                    Preview
                                                </span>
                                            </div>
                                        ` : ''}
                                    </div>
                                    <div class="flex flex-col space-y-1">
                                        <button class="filter-option-toggle text-xs ${option.is_active ? 'text-yellow-600 hover:text-yellow-800' : 'text-green-600 hover:text-green-800'}" data-option-id="${option.id}">
                                            ${option.is_active ? 'Deactivate' : 'Activate'}
                                        </button>
                                        <button class="filter-option-edit text-xs text-blue-600 hover:text-blue-800" data-option-id="${option.id}">
                                            Edit
                                        </button>
                                        <button class="filter-option-delete text-xs text-red-600 hover:text-red-800" data-option-id="${option.id}">
                                            Delete
                                        </button>
                                    </div>
                                </div>
                                <div class="text-xs text-gray-400 mt-2">
                                    Sort Order: ${option.sort_order}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <p class="text-gray-500 text-center py-4">No options configured for this category.</p>
                `}
            </div>
        `).join('');
    }

    async toggleFilterOption(optionId) {
        try {
            await this.makeRequest(`/admin/api/filters/options/${optionId}/toggle`, {
                method: 'PATCH'
            });
            this.showMessage('Filter option updated successfully', 'success');
            this.loadFilters();
        } catch (error) {
            this.showMessage('Error updating filter option: ' + error.message, 'error');
        }
    }

    addFilterOption(categoryId) {
        // Implement add filter option modal
        this.showMessage('Add filter option functionality - implement modal', 'info');
    }

    editFilterOption(optionId) {
        // Implement edit filter option modal
        this.showMessage('Edit filter option functionality - implement modal', 'info');
    }

    async deleteFilterOption(optionId) {
        if (confirm('Are you sure you want to delete this filter option?')) {
            try {
                await this.makeRequest(`/admin/api/filters/options/${optionId}`, {
                    method: 'DELETE'
                });
                this.showMessage('Filter option deleted successfully', 'success');
                this.loadFilters();
            } catch (error) {
                this.showMessage('Error deleting filter option: ' + error.message, 'error');
            }
        }
    }

    // User Management Functions (existing)
    openAddUserModal() {
        this.editingUserId = null;
        const modalTitle = document.getElementById('modalTitle');
        const passwordGroup = document.getElementById('passwordGroup');
        const password = document.getElementById('password');
        
        if (modalTitle) modalTitle.textContent = 'Add New User';
        if (passwordGroup) passwordGroup.style.display = 'block';
        if (password) password.required = true;
        
        // Reset form
        const userForm = document.getElementById('userForm');
        const isActive = document.getElementById('isActive');
        
        if (userForm) userForm.reset();
        if (isActive) isActive.checked = true;
        
        // Uncheck all roles
        document.querySelectorAll('input[name="roles"]').forEach(cb => cb.checked = false);
        
        const userModal = document.getElementById('userModal');
        if (userModal) userModal.classList.remove('hidden');
    }

    async editUser(userId) {
        this.editingUserId = userId;
        const modalTitle = document.getElementById('modalTitle');
        const passwordGroup = document.getElementById('passwordGroup');
        const password = document.getElementById('password');
        
        if (modalTitle) modalTitle.textContent = 'Edit User';
        if (passwordGroup) passwordGroup.style.display = 'none';
        if (password) password.required = false;
        
        try {
            const user = await this.makeRequest(`/admin/api/users/${userId}`);
            
            // Populate form
            const username = document.getElementById('username');
            const email = document.getElementById('email');
            const firstName = document.getElementById('firstName');
            const lastName = document.getElementById('lastName');
            const isActive = document.getElementById('isActive');
            
            if (username) username.value = user.username || '';
            if (email) email.value = user.email || '';
            if (firstName) firstName.value = user.first_name || '';
            if (lastName) lastName.value = user.last_name || '';
            if (isActive) isActive.checked = user.is_active;
            
            // Set roles
            document.querySelectorAll('input[name="roles"]').forEach(cb => {
                cb.checked = (user.roles || []).includes(cb.value);
            });
            
            const userModal = document.getElementById('userModal');
            if (userModal) userModal.classList.remove('hidden');
        } catch (error) {
            this.showMessage('Error loading user: ' + error.message, 'error');
        }
    }

    closeUserModal() {
        const userModal = document.getElementById('userModal');
        const userForm = document.getElementById('userForm');
        
        if (userModal) userModal.classList.add('hidden');
        if (userForm) userForm.reset();
        this.editingUserId = null;
    }

    async handleUserSubmit(e) {
        e.preventDefault();
        
        const saveBtn = document.getElementById('saveBtn');
        const saveText = document.getElementById('saveText');
        const savingText = document.getElementById('savingText');
        
        if (saveBtn) saveBtn.disabled = true;
        if (saveText) saveText.classList.add('hidden');
        if (savingText) savingText.classList.remove('hidden');
        
        try {
            const formData = new FormData(e.target);
            const roles = Array.from(document.querySelectorAll('input[name="roles"]:checked'))
                              .map(cb => cb.value);
            
            const userData = {
                username: formData.get('username'),
                email: formData.get('email'),
                first_name: formData.get('first_name'),
                last_name: formData.get('last_name'),
                role_names: roles,
                is_active: formData.get('is_active') === 'on'
            };
            
            if (!this.editingUserId) {
                // Adding new user
                userData.password = formData.get('password');
                await this.makeRequest('/admin/api/users', {
                    method: 'POST',
                    body: JSON.stringify(userData)
                });
            } else {
                // Editing existing user
                await this.makeRequest(`/admin/api/users/${this.editingUserId}`, {
                    method: 'PUT',
                    body: JSON.stringify(userData)
                });
            }
            
            this.closeUserModal();
            this.loadUsers();
            this.loadStats();
            this.showMessage('User saved successfully', 'success');
            
        } catch (error) {
            this.showMessage('Error saving user: ' + error.message, 'error');
        } finally {
            if (saveBtn) saveBtn.disabled = false;
            if (saveText) saveText.classList.remove('hidden');
            if (savingText) savingText.classList.add('hidden');
        }
    }

    resetPassword(userId) {
        const resetUserId = document.getElementById('resetUserId');
        const passwordModal = document.getElementById('passwordModal');
        
        if (resetUserId) resetUserId.value = userId;
        if (passwordModal) passwordModal.classList.remove('hidden');
    }

    closePasswordModal() {
        const passwordModal = document.getElementById('passwordModal');
        const passwordForm = document.getElementById('passwordForm');
        
        if (passwordModal) passwordModal.classList.add('hidden');
        if (passwordForm) passwordForm.reset();
    }

    async handlePasswordReset(e) {
        e.preventDefault();
        
        const resetUserId = document.getElementById('resetUserId');
        const newPassword = document.getElementById('newPassword');
        const forceChange = document.getElementById('forceChangeOnLogin');
        
        const userId = resetUserId ? resetUserId.value : null;
        
        if (!userId) return;
        
        try {
            await this.makeRequest(`/admin/api/users/${userId}/reset-password`, {
                method: 'POST',
                body: JSON.stringify({
                    new_password: newPassword ? newPassword.value : '',
                    force_change_on_login: forceChange ? forceChange.checked : true
                })
            });
            
            this.closePasswordModal();
            this.showMessage('Password reset successfully', 'success');
            this.loadUsers();
            
        } catch (error) {
            this.showMessage('Error resetting password: ' + error.message, 'error');
        }
    }

    async resetMFA(userId) {
        if (confirm('Are you sure you want to reset MFA for this user? They will need to set up MFA again.')) {
            try {
                await this.makeRequest(`/admin/api/users/${userId}/reset-mfa`, {
                    method: 'POST'
                });
                this.showMessage('MFA reset successfully', 'success');
                this.loadUsers();
                this.loadStats();
            } catch (error) {
                this.showMessage('Error resetting MFA: ' + error.message, 'error');
            }
        }
    }

    async unlockUser(userId) {
        try {
            await this.makeRequest(`/admin/api/users/${userId}/unlock`, {
                method: 'POST'
            });
            this.showMessage('User unlocked successfully', 'success');
            this.loadUsers();
            this.loadStats();
        } catch (error) {
            this.showMessage('Error unlocking user: ' + error.message, 'error');
        }
    }

    async activateUser(userId) {
        try {
            await this.makeRequest(`/admin/api/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify({ is_active: true })
            });
            this.loadUsers();
            this.loadStats();
        } catch (error) {
            this.showMessage('Error activating user: ' + error.message, 'error');
        }
    }

    async deactivateUser(userId) {
        if (confirm('Are you sure you want to deactivate this user?')) {
            try {
                await this.makeRequest(`/admin/api/users/${userId}`, {
                    method: 'PUT',
                    body: JSON.stringify({ is_active: false })
                });
                this.loadUsers();
                this.loadStats();
            } catch (error) {
                this.showMessage('Error deactivating user: ' + error.message, 'error');
            }
        }
    }

    showMessage(message, type = 'info') {
        // Create a simple toast message
        const toast = document.createElement('div');
        toast.className = `admin-message ${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Initialize section-specific functionality
    initializeSection() {
        switch(this.currentSection) {
            case 'users':
                this.loadStats();
                break;
            case 'filters':
                this.loadFilters();
                break;
            case 'settings':
                this.loadSystemSettings();
                break;
            case 'logs':
                this.loadAuditLogs();
                break;
            default:
                this.loadStats();
        }
    }

    async loadSystemSettings() {
        try {
            const response = await this.makeRequest('/admin/api/system-settings');
            this.renderSystemSettings(response);
        } catch (error) {
            console.error('Error loading system settings:', error);
        }
    }

    async loadAuditLogs() {
        try {
            const response = await this.makeRequest('/admin/api/audit-logs');
            this.renderAuditLogs(response);
        } catch (error) {
            console.error('Error loading audit logs:', error);
        }
    }

    renderSystemSettings(settings) {
        const container = document.getElementById('systemSettingsContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">System Configuration</h3>
                <p class="text-gray-600">System settings functionality will be implemented here.</p>
                <pre class="mt-4 bg-gray-100 p-4 rounded text-sm">${JSON.stringify(settings, null, 2)}</pre>
            </div>
        `;
    }

    renderAuditLogs(logs) {
        const container = document.getElementById('auditLogsContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Audit Trail</h3>
                <p class="text-gray-600">Audit logs functionality will be implemented here.</p>
                <pre class="mt-4 bg-gray-100 p-4 rounded text-sm">${JSON.stringify(logs, null, 2)}</pre>
            </div>
        `;
    }
}

// Initialize admin manager
let adminManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    adminManager = new AdminManager();
    
    // Initialize section-specific functionality
    adminManager.initializeSection();
    
    // Restore sidebar state
    const sidebarCollapsed = localStorage.getItem('admin_sidebar_collapsed') === 'true';
    if (sidebarCollapsed) {
        adminManager.toggleSidebar();
    }
});