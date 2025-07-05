// js/sidebar.js - Updated for Flask admin system
class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.mainContent = document.getElementById('mainContent');
        this.toggleBtn = document.getElementById('sidebarToggle');
        this.isMobile = window.innerWidth <= 768;
        this.userRoles = [];
        this.adminCheckAttempts = 0;
        this.maxAdminCheckAttempts = 3;
        this.adminAccessConfirmed = false;
        
        this.init();
    }

    init() {
        this.loadUserRoles();
        this.forcePermanentCollapse();
        this.bindEvents();
        this.handleResize();
        
        // Check admin access with Flask-specific methods
        this.initializeAdminAccess();
    }

    initializeAdminAccess() {
        // Strategy 1: Check if admin info is in session (server-side rendered)
        const adminFromSession = this.checkAdminFromSession();
        if (adminFromSession) {
            this.showAdminMenu();
            this.adminAccessConfirmed = true;
            return;
        }

        // Strategy 2: Check localStorage
        const adminFromStorage = this.checkAdminFromStorage();
        if (adminFromStorage) {
            this.showAdminMenu();
            this.adminAccessConfirmed = true;
            return;
        }

        // Strategy 3: Check if we're currently on admin page
        if (window.location.pathname.includes('/admin')) {
            this.showAdminMenu();
            this.setAdminInStorage();
            this.adminAccessConfirmed = true;
            return;
        }

        // Strategy 4: Flask API checking
        this.checkAdminAccessWithRetry();
    }

    checkAdminFromSession() {
        try {
            // Check if the admin menu item is already visible (server-side rendered)
            const adminMenuItem = document.getElementById('adminMenuItem');
            if (adminMenuItem && adminMenuItem.style.display !== 'none' && !adminMenuItem.classList.contains('hidden')) {
                console.log('✅ Admin access confirmed from server-side rendering');
                return true;
            }

            // Check for Flask-specific data attributes or hidden fields
            const adminFlag = document.querySelector('[data-admin-access="true"]');
            if (adminFlag) {
                console.log('✅ Admin access confirmed from data attribute');
                return true;
            }

            return false;
        } catch (error) {
            console.log('❌ Error checking admin from session:', error);
            return false;
        }
    }

    checkAdminFromStorage() {
        try {
            const adminConfirmed = localStorage.getItem('admin_access_confirmed');
            const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
            
            if (adminConfirmed === 'true') {
                console.log('✅ Admin access confirmed from storage');
                return true;
            }

            // Check for admin flag in user info (set by Flask login)
            if (userInfo.is_admin === true) {
                console.log('✅ Admin flag found in user info');
                this.setAdminInStorage();
                return true;
            }

            const roles = userInfo.user_roles || userInfo.roles || [];
            const hasAdminRole = roles.some(role => 
                role.toLowerCase() === 'admin' || 
                role.toLowerCase() === 'administrator' ||
                role.toLowerCase() === 'system_admin'
            );

            if (hasAdminRole) {
                console.log('✅ Admin role found in user info');
                this.setAdminInStorage();
                return true;
            }

            return false;
        } catch (error) {
            console.log('❌ Error checking admin from storage:', error);
            return false;
        }
    }

    setAdminInStorage() {
        try {
            localStorage.setItem('admin_access_confirmed', 'true');
            
            // Update user info with admin flag
            const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
            userInfo.is_admin = true;
            if (!userInfo.user_roles) {
                userInfo.user_roles = [];
            }
            if (!userInfo.user_roles.includes('admin')) {
                userInfo.user_roles.push('admin');
            }
            localStorage.setItem('user_info', JSON.stringify(userInfo));
            
            console.log('✅ Admin access saved to storage');
        } catch (error) {
            console.log('❌ Error saving admin access:', error);
        }
    }

    checkAdminAccessWithRetry() {
        // Check immediately
        this.checkAdminAccess();
        
        // Check 2 more times with longer intervals
        setTimeout(() => {
            if (!this.adminAccessConfirmed) {
                this.checkAdminAccess();
            }
        }, 2000);
        
        setTimeout(() => {
            if (!this.adminAccessConfirmed) {
                this.checkAdminAccess();
            }
        }, 5000);
    }

    async checkAdminAccess() {
        if (this.adminAccessConfirmed) {
            return;
        }

        const adminMenuItem = document.getElementById('adminMenuItem');
        if (!adminMenuItem) {
            console.log('❌ Admin menu item not found in DOM');
            return;
        }

        try {
            const hasAccess = await this.verifyAdminAccess();
            if (hasAccess) {
                console.log('✅ Admin access confirmed via Flask API');
                this.showAdminMenu();
                this.setAdminInStorage();
                this.adminAccessConfirmed = true;
            }
        } catch (error) {
            console.log('❌ Flask admin check failed:', error);
        }
    }

    async verifyAdminAccess() {
        try {
            console.log('🔍 Verifying admin access via Flask API...');
            
            // Flask admin endpoints to check
            const endpoints = [
                '/admin/api/stats',
                '/admin/api/roles'
            ];

            for (const endpoint of endpoints) {
                try {
                    console.log(`🔍 Checking Flask endpoint: ${endpoint}`);
                    const response = await fetch(endpoint, {
                        method: 'GET',
                        credentials: 'same-origin', // Important for Flask session
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok) {
                        console.log(`✅ Admin access confirmed via ${endpoint}`);
                        return true;
                    } else {
                        console.log(`❌ ${endpoint} returned status: ${response.status}`);
                    }
                } catch (error) {
                    console.log(`❌ Error checking ${endpoint}:`, error);
                }
            }
            
            return false;
        } catch (error) {
            console.log('❌ Flask admin API request failed:', error);
            return false;
        }
    }

    showAdminMenu() {
        const adminMenuItem = document.getElementById('adminMenuItem');
        if (adminMenuItem) {
            adminMenuItem.style.display = 'block';
            adminMenuItem.style.visibility = 'visible';
            adminMenuItem.classList.remove('hidden');
            console.log('✅ Admin menu item shown');
            
            this.adminAccessConfirmed = true;
        } else {
            console.log('❌ Admin menu item not found when trying to show');
        }
    }

    hideAdminMenu() {
        const adminMenuItem = document.getElementById('adminMenuItem');
        if (adminMenuItem) {
            adminMenuItem.style.display = 'none';
            console.log('❌ Admin menu item hidden');
        }
    }

    loadUserRoles() {
        try {
            const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
            this.userRoles = userInfo.user_roles || userInfo.roles || [];
            
            console.log('👤 Loaded user roles:', this.userRoles);
            console.log('👤 User is admin:', userInfo.is_admin);
            
            // Check if we're on admin page
            if (window.location.pathname.includes('/admin')) {
                console.log('📍 On admin page - confirming admin access');
                if (!this.userRoles.includes('admin')) {
                    this.userRoles.push('admin');
                }
                this.setAdminInStorage();
            }
        } catch (error) {
            console.log('❌ Error loading user roles:', error);
            this.userRoles = [];
        }
    }

    forcePermanentCollapse() {
        // Force sidebar to always be in collapsed (icon-only) mode
        if (!this.isMobile) {
            this.sidebar.classList.add('collapsed');
            this.mainContent.classList.add('expanded');
            
            this.sidebar.style.transition = 'none';
            this.mainContent.style.transition = 'none';
            
            if (this.toggleBtn) {
                this.toggleBtn.style.display = 'flex';
                this.toggleBtn.style.opacity = '0.5';
                this.toggleBtn.style.cursor = 'not-allowed';
                this.toggleBtn.title = 'Sidebar expansion disabled';
            }
        }
    }

    bindEvents() {
        window.addEventListener('resize', () => this.handleResize());

        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => {
                if (this.isMobile) {
                    this.toggleMobile();
                }
            });
        }

        document.addEventListener('click', (e) => {
            if (this.isMobile && this.sidebar && !this.sidebar.contains(e.target) && 
                !this.toggleBtn.contains(e.target) && this.sidebar.classList.contains('mobile-open')) {
                this.closeMobile();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isMobile && this.sidebar.classList.contains('mobile-open')) {
                this.closeMobile();
            }
        });

        this.bindNavigationEvents();

        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.adminAccessConfirmed) {
                setTimeout(() => this.checkAdminAccess(), 1000);
            }
        });

        window.addEventListener('storage', (e) => {
            if (e.key === 'admin_access_confirmed' && e.newValue === 'true') {
                this.showAdminMenu();
                this.adminAccessConfirmed = true;
            }
        });
    }

    bindNavigationEvents() {
        const navItems = document.querySelectorAll('.sidebar-nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const href = item.getAttribute('href');
                
                if (href && href.includes('/admin')) {
                    console.log('🔄 Navigating to admin page');
                    this.setAdminInStorage();
                }
                
                if (this.isMobile) {
                    this.closeMobile();
                }
            });
        });
    }

    // Mobile methods
    toggleMobile() {
        this.sidebar.classList.toggle('mobile-open');
        
        if (this.sidebar.classList.contains('mobile-open')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }

    closeMobile() {
        this.sidebar.classList.remove('mobile-open');
        document.body.style.overflow = '';
    }

    openMobile() {
        this.sidebar.classList.add('mobile-open');
        document.body.style.overflow = 'hidden';
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;

        if (wasMobile !== this.isMobile) {
            this.sidebar.classList.remove('mobile-open');
            document.body.style.overflow = '';
            
            if (this.isMobile) {
                if (this.toggleBtn) {
                    this.toggleBtn.style.display = 'flex';
                    this.toggleBtn.style.opacity = '1';
                    this.toggleBtn.style.cursor = 'pointer';
                    this.toggleBtn.title = '';
                }
                this.sidebar.classList.remove('collapsed');
                this.mainContent.classList.remove('expanded');
            } else {
                this.forcePermanentCollapse();
            }
            
            if (!this.adminAccessConfirmed) {
                setTimeout(() => this.checkAdminAccess(), 500);
            }
        }
    }

    // Public methods
    getState() {
        return {
            isCollapsed: !this.isMobile,
            isMobile: this.isMobile,
            isOpen: this.sidebar.classList.contains('mobile-open'),
            userRoles: this.userRoles,
            hasAdminAccess: this.adminAccessConfirmed,
            adminMenuVisible: document.getElementById('adminMenuItem')?.style.display !== 'none'
        };
    }

    setActiveFromCurrentPage() {
        const currentPath = window.location.pathname;
        
        const navItems = document.querySelectorAll('.sidebar-nav-item');
        navItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && (currentPath.includes(href) || currentPath.endsWith(href))) {
                this.setActiveNavItem(item);
            }
        });
    }

    setActiveNavItem(activeItem) {
        const navItems = document.querySelectorAll('.sidebar-nav-item');
        navItems.forEach(item => item.classList.remove('active'));
        activeItem.classList.add('active');
    }

    updateUserRoles(roles, isAdmin = false) {
        console.log('🔄 Updating user roles:', roles, 'isAdmin:', isAdmin);
        this.userRoles = roles || [];
        
        const hasAdminRole = isAdmin || this.userRoles.some(role => 
            role.toLowerCase() === 'admin' || 
            role.toLowerCase() === 'administrator'
        );
        
        if (hasAdminRole) {
            this.showAdminMenu();
            this.setAdminInStorage();
            this.adminAccessConfirmed = true;
        }
    }

    refreshAdminAccess() {
        console.log('🔄 Refreshing admin access check');
        this.loadUserRoles();
        this.adminAccessConfirmed = false;
        this.checkAdminAccess();
    }

    forceShowAdminMenu() {
        console.log('🔧 Force showing admin menu');
        this.showAdminMenu();
        this.setAdminInStorage();
        this.adminAccessConfirmed = true;
    }

    clearAdminAccess() {
        localStorage.removeItem('admin_access_confirmed');
        this.adminAccessConfirmed = false;
        this.hideAdminMenu();
    }
}

// Initialize sidebar manager
let sidebarManager;

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing sidebar manager for Flask');
    sidebarManager = new SidebarManager();
    
    sidebarManager.setActiveFromCurrentPage();
    window.sidebarManager = sidebarManager;
    window.forceShowAdminMenu = () => sidebarManager.forceShowAdminMenu();
});

// Global utility functions
window.toggleSidebar = function() {
    if (window.sidebarManager && window.sidebarManager.isMobile) {
        window.sidebarManager.toggle();
    }
};

window.getSidebarState = function() {
    return window.sidebarManager ? window.sidebarManager.getState() : null;
};

window.updateSidebarUserRoles = function(roles, isAdmin) {
    if (window.sidebarManager) {
        window.sidebarManager.updateUserRoles(roles, isAdmin);
    }
};

window.refreshSidebarAdminAccess = function() {
    if (window.sidebarManager) {
        window.sidebarManager.refreshAdminAccess();
    }
};

window.emergencyShowAdminMenu = function() {
    console.log('🚨 Emergency admin menu activation');
    if (window.sidebarManager) {
        window.sidebarManager.forceShowAdminMenu();
    } else {
        const adminMenuItem = document.getElementById('adminMenuItem');
        if (adminMenuItem) {
            adminMenuItem.style.display = 'block';
            localStorage.setItem('admin_access_confirmed', 'true');
            console.log('✅ Emergency admin menu shown');
        }
    }
};

window.clearAdminAccess = function() {
    if (window.sidebarManager) {
        window.sidebarManager.clearAdminAccess();
    }
    localStorage.removeItem('admin_access_confirmed');
};

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SidebarManager;
}