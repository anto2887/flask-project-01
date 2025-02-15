import React, { useEffect } from 'react';
import { useUser } from '../../contexts/UserContext';
import { useMatches } from '../../contexts/MatchContext';
import { usePredictions } from '../../contexts/PredictionContext';
import { useGroups } from '../../contexts/GroupContext';
import DashboardStats from './DashboardStats';
import LiveMatches from './LiveMatches';
import UpcomingMatches from './UpcomingMatches';
import RecentPredictions from './RecentPredictions';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';

const Dashboard = () => {
  const { profile, stats, loading: userLoading, error: userError } = useUser();
  const { liveMatches, loading: matchesLoading, error: matchesError } = useMatches();
  const { userPredictions, loading: predictionsLoading, error: predictionsError } = usePredictions();
  const { userGroups, loading: groupsLoading, error: groupsError } = useGroups();

  const isLoading = userLoading || matchesLoading || predictionsLoading || groupsLoading;
  const error = userError || matchesError || predictionsError || groupsError;

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {profile?.username}!
        </h1>
        <p className="mt-1 text-gray-600">
          Here's what's happening with your predictions
        </p>
      </div>

      {/* Stats Overview */}
      <DashboardStats stats={stats} />

      {/* Live Matches */}
      {liveMatches.length > 0 && (
        <section className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Live Matches</h2>
          </div>
          <LiveMatches matches={liveMatches} />
        </section>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Matches */}
        <section className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Upcoming Matches</h2>
          </div>
          <UpcomingMatches />
        </section>

        {/* Recent Predictions */}
        <section className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Recent Predictions</h2>
          </div>
          <RecentPredictions predictions={userPredictions.slice(0, 5)} />
        </section>
      </div>

      {/* Your Groups */}
      {userGroups.length > 0 && (
        <section className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Your Groups</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {userGroups.map(group => (
                <div 
                  key={group.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <h3 className="font-medium text-gray-900">{group.name}</h3>
                  <p className="text-sm text-gray-500">{group.league}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    {group.member_count} members
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

export default Dashboard;