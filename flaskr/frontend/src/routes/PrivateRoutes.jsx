import React from 'react';
import { Outlet } from 'react-router-dom';
import ProtectedRoute from '../components/auth/ProtectedRoute';

export const PrivateRoutes = () => {
  return (
    <ProtectedRoute>
      <Outlet />
    </ProtectedRoute>
  );
};

export default PrivateRoutes;