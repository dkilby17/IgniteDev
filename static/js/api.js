// static/js/api.js - Basic API client for Flask templates
const API_BASE_URL = 'http://127.0.0.1:8000/api';

class ApiClient {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            ...options,
            headers: {
                ...this.getAuthHeaders(),
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                console.warn('Unauthorized access - redirecting to login');
                this.logout();
                return;
            }

            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `HTTP error! status: ${response.status}`;
                
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || errorJson.message || errorMessage;
                } catch (e) {
                    if (errorText) {
                        errorMessage += `, message: ${errorText}`;
                    }
                }
                
                throw new Error(errorMessage);
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

    logout() {
        console.log('🚪 API Client logout initiated...');
        
        try {
            // Clear all authentication data
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
            localStorage.removeItem('temp_token');
            localStorage.removeItem('pending_user_info');
            localStorage.removeItem('admin_access_confirmed');
            
            console.log('✅ Cleared all localStorage items');
            
            // Redirect to login
            window.location.href = '/login';
            
        } catch (error) {
            console.error('❌ Logout error:', error);
            // Force redirect even if there's an error
            window.location.href = '/login';
        }
    }
}

// Create global API client instance
window.api = new ApiClient();