import api from './axios';

/**
 * Planning Dashboard API Services
 */

// Get planning dashboard summary
export const getPlanningDashboardSummary = (projectId = null, operatorId = null) => {
    const params = {};
    if (projectId && projectId !== 'all') params.project_id = projectId;
    if (operatorId && operatorId !== 'all') params.operator_id = operatorId;
    return api.get('/planning/dashboard-summary', { params });
};
