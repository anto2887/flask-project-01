import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const PublicRoutes = () => {
  const { isAuthenticated } = useAuth();

  // Redirect authenticated users away from public routes
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};