import api from './axios';

/**
 * Attendance API Services
 */

// Mark user as present (called on login)
export const markPresent = (userId) => {
    return api.post('/attendance/mark-present', { user_id: userId });
};

// Mark user as checked out (called on explicit logout)
export const markCheckout = (userId) => {
    return api.post('/attendance/check-out', { user_id: userId });
};

// Get attendance summary for today
export const getAttendanceSummary = () => {
    return api.get('/attendance/summary');
};
