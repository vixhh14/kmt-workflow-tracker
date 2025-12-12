import React, { useState, useEffect } from 'react';
import { getSupervisorProjectSummary, getSupervisorPendingTasks, getSupervisorOperatorTaskStatus, getSupervisorPriorityStatus } from '../../api/supervisor';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Folder, CheckCircle, Clock, TrendingUp, AlertCircle, RefreshCw, UserPlus } from 'lucide-react';

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
    const [operatorStatus, setOperatorStatus] = useState([]);
    const [priorityStatus, setPriorityStatus] = useState({
        high: 0,
        medium: 0,
        low: 0
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboard();
    }, []);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('🔄 Fetching supervisor dashboard...');

            const [summaryRes, tasksRes, operatorRes, priorityRes] = await Promise.all([
                getSupervisorProjectSummary(),
                getSupervisorPendingTasks(),
                getSupervisorOperatorTaskStatus(),
                getSupervisorPriorityStatus()
            ]);

            console.log('✅ Supervisor dashboard loaded:', {
                summary: summaryRes.data,
                tasks: tasksRes.data,
                operators: operatorRes.data,
                priority: priorityRes.data
            });

            setProjectSummary({
                total_projects: summaryRes.data?.total_projects || 0,
                completed_projects: summaryRes.data?.completed_projects || 0,
                pending_projects: summaryRes.data?.pending_projects || 0,
                active_projects: summaryRes.data?.active_projects || 0
            });

            setPendingTasks(Array.isArray(tasksRes.data) ? tasksRes.data : []);
            setOperatorStatus(Array.isArray(operatorRes.data) ? operatorRes.data : []);

            setPriorityStatus({
                high: priorityRes.data?.high || 0,
                medium: priorityRes.data?.medium || 0,
                low: priorityRes.data?.low || 0
            });

        } catch (err) {
            console.error('❌ Failed to fetch supervisor dashboard:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const priorityChartData = [
        { name: 'High', value: priorityStatus.high, color: PRIORITY_COLORS.high },
        { name: 'Medium', value: priorityStatus.medium, color: PRIORITY_COLORS.medium },
        { name: 'Low', value: priorityStatus.low, color: PRIORITY_COLORS.low }
    ].filter(item => item.value > 0);

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

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
                <button
                    onClick={fetchDashboard}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto"
                >
                    <RefreshCw size={18} />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Project Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                <StatCard
                    title="Total Projects"
                    value={projectSummary.total_projects}
                    icon={Folder}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Active Projects"
                    value={projectSummary.active_projects}
                    icon={TrendingUp}
                    color="bg-purple-500"
                />
                <StatCard
                    title="Pending Projects"
                    value={projectSummary.pending_projects}
                    icon={Clock}
                    color="bg-yellow-500"
                />
                <StatCard
                    title="Completed Projects"
                    value={projectSummary.completed_projects}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                {/* Operator Task Status */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Operator Task Status</h2>
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
                            <TrendingUp className="mx-auto mb-4" size={48} />
                            <p>No operator data available</p>
                        </div>
                    )}
                </div>

                {/* Priority Distribution */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Priority Distribution</h2>
                    {priorityChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={priorityChartData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {priorityChartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            <AlertCircle className="mx-auto mb-4" size={48} />
                            <p>No priority data available</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Pending Tasks - Quick Assign */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                        <UserPlus className="text-blue-600 mr-2" size={24} />
                        <h2 className="text-lg font-semibold text-gray-900">Pending Tasks - Quick Assign</h2>
                    </div>
                    <span className="text-sm text-gray-600">{pendingTasks.length} task(s)</span>
                </div>
                {pendingTasks.length > 0 ? (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                        {pendingTasks.map(task => (
                            <div key={task.id} className="border rounded-lg p-4 hover:bg-gray-50 transition">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <h3 className="font-medium text-gray-900">{task.title || 'Untitled Task'}</h3>
                                        {task.project && (
                                            <p className="text-sm text-gray-600 mt-1">Project: {task.project}</p>
                                        )}
                                        {task.description && (
                                            <p className="text-sm text-gray-700 mt-1">{task.description}</p>
                                        )}
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {task.priority && (
                                                <span className={`px-2 py-1 text-xs font-medium rounded ${getPriorityColor(task.priority)}`}>
                                                    {task.priority.toUpperCase()}
                                                </span>
                                            )}
                                            {task.machine_name && (
                                                <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                                                    {task.machine_name}
                                                </span>
                                            )}
                                            {task.due_date && (
                                                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                                                    Due: {task.due_date}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
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
        </div>
    );
};

export default SupervisorDashboard;
