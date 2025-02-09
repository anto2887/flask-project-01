import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../../api/auth';

export const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await login(formData.username, formData.password);
      if (response.status === 'success') {
        navigate('/dashboard');
      }
    } catch (error) {
      setError(error.message || 'Login failed');
      console.error('Login failed:', error);
    }
  };

  return (
    <div className="container">
      <div className="card login-container">
        <img src="/static/pictures/soccer-ball.png" alt="Soccer Ball" className="logo" />
        <h2>PrdiktIt - Log In</h2>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <button type="submit" className="btn">Log In</button>
          </div>
        </form>
        <div className="footer">
          <Link to="/register">Create Account</Link> | 
          <Link to="/reset-password">Forgot Password?</Link>
        </div>
      </div>
    </div>
  );
};