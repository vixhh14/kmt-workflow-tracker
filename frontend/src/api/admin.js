import api from './axios';

/**
 * Admin Dashboard API Services
 */

// Get overall project statistics (not filtered)
export const getOverallStats = () => {
    return api.get('/admin/overall-stats');
};

// Get list of all projects
export const getProjects = () => {
    return api.get('/admin/projects');
};

// Get project status distribution (filterable by project)
export const getProjectStatus = (project = null) => {
    const params = project ? { project } : {};
    return api.get('/admin/project-status', { params });
};

// Get task statistics (filterable by project)
export const getTaskStats = (project = null) => {
    const params = project ? { project } : {};
    return api.get('/admin/task-stats', { params });
};

// Get project summary for admin dashboard (LEGACY)
export const getProjectSummary = () => {
    return api.get('/admin/project-summary');
};

// Get project status chart data (LEGACY)
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
