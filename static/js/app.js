// static/js/app.js - Main Application JavaScript (TOOLTIP FIXED VERSION)
class App {
    constructor() {
        this.apiClient = new APIClient();
        this.init();
    }

    init() {
        // Initialize components
        this.initSidebar();
        this.initGlobalEvents();
        // REMOVED: this.initTooltips(); - This was conflicting with CSS tooltips
        
        // Page-specific initialization
        this.initPageSpecific();
    }

    initSidebar() {
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('#sidebarOverlay');

        function toggleMobileSidebar() {
            // This toggles the slide-out menu ONLY for mobile
            if (sidebar) {
                sidebar.classList.toggle('mobile-open');
            }
            if (overlay) {
                overlay.classList.toggle('hidden');
            }
        }

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleMobileSidebar);
        }
        if (overlay) {
            overlay.addEventListener('click', toggleMobileSidebar);
        }
    }

    handleResponsiveSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            if (window.innerWidth <= 768) {
                sidebar.classList.add('sidebar-mobile');
            } else {
                sidebar.classList.remove('sidebar-mobile');
            }
        }
    }

    initGlobalEvents() {
        // Global form handling
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });

        // Global click handling
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('ajax-link')) {
                e.preventDefault();
                this.handleAjaxLink(e.target);
            }
        });
    }

    // REMOVED: initTooltips() method completely to prevent conflicts

    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const method = form.method || 'POST';
        const url = form.action;

        try {
            this.showLoading(form);
            
            const response = await fetch(url, {
                method: method,
                body: formData
            });

            if (response.ok) {
                if (response.headers.get('content-type')?.includes('application/json')) {
                    const data = await response.json();
                    this.handleFormSuccess(form, data);
                } else {
                    window.location.reload();
                }
            } else {
                throw new Error('Form submission failed');
            }
        } catch (error) {
            this.showError('Error submitting form: ' + error.message);
        } finally {
            this.hideLoading(form);
        }
    }

    async handleAjaxLink(link) {
        const url = link.href;
        
        try {
            this.showLoading();
            
            const response = await fetch(url);
            if (response.ok) {
                const html = await response.text();
                this.updatePageContent(html);
            } else {
                throw new Error('Request failed');
            }
        } catch (error) {
            this.showError('Error loading content: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    initPageSpecific() {
        const page = document.body.dataset.page;
        
        switch (page) {
            case 'accounts':
                if (typeof AccountsManager !== 'undefined') {
                    new AccountsManager();
                }
                break;
            case 'loans':
                if (typeof LoansManager !== 'undefined') {
                    new LoansManager();
                }
                break;
            case 'contacts':
                if (typeof ContactsManager !== 'undefined') {
                    new ContactsManager();
                }
                break;
            case 'assets':
                if (typeof AssetsManager !== 'undefined') {
                    new AssetsManager();
                }
                break;
            case 'cases':
                if (typeof CasesManager !== 'undefined') {
                    new CasesManager();
                }
                break;
        }
    }

    showLoading(element = null) {
        if (element) {
            element.classList.add('loading');
        } else {
            const loader = document.getElementById('globalLoader');
            if (loader) loader.classList.remove('hidden');
        }
    }

    hideLoading(element = null) {
        if (element) {
            element.classList.remove('loading');
        } else {
            const loader = document.getElementById('globalLoader');
            if (loader) loader.classList.add('hidden');
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-error fixed top-4 right-4 z-50 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded';
        errorDiv.innerHTML = `
            <span>${message}</span>
            <button class="ml-2 text-red-500 hover:text-red-700" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success fixed top-4 right-4 z-50 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded';
        successDiv.innerHTML = `
            <span>${message}</span>
            <button class="ml-2 text-green-500 hover:text-green-700" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentElement) {
                successDiv.remove();
            }
        }, 5000);
    }

    handleFormSuccess(form, data) {
        if (data.message) {
            this.showSuccess(data.message);
        }
        
        if (data.redirect) {
            window.location.href = data.redirect;
        } else {
            form.reset();
        }
    }

    updatePageContent(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newContent = doc.querySelector('#mainContent');
        const currentContent = document.querySelector('#mainContent');
        
        if (newContent && currentContent) {
            currentContent.innerHTML = newContent.innerHTML;
            this.initPageSpecific();
        }
    }
}

// static/js/api.js - Simplified API Client for Flask
class APIClient {
    constructor() {
        this.baseURL = window.API_BASE_URL || '';
    }

    async request(endpoint, options = {}) {
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN || ''
            },
            ...options
        };

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            if (response.status === 401) {
                window.location.href = '/auth/login';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url);
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US');
}

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