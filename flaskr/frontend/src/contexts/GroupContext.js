import React, { createContext, useContext, useState, useCallback } from 'react';
import apiClient from '../api/client';

const GroupContext = createContext(null);

export const GroupProvider = ({ children }) => {
    const [userGroups, setUserGroups] = useState([]);
    const [currentGroup, setCurrentGroup] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchUserGroups = useCallback(async () => {
        try {
            setLoading(true);
            const response = await apiClient.get('/groups');
            if (response.status === 'success') {
                setUserGroups(response.data);
            }
        } catch (err) {
            console.error('Error fetching groups:', err);
            setError('Failed to load groups');
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchTeamsForLeague = async (leagueId) => {
        try {
            const response = await apiClient.get(`/teams/${leagueId}`);
            if (response.status === 'success') {
                return response.data;
            }
            throw new Error('Failed to fetch teams');
        } catch (err) {
            console.error('Error fetching teams:', err);
            throw err;
        }
    };

    const createGroup = async (groupData) => {
        try {
            setLoading(true);
            const response = await apiClient.post('/groups', {
                name: groupData.name,
                league: groupData.league,
                privacy_type: 'PRIVATE',
                tracked_teams: groupData.tracked_teams,
                description: groupData.description || ''
            });
            
            if (response.status === 'success') {
                setCurrentGroup(response.data);
                setUserGroups(prev => [...prev, response.data]);
                return response;
            }
            throw new Error(response.message || 'Failed to create group');
        } catch (err) {
            setError(err.message || 'Failed to create group');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const joinGroup = async (inviteCode) => {
        try {
            setLoading(true);
            const response = await apiClient.post('/groups/join', { invite_code: inviteCode });
            if (response.status === 'success') {
                await fetchUserGroups(); // Refresh groups list
                return true;
            }
            return false;
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to join group');
            return false;
        } finally {
            setLoading(false);
        }
    };

    const fetchGroupDetails = async (groupId) => {
        try {
            setLoading(true);
            const response = await apiClient.get(`/groups/${groupId}`);
            if (response.status === 'success') {
                setCurrentGroup(response.data);
                return response.data;
            }
            throw new Error(response.message || 'Failed to load group details');
        } catch (err) {
            setError(err.message || 'Failed to load group details');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const fetchGroupMembers = async (groupId) => {
        try {
            const response = await apiClient.get(`/groups/${groupId}/members`);
            if (response.status === 'success') {
                return response.data;
            }
            throw new Error(response.message || 'Failed to load group members');
        } catch (err) {
            setError(err.message || 'Failed to load group members');
            throw err;
        }
    };

    const manageMember = async (groupId, userId, action) => {
        try {
            setLoading(true);
            const response = await apiClient.post(`/groups/${groupId}/members`, {
                user_id: userId,
                action
            });
            if (response.status === 'success') {
                await fetchGroupDetails(groupId);
                return true;
            }
            return false;
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to manage member');
            return false;
        } finally {
            setLoading(false);
        }
    };

    const regenerateInviteCode = async (groupId) => {
        try {
            setLoading(true);
            const response = await apiClient.post(`/groups/${groupId}/regenerate-code`);
            if (response.status === 'success') {
                await fetchGroupDetails(groupId);
                return response.data.invite_code;
            }
            throw new Error('Failed to regenerate invite code');
        } catch (err) {
            setError(err.message || 'Failed to regenerate invite code');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const clearError = () => {
        setError(null);
    };

    return (
        <GroupContext.Provider value={{
            userGroups,
            currentGroup,
            loading,
            error,
            fetchUserGroups,
            createGroup,
            joinGroup,
            fetchGroupDetails,
            fetchGroupMembers,
            manageMember,
            fetchTeamsForLeague,
            regenerateInviteCode,
            clearError,
            clearCurrentGroup: () => setCurrentGroup(null)
        }}>
            {children}
        </GroupContext.Provider>
    );
};

export const useGroups = () => {
    const context = useContext(GroupContext);
    if (!context) {
        throw new Error('useGroups must be used within a GroupProvider');
    }
    return context;
};