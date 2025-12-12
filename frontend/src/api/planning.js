import api from './axios';

/**
 * Planning Dashboard API Services
 */

// Get planning dashboard summary
export const getPlanningDashboardSummary = () => {
    return api.get('/planning/dashboard-summary');
};
