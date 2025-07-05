// js/contacts.js - Contact management functionality (Full version with table support)

(function() {
    'use strict';
    
    class ContactManager {
        constructor() {
            this.contacts = [];
            this.contactToDelete = null;
            this.deleteModal = null;
            this.deleteContactName = null;
            this.cancelDeleteBtn = null;
            this.confirmDeleteBtn = null;
            this.isTableMode = false;
            
            this.init();
        }

        init() {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.initializeElements();
                    this.setupEventListeners();
                    this.checkAdminAccessAndShowDeleteButtons();
                    this.setupBackupAdminCheck();
                    this.detectMode();
                    
                    // Only load contacts dynamically if we're in dynamic mode
                    if (!this.isTableMode) {
                        this.loadContacts();
                    }
                });
            } else {
                this.initializeElements();
                this.setupEventListeners();
                this.checkAdminAccessAndShowDeleteButtons();
                this.setupBackupAdminCheck();
                this.detectMode();
                
                // Only load contacts dynamically if we're in dynamic mode
                if (!this.isTableMode) {
                    this.loadContacts();
                }
            }
        }

        detectMode() {
            // Check if we have a table with server-rendered contacts or a dynamic grid
            const table = document.querySelector('table tbody');
            const contactRows = document.querySelectorAll('.contact-row');
            
            if (table && contactRows.length > 0) {
                this.isTableMode = true;
                console.log('Contacts: Using server-side table mode');
                this.setupContactRowListeners();
            } else {
                this.isTableMode = false;
                console.log('Contacts: Using dynamic grid mode');
            }
        }

        initializeElements() {
            this.deleteModal = document.getElementById('deleteModal');
            this.deleteContactName = document.getElementById('deleteContactName');
            this.cancelDeleteBtn = document.getElementById('cancelDelete');
            this.confirmDeleteBtn = document.getElementById('confirmDelete');
        }

        setupEventListeners() {
            // Filter and search for dynamic mode
            const applyFiltersBtn = document.getElementById('applyFilters');
            const searchInput = document.getElementById('searchInput');
            
            if (applyFiltersBtn) {
                applyFiltersBtn.addEventListener('click', () => this.loadContacts());
            }
            
            if (searchInput) {
                searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.loadContacts();
                    }
                });
            }

            // Add contact buttons
            const addContactBtn = document.getElementById('addContactBtn');
            const addContactFromEmpty = document.getElementById('addContactFromEmpty');
            
            if (addContactBtn) {
                addContactBtn.addEventListener('click', () => this.addNewContact());
            }
            
            if (addContactFromEmpty) {
                addContactFromEmpty.addEventListener('click', () => this.addNewContact());
            }

            this.setupDeleteModal();
        }

        setupContactRowListeners() {
            // Setup listeners for server-side rendered table rows
            document.querySelectorAll('.contact-row').forEach(row => {
                row.addEventListener('click', (e) => {
                    // Don't navigate if clicking on action buttons, email links, or phone links
                    if (e.target.closest('.action-icon') || 
                        e.target.closest('a[href^="mailto:"]') || 
                        e.target.closest('a[href^="tel:"]')) {
                        return;
                    }
                    
                    const contactId = row.dataset.contactId;
                    if (contactId) {
                        this.viewContact(contactId);
                    }
                });
            });
        }

        addNewContact() {
            // For now, we'll redirect to a contacts form page
            window.location.href = '/contacts/new';
        }

        async loadContacts() {
            // Only used in dynamic mode
            if (this.isTableMode) {
                console.log('Skipping dynamic load - using server-side table');
                return;
            }

            try {
                this.showLoading(true);
                
                const token = localStorage.getItem('access_token');
                if (!token) {
                    console.error('No access token found');
                    window.location.href = '/login';
                    return;
                }

                // Get filter values
                const searchInput = document.getElementById('searchInput');
                const typeFilter = document.getElementById('typeFilter');
                
                const params = new URLSearchParams();
                
                if (searchInput && searchInput.value.trim()) {
                    params.append('search', searchInput.value.trim());
                }
                
                if (typeFilter && typeFilter.value) {
                    params.append('contact_type', typeFilter.value);
                }

                const endpoint = `/api/contacts${params.toString() ? '?' + params.toString() : ''}`;
                console.log('Loading contacts from:', endpoint);
                
                const response = await fetch(endpoint, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                // Handle different response formats
                if (Array.isArray(data)) {
                    this.contacts = data;
                } else if (data.items && Array.isArray(data.items)) {
                    this.contacts = data.items;
                } else if (data.contacts && Array.isArray(data.contacts)) {
                    this.contacts = data.contacts;
                } else {
                    this.contacts = [];
                }

                console.log(`Loaded ${this.contacts.length} contacts`);
                this.renderContacts();
                
            } catch (error) {
                console.error('Error loading contacts:', error);
                this.showError('Failed to load contacts: ' + error.message);
            } finally {
                this.showLoading(false);
            }
        }

        renderContacts() {
            // Only used in dynamic mode
            if (this.isTableMode) {
                console.log('Skipping render - using server-side table');
                return;
            }

            const contactsGrid = document.getElementById('contactsGrid');
            const emptyState = document.getElementById('emptyState');
            
            if (!this.contacts || this.contacts.length === 0) {
                if (contactsGrid) contactsGrid.innerHTML = '';
                if (emptyState) emptyState.classList.remove('hidden');
                return;
            }

            if (emptyState) emptyState.classList.add('hidden');
            
            // Check if we should render as table or cards
            const table = document.querySelector('table tbody');
            if (table) {
                this.renderContactsTable(table);
            } else {
                this.renderContactsGrid(contactsGrid);
            }
        }

        renderContactsTable(tbody) {
            // Render contacts as table rows
            const contactRows = this.contacts.map(contact => this.createContactTableRow(contact)).join('');
            tbody.innerHTML = contactRows;
            this.setupContactRowListeners();
        }

        renderContactsGrid(contactsGrid) {
            // Render contacts as cards
            const contactCards = this.contacts.map(contact => this.createContactCard(contact)).join('');
            if (contactsGrid) contactsGrid.innerHTML = contactCards;
            this.setupContactCardListeners();
        }

        createContactTableRow(contact) {
            const initials = this.getContactInitials(contact);
            const displayName = this.getContactDisplayName(contact);
            const email = contact.email || contact.primary_email || '';
            const phone = contact.phone || contact.home_phone || contact.cell_phone || contact.mobile_phone || '';
            
            return `
                <tr class="hover:bg-gray-50 cursor-pointer contact-row" data-contact-id="${contact.id}">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <div class="flex-shrink-0 h-10 w-10">
                                <div class="h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center">
                                    <span class="text-white font-medium text-sm">
                                        ${initials}
                                    </span>
                                </div>
                            </div>
                            <div class="ml-4">
                                <div class="text-sm font-medium text-gray-900">
                                    ${displayName}
                                </div>
                                <div class="text-sm text-gray-500">
                                    ID: ${contact.id}
                                </div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${contact.is_primary_contact ? 
                            '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Primary</span>' : 
                            (contact.relationship_to_account ? 
                                `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">${contact.relationship_to_account}</span>` : 
                                '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Unknown</span>'
                            )
                        }
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${email ? `<a href="mailto:${email}" class="text-blue-600 hover:text-blue-800" onclick="event.stopPropagation();">${email}</a>` : 'N/A'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${phone ? `<a href="tel:${phone}" class="text-blue-600 hover:text-blue-800" onclick="event.stopPropagation();">${phone}</a>` : 'N/A'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div class="flex items-center space-x-2">
                            <!-- Edit Icon -->
                            <a href="/contacts/${contact.id}/edit" 
                               class="action-icon edit-icon text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50 transition-colors"
                               title="Edit Contact"
                               onclick="event.stopPropagation();">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                            </a>
                            
                            <!-- Delete Icon (Admin Only) -->
                            <button class="action-icon delete-icon text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors hidden"
                                    title="Delete Contact"
                                    data-contact-id="${contact.id}"
                                    data-contact-name="${displayName}"
                                    onclick="event.stopPropagation(); confirmDeleteContact(this);">
                                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }

        createContactCard(contact) {
            const initials = this.getContactInitials(contact);
            const displayName = this.getContactDisplayName(contact);
            
            return `
                <div class="bg-white shadow rounded-lg p-6 cursor-pointer contact-card hover:shadow-lg transition-shadow relative" data-contact-id="${contact.id}">
                    <!-- Action Icons in top-right corner -->
                    <div class="absolute top-4 right-4 flex items-center space-x-2">
                        <!-- Edit Icon -->
                        <a href="/contacts/${contact.id}/edit"
                           class="action-icon edit-icon text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50 transition-colors"
                           title="Edit Contact"
                           onclick="event.stopPropagation();">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                        </a>
                        
                        <!-- Delete Icon (Admin Only) -->
                        <button class="action-icon delete-icon text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors hidden"
                                title="Delete Contact"
                                data-contact-id="${contact.id}"
                                data-contact-name="${displayName}"
                                onclick="event.stopPropagation(); confirmDeleteContact(this);">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                    </div>

                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center">
                                <span class="text-white font-medium text-sm">
                                    ${initials}
                                </span>
                            </div>
                        </div>
                        <div class="ml-4 flex-1 pr-12">
                            <h3 class="text-lg font-medium text-gray-900">
                                ${displayName}
                            </h3>
                            <p class="text-sm text-gray-500">${contact.contact_type || 'Contact'}</p>
                        </div>
                    </div>
                    
                    <div class="mt-4 space-y-2">
                        ${contact.email ? `
                        <div class="flex items-center text-sm text-gray-600">
                            <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            <span class="truncate">${contact.email}</span>
                        </div>
                        ` : ''}
                        
                        ${contact.phone ? `
                        <div class="flex items-center text-sm text-gray-600">
                            <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                            </svg>
                            <span>${contact.phone}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        getContactInitials(contact) {
            const first = contact.first_name || contact.firstname || '';
            const last = contact.last_name || contact.lastname || '';
            
            const firstInitial = first.charAt(0).toUpperCase();
            const lastInitial = last.charAt(0).toUpperCase();
            
            return firstInitial + lastInitial || 'C';
        }

        getContactDisplayName(contact) {
            const first = contact.first_name || contact.firstname || '';
            const last = contact.last_name || contact.lastname || '';
            
            if (first && last) {
                return `${first} ${last}`;
            } else if (first) {
                return first;
            } else if (last) {
                return last;
            } else {
                return contact.display_name || contact.email || 'Unknown Contact';
            }
        }

        setupContactCardListeners() {
            document.querySelectorAll('.contact-card').forEach(card => {
                card.addEventListener('click', (e) => {
                    // Don't navigate if clicking on action buttons
                    if (e.target.closest('.action-icon')) {
                        return;
                    }
                    
                    const contactId = card.dataset.contactId;
                    if (contactId) {
                        this.viewContact(contactId);
                    }
                });
            });
        }

        viewContact(contactId) {
            // Navigate to contact detail page
            window.location.href = `/contacts/${contactId}`;
        }

        editContact(contactId) {
            // Navigate to contact edit page
            window.location.href = `/contacts/${contactId}/edit`;
        }

        setupBackupAdminCheck() {
            // Backup check - force show delete buttons for System Administrator users
            setTimeout(() => {
                const welcomeText = document.body.innerText;
                if (welcomeText.includes('System Administrator')) {
                    this.showDeleteButtons();
                }
            }, 100);
        }

        setupDeleteModal() {
            if (!this.deleteModal) return;

            // Cancel delete
            if (this.cancelDeleteBtn) {
                this.cancelDeleteBtn.addEventListener('click', () => {
                    this.hideDeleteModal();
                });
            }
            
            // Confirm delete
            if (this.confirmDeleteBtn) {
                this.confirmDeleteBtn.addEventListener('click', () => {
                    if (this.contactToDelete) {
                        this.deleteContact(this.contactToDelete);
                    }
                });
            }
            
            // Hide modal when clicking outside
            this.deleteModal.addEventListener('click', (e) => {
                if (e.target === this.deleteModal) {
                    this.hideDeleteModal();
                }
            });
        }

        hideDeleteModal() {
            if (this.deleteModal) {
                this.deleteModal.classList.add('hidden');
            }
            this.contactToDelete = null;
        }

        confirmDeleteContact(button) {
            this.contactToDelete = button.dataset.contactId;
            const contactName = button.dataset.contactName;
            
            if (this.deleteContactName) {
                this.deleteContactName.textContent = contactName;
            }
            
            if (this.deleteModal) {
                this.deleteModal.classList.remove('hidden');
            }
        }

        async deleteContact(contactId) {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) {
                    alert('Authentication required');
                    return;
                }
                
                const response = await fetch(`/api/contacts/${contactId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    if (this.isTableMode) {
                        // Success - reload the page to show updated list
                        location.reload();
                    } else {
                        // Success - reload contacts list dynamically
                        this.loadContacts();
                    }
                } else {
                    const error = await response.json();
                    alert(`Failed to delete contact: ${error.detail || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error deleting contact:', error);
                alert('An error occurred while deleting the contact');
            } finally {
                this.hideDeleteModal();
            }
        }

        showLoading(show) {
            const loadingState = document.getElementById('loadingState');
            const contactsGrid = document.getElementById('contactsGrid');
            const contactsTable = document.querySelector('table');
            
            if (show) {
                if (loadingState) loadingState.classList.remove('hidden');
                if (contactsGrid) contactsGrid.classList.add('opacity-50');
                if (contactsTable) contactsTable.classList.add('opacity-50');
            } else {
                if (loadingState) loadingState.classList.add('hidden');
                if (contactsGrid) contactsGrid.classList.remove('opacity-50');
                if (contactsTable) contactsTable.classList.remove('opacity-50');
            }
        }

        showError(message) {
            console.error(message);
            alert(message);
        }

        async checkAdminAccessAndShowDeleteButtons() {
            try {
                // Check if user has admin access from localStorage first
                const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
                const roles = userInfo.roles || [];
                
                // Check for admin role with multiple variations
                const hasAdminRole = roles.some(role => {
                    if (typeof role === 'string') {
                        return role.toLowerCase() === 'admin' || 
                               role.toLowerCase() === 'administrator' ||
                               role.toLowerCase() === 'system administrator';
                    } else if (typeof role === 'object' && role.name) {
                        return role.name.toLowerCase() === 'admin' || 
                               role.name.toLowerCase() === 'administrator' ||
                               role.name.toLowerCase() === 'system administrator';
                    }
                    return false;
                });
                
                // Also check for explicit admin confirmation
                const adminConfirmed = localStorage.getItem('admin_access_confirmed');
                
                // Check if user is explicitly named as admin
                const isAdminUser = userInfo.username === 'admin' || 
                                   userInfo.username === 'administrator' ||
                                   (userInfo.email && userInfo.email.includes('admin'));
                
                // Check if user is marked as superuser
                const isSuperuser = userInfo.is_superuser === true;
                
                if (hasAdminRole || adminConfirmed === 'true' || isAdminUser || isSuperuser) {
                    this.showDeleteButtons();
                    return;
                }
                
                // Check if page shows System Administrator
                const welcomeText = document.querySelector('body') ? document.querySelector('body').innerText : '';
                const isSystemAdmin = welcomeText.includes('System Administrator');
                
                if (isSystemAdmin) {
                    localStorage.setItem('admin_access_confirmed', 'true');
                    this.showDeleteButtons();
                    return;
                }
                
                // Always show for System Administrator - no API needed
                if (document.body.innerText.includes('System Administrator')) {
                    this.showDeleteButtons();
                    localStorage.setItem('admin_access_confirmed', 'true');
                    return;
                }
                
                // Try API check as fallback
                const token = localStorage.getItem('access_token');
                if (!token) return;
                
                const adminEndpoints = [
                    '/admin/stats',
                    '/api/admin/stats',
                    '/admin/health',
                    '/api/admin/health'
                ];
                
                for (const endpoint of adminEndpoints) {
                    try {
                        const response = await fetch(endpoint, {
                            method: 'GET',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            }
                        });
                        
                        if (response.ok) {
                            this.showDeleteButtons();
                            localStorage.setItem('admin_access_confirmed', 'true');
                            return;
                        }
                    } catch (error) {
                        // Continue to next endpoint
                    }
                }
                
                // Final fallback for System Administrator users
                if (document.body.innerText.includes('System Administrator')) {
                    this.showDeleteButtons();
                    localStorage.setItem('admin_access_confirmed', 'true');
                }
                
            } catch (error) {
                // Fallback - if there's an error, check if user appears to be admin
                try {
                    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
                    if (userInfo.username === 'admin' || document.body.innerText.includes('System Administrator')) {
                        this.showDeleteButtons();
                        localStorage.setItem('admin_access_confirmed', 'true');
                    }
                } catch (e) {
                    // Silent fail
                }
            }
        }

        showDeleteButtons() {
            const deleteButtons = document.querySelectorAll('.delete-icon');
            deleteButtons.forEach(button => {
                button.classList.remove('hidden');
                button.style.display = 'inline-flex';
                button.style.visibility = 'visible';
            });
        }
    }

    // Global function for delete confirmation (called from template)
    window.confirmDeleteContact = function(button) {
        if (window.contactManager) {
            window.contactManager.confirmDeleteContact(button);
        }
    };

    // Initialize only if not already done and make globally available
    if (!window.contactManager) {
        window.contactManager = new ContactManager();
    }

})();