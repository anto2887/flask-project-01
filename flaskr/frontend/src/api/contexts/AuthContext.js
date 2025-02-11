import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const response = await apiClient.get('/auth/status');
            if (response.status === 'success' && response.data.authenticated) {
                setUser(response.data.user);
            } else {
                setUser(null);
            }
        } catch (err) {
            console.error('Auth check failed:', err);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        try {
            const response = await apiClient.post('/auth/login', { username, password });
            if (response.status === 'success') {
                setUser(response.data);
                setError(null);
                return response.data;
            }
            throw new Error(response.message || 'Login failed');
        } catch (err) {
            setError(err.response?.data?.message || 'Login failed');
            throw err;
        }
    };

    const register = async (userData) => {
        try {
            const response = await apiClient.post('/auth/register', userData);
            if (response.status === 'success') {
                return response.data;
            }
            throw new Error(response.message || 'Registration failed');
        } catch (err) {
            setError(err.response?.data?.message || 'Registration failed');
            throw err;
        }
    };

    const logout = async () => {
        try {
            await apiClient.post('/auth/logout');
            setUser(null);
        } catch (err) {
            console.error('Logout error:', err);
        }
    };

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            error,
            login,
            logout,
            register,
            isAuthenticated: !!user
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};