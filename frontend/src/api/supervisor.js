import api from './axios';

/**
 * Supervisor Dashboard API Services
 */

// Get supervisor project summary
export const getSupervisorProjectSummary = () => {
    return api.get('/supervisor/project-summary');
};

// Get pending tasks for quick assignment
export const getSupervisorPendingTasks = () => {
    return api.get('/supervisor/pending-tasks');
};

// Get operator task status breakdown
export const getSupervisorOperatorTaskStatus = () => {
    return api.get('/supervisor/operator-task-status');
};

// Get priority task status breakdown
export const getSupervisorPriorityStatus = () => {
    return api.get('/supervisor/priority-task-status');
};
