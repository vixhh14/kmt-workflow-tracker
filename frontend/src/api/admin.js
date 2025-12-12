import api from './axios';

/**
 * Admin Dashboard API Services
 */

// Get list of all projects
export const getProjects = () => {
    return api.get('/admin/projects');
};

// Get unified project analytics (stats + chart data)
export const getProjectAnalytics = (project = null) => {
    const params = project ? { project } : {};
    return api.get('/admin/project-analytics', { params });
};

// Get attendance summary
export const getAttendanceSummary = () => {
    return api.get('/admin/attendance-summary');
};

// Legacy endpoints (for backward compatibility)
export const getOverallStats = () => {
    return api.get('/admin/overall-stats');
};

export const getProjectStatus = (project = null) => {
    const params = project ? { project } : {};
    return api.get('/admin/project-status', { params });
};

export const getTaskStats = (project = null) => {
    const params = project ? { project } : {};
    return api.get('/admin/task-stats', { params });
};

export const getProjectSummary = () => {
    return api.get('/admin/project-summary');
};

export const getProjectStatusChart = () => {
    return api.get('/admin/project-status-chart');
};

export const getTaskStatistics = () => {
    return api.get('/admin/task-statistics');
};
