import api from './axios';

/* -------------------- AUTH -------------------- */
export const login = (credentials) => api.post('/auth/login', credentials);
export const signup = (data) => api.post('/auth/signup', data);
export const getCurrentUser = () => api.get('/auth/me');
export const resetPassword = (data) => api.post('/auth/reset-password', data);
export const getSecurityQuestion = (username) => api.post('/auth/get-security-question', { username });
export const changePassword = (data) => api.post('/auth/change-password', data);

/* -------------------- USERS -------------------- */
export const getUsers = () => api.get('/users');
export const createUser = (data) => api.post('/users', data);
export const updateUser = (id, data) => api.put(`/users/${id}`, data);
export const deleteUser = (id) => api.delete(`/users/${id}`);

/* -------------------- MACHINES -------------------- */
export const getMachines = () => api.get('/machines');
export const createMachine = (data) => api.post('/machines', data);
export const updateMachine = (id, data) => api.put(`/machines/${id}`, data);
export const deleteMachine = (id) => api.delete(`/machines/${id}`);

/* -------------------- TASKS -------------------- */
export const getTasks = (month = null, year = null, assigned_to = null) => {
    const params = {};
    if (month !== null) params.month = month;
    if (year !== null) params.year = year;
    if (assigned_to !== null) params.assigned_to = assigned_to;
    return api.get('/tasks', { params });
};

export const createTask = (data) => api.post('/tasks', data);
export const updateTask = (id, data) => api.put(`/tasks/${id}`, data);
export const deleteTask = (id) => api.delete(`/tasks/${id}`);

export const startTask = (id) => api.post(`/tasks/${id}/start`);
export const holdTask = (id, reason) => api.post(`/tasks/${id}/hold`, { reason });
export const resumeTask = (id) => api.post(`/tasks/${id}/resume`);
export const completeTask = (id) => api.post(`/tasks/${id}/complete`);
export const denyTask = (id, reason) => api.post(`/tasks/${id}/deny`, { reason });

/* -------------------- ANALYTICS -------------------- */
export const getAnalytics = () => api.get('/analytics');
export const getTaskSummary = (params) => api.get('/analytics/task-summary', { params });
export const getOperatorPerformance = (month, year, operator_id = null) => {
    const params = { month, year };
    if (operator_id) params.operator_id = operator_id;
    return api.get('/analytics/operator-performance', { params });
};

/* -------------------- OUTSOURCE -------------------- */
export const getOutsource = () => api.get('/outsource');
export const createOutsource = (data) => api.post('/outsource', data);
export const updateOutsource = (id, data) => api.put(`/outsource/${id}`, data);
export const deleteOutsource = (id) => api.delete(`/outsource/${id}`);

/* -------------------- PLANNING -------------------- */
export const getPlanningTasks = () => api.get('/planning');
export const createPlanningTask = (data) => api.post('/planning', data);
export const updatePlanningTask = (id, data) => api.put(`/planning/${id}`, data);
export const deletePlanningTask = (id) => api.delete(`/planning/${id}`);
export const getPlanningOverview = () => api.get('/planning/overview');

/* -------------------- SUBTASKS -------------------- */
export const getSubtasks = (taskId) => api.get(`/subtasks/${taskId}`);
export const createSubtask = (data) => api.post('/subtasks', data);
export const updateSubtask = (subtaskId, data) => api.put(`/subtasks/${subtaskId}`, data);
export const deleteSubtask = (subtaskId) => api.delete(`/subtasks/${subtaskId}`);

/* -------------------- ADMIN -------------------- */

export const getPendingUsers = () => api.get('/admin/pending-users');
export const approveUser = (username, unitId) => api.post(`/admin/users/${username}/approve`, { unit_id: unitId });
export const rejectUser = (username) => api.post(`/admin/users/${username}/reject`);

/* -------------------- UNITS -------------------- */
export const getUnits = () => api.get('/api/units');

/* -------------------- OPERATOR -------------------- */
export const getOperatorTasks = (userId) => api.get('/operator/tasks', { params: { user_id: userId } });
export const operatorStartTask = (taskId) => api.put(`/operator/tasks/${taskId}/start`);
export const operatorCompleteTask = (taskId) => api.put(`/operator/tasks/${taskId}/complete`);
export const operatorHoldTask = (taskId, reason = '') => api.put(`/operator/tasks/${taskId}/hold`, null, { params: { reason } });
export const operatorResumeTask = (taskId) => api.put(`/operator/tasks/${taskId}/resume`);
