import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { GroupProvider } from './contexts/GroupContext';
import { MatchProvider } from './contexts/MatchContext';
import { PredictionProvider } from './contexts/PredictionContext';
import StateProvider from './components/state/StateProvider';
import ErrorBoundary from './components/common/ErrorBoundary';
import MainLayout from './components/layout/MainLayout';
import AppRoutes from './routes';
import PredictionForm from './components/predictions/PredictionForm';

const App = () => {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <NotificationProvider>
            <GroupProvider>
              <MatchProvider>
                <PredictionProvider>
                  <StateProvider>
                    <MainLayout>
                      <Routes>
                        <Route path="/predictions/new" element={<PredictionForm />} />
                      </Routes>
                    </MainLayout>
                  </StateProvider>
                </PredictionProvider>
              </MatchProvider>
            </GroupProvider>
          </NotificationProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
};

export default App;