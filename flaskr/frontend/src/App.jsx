import React from 'react';
import './style.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Login } from './components/auth/Login';
import { Register } from './components/auth/Register';
import { GroupForm } from './components/groups/GroupForm';

const App = () => (
  <Router>
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/group/create" element={<GroupForm />} />
    </Routes>
  </Router>
);

export default App;