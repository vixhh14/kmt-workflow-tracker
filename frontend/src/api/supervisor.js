import api from './axios';

/**
 * Supervisor Dashboard API Services
 */

// Get pending tasks for quick assignment
export const getPendingTasks = () => {
    return api.get('/supervisor/pending-tasks');
};

// Get running tasks
export const getRunningTasks = () => {
    return api.get('/supervisor/running-tasks');
};

// Get task status breakdown (optionally filtered by operator)
export const getTaskStatus = (operatorId = null) => {
    const params = operatorId ? { operator_id: operatorId } : {};
    return api.get('/supervisor/task-status', { params });
};

// Get projects summary for pie chart
export const getProjectsSummary = () => {
    return api.get('/supervisor/projects-summary');
};

// Get task statistics (optionally filtered by project)
export const getTaskStats = (project = null) => {
    const params = project ? { project } : {};
    return api.get('/supervisor/task-stats', { params });
};

// Assign task to operator
export const assignTask = (taskId, operatorId) => {
    return api.post('/supervisor/assign-task', {
        task_id: taskId,
        operator_id: operatorId
    });
};

// Get project summary metrics
export const getProjectSummary = () => {
    return api.get('/supervisor/project-summary');
};

// Get priority task status
export const getPriorityStatus = () => {
    return api.get('/supervisor/priority-task-status');
};

// Get all operators for dropdown
export const getOperators = () => {
    return api.get('/users').then(res => {
        return {
            ...res,
            data: res.data.filter(u => u.role === 'operator')
        };
    });
};
