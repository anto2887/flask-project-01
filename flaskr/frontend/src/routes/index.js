// src/routes/index.js
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Auth Components
import { Login } from '../components/auth/Login';
import { Register } from '../components/auth/Register';

// Route Groups
import { PublicRoutes } from './PublicRoutes';
import { PrivateRoutes } from './PrivateRoutes';
import { DashboardRoutes } from './DashboardRoutes';
import { PredictionRoutes } from './PredictionRoutes';
import { GroupRoutes } from './GroupRoutes';

// Error Page
import { NotFound } from '../components/common/ErrorPages';

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<PublicRoutes />}>
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
        } />
        <Route path="/register" element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />
        } />
      </Route>

      {/* Protected Routes */}
      <Route element={<PrivateRoutes />}>
        <Route path="/dashboard/*" element={<DashboardRoutes />} />
        <Route path="/predictions/*" element={<PredictionRoutes />} />
        <Route path="/groups/*" element={<GroupRoutes />} />
      </Route>

      {/* Default redirect */}
      <Route path="/" element={
        isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
      } />

      {/* 404 page */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRoutes;