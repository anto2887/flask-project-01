import React from 'react';
import { useLocation } from 'react-router-dom';
import Navigation from './Navigation';
import Sidebar from './Sidebar';
import Footer from './Footer';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

const MainLayout = ({ children }) => {
  const { loading, isAuthenticated } = useAuth();
  const location = useLocation();
  const isAuthPage = ['/login', '/register'].includes(location.pathname);

  if (loading) {
    return <LoadingSpinner fullScreen />;
  }

  // Use simplified layout for auth pages
  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navigation />
      <div className="flex-grow flex">
        {isAuthenticated && <Sidebar />}
        <main className="flex-grow p-6">
          <div className="container mx-auto">
            {children}
          </div>
        </main>
      </div>
      <Footer />
    </div>
  );
};

export default MainLayout;