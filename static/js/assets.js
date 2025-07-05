// js/assets.js - Enhanced version with debug functionality

(function() {
    'use strict';

    /**
     * Manages client-side interactions on the assets page, including delete actions, 
     * card clicks, admin checks, form handling, debug functionality, and asset-specific calculations.
     */
    class AssetManager {
        constructor() {
            // Properties for delete modal management
            this.assetToDelete = null;
            this.deleteModal = document.getElementById('deleteModal');
            this.deleteAssetName = document.getElementById('deleteAssetName');
            this.cancelDeleteBtn = document.getElementById('cancelDelete');
            this.confirmDeleteBtn = document.getElementById('confirmDelete');
            
            // Debug functionality
            this.debugToggle = document.getElementById('debugToggle');
            
            // Current page context
            this.currentPath = window.location.pathname;
        }

        /**
         * Initializes the asset manager by setting up event listeners and performing initial checks.
         */
        init() {
            console.log('🚗 Initializing Asset Manager:', this.currentPath);
            
            this.setupEventListeners();
            this.setupDebugFunctionality();
            this.checkAdminAccessAndShowDeleteButtons();
            this.initializePageSpecificFeatures();
            
            console.log('✅ Asset Manager initialized successfully');
        }

        /**
         * Set up debug functionality
         */
        setupDebugFunctionality() {
            console.log('🔍 Setting up debug functionality');
            
            if (this.debugToggle) {
                console.log('🔍 Debug toggle found, adding event listener');
                this.debugToggle.addEventListener('change', (e) => {
                    console.log('🔍 Debug toggle changed:', e.target.checked);
                    this.handleDebugToggle(e.target.checked);
                });
            } else {
                console.warn('⚠️ Debug toggle not found in DOM');
            }
            
            // Add debug logging for current search parameters
            this.logCurrentSearchState();
        }

        /**
         * Handle debug toggle change
         */
        handleDebugToggle(isEnabled) {
            const url = new URL(window.location);
            
            if (isEnabled) {
                url.searchParams.set('debug', '1');
                console.log('🔍 Enabling debug mode');
            } else {
                url.searchParams.delete('debug');
                console.log('🔍 Disabling debug mode');
            }
            
            console.log('🔍 Redirecting to:', url.toString());
            window.location.href = url.toString();
        }

        /**
         * Log current search state for debugging
         */
        logCurrentSearchState() {
            const urlParams = new URLSearchParams(window.location.search);
            const searchValue = document.getElementById('search')?.value || '';
            const makeValue = document.getElementById('make')?.value || '';
            const statusValue = document.getElementById('status')?.value || '';
            
            console.log('🔍 Current Search State:', {
                url: window.location.href,
                searchParam: urlParams.get('search'),
                makeParam: urlParams.get('make'),
                statusParam: urlParams.get('status'),
                debugParam: urlParams.get('debug'),
                searchInputValue: searchValue,
                makeInputValue: makeValue,
                statusInputValue: statusValue
            });

            // Log asset information visible on page
            const assetRows = document.querySelectorAll('.asset-row');
            console.log(`🔍 Found ${assetRows.length} asset rows on page`);
            
            if (assetRows.length > 0) {
                console.log('🔍 First few assets:');
                Array.from(assetRows).slice(0, 3).forEach((row, index) => {
                    const assetId = row.dataset.assetId;
                    const vinCell = row.querySelector('td:nth-child(2)');
                    const vehicleCell = row.querySelector('td:nth-child(1)');
                    
                    console.log(`  Asset ${index + 1}:`, {
                        id: assetId,
                        vehicle: vehicleCell?.textContent?.trim(),
                        vin: vinCell?.textContent?.trim()
                    });
                });
            }
        }

        /**
         * Initialize features based on the current page type
         */
        initializePageSpecificFeatures() {
            if (this.currentPath.includes('/assets')) {
                if (this.currentPath.match(/\/assets\/\d+\/edit$/)) {
                    this.initializeAssetForm('edit');
                } else if (this.currentPath.endsWith('/assets/new')) {
                    this.initializeAssetForm('new');
                } else if (this.currentPath.match(/\/assets\/\d+$/)) {
                    this.initializeAssetDetail();
                } else if (this.currentPath.endsWith('/assets')) {
                    this.initializeAssetsIndex();
                }
            }
        }

        /**
         * Sets up all necessary event listeners for the page.
         */
        setupEventListeners() {
            // Add listeners to make asset cards AND table rows clickable for navigation.
            // Handle both .asset-card (grid layout) and .asset-row (table layout)
            document.querySelectorAll('.asset-card, .asset-row').forEach(element => {
                element.addEventListener('click', (e) => {
                    // Prevent navigation if an action button within the element was clicked.
                    if (e.target.closest('button, a, .action-icon')) {
                        return;
                    }
                    
                    // FIXED: Use proper dataset access for kebab-case data attributes
                    const assetId = element.dataset.assetId || element.getAttribute('data-asset-id');
                    
                    console.log('🔍 Asset clicked:', {
                        element: element.tagName,
                        classList: element.className,
                        assetId: assetId,
                        dataAttributes: element.dataset
                    });
                    
                    if (assetId) {
                        console.log(`🚗 Navigating to asset ${assetId}`);
                        window.location.href = `/assets/${assetId}`;
                    } else {
                        console.error('❌ No asset ID found on clicked element:', element);
                    }
                });
            });

            // Set up listeners for the delete confirmation modal.
            if (this.cancelDeleteBtn) {
                this.cancelDeleteBtn.addEventListener('click', () => this.hideDeleteModal());
            }

            if (this.confirmDeleteBtn) {
                this.confirmDeleteBtn.addEventListener('click', () => {
                    if (this.assetToDelete) {
                        this.deleteAsset(this.assetToDelete);
                    }
                });
            }

            // Allow closing the modal by clicking on the background overlay.
            if (this.deleteModal) {
                this.deleteModal.addEventListener('click', (e) => {
                    if (e.target === this.deleteModal) {
                        this.hideDeleteModal();
                    }
                });
            }

            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

            // Add search form debugging
            this.setupSearchFormDebugging();
        }

        /**
         * Set up search form debugging
         */
        setupSearchFormDebugging() {
            const searchForm = document.querySelector('form');
            const searchInput = document.getElementById('search');
            
            if (searchForm) {
                searchForm.addEventListener('submit', (e) => {
                    const formData = new FormData(searchForm);
                    const searchParams = new URLSearchParams(formData);
                    
                    console.log('🔍 Form submission:', {
                        action: searchForm.action || 'current page',
                        method: searchForm.method || 'GET',
                        formData: Object.fromEntries(formData),
                        searchParams: searchParams.toString(),
                        url: `${window.location.pathname}?${searchParams.toString()}`
                    });
                    
                    // Don't prevent the submission, just log it
                });
            }
            
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    const value = e.target.value;
                    if (value.length > 3) {
                        console.log('🔍 Search input:', {
                            value: value,
                            length: value.length,
                            isVINLike: this.isVINLike(value),
                            isYearLike: this.isYearLike(value)
                        });
                    }
                });
            }
        }

        /**
         * Check if value looks like a VIN
         */
        isVINLike(value) {
            const cleanValue = value.replace(/[^A-Z0-9]/gi, '');
            return cleanValue.length >= 8 && 
                   cleanValue.length <= 17 && 
                   /^[A-HJ-NPR-Z0-9]+$/i.test(cleanValue);
        }

        /**
         * Check if value looks like a year
         */
        isYearLike(value) {
            const year = parseInt(value);
            return value.length === 4 && 
                   year >= 1900 && 
                   year <= new Date().getFullYear() + 2;
        }

        // ===== PAGE-SPECIFIC INITIALIZATION =====

        /**
         * Initialize the assets index page
         */
        initializeAssetsIndex() {
            console.log('🚗 Initializing Assets Index Page');
            
            // Debug: Check which layout we're using and log asset IDs
            const cards = document.querySelectorAll('.asset-card');
            const rows = document.querySelectorAll('.asset-row');
            
            console.log(`Assets page layout: ${cards.length} cards, ${rows.length} rows`);
            
            // Debug: Log first few asset IDs
            [...cards, ...rows].slice(0, 5).forEach((element, index) => {
                const assetId = element.dataset.assetId || element.getAttribute('data-asset-id');
                console.log(`Asset ${index + 1}: ID = ${assetId}`);
            });
            
            // Check if debug mode is enabled
            const isDebugMode = new URLSearchParams(window.location.search).get('debug') === '1';
            console.log('🔍 Debug mode enabled:', isDebugMode);
            
            if (isDebugMode && this.debugToggle && !this.debugToggle.checked) {
                console.log('🔍 Debug mode in URL but toggle not checked, updating toggle');
                this.debugToggle.checked = true;
            }
            
            console.log('✅ Assets Index Page initialized');
        }

        /**
         * Initialize the asset detail page
         */
        initializeAssetDetail() {
            console.log('🚗 Initializing Asset Detail Page');
            
            // Check for detail-specific delete button
            const deleteAssetBtn = document.querySelector('.delete-asset-btn');
            if (deleteAssetBtn) {
                deleteAssetBtn.addEventListener('click', (e) => {
                    const assetId = e.target.dataset.assetId || e.target.getAttribute('data-asset-id');
                    const assetName = e.target.dataset.assetName || e.target.getAttribute('data-asset-name');
                    this.showDeleteConfirmation(assetId, assetName);
                });
            }
            
            console.log('✅ Asset Detail Page initialized');
        }

        /**
         * Initialize asset form (new/edit) functionality
         */
        initializeAssetForm(mode = 'new') {
            console.log(`🚗 Initializing Asset Form Page (${mode})`);
            
            // Initialize auto-calculation for equity
            this.initializeEquityCalculator();
            
            // Initialize form validation
            this.initializeAssetFormValidation();
            
            // Initialize VIN auto-uppercase
            this.initializeVinFormatting();
            
            console.log('✅ Asset Form Page initialized');
        }

        // ===== EQUITY CALCULATOR =====

        /**
         * Set up automatic equity calculation when value or loan balance changes
         */
        initializeEquityCalculator() {
            const valueInput = document.querySelector('input[name="value"]');
            const loanBalanceInput = document.querySelector('input[name="loan_balance"]');
            const equityDisplay = document.getElementById('equityDisplay');

            if (!valueInput || !loanBalanceInput) {
                return; // Not on a form page with equity calculation
            }

            const calculateEquity = () => {
                const value = parseFloat(valueInput.value) || 0;
                const loanBalance = parseFloat(loanBalanceInput.value) || 0;
                const equity = value - loanBalance;
                
                if (equityDisplay) {
                    equityDisplay.textContent = this.formatCurrency(equity);
                    
                    // Color coding
                    if (equity > 0) {
                        equityDisplay.className = 'text-lg font-bold text-green-600';
                    } else if (equity < 0) {
                        equityDisplay.className = 'text-lg font-bold text-red-600';
                    } else {
                        equityDisplay.className = 'text-lg font-bold text-gray-900';
                    }
                }
            };

            // Add event listeners for auto-calculation
            [valueInput, loanBalanceInput].forEach(input => {
                if (input) {
                    input.addEventListener('input', this.debounce(calculateEquity, 300));
                    input.addEventListener('blur', calculateEquity);
                }
            });
            
            // Calculate on page load
            calculateEquity();
        }

        // ===== VIN FORMATTING =====

        /**
         * Auto-uppercase VIN input
         */
        initializeVinFormatting() {
            const vinInput = document.getElementById('VIN');
            if (vinInput) {
                vinInput.addEventListener('input', function() {
                    this.value = this.value.toUpperCase();
                });
            }
        }

        // ===== FORM VALIDATION =====

        /**
         * Set up form validation for asset forms
         */
        initializeAssetFormValidation() {
            const form = document.querySelector('form');
            if (!form) return;

            form.addEventListener('submit', (e) => {
                const requiredFields = ['Year', 'Make', 'Model', 'VIN'];
                let isValid = true;

                requiredFields.forEach(fieldName => {
                    const field = document.getElementById(fieldName);
                    if (field && !field.value.trim()) {
                        e.preventDefault();
                        this.showErrorMessage(`${fieldName} is required`);
                        field.focus();
                        isValid = false;
                        return false;
                    }
                });

                // Validate year
                const yearField = document.getElementById('Year');
                if (yearField && yearField.value) {
                    const year = parseInt(yearField.value);
                    const currentYear = new Date().getFullYear();
                    if (year < 1900 || year > currentYear + 1) {
                        e.preventDefault();
                        this.showErrorMessage(`Year must be between 1900 and ${currentYear + 1}`);
                        yearField.focus();
                        isValid = false;
                    }
                }

                // Validate VIN length
                const vinField = document.getElementById('VIN');
                if (vinField && vinField.value && vinField.value.length !== 17) {
                    e.preventDefault();
                    this.showErrorMessage('VIN must be exactly 17 characters');
                    vinField.focus();
                    isValid = false;
                }

                return isValid;
            });
        }

        // ===== DELETE FUNCTIONALITY =====

        /**
         * Shows the delete confirmation modal. This function is called from an onclick attribute in the HTML.
         * @param {HTMLElement} button The delete button that was clicked.
         */
        confirmDeleteAsset(button) {
            const assetId = button.dataset.assetId || button.getAttribute('data-asset-id');
            const assetName = button.dataset.assetName || button.getAttribute('data-asset-name');
            this.showDeleteConfirmation(assetId, assetName);
        }

        /**
         * Shows the delete confirmation modal with asset details
         * @param {string} assetId - The ID of the asset to delete
         * @param {string} assetName - The name of the asset to delete
         */
        showDeleteConfirmation(assetId, assetName) {
            this.assetToDelete = assetId;
            
            if (this.deleteAssetName) {
                this.deleteAssetName.textContent = assetName;
            }
            if (this.deleteModal) {
                this.deleteModal.classList.remove('hidden');
            }
        }

        /**
         * Hides the delete confirmation modal and resets its state.
         */
        hideDeleteModal() {
            if (this.deleteModal) {
                this.deleteModal.classList.add('hidden');
            }
            this.assetToDelete = null;
        }

        /**
         * Performs the actual deletion of an asset by calling the API.
         * @param {string} assetId The ID of the asset to delete.
         */
        async deleteAsset(assetId) {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) {
                    this.showErrorMessage('Authentication required. Please log in again.');
                    return;
                }
                
                const response = await fetch(`/api/assets/${assetId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    this.showSuccessMessage('Asset deleted successfully!');
                    
                    // Redirect based on current page
                    if (this.currentPath.includes(`/assets/${assetId}`)) {
                        // We're on the detail page, go back to index
                        window.location.href = '/assets';
                    } else {
                        // We're on the index page, reload it
                        window.location.reload();
                    }
                } else {
                    const error = await response.json().catch(() => ({}));
                    this.showErrorMessage(`Failed to delete asset: ${error.detail || 'Server error'}`);
                }
            } catch (error) {
                console.error('Error deleting asset:', error);
                this.showErrorMessage('An error occurred while deleting the asset.');
            } finally {
                this.hideDeleteModal();
            }
        }

        // ===== ADMIN ACCESS CHECKING =====

        /**
         * Checks user information and roles from localStorage to determine if admin-only buttons (like delete) should be shown.
         */
        async checkAdminAccessAndShowDeleteButtons() {
            try {
                const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
                const roles = userInfo.roles || [];
                const adminConfirmed = localStorage.getItem('admin_access_confirmed');
                const isSystemAdmin = document.body.innerText.includes('System Administrator');
                
                const hasAdminRole = roles.some(role => {
                    const roleName = (typeof role === 'string' ? role : role.name || '').toLowerCase();
                    return ['admin', 'administrator', 'system administrator'].includes(roleName);
                });
                
                const isSuperuser = userInfo.is_superuser === true;
                const isAdminUser = userInfo.username === 'admin';
                
                const isAdmin = hasAdminRole || 
                               isSuperuser || 
                               isAdminUser ||
                               adminConfirmed === 'true' || 
                               isSystemAdmin;
                
                if (isAdmin) {
                    this.showDeleteButtons();
                    localStorage.setItem('admin_access_confirmed', 'true');
                }
            } catch (error) {
                console.warn('Could not check admin access from localStorage:', error);
            }
        }
        
        /**
         * Makes all elements with delete functionality visible for admin users.
         */
        showDeleteButtons() {
            const deleteButtons = document.querySelectorAll('.delete-icon, .delete-asset-btn');
            deleteButtons.forEach(button => {
                button.classList.remove('hidden');
                button.style.display = 'inline-flex';
                button.style.visibility = 'visible';
            });
            console.log('✅ Delete buttons shown for admin user');
        }

        // ===== MESSAGE DISPLAY =====

        /**
         * Displays a temporary success message at the top right of the screen.
         * @param {string} message The message to display.
         */
        showSuccessMessage(message) {
            console.log('✅ Success:', message);
            
            const alertDiv = document.createElement('div');
            alertDiv.className = 'fixed top-4 right-4 bg-green-100 border border-green-200 text-green-800 px-4 py-3 rounded-md shadow-lg z-50';
            alertDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                padding: 12px 16px;
                background-color: #dcfce7;
                border: 1px solid #bbf7d0;
                color: #166534;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                font-family: inherit;
            `;
            alertDiv.textContent = message;
            document.body.appendChild(alertDiv);
            
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 3000);
        }

        /**
         * Displays a temporary error message at the top right of the screen.
         * @param {string} message The message to display.
         */
        showErrorMessage(message) {
            console.error('❌ Error:', message);
            
            const alertDiv = document.createElement('div');
            alertDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-200 text-red-800 px-4 py-3 rounded-md shadow-lg z-50';
            alertDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                padding: 12px 16px;
                background-color: #fee2e2;
                border: 1px solid #fecaca;
                color: #991b1b;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                font-family: inherit;
            `;
            alertDiv.textContent = message;
            document.body.appendChild(alertDiv);
            
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 5000);
        }

        // ===== KEYBOARD SHORTCUTS =====

        /**
         * Handle keyboard shortcuts for asset pages
         * @param {KeyboardEvent} e - The keyboard event
         */
        handleKeyboardShortcuts(e) {
            // Only on assets pages
            if (!this.currentPath.includes('/assets')) return;
            
            // Ctrl/Cmd + N = New Asset
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                window.location.href = '/assets/new';
            }
            
            // Escape = Close modals
            if (e.key === 'Escape') {
                if (this.deleteModal && !this.deleteModal.classList.contains('hidden')) {
                    this.hideDeleteModal();
                }
            }
        }

        // ===== UTILITY FUNCTIONS =====

        /**
         * Debounce function to limit how often a function can be called
         * @param {Function} func - The function to debounce
         * @param {number} wait - The number of milliseconds to delay
         * @returns {Function} The debounced function
         */
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

        /**
         * Format a number as currency
         * @param {number} amount - The amount to format
         * @returns {string} The formatted currency string
         */
        formatCurrency(amount) {
            try {
                const num = parseFloat(amount);
                if (isNaN(num)) return '$0.00';
                
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(num);
            } catch (error) {
                return `$${parseFloat(amount || 0).toFixed(2)}`;
            }
        }

        /**
         * Get the appropriate CSS class for an asset status badge
         * @param {string} status - The asset status
         * @returns {string} The CSS class name
         */
        getAssetStatusClass(status) {
            const statusMap = {
                'Active': 'badge-success',
                'Sold': 'badge-info',
                'Repossessed': 'badge-error',
                'Totaled': 'badge-warning',
                'Inactive': 'badge-secondary'
            };
            
            return statusMap[status] || 'badge-secondary';
        }

        /**
         * Calculate asset equity (value - loan balance)
         * @param {number} value - Asset value
         * @param {number} loanBalance - Loan balance
         * @returns {number} The calculated equity
         */
        calculateAssetEquity(value, loanBalance) {
            if (!value || !loanBalance) return 0;
            return value - loanBalance;
        }

        /**
         * Handle responsive behavior for mobile devices
         */
        handleMobileView() {
            const isMobile = window.innerWidth <= 768;
            
            if (isMobile) {
                // Disable click navigation on mobile for both cards and rows (use buttons instead)
                const clickableElements = document.querySelectorAll('.asset-card, .asset-row');
                clickableElements.forEach(element => {
                    element.style.cursor = 'default';
                });
            }
        }
    }

    // --- Main execution ---
    // Wait until the DOM is fully loaded before initializing the script.
    document.addEventListener('DOMContentLoaded', () => {
        // Create a single, global instance of the AssetManager.
        // This makes the methods available to onclick attributes in the HTML.
        if (!window.assetManager) {
            window.assetManager = new AssetManager();
            window.assetManager.init();
            
            // Make key functions available globally for HTML onclick handlers
            window.confirmDeleteAsset = (button) => window.assetManager.confirmDeleteAsset(button);
            window.formatCurrency = (amount) => window.assetManager.formatCurrency(amount);
            window.getAssetStatusClass = (status) => window.assetManager.getAssetStatusClass(status);
            window.calculateAssetEquity = (value, loanBalance) => window.assetManager.calculateAssetEquity(value, loanBalance);
            
            // Listen for window resize for responsive behavior
            window.addEventListener('resize', window.assetManager.debounce(() => {
                window.assetManager.handleMobileView();
            }, 250));
            
            // Initialize mobile responsiveness
            window.assetManager.handleMobileView();
        }
    });

    console.log('🚗 Assets JavaScript module loaded successfully');

})();