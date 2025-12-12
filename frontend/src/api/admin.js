import api from './axios';

/**
 * Admin Dashboard API Services
 */

// Get project summary for admin dashboard
export const getProjectSummary = () => {
    return api.get('/admin/project-summary');
};

// Get project status chart data
export const getProjectStatusChart = () => {
    return api.get('/admin/project-status-chart');
};

// Get attendance summary
export const getAttendanceSummary = () => {
    return api.get('/admin/attendance-summary');
};

// Get task statistics
export const getTaskStatistics = () => {
    return api.get('/admin/task-statistics');
};
