import React, { createContext, useContext, useState, useEffect } from 'react';
import { login as loginApi } from '../api/services';
import { markPresent, markCheckout } from '../api/attendance';
import api from '../api/axios';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            const response = await loginApi({ username, password });
            const { access_token, user: userData } = response.data;

            setToken(access_token);
            setUser(userData);

            localStorage.setItem('token', access_token);
            localStorage.setItem('user', JSON.stringify(userData));

            // Mark user as present (attendance is already marked by backend on login)
            // This is optional frontend call for confirmation
            try {
                await markPresent(userData.user_id);
                console.log('✅ Attendance marked for user:', userData.username);
            } catch (attendanceErr) {
                console.warn('⚠️ Frontend attendance marking failed (backend already handled):', attendanceErr);
            }

            return { success: true, user: userData };
        } catch (error) {
            console.error('Login failed:', error);
            return { success: false, error: error.response?.data?.detail || 'Login failed' };
        }
    };

    const logout = async () => {
        try {
            // Call logout endpoint to mark checkout
            if (token && user) {
                try {
                    await api.post('/auth/logout');
                    console.log('✅ Logout and checkout recorded');
                } catch (logoutErr) {
                    console.warn('⚠️ Logout API call failed:', logoutErr);
                }
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Always clear local state
            setToken(null);
            setUser(null);
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        }
    };

    const value = {
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token,
        loading
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};