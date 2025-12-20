import React, { useState, useEffect } from 'react';
import { getProjects, getAttendanceSummary } from '../../api/admin';
import { getRunningTasks } from '../../api/supervisor';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { TrendingUp, CheckCircle, Clock, Pause, UserCheck, UserX, Folder, RefreshCw, BarChart3, Play } from 'lucide-react';
import ReportsSection from './ReportsSection';
import { getDashboardOverview, getProjectOverviewStats, getAdminUnifiedDashboard } from '../../api/services';
import QuickAssign from '../../components/QuickAssign';

const COLORS = {
    'Yet to Start': '#6b7280',
    'In Progress': '#3b82f6',
    'Completed': '#10b981',
    'On Hold': '#f59e0b',
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

const AdminDashboard = () => {
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('all');
    // Separate state for project-level stats vs task-level stats
    const [projectStats, setProjectStats] = useState({
        total: 0,
        yet_to_start: 0,
        in_progress: 0,
        completed: 0,
        held: 0
    });
    const [taskStats, setTaskStats] = useState({
        total: 0,
        pending: 0,
        in_progress: 0,
        completed: 0,
        on_hold: 0
    });

    const [attendanceSummary, setAttendanceSummary] = useState({
        date: '',
        present: 0,
        absent: 0,
        late: 0,
        present_users: [],
        absent_users: [],
        total_users: 0,
        records: []
    });
    const [runningTasks, setRunningTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboard();
    }, []);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('🔄 Fetching admin dashboard data...');

            const [unifiedRes, attendanceRes, runningTasksRes] = await Promise.all([
                getAdminUnifiedDashboard(),
                getAttendanceSummary(),
                getRunningTasks()
            ]);

            console.log('✅ Admin dashboard data loaded');

            const unified = unifiedRes?.data || {};
            const overview = unified.overview || {};
            const tasks = overview.tasks || { total: 0, pending: 0, in_progress: 0, completed: 0, on_hold: 0 };
            const projectsData = unified.projects || [];
            const projectStats = overview.projects || { total: 0, yet_to_start: 0, in_progress: 0, completed: 0, held: 0 };

            setProjects(Array.isArray(projectsData) ? projectsData : []);

            // 1. Task Stats (from Dashboard Overview)
            setTaskStats({
                total: tasks.total || 0,
                pending: tasks.pending || 0,
                in_progress: tasks.in_progress || 0,
                completed: tasks.completed || 0,
                on_hold: tasks.on_hold || 0
            });

            // 2. Project Stats (Unified logic)
            setProjectStats(projectStats);

            setAttendanceSummary(attendanceRes?.data || {
                date: '',
                present: 0,
                absent: 0,
                late: 0,
                present_users: [],
                absent_users: [],
                total_users: 0,
                records: []
            });
            setRunningTasks(Array.isArray(runningTasksRes?.data) ? runningTasksRes.data : []);

        } catch (err) {
            console.error('❌ Failed to fetch admin dashboard data:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    // Note: Removed fetchAnalytics() for individual project filtering for now to simplify
    // and enforce the "Unified Overview" rule first. Filtering can be re-added later if strictly needed,
    // but the prompt demands identical numbers across dashboards.

    const formatTime = (isoString) => {
        if (!isoString) return 'N/A';
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' });
        } catch {
            return 'N/A';
        }
    };

    const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
        if (percent === 0) return null;
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
        const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                className="text-xs font-semibold"
            >
                {`${(percent * 100).toFixed(0)}%`}
            </text>
        );
    };

    const chartData = [
        { name: 'Yet to Start', value: taskStats.pending || 0, color: COLORS['Yet to Start'] },
        { name: 'In Progress', value: taskStats.in_progress || 0, color: COLORS['In Progress'] },
        { name: 'Completed', value: taskStats.completed || 0, color: COLORS['Completed'] },
        { name: 'On Hold', value: taskStats.on_hold || 0, color: COLORS['On Hold'] }
    ].filter(item => item.value > 0);

    const formatDuration = (seconds) => {
        if (!seconds || seconds <= 0) return '0m';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return h > 0 ? `${h}h ${m}m` : `${m}m`;
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
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">Overview of projects, tasks, and team</p>
                </div>
                <button
                    onClick={fetchDashboard}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto"
                >
                    <RefreshCw size={18} />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Unified Operations Overview */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-4">
                    <div className="flex items-center">
                        <BarChart3 className="text-blue-600 mr-2" size={24} />
                        <h2 className="text-lg font-semibold text-gray-900">Operations Overview</h2>
                    </div>
                    <span className="text-sm text-gray-500">Global Overview</span>
                </div>

                {/* Status Cards - Aligned with Supervisor (Total Projects + Task Stats) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4 mb-6">
                    <StatCard
                        title="Total Projects"
                        value={projectStats.total}
                        icon={Folder}
                        color="bg-purple-500"
                    />
                    <StatCard
                        title="Pending"
                        value={taskStats.pending}
                        icon={Clock}
                        color="bg-gray-500"
                    />
                    <StatCard
                        title="In Progress"
                        value={taskStats.in_progress}
                        icon={TrendingUp}
                        color="bg-blue-500"
                    />
                    <StatCard
                        title="Completed"
                        value={taskStats.completed}
                        icon={CheckCircle}
                        color="bg-green-500"
                    />
                    <StatCard
                        title="On Hold"
                        value={taskStats.on_hold}
                        icon={Pause}
                        color="bg-yellow-500"
                    />
                </div>

                {/* Running Tasks Highlights - New Admin Timing Section */}
                <div className="mt-8">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center">
                            <Play className="text-green-600 mr-2" size={20} />
                            <h3 className="text-md font-bold text-gray-800 uppercase tracking-tight">Active Work Monitoring</h3>
                        </div>
                        <span className="text-xs font-semibold bg-green-100 text-green-800 px-2 py-1 rounded-full uppercase">
                            {runningTasks.length} Live
                        </span>
                    </div>

                    {runningTasks.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {runningTasks.map(task => (
                                <div key={task.id} className="bg-gray-50 border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h4 className="font-bold text-gray-900 leading-tight">{task.title}</h4>
                                            <p className="text-[11px] text-gray-500 mt-0.5 font-medium uppercase truncate">Project: {task.project}</p>
                                        </div>
                                        <div className="bg-white px-2 py-1 rounded border border-gray-100 flex items-center shadow-xs">
                                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                                            <span className="text-[10px] font-bold text-green-700">LIVE</span>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3 mb-3">
                                        <div className="bg-white p-2 rounded-lg border border-gray-100">
                                            <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">Assignment</p>
                                            <p className="text-xs font-semibold text-gray-800 truncate">👤 {task.operator_name}</p>
                                            <p className="text-xs text-gray-600 mt-1 truncate">⚙️ {task.machine_name}</p>
                                        </div>
                                        <div className="bg-white p-2 rounded-lg border border-gray-100">
                                            <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">Time Trace</p>
                                            <p className="text-xs font-bold text-blue-600">⏱️ {formatDuration(task.duration_seconds)}</p>
                                            <p className="text-[10px] text-gray-500 mt-1">Start: {formatTime(task.started_at)}</p>
                                        </div>
                                    </div>

                                    <div className="bg-white p-2 rounded-lg border border-gray-100">
                                        <div className="flex justify-between items-center mb-1">
                                            <p className="text-[10px] text-gray-400 font-bold uppercase">Hold Analytics</p>
                                            <span className="text-[10px] font-bold text-amber-600">Total: {formatDuration(task.total_held_seconds)}</span>
                                        </div>
                                        {task.holds && task.holds.length > 0 ? (
                                            <div className="space-y-1 max-h-20 overflow-y-auto pr-1">
                                                {task.holds.map((hold, idx) => (
                                                    <React.Fragment key={idx}>
                                                        <div className="flex justify-between items-center text-[10px] py-1 border-b border-gray-50 last:border-0">
                                                            <span className="text-gray-600 font-medium">
                                                                {new Date(hold.start).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} → {hold.end ? new Date(hold.end).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'Now'}
                                                            </span>
                                                            <span className="bg-gray-50 px-1 rounded font-bold">{formatDuration(hold.duration_seconds)}</span>
                                                        </div>
                                                        {hold.reason && <p className="text-[9px] text-gray-500 italic px-1 pb-1"> Reason: {hold.reason}</p>}
                                                    </React.Fragment>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-[10px] text-gray-400 italic text-center py-1">No interruptions recorded</p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl py-10 text-center">
                            <Clock className="mx-auto text-gray-300 mb-2" size={32} />
                            <p className="text-gray-500 font-medium italic">No active production tasks to monitor</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Quick Assign - Pending Tasks (Now for Admin too) */}
            <QuickAssign onAssignSuccess={fetchDashboard} />

            {/* Task Statistics & Chart */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Task Status Distribution</h3>
                    <span className="text-sm font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        Total Tasks: {taskStats.total}
                    </span>
                </div>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={renderCustomLabel}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <Folder className="mx-auto mb-4" size={48} />
                        <p>No task data available</p>
                    </div>
                )}
            </div>

            {/* Attendance Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                {/* Present Users */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center">
                            <UserCheck className="text-green-600 mr-2" size={24} />
                            <h2 className="text-lg font-semibold text-gray-900">
                                Present Today ({attendanceSummary.present || 0})
                            </h2>
                        </div>
                        <span className="text-xs text-gray-500">{attendanceSummary.date}</span>
                    </div>
                    {attendanceSummary.present_users && attendanceSummary.present_users.length > 0 ? (
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                            {attendanceSummary.present_users.map(user => (
                                <div
                                    key={user.id}
                                    className="flex items-center justify-between p-2 bg-green-50 rounded-lg"
                                >
                                    <div>
                                        <p className="font-medium text-gray-900">{user.name}</p>
                                        {user.role && (
                                            <p className="text-xs text-gray-600 capitalize">{user.role}</p>
                                        )}
                                    </div>
                                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <UserCheck className="mx-auto mb-2" size={32} />
                            <p>No users marked present today</p>
                        </div>
                    )}
                </div>

                {/* Absent Users */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center">
                            <UserX className="text-red-600 mr-2" size={24} />
                            <h2 className="text-lg font-semibold text-gray-900">
                                Absent Today ({attendanceSummary.absent || 0})
                            </h2>
                        </div>
                        {attendanceSummary.late > 0 && (
                            <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
                                {attendanceSummary.late} late
                            </span>
                        )}
                    </div>
                    {attendanceSummary.absent_users && attendanceSummary.absent_users.length > 0 ? (
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                            {attendanceSummary.absent_users.map(user => (
                                <div
                                    key={user.id}
                                    className="flex items-center justify-between p-2 bg-red-50 rounded-lg"
                                >
                                    <div>
                                        <p className="font-medium text-gray-900">{user.name}</p>
                                        {user.role && (
                                            <p className="text-xs text-gray-600 capitalize">{user.role}</p>
                                        )}
                                    </div>
                                    <div className="h-2 w-2 bg-red-500 rounded-full"></div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <UserCheck className="mx-auto mb-2" size={32} />
                            <p>All users are present today</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Reports Section */}
            <ReportsSection />

            {/* Attendance Records (if available) */}
            {attendanceSummary.records && attendanceSummary.records.length > 0 && (
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Today's Attendance Records</h2>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check In</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Check Out</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {attendanceSummary.records.map((record, index) => (
                                    <tr key={index}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {record.user}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatTime(record.check_in)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatTime(record.check_out)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                                                {record.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
