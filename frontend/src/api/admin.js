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

// --- NEW REPORTING APIs ---

export const getMachineDailyReport = (dateStr) => {
    return api.get('/reports/machines/daily', { params: { date_str: dateStr } });
};

export const getUserDailyReport = (dateStr) => {
    return api.get('/reports/users/daily', { params: { date_str: dateStr } });
};

export const getMonthlyPerformance = (year) => {
    return api.get('/reports/monthly-performance', { params: { year } });
};

export const downloadMachineReport = (dateStr) => {
    return api.get('/reports/machines/export-csv', {
        params: { date_str: dateStr },
        responseType: 'blob'
    });
};

export const downloadUserReport = (dateStr) => {
    return api.get('/reports/users/export-csv', {
        params: { date_str: dateStr },
        responseType: 'blob'
    });
};

export const downloadMonthlyPerformance = (year) => {
    return api.get('/reports/monthly/export-csv', {
        params: { year },
        responseType: 'blob'
    });
};

// --- LEGACY ---

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
