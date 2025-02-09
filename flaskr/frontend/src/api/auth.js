import { handleApiError, getDefaultHeaders } from './utils';

const BASE_URL = '/api/auth';

/**
 * Login user
 * @param {string} username
 * @param {string} password
 * @returns {Promise<Object>}
 */
export const login = async (username, password) => {
  try {
    const response = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      body: JSON.stringify({ username, password }),
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw await handleApiError(response);
    }
    
    return await response.json();
  } catch (error) {
    throw error;
  }
};

/**
 * Register new user
 * @param {string} username
 * @param {string} password
 * @returns {Promise<Object>}
 */
export const register = async (username, password) => {
  try {
    const response = await fetch(`${BASE_URL}/register`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      body: JSON.stringify({ username, password }),
      credentials: 'include',
    });

    if (!response.ok) {
      throw await handleApiError(response);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

/**
 * Logout current user
 * @returns {Promise<Object>}
 */
export const logout = async () => {
  try {
    const response = await fetch(`${BASE_URL}/logout`, {
      method: 'POST',
      headers: getDefaultHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw await handleApiError(response);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

/**
 * Check authentication status
 * @returns {Promise<Object>}
 */
export const checkAuthStatus = async () => {
  try {
    const response = await fetch(`${BASE_URL}/status`, {
      headers: getDefaultHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw await handleApiError(response);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};