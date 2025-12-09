import React, { useState, useEffect, useRef } from 'react';
import { getTasks, startTask, holdTask, resumeTask, completeTask, denyTask } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { CheckSquare, Clock, AlertCircle, Play, Pause, CheckCircle, XCircle, RotateCcw, ChevronDown, ChevronUp, Timer } from 'lucide-react';
import {
    LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Subtask from '../../components/Subtask';

const OperatorDashboard = () => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();
    const [expandedTaskId, setExpandedTaskId] = useState(null);
    const [currentTime, setCurrentTime] = useState(new Date()); // For live timer updates

    // Modal states
    const [showHoldModal, setShowHoldModal] = useState(false);
    const [showDenyModal, setShowDenyModal] = useState(false);
    const [selectedTask, setSelectedTask] = useState(null);
    const [holdReason, setHoldReason] = useState('');
    const [denyReason, setDenyReason] = useState('');

    const holdReasons = [
        'Waiting for materials',
        'Machine breakdown',
        'Shift change',
        'Waiting for supervisor approval',
        'Other'
    ];

    const denyReasons = [
        'Machine not available',
        'Missing materials',
        'Unclear instructions',
        'Safety concerns',
        'Insufficient time',
        'Other'
    ];

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 30000);
        return () => clearInterval(interval);
    }, []);

    // Live timer update - refresh every second for in-progress tasks
    useEffect(() => {
        const timerInterval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        return () => clearInterval(timerInterval);
    }, []);

    const fetchTasks = async () => {
        try {
            setLoading(true);
            const response = await getTasks();
            const myTasks = response.data.filter(task => task.assigned_to === user?.user_id);
            setTasks(myTasks);
        } catch (error) {
            console.error('Failed to fetch tasks:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartTask = async (taskId) => {
        try {
            await startTask(taskId);
            fetchTasks();
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to start task');
        }
    };

    const handleHoldTask = async () => {
        if (!holdReason) {
            alert('Please select a reason');
            return;
        }
        try {
            await holdTask(selectedTask.id, holdReason);
            setShowHoldModal(false);
            setHoldReason('');
            setSelectedTask(null);
            fetchTasks();
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to hold task');
        }
    };

    const handleResumeTask = async (taskId) => {
        try {
            await resumeTask(taskId);
            fetchTasks();
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to resume task');
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (window.confirm('Are you sure you want to mark this task as completed?')) {
            try {
                await completeTask(taskId);
                alert('Task Completed Successfully!');
                fetchTasks();
            } catch (error) {
                console.error('Complete task error:', error);
                alert(error.response?.data?.detail || 'Failed to complete task');
            }
        }
    };

    const handleDenyTask = async () => {
        if (!denyReason) {
            alert('Please select a reason');
            return;
        }
        try {
            await denyTask(selectedTask.id, denyReason);
            setShowDenyModal(false);
            setDenyReason('');
            setSelectedTask(null);
            fetchTasks();
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to deny task');
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'in_progress': return 'bg-blue-100 text-blue-800';
            case 'on_hold': return 'bg-orange-100 text-orange-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            case 'denied': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
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

    const formatDuration = (seconds) => {
        if (!seconds || seconds < 0) return '0m';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
        if (minutes > 0) return `${minutes}m ${secs}s`;
        return `${secs}s`;
    };

    // Format timestamp to local readable format
    const formatTimestamp = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            day: '2-digit',
            month: 'short'
        });
    };

    // Calculate live elapsed time for in-progress tasks
    const getLiveElapsedTime = (task) => {
        if (!task.started_at || task.status !== 'in_progress') return null;
        const startTime = new Date(task.started_at);
        const elapsed = Math.floor((currentTime - startTime) / 1000); // seconds
        const totalWithPrevious = (task.total_duration_seconds || 0) + elapsed;
        return totalWithPrevious;
    };

    const getTimeSince = (timestamp) => {
        if (!timestamp) return '';
        const start = new Date(timestamp);
        const diffMs = currentTime - start;
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 60) return `${diffMins} mins ago`;
        const diffHours = Math.floor(diffMins / 60);
        return `${diffHours}h ${diffMins % 60}m ago`;
    };

    const toggleExpand = (taskId) => {
        setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    const pendingTasks = tasks.filter(t => t.status === 'pending');
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
    const onHoldTasks = tasks.filter(t => t.status === 'on_hold');
    const completedTasks = tasks.filter(t => t.status === 'completed');

    return (
        <div className="space-y-4 sm:space-y-6">
            <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Operator Dashboard</h1>
                <p className="text-sm sm:text-base text-gray-600">Welcome back, {user?.full_name || user?.username}!</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">Pending</p>
                            <p className="text-2xl sm:text-3xl font-bold text-yellow-600">{pendingTasks.length}</p>
                        </div>
                        <Clock className="text-yellow-500 flex-shrink-0" size={24} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">In Progress</p>
                            <p className="text-2xl sm:text-3xl font-bold text-blue-600">{inProgressTasks.length}</p>
                        </div>
                        <AlertCircle className="text-blue-500 flex-shrink-0" size={24} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">On Hold</p>
                            <p className="text-2xl sm:text-3xl font-bold text-orange-600">{onHoldTasks.length}</p>
                        </div>
                        <Pause className="text-orange-500 flex-shrink-0" size={24} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">Completed</p>
                            <p className="text-2xl sm:text-3xl font-bold text-green-600">{completedTasks.length}</p>
                        </div>
                        <CheckSquare className="text-green-500 flex-shrink-0" size={24} />
                    </div>
                </div>
            </div>

            {/* Personal Performance Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4">My Task Distribution</h3>
                    <div className="h-52 sm:h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={[
                                        { name: 'Completed', value: completedTasks.length, color: '#10b981' },
                                        { name: 'In Progress', value: inProgressTasks.length, color: '#3b82f6' },
                                        { name: 'Pending', value: pendingTasks.length, color: '#f59e0b' },
                                        { name: 'On Hold', value: onHoldTasks.length, color: '#ef4444' }
                                    ]}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, value }) => value > 0 ? `${name}: ${value}` : ''}
                                    outerRadius={70}
                                    dataKey="value"
                                >
                                    {[completedTasks, inProgressTasks, pendingTasks, onHoldTasks].map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={[
                                            '#10b981', '#3b82f6', '#f59e0b', '#ef4444'
                                        ][index]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4">Performance Summary</h3>
                    <div className="space-y-3 sm:space-y-4">
                        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                            <span className="text-sm sm:text-base text-gray-700">Completion Rate</span>
                            <span className="text-xl sm:text-2xl font-bold text-green-600">
                                {tasks.length > 0 ? Math.round((completedTasks.length / tasks.length) * 100) : 0}%
                            </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                            <span className="text-sm sm:text-base text-gray-700">Total Assigned</span>
                            <span className="text-xl sm:text-2xl font-bold text-blue-600">{tasks.length}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                            <span className="text-sm sm:text-base text-gray-700">Active Tasks</span>
                            <span className="text-xl sm:text-2xl font-bold text-yellow-600">
                                {pendingTasks.length + inProgressTasks.length}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* My Tasks */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 sm:p-6 border-b">
                    <h3 className="text-base sm:text-lg font-semibold">My Assigned Tasks</h3>
                </div>
                <div className="divide-y">
                    {tasks.length === 0 ? (
                        <div className="p-6 sm:p-8 text-center text-gray-500">
                            No tasks assigned to you yet.
                        </div>
                    ) : (
                        tasks.map((task) => (
                            <div key={task.id}>
                                <div className="p-4 sm:p-6 hover:bg-gray-50">
                                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center space-x-2">
                                                <button
                                                    onClick={() => toggleExpand(task.id)}
                                                    className="text-gray-400 hover:text-gray-600 transition flex-shrink-0"
                                                >
                                                    {expandedTaskId === task.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                                </button>
                                                <h4 className="font-semibold text-gray-900 text-sm sm:text-base truncate">{task.title}</h4>
                                            </div>
                                            <p className="text-xs sm:text-sm text-gray-600 mt-1 ml-7 line-clamp-2">{task.description}</p>
                                            <div className="flex flex-wrap items-center gap-2 mt-3 ml-7">
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(task.status)}`}>
                                                    {task.status.replace('_', ' ')}
                                                </span>
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getPriorityColor(task.priority)}`}>
                                                    {task.priority}
                                                </span>
                                                {/* Live Timer for in-progress tasks */}
                                                {task.status === 'in_progress' && (
                                                    <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold animate-pulse">
                                                        <Timer size={12} />
                                                        {formatDuration(getLiveElapsedTime(task))}
                                                    </span>
                                                )}
                                                {/* Started time for in-progress */}
                                                {task.started_at && task.status === 'in_progress' && (
                                                    <span className="text-xs text-gray-600 hidden sm:inline">
                                                        Started: {formatTimestamp(task.started_at)}
                                                    </span>
                                                )}
                                                {/* Completed time and total duration for completed tasks */}
                                                {task.status === 'completed' && (
                                                    <>
                                                        {task.completed_at && (
                                                            <span className="text-xs text-green-700">
                                                                Completed: {formatTimestamp(task.completed_at)}
                                                            </span>
                                                        )}
                                                        {task.total_duration_seconds > 0 && (
                                                            <span className="text-xs text-gray-600">
                                                                Total: {formatDuration(task.total_duration_seconds)}
                                                            </span>
                                                        )}
                                                    </>
                                                )}
                                                {/* Show previous duration for non-completed tasks that have been held before */}
                                                {task.status !== 'in_progress' && task.status !== 'completed' && task.total_duration_seconds > 0 && (
                                                    <span className="text-xs text-gray-600">
                                                        Previous time: {formatDuration(task.total_duration_seconds)}
                                                    </span>
                                                )}
                                            </div>
                                            {task.hold_reason && (
                                                <p className="text-xs text-orange-600 mt-2 ml-7">Hold reason: {task.hold_reason}</p>
                                            )}
                                        </div>
                                        <div className="flex flex-wrap gap-2 ml-7 sm:ml-4">
                                            {task.status === 'pending' && (
                                                <>
                                                    <button
                                                        onClick={() => handleStartTask(task.id)}
                                                        className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                                                    >
                                                        <Play size={16} />
                                                        <span>Start</span>
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            setSelectedTask(task);
                                                            setShowDenyModal(true);
                                                        }}
                                                        className="flex items-center space-x-1 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm"
                                                    >
                                                        <XCircle size={16} />
                                                        <span>Deny</span>
                                                    </button>
                                                </>
                                            )}
                                            {task.status === 'in_progress' && (
                                                <>
                                                    <button
                                                        onClick={() => {
                                                            setSelectedTask(task);
                                                            setShowHoldModal(true);
                                                        }}
                                                        className="flex items-center space-x-1 px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition text-sm"
                                                    >
                                                        <Pause size={16} />
                                                        <span>Hold</span>
                                                    </button>
                                                    <button
                                                        onClick={() => handleCompleteTask(task.id)}
                                                        className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm"
                                                    >
                                                        <CheckCircle size={16} />
                                                        <span>Complete</span>
                                                    </button>
                                                </>
                                            )}
                                            {task.status === 'on_hold' && (
                                                <button
                                                    onClick={() => handleResumeTask(task.id)}
                                                    className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                                                >
                                                    <RotateCcw size={16} />
                                                    <span>Resume</span>
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                {expandedTaskId === task.id && (
                                    <div className="px-4 sm:px-6 pb-6 bg-gray-50 border-t border-gray-100">
                                        <Subtask taskId={task.id} />
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Hold Modal */}
            {showHoldModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg p-4 sm:p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold mb-4">Hold Task</h3>
                        <p className="text-sm text-gray-600 mb-4">Please select a reason for holding this task:</p>
                        <select
                            value={holdReason}
                            onChange={(e) => setHoldReason(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 text-sm sm:text-base"
                        >
                            <option value="">Select a reason...</option>
                            {holdReasons.map(reason => (
                                <option key={reason} value={reason}>{reason}</option>
                            ))}
                        </select>
                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={handleHoldTask}
                                className="flex-1 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 text-sm sm:text-base"
                            >
                                Hold Task
                            </button>
                            <button
                                onClick={() => {
                                    setShowHoldModal(false);
                                    setHoldReason('');
                                    setSelectedTask(null);
                                }}
                                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm sm:text-base"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Deny Modal */}
            {showDenyModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg p-4 sm:p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold mb-4">Deny Task</h3>
                        <p className="text-sm text-gray-600 mb-4">Please select a reason for denying this task:</p>
                        <select
                            value={denyReason}
                            onChange={(e) => setDenyReason(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 text-sm sm:text-base"
                        >
                            <option value="">Select a reason...</option>
                            {denyReasons.map(reason => (
                                <option key={reason} value={reason}>{reason}</option>
                            ))}
                        </select>
                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={handleDenyTask}
                                className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm sm:text-base"
                            >
                                Deny Task
                            </button>
                            <button
                                onClick={() => {
                                    setShowDenyModal(false);
                                    setDenyReason('');
                                    setSelectedTask(null);
                                }}
                                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm sm:text-base"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default OperatorDashboard;
