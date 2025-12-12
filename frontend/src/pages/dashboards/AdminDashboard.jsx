import React, { useState, useEffect } from 'react';
import { getOverallStats, getProjects, getProjectStatus, getTaskStats, getAttendanceSummary } from '../../api/admin';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { TrendingUp, CheckCircle, Clock, Pause, Users, UserCheck, UserX, Folder, RefreshCw } from 'lucide-react';

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
    const [overallStats, setOverallStats] = useState({
        total_projects: 0,
        completed: 0,
        in_progress: 0,
        yet_to_start: 0,
        held: 0
    });
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState('all');
    const [projectStatusData, setProjectStatusData] = useState({});
    const [taskStats, setTaskStats] = useState({
        total: 0,
        pending: 0,
        in_progress: 0,
        completed: 0,
        on_hold: 0
    });
    const [attendanceSummary, setAttendanceSummary] = useState({
        present_users: [],
        absent_users: [],
        total_users: 0,
        present_count: 0,
        absent_count: 0
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboard();
    }, []);

    useEffect(() => {
        if (!loading) {
            fetchFilteredData();
        }
    }, [selectedProject]);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('🔄 Fetching admin dashboard data...');

            const [statsRes, projectsRes, attendanceRes] = await Promise.all([
                getOverallStats(),
                getProjects(),
                getAttendanceSummary()
            ]);

            console.log('✅ Admin dashboard data loaded');

            setOverallStats({
                total_projects: statsRes.data?.total_projects || 0,
                completed: statsRes.data?.completed || 0,
                in_progress: statsRes.data?.in_progress || 0,
                yet_to_start: statsRes.data?.yet_to_start || 0,
                held: statsRes.data?.held || 0
            });

            setProjects(Array.isArray(projectsRes.data) ? projectsRes.data : []);

            setAttendanceSummary({
                present_users: Array.isArray(attendanceRes.data?.present_users) ? attendanceRes.data.present_users : [],
                absent_users: Array.isArray(attendanceRes.data?.absent_users) ? attendanceRes.data.absent_users : [],
                total_users: attendanceRes.data?.total_users || 0,
                present_count: attendanceRes.data?.present_count || 0,
                absent_count: attendanceRes.data?.absent_count || 0
            });

            // Fetch initial filtered data
            await fetchFilteredData();

        } catch (err) {
            console.error('❌ Failed to fetch admin dashboard data:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    const fetchFilteredData = async () => {
        try {
            const project = selectedProject === 'all' ? null : selectedProject;

            const [statusRes, statsRes] = await Promise.all([
                getProjectStatus(project),
                getTaskStats(project)
            ]);

            setProjectStatusData(statusRes.data || {});
            setTaskStats(statsRes.data || {});
        } catch (err) {
            console.error('Failed to fetch filtered data:', err);
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
        { name: 'Yet to Start', value: projectStatusData.yet_to_start || 0, color: COLORS['Yet to Start'] },
        { name: 'In Progress', value: projectStatusData.in_progress || 0, color: COLORS['In Progress'] },
        { name: 'Completed', value: projectStatusData.completed || 0, color: COLORS['Completed'] },
        { name: 'On Hold', value: projectStatusData.on_hold || 0, color: COLORS['On Hold'] }
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
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">Overview of all projects and tasks</p>
                </div>
                <button
                    onClick={fetchDashboard}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto"
                >
                    <RefreshCw size={18} />
                    <span>Refresh</span>
                </button>
            </div>

            {/* Overall Project Status Overview Cards */}
            <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Overall Project Status</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                    <StatCard
                        title="Total Projects"
                        value={overallStats.total_projects}
                        icon={Folder}
                        color="bg-blue-500"
                    />
                    <StatCard
                        title="Yet to Start"
                        value={overallStats.yet_to_start}
                        icon={Clock}
                        color="bg-gray-500"
                    />
                    <StatCard
                        title="In Progress"
                        value={overallStats.in_progress}
                        icon={TrendingUp}
                        color="bg-blue-500"
                    />
                    <StatCard
                        title="Completed"
                        value={overallStats.completed}
                        icon={CheckCircle}
                        color="bg-green-500"
                    />
                    <StatCard
                        title="Held"
                        value={overallStats.held}
                        icon={Pause}
                        color="bg-yellow-500"
                    />
                </div>
            </div>

            {/* Project Analytics Section */}
            <div>
                <div className="flex justify-between items-center mb-3">
                    <h2 className="text-lg font-semibold text-gray-900">Project Analytics</h2>
                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">All Projects</option>
                        {projects.map(proj => (
                            <option key={proj} value={proj}>{proj}</option>
                        ))}
                    </select>
                </div>

                {/* Task Statistics Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4 mb-6">
                    <StatCard
                        title="Total Tasks"
                        value={taskStats.total || 0}
                        icon={Folder}
                        color="bg-purple-500"
                        subtitle={selectedProject !== 'all' ? selectedProject : 'All projects'}
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

                {/* Project Status Distribution Pie Chart */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        Task Status Distribution
                        {selectedProject !== 'all' && <span className="text-sm font-normal text-gray-600"> - {selectedProject}</span>}
                    </h2>
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
