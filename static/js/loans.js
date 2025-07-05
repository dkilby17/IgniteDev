// loans.js - Complete loans JavaScript functionality

// ===== PAGE-SPECIFIC INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    initializeLoansPage();
});

function initializeLoansPage() {
    const currentPath = window.location.pathname;
    console.log('🏦 Initializing loans page:', currentPath);
    
    if (currentPath.includes('/loans')) {
        // Initialize based on the specific loans page
        if (currentPath.match(/\/loans\/\d+\/edit$/)) {
            initializeLoanForm('edit');
        } else if (currentPath.endsWith('/loans/new')) {
            initializeLoanForm('new');
        } else if (currentPath.match(/\/loans\/\d+$/)) {
            initializeLoanDetail();
        } else if (currentPath.endsWith('/loans')) {
            initializeLoansIndex();
        }
    }
}

// ===== LOANS INDEX PAGE =====

function initializeLoansIndex() {
    console.log('🏦 Initializing Loans Index Page');
    
    // Make table rows clickable
    const loanRows = document.querySelectorAll('.loan-row');
    loanRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't navigate if clicking on action buttons
            if (e.target.closest('.action-icon')) {
                return;
            }
            
            const loanId = this.dataset.loanId;
            if (loanId) {
                window.location.href = `/loans/${loanId}`;
            }
        });
    });
    
    // Initialize delete functionality
    initializeLoanDeleteModal();
    
    // Check admin access for delete buttons
    checkAdminAccessAndShowDeleteButtons();
    
    console.log('✅ Loans Index Page initialized');
}

// ===== LOAN DETAIL PAGE =====

function initializeLoanDetail() {
    console.log('🏦 Initializing Loan Detail Page');
    
    // Initialize delete functionality
    initializeLoanDeleteModal();
    
    // Check admin access for delete buttons
    checkAdminAccessAndShowDeleteButtons();
    
    // Initialize progress bar animation
    initializeLoanProgressBar();
    
    // Initialize detail page specific features
    initializeLoanDetailFeatures();
    
    console.log('✅ Loan Detail Page initialized');
}

// Detail page specific features
function initializeLoanDetailFeatures() {
    // Admin access checking for detail page
    checkAdminAccessAndShowDeleteButton();
    
    // Initialize modal functionality
    initializeDetailDeleteModal();
}

// Detail page admin access checking
function checkAdminAccessAndShowDeleteButton() {
    try {
        const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
        const adminConfirmed = localStorage.getItem('admin_access_confirmed');
        const isSystemAdmin = document.body.innerText.includes('System Administrator');
        
        if (adminConfirmed === 'true' || isSystemAdmin || userInfo.username === 'admin') {
            const deleteLoanBtn = document.querySelector('.delete-loan-btn');
            if (deleteLoanBtn) {
                deleteLoanBtn.classList.remove('hidden');
            }
        }
    } catch (error) {
        console.error('Error checking admin access:', error);
    }
}

// Detail page delete modal functionality
function initializeDetailDeleteModal() {
    const deleteModal = document.getElementById('deleteModal');
    const deleteLoanName = document.getElementById('deleteLoanName');
    const cancelDelete = document.getElementById('cancelDelete');
    const confirmDelete = document.getElementById('confirmDelete');
    const deleteLoanBtn = document.querySelector('.delete-loan-btn');
    let loanToDelete = null;
    
    if (!deleteModal) return;
    
    // Delete button click handler
    if (deleteLoanBtn) {
        deleteLoanBtn.addEventListener('click', function() {
            loanToDelete = this.dataset.loanId;
            const loanName = this.dataset.loanName;
            
            if (deleteLoanName) {
                deleteLoanName.textContent = loanName;
            }
            deleteModal.classList.remove('hidden');
        });
    }
    
    // Cancel delete
    if (cancelDelete) {
        cancelDelete.addEventListener('click', function() {
            hideDetailDeleteModal();
        });
    }
    
    // Confirm delete
    if (confirmDelete) {
        confirmDelete.addEventListener('click', function() {
            if (loanToDelete) {
                deleteDetailLoan(loanToDelete);
            }
        });
    }
    
    // Hide modal when clicking outside
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === deleteModal) {
                hideDetailDeleteModal();
            }
        });
    }
    
    function hideDetailDeleteModal() {
        if (deleteModal) {
            deleteModal.classList.add('hidden');
        }
        loanToDelete = null;
    }
    
    // Detail page specific delete function
    async function deleteDetailLoan(loanId) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                showError('Authentication required');
                return;
            }
            
            const response = await fetch(`/api/loans/${loanId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                showSuccess('Loan deleted successfully!');
                // Redirect to loans list from detail page
                window.location.href = '/loans';
            } else {
                const error = await response.json().catch(() => ({}));
                showError(`Failed to delete loan: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error deleting loan:', error);
            showError('An error occurred while deleting the loan');
        } finally {
            hideDetailDeleteModal();
        }
    }
}

// ===== LOAN FORM PAGE =====

function initializeLoanForm(mode = 'new') {
    console.log(`🏦 Initializing Loan Form Page (${mode})`);
    
    // Initialize auto-calculation
    initializeLoanCalculator();
    
    // Initialize form validation
    initializeLoanFormValidation();
    
    console.log('✅ Loan Form Page initialized');
}

// ===== LOAN CALCULATOR =====

function initializeLoanCalculator() {
    const loanAmount = document.querySelector('input[name="loan_amount"]');
    const interestRate = document.querySelector('input[name="interest_rate"]');
    const loanTerm = document.querySelector('input[name="loan_term"]');
    const monthlyPayment = document.querySelector('input[name="monthly_payment"]');

    if (!loanAmount || !interestRate || !loanTerm || !monthlyPayment) {
        return; // Not on a form page
    }

    function calculatePayment() {
        const principal = parseFloat(loanAmount.value) || 0;
        const rate = parseFloat(interestRate.value) || 0;
        const years = parseFloat(loanTerm.value) || 0;

        if (principal > 0 && rate > 0 && years > 0) {
            const monthlyRate = rate / 100 / 12;
            const numPayments = years * 12;
            
            const payment = principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                           (Math.pow(1 + monthlyRate, numPayments) - 1);
            
            monthlyPayment.value = payment.toFixed(2);
            
            // Add visual feedback
            monthlyPayment.style.backgroundColor = '#dcfce7';
            setTimeout(() => {
                monthlyPayment.style.backgroundColor = '';
            }, 1000);
        }
    }

    // Add event listeners for auto-calculation
    [loanAmount, interestRate, loanTerm].forEach(input => {
        if (input) {
            input.addEventListener('input', debounce(calculatePayment, 300));
            input.addEventListener('blur', calculatePayment);
        }
    });
}

// ===== FORM VALIDATION =====

function initializeLoanFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        const contractNumber = document.querySelector('input[name="contract_number"]');
        
        if (contractNumber && !contractNumber.value.trim()) {
            e.preventDefault();
            showError('Contract number is required');
            contractNumber.focus();
            return false;
        }
        
        // Additional validation can be added here
        return true;
    });
}

// ===== DELETE FUNCTIONALITY =====

function initializeLoanDeleteModal() {
    const deleteModal = document.getElementById('deleteModal');
    const deleteLoanName = document.getElementById('deleteLoanName');
    const cancelDelete = document.getElementById('cancelDelete');
    const confirmDelete = document.getElementById('confirmDelete');
    let loanToDelete = null;
    
    if (!deleteModal) return;
    
    // Global function for delete confirmation (called from HTML)
    window.confirmDeleteLoan = function(button) {
        loanToDelete = button.dataset.loanId;
        const loanName = button.dataset.loanName;
        
        if (deleteLoanName) {
            deleteLoanName.textContent = loanName;
        }
        deleteModal.classList.remove('hidden');
    };
    
    // Cancel delete
    if (cancelDelete) {
        cancelDelete.addEventListener('click', function() {
            hideDeleteModal();
        });
    }
    
    // Confirm delete
    if (confirmDelete) {
        confirmDelete.addEventListener('click', function() {
            if (loanToDelete) {
                deleteLoan(loanToDelete);
            }
        });
    }
    
    // Hide modal when clicking outside
    deleteModal.addEventListener('click', function(e) {
        if (e.target === deleteModal) {
            hideDeleteModal();
        }
    });
    
    function hideDeleteModal() {
        deleteModal.classList.add('hidden');
        loanToDelete = null;
    }
}

async function deleteLoan(loanId) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            showError('Authentication required');
            return;
        }
        
        const response = await fetch(`/api/loans/${loanId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('Loan deleted successfully!');
            
            // Redirect based on current page
            if (window.location.pathname.includes(`/loans/${loanId}`)) {
                // We're on the detail page, go back to index
                window.location.href = '/loans';
            } else {
                // We're on the index page, reload it
                window.location.reload();
            }
        } else {
            const error = await response.json().catch(() => ({}));
            showError(`Failed to delete loan: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting loan:', error);
        showError('An error occurred while deleting the loan');
    } finally {
        // Hide modal
        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal) {
            deleteModal.classList.add('hidden');
        }
    }
}

// ===== ADMIN ACCESS CHECKING =====

function checkAdminAccessAndShowDeleteButtons() {
    try {
        // Check multiple sources for admin access
        const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
        const roles = userInfo.roles || [];
        const adminConfirmed = localStorage.getItem('admin_access_confirmed');
        const isSystemAdmin = document.body.innerText.includes('System Administrator');
        
        // Check for admin role
        const hasAdminRole = roles.some(role => {
            if (typeof role === 'string') {
                return role.toLowerCase().includes('admin');
            } else if (typeof role === 'object' && role.name) {
                return role.name.toLowerCase().includes('admin');
            }
            return false;
        });
        
        // Multiple ways to confirm admin access
        const isAdmin = hasAdminRole || 
                       adminConfirmed === 'true' || 
                       isSystemAdmin || 
                       userInfo.username === 'admin' || 
                       userInfo.is_superuser === true;
        
        if (isAdmin) {
            showDeleteButtons();
            localStorage.setItem('admin_access_confirmed', 'true');
        }
        
    } catch (error) {
        console.error('Error checking admin access:', error);
    }
}

function showDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-icon, .delete-loan-btn');
    deleteButtons.forEach(button => {
        button.classList.remove('hidden');
        button.style.display = 'inline-flex';
        button.style.visibility = 'visible';
    });
    console.log('✅ Delete buttons shown for admin user');
}

// ===== PROGRESS BAR ANIMATION =====

function initializeLoanProgressBar() {
    // Set progress from data attributes
    document.querySelectorAll('.loan-progress-fill, .loan-progress-bar').forEach(bar => {
        const progress = parseFloat(bar.dataset.progress) || 0;
        console.log('Progress bar element found with progress:', progress);
        
        if (progress >= 0) {
            // Ensure progress is within valid bounds
            const safeProgress = Math.min(Math.max(progress, 0), 100);
            console.log('Safe progress calculated:', safeProgress);
            
            // Start at 0 width
            bar.style.width = '0%';
            
            // Animate to target width after a short delay
            setTimeout(() => {
                bar.style.width = safeProgress + '%';
                console.log('Progress bar animated to:', safeProgress + '%');
            }, 200);
        }
    });
    
    // Also handle any existing progress bars on the page (legacy support)
    document.querySelectorAll('[data-progress]').forEach(bar => {
        const progress = parseFloat(bar.dataset.progress) || 0;
        if (progress >= 0 && !bar.classList.contains('loan-progress-bar')) {
            const safeProgress = Math.min(Math.max(progress, 0), 100);
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = safeProgress + '%';
            }, 200);
        }
    });
}

// ===== UTILITY FUNCTIONS =====

function debounce(func, wait) {
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

function showError(message) {
    console.error('❌ Error:', message);
    
    // Try to use existing alert system or create a simple one
    if (typeof window.showAlert === 'function') {
        window.showAlert(message, 'error');
    } else {
        // Create a temporary error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-error';
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
        `;
        alertDiv.textContent = message;
        
        document.body.appendChild(alertDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

function showSuccess(message) {
    console.log('✅ Success:', message);
    
    // Try to use existing alert system or create a simple one
    if (typeof window.showAlert === 'function') {
        window.showAlert(message, 'success');
    } else {
        // Create a temporary success message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success';
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
        `;
        alertDiv.textContent = message;
        
        document.body.appendChild(alertDiv);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 3000);
    }
}

// ===== CURRENCY FORMATTING =====

function formatCurrency(amount) {
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

// ===== LOAN STATUS HELPERS =====

function getLoanStatusClass(status) {
    const statusMap = {
        'Active': 'loan-status-active',
        'Default': 'loan-status-default', 
        'Paid Off': 'loan-status-paid',
        'Pending': 'loan-status-pending'
    };
    
    return statusMap[status] || 'badge-secondary';
}

function calculateLoanProgress(loanAmount, principalBalance) {
    if (!loanAmount || !principalBalance) return 0;
    
    const paidAmount = loanAmount - principalBalance;
    const progress = (paidAmount / loanAmount) * 100;
    
    return Math.max(0, Math.min(100, progress));
}

// ===== TABLE ENHANCEMENTS =====

function enhanceLoansTable() {
    const table = document.querySelector('.loans-table');
    if (!table) return;
    
    // Add sorting functionality
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            const currentOrder = this.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Update visual indicators
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            this.classList.add(`sort-${newOrder}`);
            this.dataset.order = newOrder;
            
            // Perform sort (you would integrate this with your data loading)
            console.log(`Sort by ${sortField} ${newOrder}`);
        });
    });
}

// ===== RESPONSIVE BEHAVIOR =====

function handleMobileView() {
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // Disable row click navigation on mobile (use buttons instead)
        const loanRows = document.querySelectorAll('.loan-row');
        loanRows.forEach(row => {
            row.style.cursor = 'default';
        });
    }
}

// Listen for window resize
window.addEventListener('resize', debounce(handleMobileView, 250));

// ===== KEYBOARD SHORTCUTS =====

document.addEventListener('keydown', function(e) {
    // Only on loans pages
    if (!window.location.pathname.includes('/loans')) return;
    
    // Ctrl/Cmd + N = New Loan
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/loans/new';
    }
    
    // Escape = Close modals
    if (e.key === 'Escape') {
        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal && !deleteModal.classList.contains('hidden')) {
            deleteModal.classList.add('hidden');
        }
    }
});

// ===== LOAN SPECIFIC ENHANCEMENTS =====

// Calculate and display loan metrics
function calculateLoanMetrics(loan) {
    const metrics = {};
    
    if (loan.loan_amount && loan.principal_balance) {
        metrics.amountPaid = loan.loan_amount - loan.principal_balance;
        metrics.percentPaid = (metrics.amountPaid / loan.loan_amount) * 100;
        metrics.percentRemaining = 100 - metrics.percentPaid;
    }
    
    if (loan.monthly_payment && loan.principal_balance && loan.interest_rate) {
        // Calculate remaining payments
        const monthlyRate = (loan.interest_rate / 100) / 12;
        if (monthlyRate > 0) {
            metrics.remainingPayments = Math.ceil(
                Math.log(1 + (loan.principal_balance * monthlyRate) / loan.monthly_payment) / 
                Math.log(1 + monthlyRate)
            );
            metrics.remainingYears = metrics.remainingPayments / 12;
        }
    }
    
    return metrics;
}

// Format loan dates for display
function formatLoanDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        return dateString;
    }
}

// Check if loan is delinquent
function isLoanDelinquent(loan) {
    return loan.days_past_due && loan.days_past_due > 0;
}

// Get delinquency severity level
function getDelinquencyLevel(daysPastDue) {
    if (!daysPastDue || daysPastDue <= 0) return 'current';
    if (daysPastDue <= 30) return 'mild';
    if (daysPastDue <= 60) return 'moderate';
    if (daysPastDue <= 90) return 'serious';
    return 'severe';
}

// ===== EXPORT FUNCTIONS FOR GLOBAL USE =====

// Make functions available globally for HTML onclick handlers
window.confirmDeleteLoan = window.confirmDeleteLoan || function() {};
window.formatCurrency = formatCurrency;
window.getLoanStatusClass = getLoanStatusClass;
window.calculateLoanProgress = calculateLoanProgress;
window.calculateLoanMetrics = calculateLoanMetrics;
window.formatLoanDate = formatLoanDate;
window.isLoanDelinquent = isLoanDelinquent;
window.getDelinquencyLevel = getDelinquencyLevel;

// Initialize mobile responsiveness
handleMobileView();

console.log('🏦 Loans JavaScript module loaded successfully');