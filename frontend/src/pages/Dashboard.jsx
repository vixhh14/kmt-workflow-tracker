import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
    const { user } = useAuth();

    if (!user) {
        return <Navigate to="/login" />;
    }

    switch (user.role) {
        case 'admin':
            return <Navigate to="/dashboard/admin" />;
        case 'operator':
            return <Navigate to="/dashboard/operator" />;
        case 'supervisor':
            return <Navigate to="/dashboard/supervisor" />;
        case 'planning':
            return <Navigate to="/dashboard/planning" />;
        default:
            return <Navigate to="/login" />;
    }
};

export default Dashboard;
