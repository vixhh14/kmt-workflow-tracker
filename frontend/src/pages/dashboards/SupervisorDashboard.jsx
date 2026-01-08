import React, { useState, useEffect } from 'react';
import { getRunningTasks, getTaskStatus, getProjectsSummary, getTaskStats, getProjectSummary, getPriorityStatus, getOperators, assignTask } from '../../api/supervisor';
import QuickAssign from '../../components/QuickAssign';
import { getUsers, getDashboardOverview, getProjectOverviewStats, getSupervisorUnifiedDashboard, endTask, completeTask } from '../../api/services';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Folder, CheckCircle, Clock, TrendingUp, AlertCircle, RefreshCw, UserPlus, Play, Users, X, Pause } from 'lucide-react';
import { resolveMachineName } from '../../utils/machineUtils';


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
    const [selectedOperator, setSelectedOperator] = useState('all');
    const [selectedProject, setSelectedProject] = useState('all');
    const [selectedTask, setSelectedTask] = useState(null);
    const [showAssignModal, setShowAssignModal] = useState(false);
    const [assigningOperator, setAssigningOperator] = useState('');
    const [operators, setOperators] = useState([]);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const isMounted = React.useRef(false);

    // Ref to hold current filters for the interval
    const filtersRef = React.useRef({ project: 'all', operator: 'all' });

    useEffect(() => {
        // Update ref when state changes
        filtersRef.current = { project: selectedProject, operator: selectedOperator };

        // Fetch data on filter change
        if (isMounted.current) {
            fetchDashboard();
        } else {
            isMounted.current = true;
            fetchDashboard();
        }
    }, [selectedProject, selectedOperator]);

    useEffect(() => {
        const interval = setInterval(fetchRunningTasksOnly, 15000); // 15s recommended for live feel
        return () => clearInterval(interval);
    }, []);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);

            const { project, operator } = filtersRef.current;
            console.log('🔄 Fetching supervisor dashboard data...', { project, operator });

            // Pass filters to all endpoints
            const [unifiedRes, runningRes, operatorStatusRes, statsRes] = await Promise.all([
                getSupervisorUnifiedDashboard(project, operator),
                getRunningTasks(project, operator),
                getTaskStatus(operator, project),
                getTaskStats(project, operator)
            ]);

            console.log('✅ Supervisor dashboard loaded');

            const unified = unifiedRes?.data || {};
            const overview = unified.overview || {};
            const tasks = overview.tasks || { total: 0, pending: 0, in_progress: 0, completed: 0, on_hold: 0 };
            const projectStats = overview.projects || { total: 0, completed: 0, yet_to_start: 0, in_progress: 0, held: 0 };

            setProjectSummary({
                total_projects: projectStats.total || 0,
                completed_projects: projectStats.completed || 0,
                pending_projects: projectStats.yet_to_start || 0,
                active_projects: (projectStats.in_progress || 0) + (projectStats.held || 0)
            });

            setRunningTasks(Array.isArray(runningRes?.data) ? runningRes.data : []);
            setProjectsDistribution(projectStats || {});

            // Overwrite unified stats, keep project list
            setTaskStats({
                ...(statsRes?.data || {}),
                total_tasks: tasks.total || 0,
                pending: tasks.pending || 0,
                in_progress: tasks.in_progress || 0,
                completed: (tasks.completed || 0) + (tasks.ended || 0),
                on_hold: tasks.on_hold || 0,
                available_projects: statsRes?.data?.available_projects || []
            });

            setOperatorStatus(Array.isArray(operatorStatusRes?.data) ? operatorStatusRes.data : []);
            setOperators(Array.isArray(unified.operators) ? unified.operators : []);
            setMachines(Array.isArray(unified.machines) ? unified.machines : []);

        } catch (err) {
            console.error('❌ Failed to fetch supervisor dashboard:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const fetchRunningTasksOnly = async () => {
        try {
            const { project, operator } = filtersRef.current;
            const res = await getRunningTasks(project, operator);
            setRunningTasks(Array.isArray(res?.data) ? res.data : []);
        } catch (err) {
            console.error('Failed to fetch running tasks:', err);
        }
    };

    // Derived fetches are now consolidated into fetchDashboard
    // but these might be called by child components if any... 
    // Keeping safe stubs if needed, or deleting if unused. 
    // Re-adding as they were in original file to avoid breaking references if any.
    const fetchOperatorStatus = async () => { };
    const fetchTaskStatsFiltered = async () => { };

    const handleAssignClick = (task) => {
        setSelectedTask(task);
        setAssigningOperator('');
        setShowAssignModal(true);
    };

    const handleAssignSubmit = async () => {
        if (!assigningOperator || !selectedTask) return;

        try {
            await assignTask(selectedTask.id, { operator_id: assigningOperator });
            setShowAssignModal(false);
            setSelectedTask(null);
            setAssigningOperator('');
            await fetchDashboard(); // Refresh all data
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to assign task');
        }
    };

    const handleEndTask = async (taskId) => {
        if (!window.confirm("Are you sure you want to forcibly END this task? This action cannot be undone.")) return;
        try {
            await endTask(taskId);
            await fetchDashboard();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to end task');
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (!window.confirm("Mark this task as COMPLETED?")) return;
        try {
            await completeTask(taskId);
            await fetchDashboard();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to complete task');
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

    const formatDueDateTime = (dtStr) => {
        if (!dtStr) return 'N/A';
        try {
            const date = new Date(dtStr);
            if (isNaN(date.getTime())) return dtStr;
            const options = {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit', hour12: true
            };
            return date.toLocaleString('en-GB', options).replace(',', ' •').toUpperCase();
        } catch (e) { return dtStr; }
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
                            <option key={op.id} value={op.id}>
                                {op.name || op.username}
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
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 sm:gap-4">
                    <StatCard
                        title="Total Projects"
                        value={projectSummary.total_projects || 0}
                        icon={Folder}
                        color="bg-purple-500"
                    />
                    <StatCard
                        title="Total Tasks"
                        value={taskStats.total_tasks || 0}
                        icon={TrendingUp}
                        color="bg-indigo-500"
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
                        icon={Pause}
                        color="bg-yellow-500"
                    />
                </div>
            </div>

            <QuickAssign onAssignSuccess={fetchDashboard} />

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
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-bold text-gray-900">{task.title || 'Untitled'}</h3>
                                            <div className="text-right flex items-center gap-2">
                                                <span className="px-3 py-1 text-[10px] font-bold bg-green-600 text-white rounded-full uppercase tracking-wider">
                                                    IN PROGRESS
                                                </span>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
                                            <div className="text-xs space-y-1">
                                                <p className="text-gray-500 font-medium uppercase tracking-[0.05em]">Assignment</p>
                                                <p className="flex items-center text-gray-700">👤 <span className="ml-1 font-semibold">{task.operator_name}</span></p>
                                                <p className="flex items-center text-gray-700">⚙️ <span className="ml-1 truncate">{(!task.machine_name || task.machine_name === 'Unknown') ? (task.machine_id ? `Machine-${task.machine_id}` : 'Handwork') : task.machine_name}</span></p>
                                                <p className="flex items-center text-gray-700">📁 <span className="ml-1 truncate">{task.project}</span></p>
                                            </div>
                                            <div className="text-xs space-y-1">
                                                <p className="text-gray-500 font-medium uppercase tracking-[0.05em]">Timing Analytics</p>
                                                <p className="flex justify-between text-gray-600"><span>Started:</span> <span className="font-medium text-gray-900 ml-2">{formatTime(task.started_at)}</span></p>
                                                <p className="flex justify-between text-gray-600"><span>Deadline:</span> <span className="font-bold text-red-600 ml-2">{formatDueDateTime(task.due_date)}</span></p>
                                                <p className="flex justify-between text-gray-600"><span>Task Completion Duration:</span> <span className="font-medium text-gray-900 ml-2">{task.expected_completion_time || 0}m</span></p>
                                                <p className="flex justify-between text-gray-600"><span>Net Dur:</span> <span className={`font-bold ml-2 ${task.expected_completion_time && (task.duration_seconds / 60) > task.expected_completion_time
                                                    ? 'text-red-600'
                                                    : 'text-green-600'
                                                    }`}>{formatDuration(task.duration_seconds)}</span></p>
                                            </div>
                                            <div className="text-xs space-y-1">
                                                <p className="text-gray-500 font-medium uppercase tracking-[0.05em] flex justify-between">
                                                    <span>Held Time</span>
                                                    <span className="text-amber-600 font-bold">{formatDuration(task.total_held_seconds)}</span>
                                                </p>
                                                {task.holds && task.holds.length > 0 ? (
                                                    <div className="mt-1 space-y-1 bg-white p-1.5 rounded border border-green-100 max-h-16 overflow-y-auto">
                                                        {task.holds.map((hold, idx) => (
                                                            <div key={idx} className="flex justify-between text-[10px] items-center border-b border-gray-50 last:border-0 pb-0.5">
                                                                <span className="text-gray-500">{new Date(hold.start).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
                                                                <span className="font-medium text-gray-700">{formatDuration(hold.duration_seconds)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <p className="text-gray-400 italic text-[10px] pt-1 text-center">No active or previous holds</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Actions Footer */}
                                        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-green-200">
                                            <button
                                                onClick={() => handleCompleteTask(task.id)}
                                                className="px-3 py-1.5 bg-green-600 text-white text-xs font-bold rounded-md hover:bg-green-700 flex items-center gap-1 shadow-sm"
                                            >
                                                <CheckCircle size={14} />
                                                COMPLETE
                                            </button>
                                            <button
                                                onClick={() => handleEndTask(task.id)}
                                                className="px-3 py-1.5 bg-red-600 text-white text-xs font-bold rounded-md hover:bg-red-700 flex items-center gap-1 shadow-sm"
                                            >
                                                <X size={14} />
                                                END TASK
                                            </button>
                                        </div>
                                    </div>
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

                {/* Machine Status (Read-only) */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-gray-900">Machine Status</h2>
                        <span className="text-xs text-gray-500">Live Status</span>
                    </div>
                    {Array.isArray(machines) && machines.length > 0 ? (
                        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                            {machines.map(machine => (
                                <div key={machine.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
                                    <div className="flex items-center">
                                        <div className={`w-3 h-3 rounded-full mr-3 ${machine.status === 'active' ? 'bg-green-500 animate-pulse' : machine.status === 'maintenance' ? 'bg-amber-500' : 'bg-gray-400'}`}></div>
                                        <div>
                                            <p className="text-sm font-bold text-gray-800">{resolveMachineName(machine)}</p>
                                            <p className="text-[10px] text-gray-500 uppercase">{machine.category_name || 'General'}</p>
                                        </div>
                                    </div>
                                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${machine.status === 'active' ? 'text-green-700 bg-green-100' : 'text-gray-700 bg-gray-200'}`}>
                                        {machine.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 text-gray-500">
                            <TrendingUp className="mx-auto mb-4" size={48} />
                            <p>No machine data available</p>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
};

export default SupervisorDashboard;
