import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { joinGroup } from '../../api/groups';

export const JoinGroup = () => {
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await joinGroup(inviteCode);
      if (response.status === 'success') {
        navigate('/dashboard');
      }
    } catch (error) {
      setError(error.message || 'Failed to join group');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card max-w-md mx-auto">
        <h1 className="text-2xl font-bold text-[#05445E] mb-6">Join a Group</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="form-group">
            <label htmlFor="invite_code" className="block text-[#05445E] font-medium mb-2">
              Enter Invite Code
            </label>
            <input
              type="text"
              id="invite_code"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              className="w-full p-3 border rounded text-center uppercase tracking-wider"
              placeholder="XXXX-0000"
              pattern="[A-Z0-9]{8}"
              required
              disabled={loading}
            />
          </div>
          <button 
            type="submit" 
            className={`w-full bg-[#189AB4] text-white px-6 py-3 rounded hover:bg-[#05445E] ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={loading}
          >
            {loading ? 'Joining...' : 'Join Group'}
          </button>
        </form>
        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};