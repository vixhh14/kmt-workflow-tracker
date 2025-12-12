import React, { useState, useEffect } from 'react';
import { getTasks, startTask, holdTask, resumeTask, completeTask, denyTask, getTaskSummary } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { CheckSquare, Clock, AlertCircle, Play, Pause, CheckCircle, XCircle, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';
import {
    LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import Subtask from '../../components/Subtask';

const OperatorDashboard = () => {
    const [tasks, setTasks] = useState([]);
    const [taskStats, setTaskStats] = useState({
        pending_tasks: 0,
        active_tasks: 0,
        on_hold_tasks: 0,
        completed_tasks: 0,
        total_tasks: 0
    });
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();
    const [expandedTaskId, setExpandedTaskId] = useState(null);

    // Modal states
    const [showHoldModal, setShowHoldModal] = useState(false);
    const [showRescheduleModal, setShowRescheduleModal] = useState(false);
    const [selectedTask, setSelectedTask] = useState(null);
    const [holdReason, setHoldReason] = useState('');

    // Reschedule states
    const [rescheduleDate, setRescheduleDate] = useState('');
    const [rescheduleReason, setRescheduleReason] = useState('');

    const holdReasons = [
        'Waiting for materials',
        'Machine breakdown',
        'Shift change',
        'Waiting for supervisor approval',
        'Tool not available',
        'Other'
    ];

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, [user]);

    const fetchData = async () => {
        if (!user) return;
        try {
            setLoading(true);
            // Pass user_id to getTasks for server-side filtering
            const [tasksRes, statsRes] = await Promise.all([
                getTasks(null, null, user.user_id),
                getTaskSummary({ user_id: user.user_id })
            ]);

            setTasks(tasksRes.data);
            setTaskStats(statsRes.data);
        } catch (error) {
            console.error('Failed to fetch data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartTask = async (taskId) => {
        try {
            await startTask(taskId);
            fetchData();
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
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to hold task');
        }
    };

    const handleResumeTask = async (taskId) => {
        try {
            await resumeTask(taskId);
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || 'Failed to resume task');
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (window.confirm('Are you sure you want to mark this task as completed?')) {
            try {
                await completeTask(taskId);
                alert('Task Completed Successfully!');
                fetchData();
            } catch (error) {
                console.error('Complete task error:', error);
                alert(error.response?.data?.detail || 'Failed to complete task');
            }
        }
    };

    const handleRequestReschedule = async () => {
        if (!rescheduleDate || !rescheduleReason) {
            alert('Please provide both date and reason');
            return;
        }
        try {
            const token = localStorage.getItem('token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/tasks/${selectedTask.id}/reschedule-request`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    requested_date: new Date(rescheduleDate).toISOString(),
                    reason: rescheduleReason
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to submit request');
            }

            alert('Reschedule request submitted successfully');
            setShowRescheduleModal(false);
            setRescheduleDate('');
            setRescheduleReason('');
            setSelectedTask(null);
        } catch (error) {
            alert(error.message || 'Failed to submit request');
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

    const toggleExpand = (taskId) => {
        setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

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
                            <p className="text-2xl sm:text-3xl font-bold text-yellow-600">{taskStats.pending_tasks}</p>
                        </div>
                        <Clock className="text-yellow-500 flex-shrink-0" size={24} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">In Progress</p>
                            <p className="text-2xl sm:text-3xl font-bold text-blue-600">{taskStats.active_tasks}</p>
                        </div>
                        <AlertCircle className="text-blue-500 flex-shrink-0" size={24} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">On Hold</p>
                            <p className="text-2xl sm:text-3xl font-bold text-orange-600">{taskStats.on_hold_tasks}</p>
                        </div>
                        <Pause className="text-orange-500 flex-shrink-0" size={24} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between">
                        <div className="min-w-0">
                            <p className="text-xs sm:text-sm text-gray-600 mb-1">Completed</p>
                            <p className="text-2xl sm:text-3xl font-bold text-green-600">{taskStats.completed_tasks}</p>
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
                                        { name: 'Completed', value: taskStats.completed_tasks, color: '#10b981' },
                                        { name: 'In Progress', value: taskStats.active_tasks, color: '#3b82f6' },
                                        { name: 'Pending', value: taskStats.pending_tasks, color: '#f59e0b' },
                                        { name: 'On Hold', value: taskStats.on_hold_tasks, color: '#ef4444' }
                                    ]}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, value }) => value > 0 ? `${name}: ${value}` : ''}
                                    outerRadius={70}
                                    dataKey="value"
                                >
                                    {[taskStats.completed_tasks, taskStats.active_tasks, taskStats.pending_tasks, taskStats.on_hold_tasks].map((_, index) => (
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
                                {taskStats.total_tasks > 0 ? Math.max(0, Math.round(((taskStats.completed_tasks / taskStats.total_tasks) * 100) - 2)) : 0}%
                            </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                            <span className="text-sm sm:text-base text-gray-700">Total Assigned</span>
                            <span className="text-xl sm:text-2xl font-bold text-blue-600">{taskStats.total_tasks}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                            <span className="text-sm sm:text-base text-gray-700">Active Tasks</span>
                            <span className="text-xl sm:text-2xl font-bold text-yellow-600">
                                {taskStats.pending_tasks + taskStats.active_tasks}
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

                                                {/* Started time for in-progress */}
                                                {task.started_at && task.status === 'in_progress' && (
                                                    <span className="text-xs text-blue-700 font-medium">
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
                                                                Duration: {formatDuration(task.total_duration_seconds)}
                                                            </span>
                                                        )}
                                                    </>
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
                                                            setShowHoldModal(true);
                                                        }}
                                                        className="flex items-center space-x-1 px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition text-sm"
                                                    >
                                                        <Pause size={16} />
                                                        <span>Hold Task</span>
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            setSelectedTask(task);
                                                            setShowRescheduleModal(true);
                                                        }}
                                                        className="flex items-center space-x-1 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition text-sm"
                                                    >
                                                        <Clock size={16} />
                                                        <span>Reschedule</span>
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

            {/* Reschedule Modal */}
            {showRescheduleModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg p-4 sm:p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold mb-4">Request Reschedule</h3>
                        <p className="text-sm text-gray-600 mb-4">Please provide a new date and reason:</p>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Requested Date</label>
                            <input
                                type="datetime-local"
                                value={rescheduleDate}
                                onChange={(e) => setRescheduleDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            />
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                            <textarea
                                value={rescheduleReason}
                                onChange={(e) => setRescheduleReason(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                                rows="3"
                                placeholder="Why do you need to reschedule?"
                            ></textarea>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-3">
                            <button
                                onClick={handleRequestReschedule}
                                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm sm:text-base"
                            >
                                Submit Request
                            </button>
                            <button
                                onClick={() => {
                                    setShowRescheduleModal(false);
                                    setRescheduleDate('');
                                    setRescheduleReason('');
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
