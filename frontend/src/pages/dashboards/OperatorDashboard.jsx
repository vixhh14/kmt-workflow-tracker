import React, { useState, useEffect } from 'react';
import { getOperatorTasks, operatorStartTask, operatorCompleteTask, operatorHoldTask, operatorResumeTask } from '../../api/services';
import { Play, CheckCircle, Pause, Clock, AlertCircle, TrendingUp, ListTodo, Target, ChevronDown, ChevronUp } from 'lucide-react';
import Subtask from '../../components/Subtask';

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

const OperatorDashboard = () => {
    const [tasks, setTasks] = useState([]);
    const [stats, setStats] = useState({
        total_tasks: 0,
        completed_tasks: 0,
        in_progress_tasks: 0,
        pending_tasks: 0,
        on_hold_tasks: 0
    });
    const [userInfo, setUserInfo] = useState({ username: '', full_name: '' });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState({});
    const [selectedStatus, setSelectedStatus] = useState('all');
    const [holdReasons, setHoldReasons] = useState({});
    const [expandedTaskId, setExpandedTaskId] = useState(null);

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchTasks = async () => {
        try {
            setError(null);
            const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
            const userId = currentUser.user_id;

            if (!userId) {
                setError('User not logged in');
                setLoading(false);
                return;
            }

            console.log('🔄 Fetching operator tasks for user:', userId);
            const response = await getOperatorTasks(userId);
            console.log('✅ Operator tasks response:', response.data);

            const { tasks: taskList, stats: taskStats, user } = response.data;

            // Ensure all numeric values are safe
            setTasks(Array.isArray(taskList) ? taskList : []);
            setStats({
                total_tasks: taskStats?.total_tasks || 0,
                completed_tasks: taskStats?.completed_tasks || 0,
                in_progress_tasks: taskStats?.in_progress_tasks || 0,
                pending_tasks: taskStats?.pending_tasks || 0,
                on_hold_tasks: taskStats?.on_hold_tasks || 0
            });
            setUserInfo({
                username: user?.username || 'Operator',
                full_name: user?.full_name || user?.username || 'Operator'
            });
        } catch (err) {
            console.error('❌ Failed to fetch operator tasks:', err);
            setError(err.response?.data?.detail || 'Failed to load tasks');
            setTasks([]);
        } finally {
            setLoading(false);
        }
    };

    const handleStartTask = async (taskId) => {
        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'starting' }));
            await operatorStartTask(taskId);
            await fetchTasks(); // Refresh tasks
            console.log('✅ Task started successfully');
        } catch (err) {
            console.error('❌ Failed to start task:', err);
            alert(err.response?.data?.detail || 'Failed to start task');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (!window.confirm('Are you sure you want to complete this task?')) return;

        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'completing' }));
            await operatorCompleteTask(taskId);
            await fetchTasks(); // Refresh tasks
            console.log('✅ Task completed successfully');
        } catch (err) {
            console.error('❌ Failed to complete task:', err);
            alert(err.response?.data?.detail || 'Failed to complete task');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const handleHoldTask = async (taskId) => {
        const reason = holdReasons[taskId] || window.prompt('Enter hold reason:');
        if (!reason) return;

        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'holding' }));
            await operatorHoldTask(taskId, reason);
            await fetchTasks(); // Refresh tasks
            setHoldReasons(prev => ({ ...prev, [taskId]: '' }));
            console.log('✅ Task put on hold successfully');
        } catch (err) {
            console.error('❌ Failed to hold task:', err);
            alert(err.response?.data?.detail || 'Failed to put task on hold');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const handleResumeTask = async (taskId) => {
        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'resuming' }));
            await operatorResumeTask(taskId);
            await fetchTasks(); // Refresh tasks
            console.log('✅ Task resumed successfully');
        } catch (err) {
            console.error('❌ Failed to resume task:', err);
            alert(err.response?.data?.detail || 'Failed to resume task');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const formatDuration = (seconds) => {
        if (!seconds || isNaN(seconds) || seconds <= 0) return '0m';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    const formatMinutesToHHMM = (minutes) => {
        if (!minutes || isNaN(minutes)) return '00:00';
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Not set';
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-IN', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Asia/Kolkata'
            });
        } catch (e) {
            return 'Invalid date';
        }
    };

    const formatDueDateTime = (isoString, fallbackDate) => {
        if (!isoString) {
            if (!fallbackDate || typeof fallbackDate !== 'string') return 'Not set';
            try {
                const [year, month, day] = fallbackDate.split('-');
                if (!year || !month || !day) return fallbackDate;
                const date = new Date(year, month - 1, day, 9, 0);
                return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + " • 09:00 AM";
            } catch (e) { return fallbackDate; }
        }
        try {
            const date = new Date(isoString);
            if (isNaN(date.getTime())) return isoString;
            const options = {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit', hour12: true
            };
            return date.toLocaleString('en-GB', options).replace(',', ' •').toUpperCase();
        } catch (e) { return isoString; }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'ended': return 'bg-purple-100 text-purple-800';
            case 'in_progress': return 'bg-blue-100 text-blue-800';
            case 'on_hold': return 'bg-yellow-100 text-yellow-800';
            case 'pending': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getPriorityColor = (priority) => {
        const p = priority?.toLowerCase();
        switch (p) {
            case 'urgent': return 'bg-red-500 text-white shadow-sm ring-1 ring-red-600/20';
            case 'high': return 'bg-orange-500 text-white shadow-sm ring-1 ring-orange-600/20';
            case 'medium': return 'bg-blue-500 text-white shadow-sm ring-1 ring-blue-600/20';
            case 'low': return 'bg-green-500 text-white shadow-sm ring-1 ring-green-600/20';
            default: return 'bg-gray-500 text-white shadow-sm ring-1 ring-gray-600/20';
        }
    };

    const filteredTasks = selectedStatus === 'all'
        ? tasks
        : tasks.filter(t => t.status === selectedStatus);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading tasks...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
                    <div className="flex items-center mb-2">
                        <AlertCircle className="text-red-600 mr-2" size={24} />
                        <h3 className="text-lg font-semibold text-red-900">Error</h3>
                    </div>
                    <p className="text-red-700">{error}</p>
                    <button
                        onClick={fetchTasks}
                        className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
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
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Operator Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">Welcome, {userInfo.full_name}</p>
                </div>
                <button
                    onClick={fetchTasks}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto"
                >
                    <Clock size={18} />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
                <StatCard
                    title="Total Tasks"
                    value={stats.total_tasks}
                    icon={ListTodo}
                    color="bg-blue-500"
                />
                <StatCard
                    title="In Progress"
                    value={stats.in_progress_tasks}
                    icon={Play}
                    color="bg-purple-500"
                />
                <StatCard
                    title="Completed"
                    value={stats.completed_tasks}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
                <StatCard
                    title="On Hold"
                    value={stats.on_hold_tasks}
                    icon={Pause}
                    color="bg-yellow-500"
                />
            </div>

            {/* Filter */}
            <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center gap-3">
                    <label className="text-sm font-medium text-gray-700">Filter:</label>
                    <select
                        value={selectedStatus}
                        onChange={(e) => setSelectedStatus(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Tasks</option>
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="on_hold">On Hold</option>
                        <option value="completed">Completed</option>
                    </select>
                    <span className="text-sm text-gray-600">
                        {filteredTasks.length} task(s)
                    </span>
                </div>
            </div>

            {/* Tasks List */}
            <div className="space-y-4">
                {filteredTasks.length === 0 ? (
                    <div className="bg-white rounded-lg shadow p-8 text-center">
                        <Target className="mx-auto text-gray-400 mb-4" size={48} />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No tasks found</h3>
                        <p className="text-gray-600">
                            {selectedStatus === 'all'
                                ? 'You have no assigned tasks at the moment.'
                                : `No ${selectedStatus.replace('_', ' ')} tasks.`}
                        </p>
                    </div>
                ) : (
                    filteredTasks.map(task => (
                        <div key={task.id} className="bg-white rounded-lg shadow p-4 sm:p-6">
                            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                                {/* Task Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-center gap-2 mb-2">
                                        <h3 className="text-lg font-semibold text-gray-900">{task.title || 'Untitled Task'}</h3>
                                        <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(task.status)}`}>
                                            {(task.status || 'pending').replace('_', ' ').toUpperCase()}
                                        </span>
                                        <span className={`px-2 py-1 text-[10px] font-black rounded uppercase ${getPriorityColor(task.priority)}`}>
                                            {(task.priority || 'medium')}
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-600">
                                        {task.project && (
                                            <p><span className="font-medium">Project:</span> {task.project}</p>
                                        )}
                                        {task.part_item && (
                                            <p><span className="font-medium">Part:</span> {task.part_item}</p>
                                        )}
                                        {task.nos_unit && (
                                            <p><span className="font-medium">Quantity:</span> {task.nos_unit}</p>
                                        )}
                                        {task.machine_name && (
                                            <p><span className="font-medium">Machine:</span> {task.machine_name}</p>
                                        )}
                                        {(task.due_datetime || task.due_date) && (
                                            <p><span className="font-medium text-red-600">Deadline:</span> <span className="font-bold">{formatDueDateTime(task.due_datetime, task.due_date)}</span></p>
                                        )}
                                        {task.assigned_by_name && (
                                            <p><span className="font-medium">Assigned By:</span> {task.assigned_by_name}</p>
                                        )}
                                    </div>

                                    {task.description && (
                                        <p className="mt-2 text-sm text-gray-700">{task.description}</p>
                                    )}

                                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-xs border-t pt-3">
                                        <div className="space-y-1">
                                            <p className="text-gray-500 font-medium uppercase tracking-wider">Timing Details</p>
                                            {task.expected_completion_time && (
                                                <p><span className="text-gray-600">Task Completion Duration:</span> <span className="text-blue-600 font-bold">{formatMinutesToHHMM(task.expected_completion_time)} (HH:MM)</span></p>
                                            )}
                                            <p><span className="text-gray-600">Actual Runtime:</span> <span className={`font-bold ${task.expected_completion_time && (task.total_duration_seconds / 60) > task.expected_completion_time ? 'text-red-600' : 'text-green-600'}`}>{formatDuration(task.total_duration_seconds)}</span></p>
                                            {task.total_held_seconds > 0 && (
                                                <p><span className="text-gray-600">Time Held:</span> <span className="text-amber-600 font-bold">{formatDuration(task.total_held_seconds)}</span></p>
                                            )}
                                            {task.actual_start_time && (
                                                <p><span className="text-gray-600">Started at:</span> <span className="text-gray-900 font-medium">{formatDate(task.actual_start_time)}</span></p>
                                            )}
                                            {task.actual_end_time && (
                                                <p><span className="text-gray-600">Completed at:</span> <span className="text-gray-900 font-medium">{formatDate(task.actual_end_time)}</span></p>
                                            )}
                                        </div>

                                        <div className="space-y-1">
                                            <p className="text-gray-500 font-medium uppercase tracking-wider">Hold History</p>
                                            <p><span className="text-gray-600">Total Held:</span> <span className="text-gray-900 font-medium">{formatDuration(task.total_held_seconds || 0)}</span></p>

                                            {task.holds && task.holds.length > 0 && (
                                                <div className="mt-2 space-y-1 bg-gray-50 p-2 rounded border border-gray-100 max-h-32 overflow-y-auto">
                                                    <p className="text-[10px] text-gray-400 font-bold uppercase">Hold Intervals:</p>
                                                    {task.holds.map((hold, idx) => (
                                                        <div key={idx} className="flex justify-between items-start text-[10px] py-1 border-b border-gray-100 last:border-0">
                                                            <div>
                                                                <p className="text-gray-700">{formatDate(hold.start).split(', ')[1]} → {hold.end ? formatDate(hold.end).split(', ')[1] : 'Present'}</p>
                                                                {hold.reason && <p className="text-gray-500 italic">"{hold.reason}"</p>}
                                                            </div>
                                                            <span className="font-medium text-gray-900 pl-2">{formatDuration(hold.duration_seconds)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex flex-row lg:flex-col gap-2 flex-shrink-0">
                                    <button
                                        onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)}
                                        className="flex items-center justify-center gap-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 flex-1 lg:flex-none"
                                        title={expandedTaskId === task.id ? "Hide Subtasks" : "Show Subtasks"}
                                    >
                                        {expandedTaskId === task.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                        <span>{expandedTaskId === task.id ? "Hide Details" : "Details"}</span>
                                    </button>

                                    {task.status === 'pending' && (
                                        <button
                                            onClick={() => handleStartTask(task.id)}
                                            disabled={actionLoading[task.id]}
                                            className="flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex-1 lg:flex-none"
                                        >
                                            <Play size={16} />
                                            {actionLoading[task.id] === 'starting' ? 'Starting...' : 'Start'}
                                        </button>
                                    )}

                                    {task.status === 'in_progress' && (
                                        <>
                                            <button
                                                onClick={() => handleCompleteTask(task.id)}
                                                disabled={actionLoading[task.id]}
                                                className="flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex-1 lg:flex-none"
                                            >
                                                <CheckCircle size={16} />
                                                {actionLoading[task.id] === 'completing' ? 'Completing...' : 'Complete'}
                                            </button>
                                            <button
                                                onClick={() => handleHoldTask(task.id)}
                                                disabled={actionLoading[task.id]}
                                                className="flex items-center justify-center gap-2 bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed flex-1 lg:flex-none"
                                            >
                                                <Pause size={16} />
                                                {actionLoading[task.id] === 'holding' ? 'Holding...' : 'Hold'}
                                            </button>
                                        </>
                                    )}

                                    {task.status === 'on_hold' && (
                                        <button
                                            onClick={() => handleResumeTask(task.id)}
                                            disabled={actionLoading[task.id]}
                                            className="flex items-center justify-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex-1 lg:flex-none"
                                        >
                                            <Play size={16} />
                                            {actionLoading[task.id] === 'resuming' ? 'Resuming...' : 'Resume'}
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Expanded Content: Subtasks */}
                            {expandedTaskId === task.id && (
                                <div className="mt-6 pt-6 border-t border-gray-100 animate-fade-in">
                                    <Subtask taskId={task.id} taskAssigneeId={task.assigned_to} />
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default OperatorDashboard;
