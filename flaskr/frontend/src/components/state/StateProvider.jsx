import React from 'react';
import { AuthProvider } from '../../contexts/AuthContext';
import { UserProvider } from '../../contexts/UserContext';
import { MatchProvider } from '../../contexts/MatchContext';
import { PredictionProvider } from '../../contexts/PredictionContext';
import { GroupProvider } from '../../contexts/GroupContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationContainer from '../common/NotificationContainer';

const StateProvider = ({ children }) => {
    return (
        <NotificationProvider>
            <AuthProvider>
                <UserProvider>
                    <GroupProvider>
                        <MatchProvider>
                            <PredictionProvider>
                                {children}
                                <NotificationContainer />
                            </PredictionProvider>
                        </MatchProvider>
                    </GroupProvider>
                </UserProvider>
            </AuthProvider>
        </NotificationProvider>
    );
};

export default StateProvider;