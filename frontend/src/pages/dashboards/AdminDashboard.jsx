import React, { useState, useEffect, useMemo } from 'react';
import {
    getAnalytics,
    getTasks,
    getMachines,
    getUsers,
    getTaskSummary
} from '../../api/services';
import {
    CheckSquare,
    TrendingUp,
    Users as UsersIcon
} from 'lucide-react';
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

/* ---------- Small reusable Stat Card ---------- */
const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
        <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-600 mb-1 truncate">{title}</p>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value}</p>
            </div>
            <div className={`p-2 sm:p-3 rounded-full ${color} flex-shrink-0 ml-2`}>
                <Icon className="text-white" size={20} />
            </div>
        </div>
    </div>
);

/* ---------- Colors ---------- */
const STATUS_COLORS = {
    'Yet to Start': '#6b7280', // Gray
    'In Progress': '#3b82f6', // Blue
    'Completed': '#10b981', // Green
    'On Hold': '#ef4444' // Red
};

const getPriorityColor = (priority) => {
    switch (priority) {
        case 'high': return '#ef4444';
        case 'medium': return '#eab308';
        case 'low': return '#22c55e';
        default: return '#6b7280';
    }
};

/* ---------- Admin Dashboard Component ---------- */
const AdminDashboard = () => {
    const [analytics, setAnalytics] = useState(null);
    const [projectStats, setProjectStats] = useState({
        total: 0, completed: 0, in_progress: 0, yet_to_start: 0, held: 0
    });
    const [users, setUsers] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedMonth, setSelectedMonth] = useState(0); // 0 => all months
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [selectedProject, setSelectedProject] = useState('all');
    const [priorityFilter, setPriorityFilter] = useState('all');

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30 * 1000); // refresh every 30s for near-realtime
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedMonth, selectedYear]);

    const fetchData = async () => {
        setLoading(true);
        try {
            // fetch analytics and project stats in parallel
            const [analyticsRes, statsRes] = await Promise.allSettled([
                getAnalytics(),
                getTaskSummary({})
            ]);

            if (analyticsRes.status === 'fulfilled') {
                setAnalytics(analyticsRes.value.data);
            } else {
                console.error('getAnalytics failed', analyticsRes.reason);
            }

            if (statsRes.status === 'fulfilled' && statsRes.value.data.project_stats) {
                setProjectStats(statsRes.value.data.project_stats);
            } else {
                console.error('getTaskSummary failed or returned no project_stats', statsRes.reason);
            }

            // users
            try {
                const usersRes = await getUsers();
                setUsers(usersRes.data || []);
            } catch (err) {
                console.error('getUsers failed', err);
            }

            // tasks (with month/year filters)
            try {
                const tasksRes = await getTasks(
                    selectedMonth === 0 ? null : selectedMonth,
                    selectedYear === 0 ? null : selectedYear
                );
                setTasks(tasksRes.data || []);
            } catch (err) {
                console.error('getTasks failed', err);
                setTasks([]);
            }

            // machines
            try {
                const machinesRes = await getMachines();
                setMachines(machinesRes.data || []);
            } catch (err) {
                console.error('getMachines failed', err);
            }
        } catch (error) {
            console.error('Unexpected fetchData error:', error);
        } finally {
            setLoading(false);
        }
    };

    // unique sorted project list
    const projectList = useMemo(() => {
        const projects = [...new Set(tasks.map(t => t.project).filter(Boolean))];
        return projects.sort();
    }, [tasks]);

    // filtered tasks by selected project
    const filteredTasks = useMemo(() => {
        if (selectedProject === 'all') return tasks;
        return tasks.filter(t => t.project === selectedProject);
    }, [tasks, selectedProject]);

    // project overview data (pie)
    const projectOverviewData = useMemo(() => [
        { name: 'Yet to Start', value: projectStats.yet_to_start || 0, color: STATUS_COLORS['Yet to Start'] },
        { name: 'In Progress', value: projectStats.in_progress || 0, color: STATUS_COLORS['In Progress'] },
        { name: 'Completed', value: projectStats.completed || 0, color: STATUS_COLORS['Completed'] },
        { name: 'On Hold', value: projectStats.held || 0, color: STATUS_COLORS['On Hold'] }
    ], [projectStats]);

    // task breakdown for selected project
    const taskBreakdownData = useMemo(() => {
        const stats = { 'Yet to Start': 0, 'In Progress': 0, 'Completed': 0, 'On Hold': 0 };
        filteredTasks.forEach(task => {
            if (task.status === 'completed') stats['Completed']++;
            else if (task.status === 'in_progress') stats['In Progress']++;
            else if (task.status === 'on_hold') stats['On Hold']++;
            else stats['Yet to Start']++;
        });
        return [
            { name: 'Yet to Start', value: stats['Yet to Start'], color: STATUS_COLORS['Yet to Start'] },
            { name: 'In Progress', value: stats['In Progress'], color: STATUS_COLORS['In Progress'] },
            { name: 'On Hold', value: stats['On Hold'], color: STATUS_COLORS['On Hold'] },
            { name: 'Completed', value: stats['Completed'], color: STATUS_COLORS['Completed'] }
        ];
    }, [filteredTasks]);

    // priority chart data (top 10 by recency)
    const priorityTaskData = useMemo(() => {
        let filtered = tasks;
        if (priorityFilter !== 'all') filtered = tasks.filter(t => t.priority === priorityFilter);
        return filtered.slice(0, 10).map(task => ({
            name: task.title ? (task.title.length > 18 ? `${task.title.substring(0, 18)}...` : task.title) : 'Untitled',
            value: 1,
            priority: task.priority,
            fill: getPriorityColor(task.priority)
        }));
    }, [tasks, priorityFilter]);

    // per-project completion (with -2 adjustment)
    const projectCompletionList = useMemo(() => {
        const groups = tasks.reduce((acc, task) => {
            const project = task.project || 'No Project';
            acc[project] = acc[project] || { total: 0, completed: 0 };
            acc[project].total++;
            if (task.status === 'completed') acc[project].completed++;
            return acc;
        }, {});
        return Object.entries(groups).map(([proj, stats]) => {
            const actualPercent = stats.total > 0 ? (stats.completed / stats.total) * 100 : 0;
            const adjustedPercent = Math.max(0, Math.round((actualPercent - 2) * 100) / 100);
            return {
                name: proj.length > 22 ? `${proj.substring(0, 22)}...` : proj,
                completion: adjustedPercent,
                total: stats.total,
                completed: stats.completed
            };
        });
    }, [tasks]);

    const months = [
        { value: 0, label: 'All Months' },
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

    if (loading) return <div className="text-center py-8">Loading...</div>;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">System overview and analytics</p>
                </div>

                <div className="flex gap-2">
                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                        className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
                    >
                        {months.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                    </select>
                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                        className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
                    >
                        <option value={0}>All Years</option>
                        {[2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                </div>
            </div>

            {/* Top stat cards (summary) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <StatCard title="Active Projects" value={analytics?.active_projects_count || 0} icon={CheckSquare} color="bg-indigo-500" />
                <StatCard title="Present Today" value={analytics?.attendance?.present_count || 0} icon={UsersIcon} color="bg-green-500" />
                <StatCard title="On Leave / Absent" value={analytics?.attendance?.absent_count || 0} icon={UsersIcon} color="bg-red-500" />
            </div>

            {/* Status of Projects */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-100 rounded-lg"><TrendingUp className="text-purple-600" size={20} /></div>
                        <h3 className="text-lg font-semibold text-gray-900">Status of Projects</h3>
                    </div>

                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="w-full sm:w-64 px-3 py-2 text-sm border border-gray-300 rounded-lg"
                    >
                        <option value="all">All Projects (Overview)</option>
                        {projectList.map(project => <option key={project} value={project}>{project}</option>)}
                    </select>
                </div>

                {/* Summary */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
                    <div className="bg-gray-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-gray-500 uppercase">Total Projects</p>
                        <p className="text-xl font-bold text-gray-900">{projectStats.total}</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-green-600 uppercase">Completed</p>
                        <p className="text-xl font-bold text-green-700">{projectStats.completed}</p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-blue-600 uppercase">In Progress</p>
                        <p className="text-xl font-bold text-blue-700">{projectStats.in_progress}</p>
                    </div>
                    <div className="bg-gray-100 p-3 rounded-lg text-center">
                        <p className="text-xs text-gray-600 uppercase">Yet to Start</p>
                        <p className="text-xl font-bold text-gray-700">{projectStats.yet_to_start}</p>
                    </div>
                    <div className="bg-red-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-red-600 uppercase">Held</p>
                        <p className="text-xl font-bold text-red-700">{projectStats.held}</p>
                    </div>
                </div>

                {/* Pie Chart */}
                <div className="border border-gray-100 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-4">
                        {selectedProject === 'all' ? 'Status of Projects' : `"${selectedProject}" - Project Status`}
                    </h4>

                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={selectedProject === 'all' ? projectOverviewData : taskBreakdownData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine
                                    label={({ name, value }) => (value > 0 ? `${name}: ${value}` : null)}
                                    outerRadius={70}
                                    dataKey="value"
                                >
                                    {(selectedProject === 'all' ? projectOverviewData : taskBreakdownData).map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip formatter={(value, name) => [value, name]} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="flex flex-wrap justify-center gap-4 mt-4">
                        {Object.entries(STATUS_COLORS).map(([status, color]) => (
                            <div key={status} className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                                <span className="text-xs text-gray-600">{status}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Attendance Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base font-semibold mb-4 text-green-700">Present Users</h3>
                    <div className="max-h-60 overflow-y-auto">
                        <ul className="divide-y divide-gray-100">
                            {(analytics?.attendance?.present_list || []).length > 0 ? (
                                analytics.attendance.present_list.map((u, idx) => (
                                    <li key={idx} className="py-2 flex justify-between items-center">
                                        <span className="font-medium text-gray-800 text-sm sm:text-base truncate">{u.full_name || u.username}</span>
                                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full capitalize flex-shrink-0 ml-2">{u.role}</span>
                                    </li>
                                ))
                            ) : <p className="text-gray-500 text-sm">No users present yet.</p>}
                        </ul>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base font-semibold mb-4 text-red-700">Absent / On Leave</h3>
                    <div className="max-h-60 overflow-y-auto">
                        <ul className="divide-y divide-gray-100">
                            {(analytics?.attendance?.absent_list || []).length > 0 ? (
                                analytics.attendance.absent_list.map((u, idx) => (
                                    <li key={idx} className="py-2 flex justify-between items-center">
                                        <span className="font-medium text-gray-800 text-sm sm:text-base truncate">{u.full_name || u.username}</span>
                                        <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full capitalize flex-shrink-0 ml-2">{u.role}</span>
                                    </li>
                                ))
                            ) : <p className="text-gray-500 text-sm">Everyone is present!</p>}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Tasks by Priority */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base sm:text-lg font-semibold">Tasks by Priority</h3>
                    <select
                        className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
                        value={priorityFilter}
                        onChange={(e) => setPriorityFilter(e.target.value)}
                    >
                        <option value="all">All Priorities</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>
                </div>

                <div className="mb-3 flex flex-wrap items-center gap-2 text-xs sm:text-sm">
                    <div className="flex items-center">
                        <div className="w-3 h-3 bg-red-500 rounded mr-2"></div><span>High Priority</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-3 h-3 bg-yellow-500 rounded mr-2"></div><span>Medium Priority</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-3 h-3 bg-green-500 rounded mr-2"></div><span>Low Priority</span>
                    </div>
                </div>

                <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={priorityTaskData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} interval={0} tick={{ fontSize: 10 }} />
                            <YAxis />
                            <Tooltip
                                content={({ active, payload }) => {
                                    if (active && payload && payload.length) {
                                        const data = payload[0].payload;
                                        return (
                                            <div className="bg-white p-2 border border-gray-200 rounded shadow text-xs sm:text-sm">
                                                <p className="font-semibold">{data.name}</p>
                                                <p className="capitalize">Priority: {data.priority || 'N/A'}</p>
                                            </div>
                                        );
                                    }
                                    return null;
                                }}
                            />
                            <Bar dataKey="value" name="Task">
                                {priorityTaskData.map((entry, index) => <Cell key={`cell-prio-${index}`} fill={entry.fill} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Project completion list (optional visualization) */}
            <div className="bg-white rounded-lg shadow p-4">
                <h3 className="text-base font-semibold mb-3">Projects - Completion (adjusted -2%)</h3>
                {projectCompletionList.length === 0 ? (
                    <p className="text-gray-500">No projects found</p>
                ) : (
                    <div className="space-y-3">
                        {projectCompletionList.map((p) => (
                            <div key={p.name} className="flex items-center justify-between">
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-gray-800 truncate">{p.name}</p>
                                    <p className="text-xs text-gray-500">{p.completed}/{p.total} completed</p>
                                </div>
                                <div className="ml-4 text-right">
                                    <p className="text-sm font-semibold text-gray-900">{p.completion}%</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminDashboard;
