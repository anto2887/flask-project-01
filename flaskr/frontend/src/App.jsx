import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import StateProvider from './components/state/StateProvider';
import ErrorBoundary from './components/common/ErrorBoundary';
import MainLayout from './components/layout/MainLayout';
import AppRoutes from './routes';

/**
 * Root application component.
 * Uses StateProvider to manage all application state through contexts.
 * ErrorBoundary catches any rendering errors.
 * Router enables client-side routing.
 * MainLayout provides consistent layout structure.
 */
const App = () => {
    return (
        <ErrorBoundary>
            <Router>
                <StateProvider>
                    <MainLayout>
                        <AppRoutes />
                    </MainLayout>
                </StateProvider>
            </Router>
        </ErrorBoundary>
    );
};

export default App;