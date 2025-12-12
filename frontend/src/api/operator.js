import api from './axios';

/**
 * Operator Dashboard API Services
 */

// Get tasks assigned to the logged-in operator
export const getOperatorTasks = (userId) => {
    return api.get(`/operator/tasks`, {
        params: { user_id: userId }
    });
};

// Start a task
export const startTask = (taskId) => {
    return api.put(`/operator/tasks/${taskId}/start`);
};

// Complete a task
export const completeTask = (taskId) => {
    return api.put(`/operator/tasks/${taskId}/complete`);
};

// Put a task on hold
export const holdTask = (taskId, reason = '') => {
    return api.put(`/operator/tasks/${taskId}/hold`, null, {
        params: { reason }
    });
};

// Resume a task from hold
export const resumeTask = (taskId) => {
    return api.put(`/operator/tasks/${taskId}/resume`);
};

// Get task details
export const getTaskDetails = (taskId) => {
    return api.get(`/tasks/${taskId}`);
};
