import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { UserProvider } from './contexts/UserContext';
import { MatchProvider } from './contexts/MatchContext';
import { PredictionProvider } from './contexts/PredictionContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import MainLayout from './components/layout/MainLayout';
import AppRoutes from './routes';

const App = () => {
    return (
        <ErrorBoundary>
            <Router>
                <AuthProvider>
                    <UserProvider>
                        <MatchProvider>
                            <PredictionProvider>
                                <MainLayout>
                                    <AppRoutes />
                                </MainLayout>
                            </PredictionProvider>
                        </MatchProvider>
                    </UserProvider>
                </AuthProvider>
            </Router>
        </ErrorBoundary>
    );
};

export default App;