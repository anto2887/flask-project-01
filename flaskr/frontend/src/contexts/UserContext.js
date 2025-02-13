import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from './AuthContext';

const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
    const { user: authUser } = useAuth();
    const [profile, setProfile] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (authUser) {
            loadUserProfile();
            loadUserStats();
        } else {
            setProfile(null);
            setStats(null);
            setLoading(false);
        }
    }, [authUser]);

    const loadUserProfile = async () => {
        try {
            const response = await apiClient.get('/users/profile');
            if (response.status === 'success') {
                setProfile(response.data);
            }
        } catch (err) {
            setError('Failed to load user profile');
            console.error('Profile load error:', err);
        }
    };

    const loadUserStats = async () => {
        try {
            const response = await apiClient.get('/users/stats');
            if (response.status === 'success') {
                setStats(response.data);
            }
        } catch (err) {
            setError('Failed to load user stats');
            console.error('Stats load error:', err);
        } finally {
            setLoading(false);
        }
    };

    const updateProfile = async (updateData) => {
        try {
            const response = await apiClient.put('/users/profile', updateData);
            if (response.status === 'success') {
                setProfile(prev => ({ ...prev, ...updateData }));
                return true;
            }
            return false;
        } catch (err) {
            setError('Failed to update profile');
            console.error('Profile update error:', err);
            return false;
        }
    };

    return (
        <UserContext.Provider value={{
            profile,
            stats,
            loading,
            error,
            updateProfile,
            refreshProfile: loadUserProfile,
            refreshStats: loadUserStats
        }}>
            {children}
        </UserContext.Provider>
    );
};

export const useUser = () => {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUser must be used within a UserProvider');
    }
    return context;
};