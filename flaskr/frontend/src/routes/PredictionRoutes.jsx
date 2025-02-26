import React from 'react';
import { Routes, Route } from 'react-router-dom';
import PredictionList from '../components/predictions/PredictionList';
import PredictionForm from '../components/dashboard/PredictionForm';
import PredictionHistory from '../components/predictions/PredictionHistory';
import PredictionStats from '../components/predictions/PredictionStats';

export const PredictionRoutes = () => {
  return (
    <Routes>
      <Route index element={<PredictionList />} />
      <Route path="new" element={<PredictionForm />} />
      <Route path="edit/:id" element={<PredictionForm />} />
      <Route path="history" element={<PredictionHistory />} />
      <Route path="stats" element={<PredictionStats />} />
    </Routes>
  );
};

export default PredictionRoutes;