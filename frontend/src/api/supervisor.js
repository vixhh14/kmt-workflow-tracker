import api from './axios';

/**
 * Supervisor Dashboard API Services
 */

// Get pending tasks for quick assignment
export const getPendingTasks = () => {
    return api.get('/supervisor/pending-tasks');
};

// Get running tasks
export const getRunningTasks = (projectId = null, operatorId = null) => {
    const params = {};
    if (projectId && projectId !== 'all') params.project_id = projectId;
    if (operatorId && operatorId !== 'all') params.operator_id = operatorId;
    return api.get('/supervisor/running-tasks', { params });
};

// Get task status breakdown (optionally filtered by operator and project)
export const getTaskStatus = (operatorId = null, projectId = null) => {
    const params = {};
    if (operatorId && operatorId !== 'all') params.operator_id = operatorId;
    if (projectId && projectId !== 'all') params.project_id = projectId;
    return api.get('/supervisor/task-status', { params });
};

// Get projects summary for pie chart
export const getProjectsSummary = () => {
    return api.get('/supervisor/projects-summary');
};

// Get task statistics (optionally filtered by project and operator)
export const getTaskStats = (projectId = null, operatorId = null) => {
    const params = {};
    if (projectId && projectId !== 'all') params.project = projectId; // Backend supports 'project' (name/id)
    if (operatorId && operatorId !== 'all') params.operator_id = operatorId;
    return api.get('/supervisor/task-stats', { params });
};

// Assign task to operator
export const assignTask = (taskId, assignmentData) => {
    return api.post('/supervisor/assign-task', {
        task_id: taskId,
        ...assignmentData
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

// Get all assignable users for dropdown
export const getOperators = () => {
    return api.get('/users').then(res => {
        return {
            ...res,
            data: res.data.filter(u => u.role !== 'admin')
        };
    });
};
