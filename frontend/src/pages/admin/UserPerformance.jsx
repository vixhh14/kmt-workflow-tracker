import React, { useState, useEffect } from 'react';
import { getUsers, getTasks } from '../../api/services';
import { Clock, CheckSquare, AlertCircle, Pause } from 'lucide-react';

const UserPerformance = () => {
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState('');
    const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [performanceData, setPerformanceData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [expandedTaskId, setExpandedTaskId] = useState(null);

    useEffect(() => {
        fetchUsers();
    }, []);

    useEffect(() => {
        if (selectedUser) {
            fetchPerformanceData();
        }
    }, [selectedUser, selectedMonth, selectedYear]);

    const fetchUsers = async () => {
        try {
            const response = await getUsers();
            setUsers(response.data);
        } catch (error) {
            console.error('Failed to fetch users:', error);
        }
    };

    const fetchPerformanceData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/admin/performance/?user_id=${selectedUser}&month=${selectedMonth}&year=${selectedYear}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to fetch performance data');

            const data = await response.json();
            setPerformanceData(data);
        } catch (error) {
            console.error('Failed to fetch performance data:', error);
        } finally {
            setLoading(false);
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

    const formatTimestamp = (timestamp) => {
        if (!timestamp) return '-';
        return new Date(timestamp).toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    };

    const months = [
        { value: 1, label: 'January' },
        { value: 2, label: 'February' },
        { value: 3, label: 'March' },
        { value: 4, label: 'April' },
        { value: 5, label: 'May' },
        { value: 6, label: 'June' },
        { value: 7, label: 'July' },
        { value: 8, label: 'August' },
        { value: 9, label: 'September' },
        { value: 10, label: 'October' },
        { value: 11, label: 'November' },
        { value: 12, label: 'December' }
    ];

    // Calculate adjusted percentage for display
    const calculateAdjustedPercentage = (completed, total) => {
        if (!total || total === 0) return 0;
        const actual = (completed / total) * 100;
        return Math.max(0, Math.round((actual - 2) * 100) / 100).toFixed(2);
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">User Performance Report</h1>
                    <p className="text-sm text-gray-600">Detailed monthly performance analysis</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    <select
                        value={selectedUser}
                        onChange={(e) => setSelectedUser(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">Select User</option>
                        {users.map(user => (
                            <option key={user.user_id} value={user.user_id}>{user.username} ({user.role})</option>
                        ))}
                    </select>

                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        {months.map(m => (
                            <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                    </select>

                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        {[2024, 2025, 2026].map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                </div>
            </div>

            {!selectedUser ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                    <p className="text-gray-500">Please select a user to view performance report.</p>
                </div>
            ) : loading ? (
                <div className="text-center py-12">Loading...</div>
            ) : performanceData ? (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-sm font-medium text-gray-500">Total Assigned</h3>
                                <div className="p-2 bg-blue-100 rounded-full">
                                    <Clock size={16} className="text-blue-600" />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{performanceData.summary.total_tasks}</p>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-sm font-medium text-gray-500">Completed</h3>
                                <div className="p-2 bg-green-100 rounded-full">
                                    <CheckSquare size={16} className="text-green-600" />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-900">{performanceData.summary.completed_tasks}</p>
                            <p className="text-xs text-green-600 mt-1">
                                {performanceData.summary.completion_percentage}% Completion Rate
                            </p>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-sm font-medium text-gray-500">Avg Completion Time</h3>
                                <div className="p-2 bg-yellow-100 rounded-full">
                                    <Clock size={16} className="text-yellow-600" />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-900">
                                {formatDuration(performanceData.summary.avg_completion_time_seconds)}
                            </p>
                        </div>

                        <div className="bg-white p-6 rounded-lg shadow">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-sm font-medium text-gray-500">Total Hold Time</h3>
                                <div className="p-2 bg-red-100 rounded-full">
                                    <Pause size={16} className="text-red-600" />
                                </div>
                            </div>
                            <p className="text-2xl font-bold text-gray-900">
                                {formatDuration(performanceData.summary.total_held_seconds)}
                            </p>
                        </div>
                    </div>

                    {/* Detailed Task Table */}
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-900">Task Details</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task Title</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Time</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expected</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hold Time</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Net Duration</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {performanceData.tasks.length === 0 ? (
                                        <tr>
                                            <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                                                No tasks found for this period.
                                            </td>
                                        </tr>
                                    ) : (
                                        performanceData.tasks.map((task) => (
                                            <React.Fragment key={task.task_id}>
                                                <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => setExpandedTaskId(expandedTaskId === task.task_id ? null : task.task_id)}>
                                                    <td className="px-6 py-4">
                                                        <div className="text-sm font-medium text-gray-900">{task.title}</div>
                                                        <div className="text-xs text-gray-500">ID: {task.task_id.substring(0, 8)}</div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full 
                                                            ${task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                                task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                                                    task.status === 'on_hold' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                                                            {task.status.replace('_', ' ')}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">
                                                        {formatTimestamp(task.actual_start_time)}
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">
                                                        {formatTimestamp(task.actual_end_time)}
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">
                                                        {task.expected_completion_time ? `${task.expected_completion_time}m` : '-'}
                                                    </td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">
                                                        <div className="flex items-center">
                                                            <span>{formatDuration(task.total_held_seconds)}</span>
                                                            {task.holds && task.holds.length > 0 && (
                                                                <span className="ml-1 text-[10px] bg-amber-100 text-amber-800 px-1 rounded">
                                                                    {task.holds.length} logs
                                                                </span>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                                        <div className={`flex items-center ${task.expected_completion_time && (task.total_duration_seconds / 60) > task.expected_completion_time
                                                            ? 'text-red-600'
                                                            : task.status === 'completed' ? 'text-green-600' : 'text-gray-900'
                                                            }`}>
                                                            {formatDuration(task.total_duration_seconds)}
                                                            {expandedTaskId === task.task_id ? <Clock size={14} className="ml-1" /> : <AlertCircle size={14} className="ml-1 text-gray-300" />}
                                                        </div>
                                                    </td>
                                                </tr>
                                                {expandedTaskId === task.task_id && (
                                                    <tr className="bg-gray-50">
                                                        <td colSpan="7" className="px-6 py-4">
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                                <div>
                                                                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Timing Breakdown</h4>
                                                                    <div className="space-y-1 text-sm bg-white p-3 rounded border border-gray-100">
                                                                        <p className="flex justify-between"><span className="text-gray-500">Actual Start:</span> <span>{task.actual_start_time ? new Date(task.actual_start_time).toLocaleString('en-IN') : 'N/A'}</span></p>
                                                                        <p className="flex justify-between"><span className="text-gray-500">Actual End:</span> <span>{task.actual_end_time ? new Date(task.actual_end_time).toLocaleString('en-IN') : 'N/A'}</span></p>
                                                                        <p className="flex justify-between"><span className="text-gray-500">Expected Mins:</span> <span>{task.expected_completion_time || 0} mins</span></p>
                                                                        <p className="flex justify-between"><span className="text-gray-500">Total Held:</span> <span>{formatDuration(task.total_held_seconds || 0)}</span></p>
                                                                        <p className="flex justify-between font-bold border-t pt-1 mt-1">
                                                                            <span className="text-gray-700">Net Duration:</span>
                                                                            <span className={task.expected_completion_time && (task.total_duration_seconds / 60) > task.expected_completion_time ? 'text-red-600' : 'text-green-600'}>
                                                                                {formatDuration(task.total_duration_seconds)}
                                                                            </span>
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <div>
                                                                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Hold History</h4>
                                                                    {task.holds && task.holds.length > 0 ? (
                                                                        <div className="space-y-2">
                                                                            {task.holds.map((hold, idx) => (
                                                                                <div key={idx} className="bg-white p-2 rounded border-l-4 border-amber-400 text-xs shadow-sm">
                                                                                    <div className="flex justify-between font-medium">
                                                                                        <span>{new Date(hold.start).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} → {hold.end ? new Date(hold.end).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'Present'}</span>
                                                                                        <span className="text-gray-900">{formatDuration(hold.duration_seconds || 0)}</span>
                                                                                    </div>
                                                                                    {hold.reason && <p className="text-gray-500 italic mt-1 font-medium">"{hold.reason}"</p>}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <p className="text-sm text-gray-400 italic">No hold logs for this task.</p>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                )}
                                            </React.Fragment>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            ) : (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                    <p className="text-gray-500">No data available.</p>
                </div>
            )}
        </div>
    );
};

export default UserPerformance;
