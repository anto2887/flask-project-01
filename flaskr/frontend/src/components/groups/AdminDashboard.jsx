import React, { useState, useEffect } from 'react';
import { 
  getGroupById, 
  getGroupMembers, 
  manageMembers, 
  removeMember, 
  regenerateInviteCode 
} from '../../api/groups';

export const AdminDashboard = ({ groupId }) => {
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGroupData = async () => {
      setLoading(true);
      try {
        // Get group details including analytics
        const groupResponse = await getGroupById(groupId);
        if (groupResponse.status === 'success') {
          setGroup(groupResponse.data);
        }

        // Get group members
        const membersResponse = await getGroupMembers(groupId);
        if (membersResponse.status === 'success') {
          setMembers(membersResponse.data);
          // Filter pending requests from members
          setPendingRequests(membersResponse.data.filter(
            member => member.status === 'PENDING'
          ));
        }
      } catch (err) {
        setError(err.message || 'Failed to fetch group data');
        console.error('Error fetching group data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGroupData();
  }, [groupId]);

  const handleMemberAction = async (userId, action) => {
    try {
      const response = await manageMembers(groupId, action, [userId]);
      if (response.status === 'success') {
        // Refresh member list
        const updatedMembers = await getGroupMembers(groupId);
        if (updatedMembers.status === 'success') {
          setMembers(updatedMembers.data);
          setPendingRequests(updatedMembers.data.filter(
            member => member.status === 'PENDING'
          ));
        }
      }
    } catch (err) {
      console.error(`Failed to ${action} member:`, err);
      setError(err.message || `Failed to ${action} member`);
    }
  };

  const handleRegenerateCode = async () => {
    try {
      const response = await regenerateInviteCode(groupId);
      if (response.status === 'success') {
        setGroup(prev => ({
          ...prev,
          invite_code: response.data.invite_code
        }));
      }
    } catch (err) {
      setError(err.message || 'Failed to regenerate invite code');
    }
  };

  if (loading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-center p-8 text-red-600">
        Error: {error}
      </div>
    );
  }

  if (!group) return null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-[#05445E]">{group.name}</h1>
            <p className="text-[#189AB4]">{group.league}</p>
          </div>
          <div>
            <p className="text-sm">Invite Code: {group.invite_code}</p>
            <button
              onClick={handleRegenerateCode}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Regenerate Code
            </button>
          </div>
        </div>

        {/* Members Section */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Members ({members.length})</h2>
          <div className="grid gap-4">
            {members.map(member => (
              <div key={member.user_id} className="flex justify-between items-center p-4 bg-gray-50 rounded">
                <div>
                  <p className="font-medium">{member.username}</p>
                  <p className="text-sm text-gray-600">{member.role}</p>
                </div>
                {member.role !== 'ADMIN' && (
                  <div className="space-x-2">
                    <button
                      onClick={() => handleMemberAction(member.user_id, 'PROMOTE_MODERATOR')}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Promote
                    </button>
                    <button
                      onClick={() => handleMemberAction(member.user_id, 'REMOVE')}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Pending Requests Section */}
        {pendingRequests.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Pending Requests</h2>
            <div className="grid gap-4">
              {pendingRequests.map(request => (
                <div key={request.user_id} className="flex justify-between items-center p-4 bg-yellow-50 rounded">
                  <p className="font-medium">{request.username}</p>
                  <div className="space-x-2">
                    <button
                      onClick={() => handleMemberAction(request.user_id, 'APPROVE')}
                      className="text-green-600 hover:text-green-800"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleMemberAction(request.user_id, 'REJECT')}
                      className="text-red-600 hover:text-red-800"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Section */}
        {group.analytics && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Group Analytics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <h3 className="font-medium">Overall Stats</h3>
                <p>Total Predictions: {group.analytics.overall_stats.total_predictions}</p>
                <p>Average Points: {group.analytics.overall_stats.average_points}</p>
                <p>Perfect Predictions: {group.analytics.overall_stats.perfect_predictions}</p>
              </div>
              {/* Add more analytics sections as needed */}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};