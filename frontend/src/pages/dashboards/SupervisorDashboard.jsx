import React, { useState, useEffect } from 'react';
import { getPendingTasks, getRunningTasks, getTaskStatus, getProjectsSummary, getTaskStats, assignTask, getProjectSummary, getPriorityStatus, getOperators } from '../../api/supervisor';
import { getUsers } from '../../api/services';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Folder, CheckCircle, Clock, TrendingUp, AlertCircle, RefreshCw, UserPlus, Play, Users, X } from 'lucide-react';
import { getDashboardOverview } from '../../api/services';

const COLORS = {
    'Yet to Start': '#6b7280',
    'In Progress': '#3b82f6',
    'Completed': '#10b981',
    'On Hold': '#f59e0b',
};

const PRIORITY_COLORS = {
    high: '#ef4444',
    medium: '#f59e0b',
    low: '#10b981'
};

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
        <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-600 mb-1 truncate">{title}</p>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value}</p>
                {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
            </div>
            <div className={`p-2 sm:p-3 rounded-full ${color} flex-shrink-0 ml-2`}>
                <Icon className="text-white" size={20} />
            </div>
        </div>
    </div>
);

const SupervisorDashboard = () => {
    const [projectSummary, setProjectSummary] = useState({
        total_projects: 0,
        completed_projects: 0,
        pending_projects: 0,
        active_projects: 0
    });
    const [pendingTasks, setPendingTasks] = useState([]);
    const [runningTasks, setRunningTasks] = useState([]);
    const [operatorStatus, setOperatorStatus] = useState([]);
    const [projectsDistribution, setProjectsDistribution] = useState({});
    const [taskStats, setTaskStats] = useState({
        total_tasks: 0,
        pending: 0,
        in_progress: 0,
        completed: 0,
        on_hold: 0,
        available_projects: [],
        selected_project: 'all'
    });
    const [operators, setOperators] = useState([]);
    const [selectedOperator, setSelectedOperator] = useState('all');
    const [selectedProject, setSelectedProject] = useState('all');
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [selectedTask, setSelectedTask] = useState(null);
    const [assigningOperator, setAssigningOperator] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboard();
        const interval = setInterval(fetchRunningTasksOnly, 60000); // Update running tasks every minute
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        fetchOperatorStatus();
    }, [selectedOperator]);

    useEffect(() => {
        fetchTaskStatsFiltered();
    }, [selectedProject]);



    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('🔄 Fetching supervisor dashboard...');

            const [overviewRes, summaryRes, pendingRes, runningRes, operatorsRes, projectsRes, statsRes, operatorStatusRes] = await Promise.all([
                getDashboardOverview(),
                getProjectSummary(),
                getPendingTasks(),
                getRunningTasks(),
                getOperators(),
                getProjectsSummary(),
                getTaskStats(),
                getTaskStatus()
            ]);

            console.log('✅ Supervisor dashboard loaded');

            const tasks = overviewRes.data.tasks;

            setProjectSummary({
                total_projects: summaryRes.data?.total_projects || 0,
                completed_projects: summaryRes.data?.completed_projects || 0,
                pending_projects: summaryRes.data?.pending_projects || 0,
                active_projects: summaryRes.data?.active_projects || 0
            });

            setPendingTasks(Array.isArray(pendingRes.data) ? pendingRes.data : []);
            setRunningTasks(Array.isArray(runningRes.data) ? runningRes.data : []);
            setOperators(Array.isArray(operatorsRes.data) ? operatorsRes.data : []);
            setProjectsDistribution(projectsRes.data || {});

            // Overwrite unified stats, keep project list
            setTaskStats({
                ...statsRes.data,
                total_tasks: tasks.total,
                pending: tasks.pending,
                in_progress: tasks.in_progress,
                completed: tasks.completed,
                on_hold: tasks.on_hold
            });

            setOperatorStatus(Array.isArray(operatorStatusRes.data) ? operatorStatusRes.data : []);

        } catch (err) {
            console.error('❌ Failed to fetch supervisor dashboard:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const fetchRunningTasksOnly = async () => {
        try {
            const res = await getRunningTasks();
            setRunningTasks(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error('Failed to fetch running tasks:', err);
        }
    };

    const fetchOperatorStatus = async () => {
        try {
            const operatorId = selectedOperator === 'all' ? null : selectedOperator;
            const res = await getTaskStatus(operatorId);
            setOperatorStatus(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error('Failed to fetch operator status:', err);
        }
    };

    const fetchTaskStatsFiltered = async () => {
        try {
            const project = selectedProject === 'all' ? null : selectedProject;
            const res = await getTaskStats(project);
            setTaskStats(res.data || {});
        } catch (err) {
            console.error('Failed to fetch task stats:', err);
        }
    };

    const handleAssignClick = (task) => {
        setSelectedTask(task);
        setAssigningOperator('');
        setShowAssignModal(true);
    };

    const handleAssignSubmit = async () => {
        if (!assigningOperator || !selectedTask) return;

        try {
            await assignTask(selectedTask.id, assigningOperator);
            setShowAssignModal(false);
            setSelectedTask(null);
            setAssigningOperator('');
            await fetchDashboard(); // Refresh all data
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to assign task');
        }
    };

    const formatDuration = (seconds) => {
        if (!seconds || isNaN(seconds) || seconds <= 0) return '0m';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    const formatTime = (isoString) => {
        if (!isoString) return 'N/A';
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        } catch {
            return 'N/A';
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const projectChartData = [
        { name: 'Yet to Start', value: projectsDistribution.yet_to_start || 0, color: COLORS['Yet to Start'] },
        { name: 'In Progress', value: projectsDistribution.in_progress || 0, color: COLORS['In Progress'] },
        { name: 'Completed', value: projectsDistribution.completed || 0, color: COLORS['Completed'] },
        { name: 'On Hold', value: projectsDistribution.on_hold || 0, color: COLORS['On Hold'] }
    ].filter(item => item.value > 0);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
                    <h3 className="text-lg font-semibold text-red-900 mb-2">Error Loading Dashboard</h3>
                    <p className="text-red-700 mb-4">{error}</p>
                    <button
                        onClick={fetchDashboard}
                        className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Supervisor Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">Monitor projects and team performance</p>
                </div>
                <div className="flex gap-2">
                    <select
                        value={selectedOperator}
                        onChange={(e) => setSelectedOperator(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Operators</option>
                        {operators.map(op => (
                            <option key={op.user_id} value={op.user_id}>
                                {op.full_name || op.username}
                            </option>
                        ))}
                    </select>
                    <button
                        onClick={fetchDashboard}
                        className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                    >
                        <RefreshCw size={18} />
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                </div>
            </div>

            {/* Task Statistics Cards */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h2 className="text-lg font-semibold text-gray-900">Overall Task Statistics</h2>
                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Projects</option>
                        {(taskStats.available_projects || []).map(proj => (
                            <option key={proj} value={proj}>{proj}</option>
                        ))}
                    </select>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                    <StatCard
                        title="Total Tasks"
                        value={taskStats.total_tasks || 0}
                        icon={Folder}
                        color="bg-purple-500"
                    />
                    <StatCard
                        title="Pending"
                        value={taskStats.pending || 0}
                        icon={Clock}
                        color="bg-gray-500"
                    />
                    <StatCard
                        title="In Progress"
                        value={taskStats.in_progress || 0}
                        icon={TrendingUp}
                        color="bg-blue-500"
                    />
                    <StatCard
                        title="Completed"
                        value={taskStats.completed || 0}
                        icon={CheckCircle}
                        color="bg-green-500"
                    />
                    <StatCard
                        title="On Hold"
                        value={taskStats.on_hold || 0}
                        icon={AlertCircle}
                        color="bg-yellow-500"
                    />
                </div>
            </div>

            {/* Quick Assign - Pending Tasks */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                        <UserPlus className="text-blue-600 mr-2" size={24} />
                        <h2 className="text-lg font-semibold text-gray-900">Quick Assign – Pending Tasks</h2>
                    </div>
                    <span className="text-sm text-gray-600">{pendingTasks.length} task(s)</span>
                </div>
                {pendingTasks.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {pendingTasks.map(task => (
                            <div key={task.id} className="border rounded-lg p-4 hover:shadow-lg transition">
                                <div className="flex items-start justify-between mb-2">
                                    <h3 className="font-medium text-gray-900 flex-1">{task.title || 'Untitled Task'}</h3>
                                    {task.priority && (
                                        <span className={`px-2 py-1 text-xs font-medium rounded ${getPriorityColor(task.priority)}`}>
                                            {task.priority.toUpperCase()}
                                        </span>
                                    )}
                                </div>
                                {task.project && (
                                    <p className="text-sm text-gray-600 mb-2">📁 {task.project}</p>
                                )}
                                {task.machine_name && (
                                    <p className="text-sm text-gray-600 mb-2">⚙️ {task.machine_name}</p>
                                )}
                                {task.due_date && (
                                    <p className="text-sm text-gray-600 mb-3">📅 Due: {task.due_date}</p>
                                )}
                                <button
                                    onClick={() => handleAssignClick(task)}
                                    className="w-full bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                                >
                                    Assign to Operator
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <CheckCircle className="mx-auto mb-4" size={48} />
                        <p>No pending tasks to assign</p>
                    </div>
                )}
            </div>

            {/* Running Tasks */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                        <Play className="text-green-600 mr-2" size={24} />
                        <h2 className="text-lg font-semibold text-gray-900">Running Tasks</h2>
                    </div>
                    <span className="text-sm text-gray-600">{runningTasks.length} task(s)</span>
                </div>
                {runningTasks.length > 0 ? (
                    <div className="space-y-3">
                        {runningTasks.map(task => (
                            <div key={task.id} className="border rounded-lg p-4 bg-green-50 border-green-200">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <h3 className="font-medium text-gray-900">{task.title || 'Untitled'}</h3>
                                        <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-600">
                                            <span>👤 {task.operator_name}</span>
                                            <span>⚙️ {task.machine_name}</span>
                                            <span>🕐 Started: {formatTime(task.started_at)}</span>
                                            <span className="font-medium text-green-700">⏱️ {formatDuration(task.duration_seconds)}</span>
                                        </div>
                                    </div>
                                    <span className="px-3 py-1 text-xs font-medium bg-green-600 text-white rounded-full">
                                        IN PROGRESS
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <Play className="mx-auto mb-4" size={48} />
                        <p>No tasks currently running</p>
                    </div>
                )}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                {/* Operator Workload */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Operator Workload</h2>
                    {operatorStatus.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={operatorStatus}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="operator" angle={-45} textAnchor="end" height={80} />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Bar dataKey="completed" fill="#10b981" name="Completed" />
                                <Bar dataKey="in_progress" fill="#3b82f6" name="In Progress" />
                                <Bar dataKey="pending" fill="#6b7280" name="Pending" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            <Users className="mx-auto mb-4" size={48} />
                            <p>No operator data available</p>
                        </div>
                    )}
                </div>

                {/* Project Status Distribution */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Status Distribution</h2>
                    {projectChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={projectChartData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {projectChartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            <Folder className="mx-auto mb-4" size={48} />
                            <p>No project data available</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Assign Task Modal */}
            {showAssignModal && selectedTask && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-900">Assign Task</h3>
                            <button
                                onClick={() => setShowAssignModal(false)}
                                className="text-gray-500 hover:text-gray-700"
                            >
                                <X size={24} />
                            </button>
                        </div>
                        <div className="mb-4">
                            <p className="text-sm text-gray-600 mb-2">Task: <span className="font-medium">{selectedTask.title}</span></p>
                            {selectedTask.project && (
                                <p className="text-sm text-gray-600 mb-2">Project: <span className="font-medium">{selectedTask.project}</span></p>
                            )}
                        </div>
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Select Operator</label>
                            <select
                                value={assigningOperator}
                                onChange={(e) => setAssigningOperator(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">-- Select Operator --</option>
                                {operators.map(op => (
                                    <option key={op.user_id} value={op.user_id}>
                                        {op.full_name || op.username}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowAssignModal(false)}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAssignSubmit}
                                disabled={!assigningOperator}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Assign
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SupervisorDashboard;
