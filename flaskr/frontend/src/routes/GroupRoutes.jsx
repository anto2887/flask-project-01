// GroupRoutes.jsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import GroupForm from '../components/groups/GroupForm';
import JoinGroup from '../components/groups/JoinGroup';
import GroupManagement from '../components/groups/GroupManagement';
import GroupInvite from '../components/groups/GroupInvite';
import ProtectedRoute from '../components/auth/ProtectedRoute';

const GroupRoutes = () => {
    return (
        <Routes>
            <Route element={<ProtectedRoute />}>
                <Route path="create" element={<GroupForm />} />
                <Route path="join" element={<JoinGroup />} />
                <Route path=":groupId/manage" element={<GroupManagement />} />
                <Route path=":groupId/invite" element={<GroupInvite />} />
            </Route>
        </Routes>
    );
};

export default GroupRoutes;