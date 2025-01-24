import React, { useState, useEffect } from 'react';
import axios from 'axios';

export const AdminDashboard = ({ groupId }) => {
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [analytics, setAnalytics] = useState({});

  useEffect(() => {
    const fetchGroupData = async () => {
      try {
        const response = await axios.get(`/group/api/${groupId}/admin-data`);
        const { group, members, pendingRequests, analytics } = response.data;
        setGroup(group);
        setMembers(members);
        setPendingRequests(pendingRequests);
        setAnalytics(analytics);
      } catch (error) {
        console.error('Failed to fetch group data:', error);
      }
    };

    fetchGroupData();
  }, [groupId]);

  const handleMemberAction = async (userId, action) => {
    try {
      await axios.post(`/group/api/${groupId}/member/${userId}/${action}`);
      // Refresh member list
      const response = await axios.get(`/group/api/${groupId}/members`);
      setMembers(response.data.members);
    } catch (error) {
      console.error(`Failed to ${action} member:`, error);
    }
  };

  if (!group) return <div>Loading...</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-[#05445E]">{group.name}</h1>
            <p className="text-[#189AB4]">{group.league}</p>
          </div>
          {/* Rest of the dashboard components */}
        </div>
      </div>
    </div>
  );
};