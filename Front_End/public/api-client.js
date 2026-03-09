/**
 * api-client.js - Centralized API client for TimeWeaver
 * Handles communication with the FastAPI backend on port 8001.
 */

const API_BASE_URL = 'http://127.0.0.1:8001/api/v1';

class ApiClient {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
        console.log('ApiClient initialized with base URL:', this.baseUrl);
    }

    /**
     * Get the stored authentication token
     */
    getToken() {
        return localStorage.getItem('token');
    }

    /**
     * Set the authentication token
     */
    setToken(token) {
        localStorage.setItem('token', token);
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('tw_session'); // Legacy cleanup
    }

    /**
     * Core request wrapper
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...(options.headers || {})
        };

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            // Handle 401 Unauthorized
            if (response.status === 401) {
                this.clearAuth();
                if (!window.location.pathname.endsWith('login.html')) {
                    window.location.href = '/login.html';
                }
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Unauthorized');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${url}]:`, error);
            throw error;
        }
    }

    /**
     * Get request
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * Post request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Put request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Delete request
     */
    async del(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Login request - returns { success, user, error } for easy consumption
     */
    async login(username, password) {
        const url = `${this.baseUrl}/auth/login`;
        console.log('Attempting login to:', url);
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData.toString()
            });

            const data = await response.json();

            if (!response.ok) {
                return { success: false, error: data.detail || 'Login failed' };
            }

            this.setToken(data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            return { success: true, user: data.user };
        } catch (error) {
            console.error('Login request error:', error);
            return { success: false, error: 'Connection error. Is server running?' };
        }
    }

    /**
     * Logout helper
     */
    logout() {
        this.clearAuth();
        window.location.href = '/login.html';
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }
}

// Global instance
const API = new ApiClient();
window.API = API; // Global accessibility
