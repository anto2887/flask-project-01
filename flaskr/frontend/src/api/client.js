import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    },
    withCredentials: true  // Important for handling Flask sessions
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        // Add CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => response.data,  // Directly return the data object
    async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
            // Check auth status and redirect to login if needed
            const response = await apiClient.get('/auth/status');
            if (!response.data.authenticated) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;