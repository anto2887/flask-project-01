import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

const MatchContext = createContext(null);

export const MatchProvider = ({ children }) => {
    const [liveMatches, setLiveMatches] = useState([]);
    const [fixtures, setFixtures] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pollingInterval, setPollingInterval] = useState(60000); // 1 minute default

    const fetchLiveMatches = useCallback(async () => {
        try {
            const response = await apiClient.get('/matches/live');
            if (response.status === 'success') {
                setLiveMatches(response.data);
            }
        } catch (err) {
            console.error('Error fetching live matches:', err);
            setError('Failed to load live matches');
        }
    }, []);

    const fetchFixtures = useCallback(async (params) => {
        try {
            setLoading(true);
            const response = await apiClient.get('/matches/fixtures', { params });
            if (response.status === 'success') {
                setFixtures(response.data);
            }
        } catch (err) {
            console.error('Error fetching fixtures:', err);
            setError('Failed to load fixtures');
        } finally {
            setLoading(false);
        }
    }, []);

    // Start polling for live matches
    useEffect(() => {
        fetchLiveMatches();
        const interval = setInterval(fetchLiveMatches, pollingInterval);
        
        return () => clearInterval(interval);
    }, [fetchLiveMatches, pollingInterval]);

    const getMatch = async (matchId) => {
        try {
            const response = await apiClient.get(`/matches/${matchId}`);
            if (response.status === 'success') {
                return response.data;
            }
            throw new Error(response.message || 'Failed to load match');
        } catch (err) {
            console.error('Error fetching match:', err);
            throw err;
        }
    };

    const updatePollingInterval = (newInterval) => {
        setPollingInterval(newInterval);
    };

    return (
        <MatchContext.Provider value={{
            liveMatches,
            fixtures,
            loading,
            error,
            fetchFixtures,
            getMatch,
            updatePollingInterval,
            refreshLiveMatches: fetchLiveMatches
        }}>
            {children}
        </MatchContext.Provider>
    );
};

export const useMatches = () => {
    const context = useContext(MatchContext);
    if (!context) {
        throw new Error('useMatches must be used within a MatchProvider');
    }
    return context;
};