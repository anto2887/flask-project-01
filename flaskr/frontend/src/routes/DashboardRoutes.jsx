import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Dashboard } from '../components/dashboard/Dashboard';
import { Profile } from '../components/dashboard/Profile';
import { Settings } from '../components/dashboard/Settings';

export const DashboardRoutes = () => {
  return (
    <Routes>
      <Route index element={<Dashboard />} />
      <Route path="profile" element={<Profile />} />
      <Route path="settings" element={<Settings />} />
    </Routes>
  );
};