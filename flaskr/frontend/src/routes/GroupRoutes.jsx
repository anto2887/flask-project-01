
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { GroupList } from '../components/groups/GroupList';
import { GroupCreate } from '../components/groups/GroupCreate';
import { GroupDetails } from '../components/groups/GroupDetails';
import { GroupSettings } from '../components/groups/GroupSettings';
import { GroupMembers } from '../components/groups/GroupMembers';
import { JoinGroup } from '../components/groups/JoinGroup';

export const GroupRoutes = () => {
  return (
    <Routes>
      <Route index element={<GroupList />} />
      <Route path="create" element={<GroupCreate />} />
      <Route path="join" element={<JoinGroup />} />
      <Route path=":groupId" element={<GroupDetails />} />
      <Route path=":groupId/settings" element={<GroupSettings />} />
      <Route path=":groupId/members" element={<GroupMembers />} />
    </Routes>
  );
};