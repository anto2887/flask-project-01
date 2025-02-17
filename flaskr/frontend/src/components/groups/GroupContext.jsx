// GroupInvite.jsx
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useGroups } from '../../contexts/GroupContext';
import LoadingSpinner from '../common/LoadingSpinner';
import QRCode from 'qrcode.react';

const GroupInvite = () => {
  const { groupId } = useParams();
  const { currentGroup, loading, error } = useGroups();

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!currentGroup) return <div>No group found</div>;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          League Created Successfully!
        </h1>
        
        <div className="mb-8">
          <h2 className="text-lg font-medium text-gray-700 mb-2">
            Invitation Code
          </h2>
          <div className="bg-gray-100 p-4 rounded-lg">
            <span className="text-2xl font-mono tracking-wider">
              {currentGroup.invite_code}
            </span>
          </div>
        </div>

        <div className="mb-8">
          <QRCode 
            value={currentGroup.invite_code}
            size={200}
            level="H"
            className="mx-auto"
          />
          <p className="mt-2 text-sm text-gray-500">
            Scan this QR code to join the league
          </p>
        </div>

        <div className="space-y-4">
          <Link
            to={`/groups/${groupId}/manage`}
            className="block w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Go to League Management
          </Link>
          <Link
            to="/dashboard"
            className="block w-full bg-gray-200 text-gray-700 py-2 px-4 rounded hover:bg-gray-300"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};

export default GroupInvite;