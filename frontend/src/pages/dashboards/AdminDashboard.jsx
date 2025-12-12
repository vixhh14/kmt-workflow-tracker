import React, { useState, useEffect } from 'react';
import { getProjectSummary, getProjectStatusChart, getAttendanceSummary, getTaskStatistics } from '../../api/admin';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { TrendingUp, CheckCircle, Clock, Pause, Users, UserCheck, UserX, Folder, RefreshCw } from 'lucide-react';

const COLORS = {
    'Yet to Start': '#6b7280',
    'In Progress': '#3b82f6',
    'Completed': '#10b981',
    'Held': '#f59e0b',
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
    const [projectSummary, setProjectSummary] = useState({
        total_projects: 0,
        completed: 0,
        in_progress: 0,
        yet_to_start: 0,
        held: 0
    });
    const [chartData, setChartData] = useState([]);
    const [attendanceSummary, setAttendanceSummary] = useState({
        present_users: [],
        absent_users: [],
        total_users: 0,
        present_count: 0,
        absent_count: 0
    });
    const [taskStats, setTaskStats] = useState({
        total_tasks: 0,
        completed: 0,
        in_progress: 0,
        pending: 0,
        on_hold: 0
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('🔄 Fetching admin dashboard data...');

            const [summaryRes, chartRes, attendanceRes, statsRes] = await Promise.all([
                getProjectSummary(),
                getProjectStatusChart(),
                getAttendanceSummary(),
                getTaskStatistics()
            ]);

            console.log('✅ Admin dashboard data loaded:', {
                summary: summaryRes.data,
                chart: chartRes.data,
                attendance: attendanceRes.data,
                stats: statsRes.data
            });

            // Set project summary
            setProjectSummary({
                total_projects: summaryRes.data?.total_projects || 0,
                completed: summaryRes.data?.completed || 0,
                in_progress: summaryRes.data?.in_progress || 0,
                yet_to_start: summaryRes.data?.yet_to_start || 0,
                held: summaryRes.data?.held || 0
            });

            // Set chart data
            const chart = Array.isArray(chartRes.data) ? chartRes.data : [];
            setChartData(chart.filter(item => item.value > 0)); // Only show non-zero values

            // Set attendance summary
            setAttendanceSummary({
                present_users: Array.isArray(attendanceRes.data?.present_users) ? attendanceRes.data.present_users : [],
                absent_users: Array.isArray(attendanceRes.data?.absent_users) ? attendanceRes.data.absent_users : [],
                total_users: attendanceRes.data?.total_users || 0,
                present_count: attendanceRes.data?.present_count || 0,
                absent_count: attendanceRes.data?.absent_count || 0
            });

            // Set task statistics
            setTaskStats({
                total_tasks: statsRes.data?.total_tasks || 0,
                completed: statsRes.data?.completed || 0,
                in_progress: statsRes.data?.in_progress || 0,
                pending: statsRes.data?.pending || 0,
                on_hold: statsRes.data?.on_hold || 0
            });

        } catch (err) {
            console.error('❌ Failed to fetch admin dashboard data:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
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
                        onClick={fetchDashboardData}
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
                    <p className="text-sm sm:text-base text-gray-600">Overview of all projects and tasks</p>
                </div>
                <button
                    onClick={fetchDashboardData}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto"
                >
                    <RefreshCw size={18} />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Project Status Overview Cards */}
            <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Project Status Overview</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                    <StatCard
                        title="Total Projects"
                        value={projectSummary.total_projects}
                        icon={Folder}
                        color="bg-blue-500"
                    />
                    <StatCard
                        title="Yet to Start"
                        value={projectSummary.yet_to_start}
                        icon={Clock}
                        color="bg-gray-500"
                    />
                    <StatCard
                        title="In Progress"
                        value={projectSummary.in_progress}
                        icon={TrendingUp}
                        color="bg-blue-500"
                    />
                    <StatCard
                        title="Completed"
                        value={projectSummary.completed}
                        icon={CheckCircle}
                        color="bg-green-500"
                    />
                    <StatCard
                        title="Held"
                        value={projectSummary.held}
                        icon={Pause}
                        color="bg-yellow-500"
                    />
                </div>
            </div>

            {/* Project Status Pie Chart */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Status Distribution</h2>
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
                                    <Cell key={`cell-${index}`} fill={COLORS[entry.label] || '#6b7280'} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="text-center py-12 text-gray-500">
                        <Folder className="mx-auto mb-4" size={48} />
                        <p>No project data available</p>
                    </div>
                )}
            </div>

            {/* Task Statistics */}
            <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Task Statistics</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                    <StatCard
                        title="Total Tasks"
                        value={taskStats.total_tasks}
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
            </div>

            {/* Attendance Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                {/* Present Users */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center mb-4">
                        <UserCheck className="text-green-600 mr-2" size={24} />
                        <h2 className="text-lg font-semibold text-gray-900">
                            Present Users ({attendanceSummary.present_count})
                        </h2>
                    </div>
                    {attendanceSummary.present_users.length > 0 ? (
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
                    <div className="flex items-center mb-4">
                        <UserX className="text-red-600 mr-2" size={24} />
                        <h2 className="text-lg font-semibold text-gray-900">
                            Absent Users ({attendanceSummary.absent_count})
                        </h2>
                    </div>
                    {attendanceSummary.absent_users.length > 0 ? (
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
        </div>
    );
};

export default AdminDashboard;
