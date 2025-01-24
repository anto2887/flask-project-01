import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Auth0ProviderWithConfig } from './auth/auth0-provider-with-config';
import { PrivateRoute } from './components/common/PrivateRoute';
import { useAuth } from './hooks/useAuth';

// Import your existing components here
// import { GroupForm } from './components/groups/GroupForm';
// import { TeamSelector } from './components/groups/TeamSelector';

const App = () => {
  return (
    <Auth0ProviderWithConfig>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          {/* Add more routes as needed */}
        </Routes>
      </Router>
    </Auth0ProviderWithConfig>
  );
};

export default App;