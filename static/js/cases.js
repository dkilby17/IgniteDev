// js/cases.js - Complete case management with full dataset sorting and database-only dynamic filters

console.log('🚀 Loading cases.js with full dataset sorting and dynamic filters...');
console.log('🚀 Loading cases.js with full dataset sorting...');
console.log('🔥 CASES.JS FILE IS DEFINITELY LOADING!'); // Add this line

// Global variables
let currentSort = {
    field: 'created_at',
    order: 'desc'
};

// Global variable to store dynamic filters
let dynamicFilters = null;

// Initialize when page is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, initializing cases...');
    initializeCases();
});

// ===========================================
// DYNAMIC FILTERS FUNCTIONALITY (UPDATED)
// ===========================================

// Load dynamic filters from API (database-only)
async function loadDynamicFilters() {
    console.log('🔄 Loading dynamic filters from API (database-only)...');
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.warn('⚠️ No access token for loading dynamic filters');
            return false;
        }

        // Use the database-only endpoint
        const response = await fetch('/api/admin/dynamic-filters/database-only', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`API call failed: ${response.status}`);
        }

        dynamicFilters = await response.json();
        console.log('✅ Dynamic filters loaded (database-only):', dynamicFilters);
        
        // Check if we got any data
        const totalOptions = dynamicFilters.case_status.length + 
                           dynamicFilters.case_type.length + 
                           dynamicFilters.case_priority.length + 
                           dynamicFilters.financial_institution.length;
        
        if (totalOptions === 0) {
            console.warn('⚠️ No filter options found in database. You may want to create some test cases first.');
            
            // Optionally show a message to the user
            showInfoMessage('No filter options found. Create some cases to populate the filters.');
        } else {
            console.log(`📊 Found ${totalOptions} total filter options in database`);
        }
        
        return true;
    } catch (error) {
        console.error('❌ Error loading dynamic filters:', error);
        
        // Set empty filters instead of fallback
        dynamicFilters = {
            case_status: [],
            case_type: [],
            case_priority: [],
            financial_institution: []
        };
        return false;
    }
}

// Populate dropdown filters with dynamic data (updated)
function populateDynamicFilterDropdowns() {
    console.log('🔄 Populating dynamic filter dropdowns (database-only)...');
    
    if (!dynamicFilters) {
        console.warn('⚠️ No dynamic filters available');
        return;
    }

    // Status Filter - ID from your template: "status"
    const statusSelect = document.getElementById('status');
    if (statusSelect) {
        const currentValue = statusSelect.value;
        const allStatusesOption = '<option value="">All Statuses</option>';
        
        if (dynamicFilters.case_status.length > 0) {
            const statusOptions = dynamicFilters.case_status.map(status => 
                `<option value="${status}" ${status === currentValue ? 'selected' : ''}>${status}</option>`
            ).join('');
            statusSelect.innerHTML = allStatusesOption + statusOptions;
            console.log(`✅ Populated status dropdown with ${dynamicFilters.case_status.length} options`);
        } else {
            statusSelect.innerHTML = allStatusesOption;
            console.log('⚠️ No status options found in database');
        }
    } else {
        console.warn('⚠️ Status dropdown with ID "status" not found');
    }

    // Case Type Filter - ID from your template: "type" 
    const typeSelect = document.getElementById('type');
    if (typeSelect) {
        const currentValue = typeSelect.value;
        const allTypesOption = '<option value="">All Types</option>';
        
        if (dynamicFilters.case_type.length > 0) {
            const typeOptions = dynamicFilters.case_type.map(type => 
                `<option value="${type}" ${type === currentValue ? 'selected' : ''}>${type}</option>`
            ).join('');
            typeSelect.innerHTML = allTypesOption + typeOptions;
            console.log(`✅ Populated type dropdown with ${dynamicFilters.case_type.length} options`);
        } else {
            typeSelect.innerHTML = allTypesOption;
            console.log('⚠️ No case type options found in database');
        }
    } else {
        console.warn('⚠️ Type dropdown with ID "type" not found');
    }

    // Priority Filter - ID from your template: "priority"
    const prioritySelect = document.getElementById('priority');
    if (prioritySelect) {
        const currentValue = prioritySelect.value;
        const allPrioritiesOption = '<option value="">All Priorities</option>';
        
        if (dynamicFilters.case_priority.length > 0) {
            const priorityOptions = dynamicFilters.case_priority.map(priority => 
                `<option value="${priority}" ${priority === currentValue ? 'selected' : ''}>${priority}</option>`
            ).join('');
            prioritySelect.innerHTML = allPrioritiesOption + priorityOptions;
            console.log(`✅ Populated priority dropdown with ${dynamicFilters.case_priority.length} options`);
        } else {
            prioritySelect.innerHTML = allPrioritiesOption;
            console.log('⚠️ No priority options found in database');
        }
    } else {
        console.warn('⚠️ Priority dropdown with ID "priority" not found');
    }

    // Financial Institution Filter - ID from your template: "financial_institution"
    const fiSelect = document.getElementById('financial_institution');
    if (fiSelect) {
        const currentValue = fiSelect.value;
        const allInstitutionsOption = '<option value="">All Institutions</option>';
        
        if (dynamicFilters.financial_institution.length > 0) {
            const fiOptions = dynamicFilters.financial_institution.map(fi => 
                `<option value="${fi}" ${fi === currentValue ? 'selected' : ''}>${fi}</option>`
            ).join('');
            fiSelect.innerHTML = allInstitutionsOption + fiOptions;
            console.log(`✅ Populated financial institution dropdown with ${dynamicFilters.financial_institution.length} options`);
        } else {
            fiSelect.innerHTML = allInstitutionsOption;
            console.log('⚠️ No financial institution options found in database');
        }
    } else {
        console.warn('⚠️ Financial institution dropdown with ID "financial_institution" not found');
    }

    // Debug: Log all found dropdowns
    const foundDropdowns = [];
    if (statusSelect) foundDropdowns.push('status');
    if (typeSelect) foundDropdowns.push('type'); 
    if (prioritySelect) foundDropdowns.push('priority');
    if (fiSelect) foundDropdowns.push('financial_institution');
    
    console.log(`✅ Dynamic filter dropdowns populated successfully. Found: ${foundDropdowns.join(', ')}`);
    
    // Update debug info in template
    updateDebugInfo();
}

// Update the debug info in your template
function updateDebugInfo() {
    const debugDiv = document.querySelector('.mt-4.p-3.bg-gray-100.rounded.text-xs.text-gray-600');
    if (debugDiv && dynamicFilters) {
        const totalOptions = dynamicFilters.case_status.length + 
                           dynamicFilters.case_type.length + 
                           dynamicFilters.case_priority.length + 
                           dynamicFilters.financial_institution.length;
        
        const debugInfo = `
            <strong>🔍 Debug Info (Updated by JavaScript):</strong>
            Dynamic filters loaded from database-only API |
            Status options: ${dynamicFilters.case_status.length} |
            Type options: ${dynamicFilters.case_type.length} |
            Priority options: ${dynamicFilters.case_priority.length} |
            FI options: ${dynamicFilters.financial_institution.length} |
            Total options: ${totalOptions} |
            Current time: ${new Date().toLocaleTimeString()}
        `;
        debugDiv.innerHTML = debugInfo;
    }
}

// Setup form handling for dynamic filters
function setupDynamicFilterForm() {
    const form = document.querySelector('form[method="GET"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('📝 Form submitted with dynamic filter values');
            
            // Log current filter values for debugging
            const statusValue = document.getElementById('status')?.value || '';
            const typeValue = document.getElementById('type')?.value || '';
            const priorityValue = document.getElementById('priority')?.value || '';
            const fiValue = document.getElementById('financial_institution')?.value || '';
            
            console.log(`Current filter values:
            - Status: "${statusValue}"
            - Type: "${typeValue}"  
            - Priority: "${priorityValue}"
            - Financial Institution: "${fiValue}"`);
        });
    }
}

// Refresh dynamic filters function
async function refreshDynamicFilters() {
    console.log('🔄 Refreshing dynamic filters...');
    const success = await loadDynamicFilters();
    if (success) {
        populateDynamicFilterDropdowns();
    }
    return success;
}

// ===========================================
// NEW TESTING AND UTILITY FUNCTIONS
// ===========================================

// Add a function to test different filter endpoints
window.testAllFilterEndpoints = async function() {
    console.log('🧪 Testing all filter endpoints...');
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error('❌ No access token found');
        return;
    }
    
    const endpoints = [
        '/api/admin/dynamic-filters/database-only',
        '/api/admin/dynamic-filters/combined', 
        '/api/admin/filter-config',
        '/api/admin/dynamic-filters/summary'
    ];
    
    for (const endpoint of endpoints) {
        try {
            console.log(`\n📡 Testing: ${endpoint}`);
            const response = await fetch(endpoint, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`✅ ${endpoint}:`, data);
            } else {
                console.error(`❌ ${endpoint} failed:`, response.status);
            }
        } catch (error) {
            console.error(`🚨 ${endpoint} error:`, error);
        }
    }
    
    console.log('\n🏁 Filter endpoint testing complete');
};

// Add a function to create test cases if database is empty
window.createTestCases = async function(count = 10) {
    console.log(`🔧 Creating ${count} test cases...`);
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error('❌ No access token found');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/create-test-cases?count=${count}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Test cases created:', data);
            
            // Refresh filters after creating test cases
            console.log('🔄 Refreshing filters...');
            await refreshDynamicFilters();
            
            showSuccessMessage(`Created ${count} test cases successfully! Filters refreshed.`);
        } else {
            const error = await response.json();
            console.error('❌ Failed to create test cases:', error);
            showErrorMessage(`Failed to create test cases: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('🚨 Error creating test cases:', error);
        showErrorMessage('Error creating test cases. Check console for details.');
    }
};

// Add an info message function
function showInfoMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'fixed top-4 right-4 bg-blue-100 border border-blue-200 text-blue-800 px-4 py-3 rounded-md shadow-lg z-50';
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// ===========================================
// MAIN INITIALIZATION FUNCTION  
// ===========================================

// Main initialization function (updated to include dynamic filters)
async function initializeCases() {
    console.log('🔧 Initializing cases functionality...');
    
    try {
        // Load dynamic filters first
        await loadDynamicFilters();
        
        // Populate the filter dropdowns with dynamic data
        populateDynamicFilterDropdowns();
        
        // Setup form handling for dynamic filters
        setupDynamicFilterForm();
        
        // Setup all existing functionality
        setupFullDatasetSorting();
        setupRowClickHandlers();
        setupAdminButtons();
        setupEventListeners();
        
        console.log('✅ Cases functionality initialized with dynamic filters');
    } catch (error) {
        console.error('❌ Error initializing cases:', error);
        // Continue with fallback initialization
        setupFullDatasetSorting();
        setupRowClickHandlers();
        setupAdminButtons();
        setupEventListeners();
        console.log('✅ Cases functionality initialized with fallback');
    }
}

// ===========================================
// FULL DATASET SORTING
// ===========================================

// Enhanced sort function that loads all cases and sorts them
async function handleSortAllCompatible(field) {
    console.log(`🔄 Full dataset sort by: ${field}`);
    
    // Determine order
    let order = 'asc';
    if (field === currentSort.field) {
        order = currentSort.order === 'asc' ? 'desc' : 'asc';
    }
    
    currentSort.field = field;
    currentSort.order = order;
    
    console.log(`Loading all cases for sorting by: ${field} ${order}`);
    
    try {
        // Show loading indicator
        showLoadingIndicator();
        
        // Load ALL cases (using multiple API calls if needed)
        const allCases = await loadAllCasesCompatible();
        
        if (allCases && allCases.length > 0) {
            console.log(`✅ Loaded ${allCases.length} cases, applying client-side sorting...`);
            
            // Sort all cases client-side
            const sortedCases = sortCasesClientSide(allCases, field, order);
            
            // Rebuild the entire table with all sorted cases
            rebuildTableWithAllCases(sortedCases);
            
            // Update UI
            updateSortIndicators(field, order);
            updateURL(field, order);
            
            console.log(`✅ Full dataset sorted by ${field} ${order} (${sortedCases.length} cases)`);
        } else {
            console.log('❌ Failed to load cases, falling back to current page sorting');
            sortTableClientSideCurrentPage(field, order);
        }
        
    } catch (error) {
        console.error('❌ Error loading all cases:', error);
        sortTableClientSideCurrentPage(field, order);
    } finally {
        hideLoadingIndicator();
    }
}

// Load all cases using multiple API calls if needed
async function loadAllCasesCompatible() {
    console.log('📡 Loading all cases (API-compatible mode)...');
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error('❌ No access token found');
        return null;
    }
    
    // Get current filters from form
    const searchInput = document.getElementById('search');
    const statusSelect = document.getElementById('status');
    const typeSelect = document.getElementById('type');
    const fiSelect = document.getElementById('financial_institution');
    
    let allCases = [];
    let skip = 0;
    let limit = 50; // Use smaller, safer limit
    let hasMore = true;
    
    while (hasMore && skip < 500) { // Safety limit to prevent infinite loops
        console.log(`📡 Loading batch: skip=${skip}, limit=${limit}`);
        
        // Build API parameters for this batch
        const params = new URLSearchParams({
            limit: limit,
            skip: skip
        });
        
        // Add current filters (but NO sorting - do that client-side)
        if (searchInput && searchInput.value.trim()) {
            params.set('search', searchInput.value.trim());
        }
        if (statusSelect && statusSelect.value) {
            params.set('status', statusSelect.value);
        }
        if (typeSelect && typeSelect.value) {
            params.set('case_type', typeSelect.value);
        }
        if (fiSelect && fiSelect.value) {
            params.set('financial_institution', fiSelect.value);
        }
        
        try {
            const response = await fetch(`/api/cases/?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`API call failed: ${response.status}`);
            }
            
            const data = await response.json();
            const cases = data.items || data || [];
            
            console.log(`📊 Batch ${Math.floor(skip/limit) + 1}: Got ${cases.length} cases`);
            
            if (cases.length === 0) {
                hasMore = false;
            } else {
                allCases = allCases.concat(cases);
                skip += limit;
                
                // If we got less than the limit, we've reached the end
                if (cases.length < limit) {
                    hasMore = false;
                }
                
                // If this looks like the total from a paginated response
                if (data.total && allCases.length >= data.total) {
                    hasMore = false;
                }
            }
            
        } catch (error) {
            console.error(`❌ Error loading batch ${Math.floor(skip/limit) + 1}:`, error);
            hasMore = false;
        }
    }
    
    console.log(`📊 Total loaded: ${allCases.length} cases`);
    return allCases;
}

// Client-side sorting for all cases
function sortCasesClientSide(cases, field, order) {
    console.log(`🔄 Client-side sorting ${cases.length} cases by ${field} ${order}`);
    
    const sortedCases = [...cases].sort((a, b) => {
        const valueA = getAPISortValue(a, field);
        const valueB = getAPISortValue(b, field);
        
        if (valueA < valueB) return order === 'asc' ? -1 : 1;
        if (valueA > valueB) return order === 'asc' ? 1 : -1;
        return 0;
    });
    
    console.log(`✅ Client-side sorting complete`);
    return sortedCases;
}

// Get sort value from API case object
function getAPISortValue(case_, field) {
    switch (field) {
        case 'id':
            return case_.id || 0;
            
        case 'subject':
            return (case_.subject || '').toLowerCase();
            
        case 'case_type':
            return (case_.case_type || '').toLowerCase();
            
        case 'status':
            return (case_.status || '').toLowerCase();
            
        case 'created_at':
            return new Date(case_.created_at || 0).getTime();
            
        case 'financial_institution':
            if (case_.loan?.financial_institution) return case_.loan.financial_institution.toLowerCase();
            if (case_.account?.financial_institution) return case_.account.financial_institution.toLowerCase();
            if (case_.contact?.financial_institution) return case_.contact.financial_institution.toLowerCase();
            return '';
            
        case 'days_past_due':
            const days = case_.loan?.days_past_due;
            return days !== null && days !== undefined ? days : -1;
            
        case 'total_owing':
            if (case_.loan) {
                const pastDue = parseFloat(case_.loan.past_due_amount || 0);
                const fees = parseFloat(case_.loan.past_due_fees || 0);
                const total = pastDue + fees;
                if (total > 0) return total;
            }
            return parseFloat(case_.amount_involved || 0);
            
        default:
            return '';
    }
}

// Rebuild table with all cases
function rebuildTableWithAllCases(cases) {
    console.log(`🔄 Rebuilding table with ${cases.length} cases...`);
    
    const tbody = document.querySelector('table tbody');
    if (!tbody) {
        console.error('❌ No table tbody found');
        return;
    }
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    if (cases.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="px-6 py-4 text-center text-gray-500">
                    No cases found
                </td>
            </tr>
        `;
        return;
    }
    
    // Create rows for all cases
    cases.forEach(case_ => {
        const row = createCaseRowFromAPI(case_);
        tbody.appendChild(row);
    });
    
    // Re-setup row clicks
    setupRowClickHandlers();
    
    // Update pagination info
    updatePaginationForAllCases(cases.length);
    
    console.log(`✅ Table rebuilt with ${cases.length} rows`);
}

// Create table row from API case data
function createCaseRowFromAPI(case_) {
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50 cursor-pointer case-row';
    row.dataset.caseId = case_.id;
    
    // Helper functions
    const getFinancialInstitution = (case_) => {
        if (case_.loan?.financial_institution) return case_.loan.financial_institution;
        if (case_.account?.financial_institution) return case_.account.financial_institution;
        if (case_.contact?.financial_institution) return case_.contact.financial_institution;
        return 'Unknown';
    };
    
    const getDaysPastDue = (case_) => {
        const days = case_.loan?.days_past_due;
        if (days === null || days === undefined) return 'N/A';
        return days > 0 ? `${days} days` : 'Current';
    };
    
    const getTotalOwing = (case_) => {
        if (case_.loan) {
            const pastDue = parseFloat(case_.loan.past_due_amount || 0);
            const fees = parseFloat(case_.loan.past_due_fees || 0);
            const total = pastDue + fees;
            if (total > 0) return total;
        }
        return parseFloat(case_.amount_involved || 0);
    };
    
    const getCaseTypeClass = (caseType) => {
        switch (caseType) {
            case 'Delinquency': return 'bg-red-100 text-red-800';
            case 'Payment Issue': return 'bg-yellow-100 text-yellow-800';
            case 'Collections': return 'bg-orange-100 text-orange-800';
            case 'Account Inquiry': return 'bg-blue-100 text-blue-800';
            case 'Technical Support': return 'bg-purple-100 text-purple-800';
            case 'Complaint': return 'bg-pink-100 text-pink-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };
    
    const getStatusClass = (status) => {
        switch (status) {
            case 'New': return 'bg-blue-100 text-blue-800';
            case 'Open': return 'bg-green-100 text-green-800';
            case 'Closed': return 'bg-gray-100 text-gray-800';
            case 'In Progress': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };
    
    const getPriorityClass = (priority) => {
        switch (priority) {
            case 'Urgent': return 'bg-red-100 text-red-800';
            case 'High': return 'bg-orange-100 text-orange-800';
            case 'Medium': return 'bg-yellow-100 text-yellow-800';
            case 'Low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };
    
    // Build row data
    const fi = getFinancialInstitution(case_);
    const daysPastDue = getDaysPastDue(case_);
    const totalOwing = getTotalOwing(case_);
    const createdDate = new Date(case_.created_at).toLocaleDateString();
    
    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-medium text-gray-900">Case #${case_.id}</div>
            <div class="text-sm text-gray-500">${case_.case_number || `CASE${String(case_.id).padStart(6, '0')}`}</div>
        </td>
        <td class="px-6 py-4">
            <div class="text-sm font-medium text-gray-900">${case_.subject || 'No Subject'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${fi === 'Unknown' ? '<span class="text-gray-400">Unknown</span>' : fi}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCaseTypeClass(case_.case_type)}">
                ${case_.case_type || 'General'}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityClass(case_.priority)}">
                ${case_.priority || 'Medium'}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            ${daysPastDue === 'N/A' ? '<span class="text-gray-400">N/A</span>' : daysPastDue}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <span class="font-medium">$${totalOwing.toFixed(2)}</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusClass(case_.status)}">
                ${case_.status || 'Open'}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${createdDate}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
            <div class="flex items-center space-x-2">
                <a href="/cases/${case_.id}" class="action-icon edit-icon text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50 transition-colors" title="Edit Case" onclick="event.stopPropagation();">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                </a>
                
                <!-- Close Case Button -->
                ${case_.status === 'Open' ? `
                <button data-close-case="${case_.id}" 
                        class="text-gray-600 hover:text-gray-900 text-sm font-medium hover:bg-gray-100 px-2 py-1 rounded"
                        onclick="event.stopPropagation();">
                    Close
                </button>
                ` : ''}
                
                <!-- Delete Button (hidden by default, shown for admins) -->
                <button class="action-icon delete-icon text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors hidden" 
                        title="Delete Case" 
                        onclick="event.stopPropagation(); window.caseManager.confirmDeleteCase(this);" 
                        data-case-id="${case_.id}" 
                        data-case-name="Case #${case_.id}">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

// Setup full dataset sorting
function setupFullDatasetSorting() {
    console.log('🔧 Setting up full dataset sorting...');
    
    // Get current sort from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentSort.field = urlParams.get('sort_by') || 'created_at';
    currentSort.order = urlParams.get('sort_order') || 'desc';
    
    console.log(`Current sort: ${currentSort.field} ${currentSort.order}`);
    
    // Find sortable headers
    const headers = document.querySelectorAll('.sortable-header');
    console.log(`Found ${headers.length} sortable headers`);
    
    if (headers.length === 0) {
        console.warn('⚠️ No sortable headers found');
        return;
    }
    
    // Setup click handlers
    headers.forEach(header => {
        const field = header.dataset.sort;
        
        // Remove any existing listeners
        header.onclick = null;
        
        // Add new click handler for full dataset sorting
        header.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log(`🖱️ Full dataset sort click: ${field}`);
            handleSortAllCompatible(field);
        };
        
        // Add hover effects
        header.style.cursor = 'pointer';
        header.onmouseenter = function() {
            this.style.backgroundColor = '#f3f4f6';
        };
        header.onmouseleave = function() {
            this.style.backgroundColor = '';
        };
    });
    
    // Update visual indicators for current sort
    updateSortIndicators(currentSort.field, currentSort.order);
    
    console.log('✅ Full dataset sorting setup complete');
}

// Update sort indicators
function updateSortIndicators(activeField, order) {
    document.querySelectorAll('.sortable-header').forEach(header => {
        const field = header.dataset.sort;
        const indicator = header.querySelector('.sort-indicator svg, .sort-indicator, svg');
        
        if (!indicator) return;
        
        if (field === activeField) {
            const path = order === 'desc' 
                ? 'M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z'
                : 'M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z';
            
            indicator.innerHTML = `<path fill-rule="evenodd" d="${path}" clip-rule="evenodd"/>`;
            indicator.classList.remove('text-gray-300');
            indicator.classList.add('text-gray-600');
        } else {
            indicator.innerHTML = '<path d="M5 12l5-5 5 5H5z"/>';
            indicator.classList.remove('text-gray-600');
            indicator.classList.add('text-gray-300');
        }
    });
}

// Update URL
function updateURL(field, order) {
    const url = new URL(window.location);
    url.searchParams.set('sort_by', field);
    url.searchParams.set('sort_order', order);
    url.searchParams.delete('page'); // Remove page param since we're showing all
    window.history.replaceState({}, '', url.toString());
    console.log(`🔗 Updated URL: ${url.toString()}`);
}

// Update pagination info for all cases
function updatePaginationForAllCases(totalCases) {
    const paginationDiv = document.querySelector('.bg-white.px-4.py-3, .pagination-info, [class*="pagination"]');
    if (paginationDiv) {
        paginationDiv.innerHTML = `
            <div class="flex-1 flex justify-center">
                <p class="text-sm text-gray-700">
                    Showing all <span class="font-medium">${totalCases}</span> cases (sorted)
                </p>
            </div>
        `;
    }
}

// Loading indicator functions
function showLoadingIndicator() {
    const tbody = document.querySelector('table tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="px-6 py-4 text-center text-gray-500">
                    <div class="flex items-center justify-center">
                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
                        Loading all cases...
                    </div>
                </td>
            </tr>
        `;
    }
}

function hideLoadingIndicator() {
    // Loading will be replaced by actual data
}

// ===========================================
// CURRENT PAGE SORTING (FALLBACK)
// ===========================================

function sortTableClientSideCurrentPage(field, order) {
    console.log(`🔄 Fallback client-side sorting: ${field} ${order}`);
    
    const tbody = document.querySelector('table tbody');
    if (!tbody) {
        console.error('❌ No table tbody found');
        return;
    }
    
    const rows = Array.from(tbody.querySelectorAll('tr.case-row'));
    console.log(`Found ${rows.length} rows to sort`);
    
    if (rows.length === 0) {
        console.log('⚠️ No rows to sort');
        return;
    }
    
    // Sort the rows
    const sortedRows = rows.sort((a, b) => {
        const valueA = getTableSortValue(a, field);
        const valueB = getTableSortValue(b, field);
        
        if (valueA < valueB) return order === 'asc' ? -1 : 1;
        if (valueA > valueB) return order === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Update the table
    tbody.innerHTML = '';
    sortedRows.forEach(row => tbody.appendChild(row));
    
    console.log(`✅ Fallback client-side sort complete`);
    
    // Re-setup row clicks
    setupRowClickHandlers();
}

// Get sort value from table row (for fallback)
function getTableSortValue(row, field) {
    try {
        switch (field) {
            case 'id':
                const caseText = row.cells[0]?.textContent || '';
                const idMatch = caseText.match(/Case #(\d+)/);
                return idMatch ? parseInt(idMatch[1]) : 0;
                
            case 'subject':
                return (row.cells[1]?.textContent || '').trim().toLowerCase();
                
            case 'financial_institution':
                return (row.cells[2]?.textContent || '').trim().toLowerCase();
                
            case 'case_type':
                return (row.cells[3]?.textContent || '').trim().toLowerCase();
                
            case 'priority':
                return (row.cells[4]?.textContent || '').trim().toLowerCase();
                
            case 'days_past_due':
                const daysText = row.cells[5]?.textContent || '';
                if (daysText.includes('Current')) return 0;
                if (daysText.includes('N/A')) return -1;
                const daysMatch = daysText.match(/(\d+)\s*days/);
                return daysMatch ? parseInt(daysMatch[1]) : -1;
                
            case 'total_owing':
                const amountText = row.cells[6]?.textContent || '';
                const amountMatch = amountText.match(/\$([0-9,]+\.?\d*)/);
                return amountMatch ? parseFloat(amountMatch[1].replace(/,/g, '')) : 0;
                
            case 'status':
                return (row.cells[7]?.textContent || '').trim().toLowerCase();
                
            case 'created_at':
                const dateText = row.cells[8]?.textContent || '';
                return new Date(dateText).getTime() || 0;
                
            default:
                return (row.cells[1]?.textContent || '').trim().toLowerCase();
        }
    } catch (error) {
        console.error(`Error getting sort value for ${field}:`, error);
        return '';
    }
}

// ===========================================
// ROW CLICK HANDLERS
// ===========================================

function setupRowClickHandlers() {
    document.querySelectorAll('.case-row').forEach(row => {
        // Remove existing handler
        row.onclick = null;
        
        // Add new handler
        row.onclick = function(e) {
            if (e.target.closest('.action-icon') || 
                e.target.closest('button') || 
                e.target.closest('a') ||
                e.target.matches('button') ||
                e.target.matches('a')) {
                return;
            }
            
            const caseId = this.dataset.caseId;
            if (caseId) {
                window.location.href = `/cases/${caseId}`;
            }
        };
    });
}

// ===========================================
// ADMIN FUNCTIONALITY
// ===========================================

function setupAdminButtons() {
    // Check for admin access and show delete buttons
    try {
        const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
        const adminConfirmed = localStorage.getItem('admin_access_confirmed');
        const welcomeText = document.body.innerText || '';
        
        if (adminConfirmed === 'true' || 
            welcomeText.includes('System Administrator') ||
            userInfo.is_superuser === true ||
            userInfo.username === 'admin') {
            
            showDeleteButtons();
        }
    } catch (error) {
        console.warn('Could not check admin access:', error);
    }
}

function showDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-icon');
    deleteButtons.forEach(button => {
        button.classList.remove('hidden');
        button.style.display = 'inline-flex';
        button.style.visibility = 'visible';
    });
}

// ===========================================
// EVENT LISTENERS
// ===========================================

function setupEventListeners() {
    // Close case buttons
    document.addEventListener('click', (e) => {
        if (e.target && e.target.matches('[data-close-case]')) {
            e.preventDefault();
            const caseId = e.target.dataset.closeCase;
            quickCloseCase(caseId);
        }
    });
    
    // Delete modal
    const deleteModal = document.getElementById('deleteModal');
    const cancelDeleteBtn = document.getElementById('cancelDelete');
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    
    if (cancelDeleteBtn) {
        cancelDeleteBtn.onclick = hideDeleteModal;
    }
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.onclick = function() {
            if (window.caseToDelete) {
                deleteCase(window.caseToDelete);
            }
        };
    }
    
    if (deleteModal) {
        deleteModal.onclick = function(e) {
            if (e.target === deleteModal) {
                hideDeleteModal();
            }
        };
    }
}

// ===========================================
// CASE ACTIONS
// ===========================================

async function quickCloseCase(caseId) {
    if (!confirm('Close this case? You can reopen it later if needed.')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/cases/${caseId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                status: 'Closed',
                resolution: 'Case closed via quick action'
            })
        });
        
        if (response.ok) {
            showSuccessMessage('Case closed successfully');
            window.location.reload();
        } else {
            showErrorMessage('Failed to close case');
        }
    } catch (error) {
        console.error('Error closing case:', error);
        showErrorMessage('Error closing case');
    }
}

function confirmDeleteCase(button) {
    window.caseToDelete = button.dataset.caseId;
    const caseName = button.dataset.caseName;
    
    const deleteCaseName = document.getElementById('deleteCaseName');
    const deleteModal = document.getElementById('deleteModal');
    
    if (deleteCaseName) {
        deleteCaseName.textContent = caseName;
    }
    if (deleteModal) {
        deleteModal.classList.remove('hidden');
    }
}

function hideDeleteModal() {
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.classList.add('hidden');
    }
    window.caseToDelete = null;
}

async function deleteCase(caseId) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            showErrorMessage('Authentication required. Please log in again.');
            return;
        }
        
        const response = await fetch(`/api/cases/${caseId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccessMessage('Case deleted successfully!');
            window.location.reload();
        } else {
            const error = await response.json();
            showErrorMessage(`Failed to delete case: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting case:', error);
        showErrorMessage('An error occurred while deleting the case.');
    } finally {
        hideDeleteModal();
    }
}

// ===========================================
// UTILITY FUNCTIONS
// ===========================================

function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'fixed top-4 right-4 bg-green-100 border border-green-200 text-green-800 px-4 py-3 rounded-md shadow-lg z-50';
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-200 text-red-800 px-4 py-3 rounded-md shadow-lg z-50';
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// ===========================================
// GLOBAL FUNCTIONS FOR COMPATIBILITY
// ===========================================

// Make functions available globally for debugging and compatibility
window.handleSortAllCompatible = handleSortAllCompatible;
window.sortTableNow = sortTableClientSideCurrentPage;
window.handleColumnSort = handleSortAllCompatible;
window.confirmDeleteCase = confirmDeleteCase;
window.currentSort = currentSort;
window.refreshDynamicFilters = refreshDynamicFilters;

// Create a comprehensive CaseManager object for compatibility
window.caseManager = {
    // Core sorting functions
    handleSort: handleSortAllCompatible,
    sortAllCases: handleSortAllCompatible,
    sortCurrentPage: sortTableClientSideCurrentPage,
    
    // Data loading functions
    loadAllCases: loadAllCasesCompatible,
    sortCases: sortCasesClientSide,
    
    // Dynamic filter functions
    loadDynamicFilters: loadDynamicFilters,
    populateFilterDropdowns: populateDynamicFilterDropdowns,
    refreshFilters: refreshDynamicFilters,
    
    // UI functions
    rebuildTable: rebuildTableWithAllCases,
    updateSortIndicators: updateSortIndicators,
    showLoading: showLoadingIndicator,
    hideLoading: hideLoadingIndicator,
    
    // Admin functions
    deleteCase: deleteCase,
    closeCase: quickCloseCase,
    confirmDeleteCase: confirmDeleteCase,
    
    // State
    currentSort: currentSort,
    dynamicFilters: dynamicFilters,
    
    // Initialize function
    init: initializeCases
};

// ===========================================
// UPDATED DEBUG AND TESTING FUNCTIONS
// ===========================================

// Updated function to check if dynamic filters are working
window.checkDynamicFilters = function() {
    console.log('🔍 Checking dynamic filters status...');
    console.log('✅ dynamicFilters loaded:', !!dynamicFilters);
    console.log('✅ dynamicFilters data:', dynamicFilters);
    
    if (dynamicFilters) {
        const totalOptions = dynamicFilters.case_status.length + 
                           dynamicFilters.case_type.length + 
                           dynamicFilters.case_priority.length + 
                           dynamicFilters.financial_institution.length;
        
        console.log(`📊 Filter Statistics (Database-Only):
        - Status options: ${dynamicFilters.case_status.length} (${dynamicFilters.case_status.join(', ') || 'none'})
        - Type options: ${dynamicFilters.case_type.length} (${dynamicFilters.case_type.join(', ') || 'none'})
        - Priority options: ${dynamicFilters.case_priority.length} (${dynamicFilters.case_priority.join(', ') || 'none'})
        - FI options: ${dynamicFilters.financial_institution.length} (${dynamicFilters.financial_institution.join(', ') || 'none'})
        - Total options: ${totalOptions}`);
        
        if (totalOptions === 0) {
            console.log('💡 No options found in database. Try: createTestCases(10)');
        }
    }
    
    // Check dropdowns
    const statusSelect = document.getElementById('status');
    const typeSelect = document.getElementById('type');
    const prioritySelect = document.getElementById('priority');
    const fiSelect = document.getElementById('financial_institution');
    
    console.log('📋 Dropdown Status:');
    console.log('  - Status dropdown:', !!statusSelect, statusSelect ? `(${statusSelect.options.length} options)` : '');
    console.log('  - Type dropdown:', !!typeSelect, typeSelect ? `(${typeSelect.options.length} options)` : '');
    console.log('  - Priority dropdown:', !!prioritySelect, prioritySelect ? `(${prioritySelect.options.length} options)` : '');
    console.log('  - FI dropdown:', !!fiSelect, fiSelect ? `(${fiSelect.options.length} options)` : '');
    
    console.log('\n🧪 Available commands:');
    console.log('  - testAllFilterEndpoints() - Test all filter API endpoints');
    console.log('  - createTestCases(10) - Create test cases to populate filters');
    console.log('  - refreshDynamicFilters() - Reload filters from API');
    
    return {
        filtersLoaded: !!dynamicFilters,
        totalOptions: dynamicFilters ? dynamicFilters.case_status.length + dynamicFilters.case_type.length + dynamicFilters.case_priority.length + dynamicFilters.financial_institution.length : 0,
        statusDropdown: !!statusSelect,
        typeDropdown: !!typeSelect,
        priorityDropdown: !!prioritySelect,
        fiDropdown: !!fiSelect,
        dynamicFilters
    };
};

// Test function for manual debugging
window.testSort = function(field = 'total_owing') {
    console.log(`🧪 Testing sort by: ${field}`);
    handleSortAllCompatible(field);
};

// Function to check if everything is working
window.checkCasesJS = function() {
    console.log('🔍 Checking cases.js status...');
    console.log('✅ handleSortAllCompatible:', typeof handleSortAllCompatible);
    console.log('✅ loadAllCasesCompatible:', typeof loadAllCasesCompatible);
    console.log('✅ sortCasesClientSide:', typeof sortCasesClientSide);
    console.log('✅ rebuildTableWithAllCases:', typeof rebuildTableWithAllCases);
    console.log('✅ loadDynamicFilters:', typeof loadDynamicFilters);
    console.log('✅ populateDynamicFilterDropdowns:', typeof populateDynamicFilterDropdowns);
    console.log('✅ refreshDynamicFilters:', typeof refreshDynamicFilters);
    console.log('✅ setupRowClickHandlers:', typeof setupRowClickHandlers);
    console.log('✅ confirmDeleteCase:', typeof confirmDeleteCase);
    console.log('✅ window.caseManager.confirmDeleteCase:', typeof window.caseManager.confirmDeleteCase);
    console.log('✅ currentSort:', currentSort);
    console.log('✅ dynamicFilters:', dynamicFilters);
    
    const headers = document.querySelectorAll('.sortable-header');
    console.log(`✅ Found ${headers.length} sortable headers`);
    
    const tbody = document.querySelector('table tbody');
    console.log('✅ Table tbody found:', !!tbody);
    
    const rows = document.querySelectorAll('.case-row');
    console.log(`✅ Found ${rows.length} case rows`);
    
    const deleteButtons = document.querySelectorAll('.delete-icon');
    console.log(`✅ Found ${deleteButtons.length} delete buttons`);
    
    console.log('🎯 To test sorting: testSort("total_owing")');
    console.log('🎯 To check filters: checkDynamicFilters()');
    console.log('🎯 CaseManager available at: window.caseManager');
    
    return {
        headers: headers.length,
        tbody: !!tbody,
        rows: rows.length,
        deleteButtons: deleteButtons.length,
        dynamicFilters: !!dynamicFilters,
        currentSort,
        ready: true
    };
};

// ===========================================
// AUTO-INITIALIZATION FALLBACK
// ===========================================

// If DOM is already loaded, initialize immediately
if (document.readyState === 'loading') {
    // DOM is still loading, event listener is already set
    console.log('⏳ Waiting for DOM to load...');
} else {
    // DOM is already loaded
    console.log('🚀 DOM already loaded, initializing immediately...');
    initializeCases();
}

// ===========================================
// ENHANCED ERROR HANDLING
// ===========================================

// Global error handler for unhandled errors
window.addEventListener('error', function(e) {
    if (e.message && (e.message.includes('cases') || e.message.includes('filter'))) {
        console.error('🚨 Cases.js Error:', e.error);
        showErrorMessage('An error occurred with the cases table. Please refresh the page.');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('🚨 Unhandled Promise Rejection in cases.js:', e.reason);
    showErrorMessage('An error occurred loading cases data. Please try again.');
});

// Enhanced error handling for filter operations
window.addEventListener('error', function(e) {
    if (e.message && e.message.includes('filter')) {
        console.error('🚨 Filter Error:', e.error);
        showErrorMessage('An error occurred with the filter dropdowns. Using fallback options.');
    }
});

console.log('✅ Cases.js fully loaded and ready with database-only dynamic filters!');
console.log('🧪 Test with: testSort("total_owing")');
console.log('🔍 Debug with: checkCasesJS()');
console.log('🔄 Check filters with: checkDynamicFilters()');
console.log('🔧 Create test cases with: createTestCases(10)');
console.log('🧪 Test all endpoints with: testAllFilterEndpoints()');
console.log('📊 Access via: window.caseManager');