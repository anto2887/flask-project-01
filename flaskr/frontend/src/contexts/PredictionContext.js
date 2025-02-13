import React, { createContext, useContext, useState, useCallback } from 'react';
import apiClient from '../api/client';

const PredictionContext = createContext(null);

export const PredictionProvider = ({ children }) => {
    const [userPredictions, setUserPredictions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchUserPredictions = useCallback(async (params) => {
        try {
            setLoading(true);
            const response = await apiClient.get('/predictions/user', { params });
            if (response.status === 'success') {
                setUserPredictions(response.data);
            }
        } catch (err) {
            console.error('Error fetching predictions:', err);
            setError('Failed to load predictions');
        } finally {
            setLoading(false);
        }
    }, []);

    const submitPrediction = async (predictionData) => {
        try {
            setLoading(true);
            const response = await apiClient.post('/predictions', predictionData);
            if (response.status === 'success') {
                // Update local state with new prediction
                setUserPredictions(prev => {
                    const index = prev.findIndex(p => p.fixture_id === predictionData.fixture_id);
                    if (index >= 0) {
                        const updated = [...prev];
                        updated[index] = response.data;
                        return updated;
                    }
                    return [...prev, response.data];
                });
                return response.data;
            }
            throw new Error(response.message || 'Failed to submit prediction');
        } catch (err) {
            setError(err.message || 'Failed to submit prediction');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const resetPrediction = async (predictionId) => {
        try {
            setLoading(true);
            const response = await apiClient.post(`/predictions/reset/${predictionId}`);
            if (response.status === 'success') {
                // Remove prediction from local state
                setUserPredictions(prev => 
                    prev.filter(p => p.prediction_id !== predictionId)
                );
                return true;
            }
            return false;
        } catch (err) {
            setError('Failed to reset prediction');
            return false;
        } finally {
            setLoading(false);
        }
    };

    return (
        <PredictionContext.Provider value={{
            userPredictions,
            loading,
            error,
            fetchUserPredictions,
            submitPrediction,
            resetPrediction
        }}>
            {children}
        </PredictionContext.Provider>
    );
};

export const usePredictions = () => {
    const context = useContext(PredictionContext);
    if (!context) {
        throw new Error('usePredictions must be used within a PredictionProvider');
    }
    return context;
};