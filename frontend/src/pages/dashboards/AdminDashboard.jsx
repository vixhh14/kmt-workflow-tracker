
import React, { useState, useEffect, useMemo } from 'react';
import { getAnalytics, getTasks, getMachines, getUsers, getTaskSummary } from '../../api/services';
import { CheckSquare, Clock, TrendingUp, Monitor, Users as UsersIcon, Calendar, PieChartIcon, Folder, Pause } from 'lucide-react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
        <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-gray-600 mb-1 truncate">{title}</p>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value}</p>
            </div>
            <div className={`p - 2 sm: p - 3 rounded - full ${color} flex - shrink - 0 ml - 2`}>
                <Icon className="text-white" size={20} />
            </div>
        </div>
    </div>
);

const COLORS = {
    pending: '#f59e0b',
    in_progress: '#3b82f6',
    completed: '#10b981',
    on_hold: '#ef4444',
    high: '#ef4444',
    medium: '#eab308',
    low: '#22c55e'
};

// Status colors for pie charts
const STATUS_COLORS = {
    'Yet to Start': '#6b7280',  // Gray
    'In Progress': '#3b82f6',   // Blue
    'Completed': '#10b981',     // Green
    'On Hold': '#ef4444'        // Red
};

const AdminDashboard = () => {
    const [analytics, setAnalytics] = useState(null);
    const [projectStats, setProjectStats] = useState({
        total: 0,
        completed: 0,
        in_progress: 0,
        yet_to_start: 0,
        held: 0
    });
    const [users, setUsers] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedMonth, setSelectedMonth] = useState(0);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [selectedProject, setSelectedProject] = useState('all');
    const [priorityFilter, setPriorityFilter] = useState('all');

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Real-time updates
        return () => clearInterval(interval);
    }, [selectedMonth, selectedYear]);

    const fetchData = async () => {
        // setLoading(true); // Don't show loading on refresh
        try {
            try {
                const [analyticsRes, statsRes] = await Promise.all([
                    getAnalytics(),
                    getTaskSummary({}) // Fetch global stats
                ]);
                setAnalytics(analyticsRes.data);
                if (statsRes.data.project_stats) {
                    setProjectStats(statsRes.data.project_stats);
                }
            } catch (error) {
                console.error('Failed to fetch analytics:', error);
            }

            try {
                const usersRes = await getUsers();
                setUsers(usersRes.data);
            } catch (error) {
                console.error('Failed to fetch users:', error);
            }

            try {
                const tasksRes = await getTasks(
                    selectedMonth === 0 ? null : selectedMonth,
                    selectedYear === 0 ? null : selectedYear
                );
                setTasks(tasksRes.data);
            } catch (error) {
                console.error('Failed to fetch tasks:', error);
            }

            try {
                const machinesRes = await getMachines();
                setMachines(machinesRes.data);
            } catch (error) {
                console.error('Failed to fetch machines:', error);
            }

        } catch (error) {
            console.error('Unexpected error in fetchData:', error);
        } finally {
            setLoading(false);
        }
    };

    // Get unique project list
    const projectList = useMemo(() => {
        const projects = [...new Set(tasks.map(t => t.project).filter(Boolean))];
        return projects.sort();
    }, [tasks]);

    // Get filtered tasks by selected project
    const filteredTasks = useMemo(() => {
        if (selectedProject === 'all') return tasks;
        return tasks.filter(t => t.project === selectedProject);
    }, [tasks, selectedProject]);

    // Calculate project-level status for pie chart
    const getProjectOverviewData = useMemo(() => {
        return [
            { name: 'Yet to Start', value: projectStats.yet_to_start, color: STATUS_COLORS['Yet to Start'] },
            { name: 'In Progress', value: projectStats.in_progress, color: STATUS_COLORS['In Progress'] },
            { name: 'Completed', value: projectStats.completed, color: STATUS_COLORS['Completed'] },
            { name: 'On Hold', value: projectStats.held, color: STATUS_COLORS['On Hold'] },
        ];
    }, [projectStats]);

    // Get task status breakdown for selected project
    const getTaskBreakdownData = useMemo(() => {
        const stats = {
            'Yet to Start': 0,
            'In Progress': 0,
            'Completed': 0,
            'On Hold': 0
        };

        filteredTasks.forEach(task => {
            if (task.status === 'completed') {
                stats['Completed']++;
            } else if (task.status === 'in_progress') {
                stats['In Progress']++;
            } else if (task.status === 'on_hold') {
                stats['On Hold']++;
            } else {
                stats['Yet to Start']++;
            }
        });

        return [
            { name: 'Yet to Start', value: stats['Yet to Start'], color: STATUS_COLORS['Yet to Start'] },
            { name: 'In Progress', value: stats['In Progress'], color: STATUS_COLORS['In Progress'] },
            { name: 'On Hold', value: stats['On Hold'], color: STATUS_COLORS['On Hold'] },
            { name: 'Completed', value: stats['Completed'], color: STATUS_COLORS['Completed'] },
        ];
    }, [filteredTasks]);

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return '#ef4444';
            case 'medium': return '#eab308';
            case 'low': return '#22c55e';
            default: return '#6b7280';
        }
    };

    const getPriorityTaskData = () => {
        let filtered = tasks;
        if (priorityFilter !== 'all') {
            filtered = tasks.filter(t => t.priority === priorityFilter);
        }
        return filtered.slice(0, 10).map(task => ({
            name: task.title.length > 15 ? task.title.substring(0, 15) + '...' : task.title,
            value: 1,
            priority: task.priority,
            fill: getPriorityColor(task.priority)
        }));
    };

    const getProjectCompletionData = () => {
        const projectGroups = tasks.reduce((acc, task) => {
            const project = task.project || 'No Project';
            if (!acc[project]) {
                acc[project] = { total: 0, completed: 0 };
            }
            acc[project].total++;
            if (task.status === 'completed') {
                acc[project].completed++;
            }
            return acc;
        }, {});

        return Object.entries(projectGroups).map(([project, stats]) => {
            const actualPercent = stats.total > 0 ? (stats.completed / stats.total) * 100 : 0;
            const adjustedPercent = Math.max(0, Math.round((actualPercent - 2) * 100) / 100);
            return {
                name: project.length > 20 ? project.substring(0, 20) + '...' : project,
                completion: adjustedPercent,
                total: stats.total,
                completed: stats.completed
            };
        });
    };

    // Custom label for pie chart that handles overlapping
    const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name, value }) => {
        if (value === 0) return null;
        const RADIAN = Math.PI / 180;
        const radius = outerRadius * 1.2;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        return (
            <text
                x={x}
                y={y}
                fill="#374151"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                fontSize={12}
            >
                {`${name}: ${value} `}
            </text>
        );
    };

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

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">System overview and analytics</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                        className="w-full sm:w-auto px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        {months.map(month => (
                            <option key={month.value} value={month.value}>{month.label}</option>
                        ))}
                    </select>
                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                        className="w-full sm:w-auto px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                        <option value={0}>All Years</option>
                        {[2024, 2025, 2026].map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Attendance & Active Projects */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                <StatCard
                    title="Active Projects"
                    value={analytics?.active_projects_count || 0}
                    icon={CheckSquare}
                    color="bg-indigo-500"
                />
                <StatCard
                    title="Present Today"
                    value={analytics?.attendance?.present_count || 0}
                    icon={UsersIcon}
                    color="bg-green-500"
                />
                <StatCard
                    title="On Leave / Absent"
                    value={analytics?.attendance?.absent_count || 0}
                    icon={UsersIcon}
                    color="bg-red-500"
                />
            </div>

            {/* Project Status Analytics Section */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-purple-100 rounded-lg">
                            <TrendingUp className="text-purple-600" size={20} />
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900">Status of Projects</h3>
                    </div>
                    <select
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="w-full sm:w-64 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="all">All Projects (Overview)</option>
                        {projectList.map(project => (
                            <option key={project} value={project}>{project}</option>
                        ))}
                    </select>
                </div>

                {/* Project Summary Block */}
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

                <div className="grid grid-cols-1 gap-6">
                    {/* Project Status Pie Chart */}
                    <div className="border border-gray-100 rounded-lg p-4">
                        <h4 className="text-sm font-semibold text-gray-700 mb-4">
                            {selectedProject === 'all' ? 'Status of Projects' : `"${selectedProject}" - Project Status`}
                        </h4>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={selectedProject === 'all' ? getProjectOverviewData : getTaskBreakdownData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={true}
                                        label={renderCustomLabel}
                                        outerRadius={70}
                                        fill="#8884d8"
                                        dataKey="value"
                                    >
                                        {(selectedProject === 'all' ? getProjectOverviewData : getTaskBreakdownData).map((entry, index) => (
                                            <Cell key={`cell - ${index} `} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        formatter={(value, name) => [value, name]}
                                        contentStyle={{ fontSize: '12px' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        {/* Legend */}
                        <div className="flex flex-wrap justify-center gap-4 mt-4">
                            {Object.entries(STATUS_COLORS).map(([status, color]) => (
                                <div key={status} className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></div>
                                    <span className="text-xs text-gray-600">{status}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Attendance Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4 text-green-700">Present Users</h3>
                    <div className="max-h-60 overflow-y-auto">
                        <ul className="divide-y divide-gray-100">
                            {analytics?.attendance?.present_list?.length > 0 ? (
                                analytics.attendance.present_list.map((u, idx) => (
                                    <li key={idx} className="py-2 flex justify-between items-center">
                                        <span className="font-medium text-gray-800 text-sm sm:text-base truncate">{u.full_name || u.username}</span>
                                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full capitalize flex-shrink-0 ml-2">{u.role}</span>
                                    </li>
                                ))
                            ) : (
                                <p className="text-gray-500 text-sm">No users present yet.</p>
                            )}
                        </ul>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4 text-red-700">Absent / On Leave</h3>
                    <div className="max-h-60 overflow-y-auto">
                        <ul className="divide-y divide-gray-100">
                            {analytics?.attendance?.absent_list?.length > 0 ? (
                                analytics.attendance.absent_list.map((u, idx) => (
                                    <li key={idx} className="py-2 flex justify-between items-center">
                                        <span className="font-medium text-gray-800 text-sm sm:text-base truncate">{u.full_name || u.username}</span>
                                        <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full capitalize flex-shrink-0 ml-2">{u.role}</span>
                                    </li>
                                ))
                            ) : (
                                <p className="text-gray-500 text-sm">Everyone is present!</p>
                            )}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Charts Row - Tasks by Priority */}
            <div className="grid grid-cols-1 gap-4 sm:gap-6">
                {/* Tasks by Priority */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base sm:text-lg font-semibold">Tasks by Priority</h3>
                        <select
                            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                            value={priorityFilter}
                            onChange={(e) => setPriorityFilter(e.target.value)}
                            id="priority-filter-dropdown"
                        >
                            <option value="all">All Priorities</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                    </div>

                    <div className="mb-3 flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm">
                        <div className="flex items-center">
                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-red-500 rounded mr-2"></div>
                            <span>High Priority</span>
                        </div>
                        <div className="flex items-center">
                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-500 rounded mr-2"></div>
                            <span>Medium Priority</span>
                        </div>
                        <div className="flex items-center">
                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-green-500 rounded mr-2"></div>
                            <span>Low Priority</span>
                        </div>
                    </div>
                    <div className="h-56 sm:h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={getPriorityTaskData()}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="name"
                                    angle={-45}
                                    textAnchor="end"
                                    height={80}
                                    interval={0}
                                    tick={{ fontSize: 10 }}
                                />
                                <YAxis />
                                <Tooltip
                                    content={({ active, payload }) => {
                <StatCard
                    title="Active Projects"
                    value={analytics?.active_projects_count || 0}
                    icon={CheckSquare}
                    color="bg-indigo-500"
                />
                <StatCard
                    title="Present Today"
                    value={analytics?.attendance?.present_count || 0}
                    icon={UsersIcon}
                    color="bg-green-500"
                />
                <StatCard
                    title="On Leave / Absent"
                    value={analytics?.attendance?.absent_count || 0}
                    icon={UsersIcon}
                    color="bg-red-500"
                />
            </div>

                            {/* Project Status Analytics Section */}
                            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                                    <div className="flex items-center gap-2">
                                        <div className="p-2 bg-purple-100 rounded-lg">
                                            <TrendingUp className="text-purple-600" size={20} />
                                        </div>
                                        <h3 className="text-lg font-semibold text-gray-900">Status of Projects</h3>
                                    </div>
                                    <select
                                        value={selectedProject}
                                        onChange={(e) => setSelectedProject(e.target.value)}
                                        className="w-full sm:w-64 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    >
                                        <option value="all">All Projects (Overview)</option>
                                        {projectList.map(project => (
                                            <option key={project} value={project}>{project}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Project Summary Block */}
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

                                <div className="grid grid-cols-1 gap-6">
                                    {/* Project Status Pie Chart */}
                                    <div className="border border-gray-100 rounded-lg p-4">
                                        <h4 className="text-sm font-semibold text-gray-700 mb-4">
                                            {selectedProject === 'all' ? 'Status of Projects' : `"${selectedProject}" - Project Status`}
                                        </h4>
                                        <div className="h-64">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <PieChart>
                                                    <Pie
                                                        data={selectedProject === 'all' ? getProjectOverviewData : getTaskBreakdownData}
                                                        cx="50%"
                                                        cy="50%"
                                                        labelLine={true}
                                                        label={renderCustomLabel}
                                                        outerRadius={70}
                                                        fill="#8884d8"
                                                        dataKey="value"
                                                    >
                                                        {(selectedProject === 'all' ? getProjectOverviewData : getTaskBreakdownData).map((entry, index) => (
                                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                                        ))}
                                                    </Pie>
                                                    <Tooltip
                                                        formatter={(value, name) => [value, name]}
                                                        contentStyle={{ fontSize: '12px' }}
                                                    />
                                                </PieChart>
                                            </ResponsiveContainer>
                                        </div>
                                        {/* Legend */}
                                        <div className="flex flex-wrap justify-center gap-4 mt-4">
                                            {Object.entries(STATUS_COLORS).map(([status, color]) => (
                                                <div key={status} className="flex items-center gap-2">
                                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></div>
                                                    <span className="text-xs text-gray-600">{status}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Attendance Details */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                                    <h3 className="text-base sm:text-lg font-semibold mb-4 text-green-700">Present Users</h3>
                                    <div className="max-h-60 overflow-y-auto">
                                        <ul className="divide-y divide-gray-100">
                                            {analytics?.attendance?.present_list?.length > 0 ? (
                                                analytics.attendance.present_list.map((u, idx) => (
                                                    <li key={idx} className="py-2 flex justify-between items-center">
                                                        <span className="font-medium text-gray-800 text-sm sm:text-base truncate">{u.full_name || u.username}</span>
                                                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full capitalize flex-shrink-0 ml-2">{u.role}</span>
                                                    </li>
                                                ))
                                            ) : (
                                                <p className="text-gray-500 text-sm">No users present yet.</p>
                                            )}
                                        </ul>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                                    <h3 className="text-base sm:text-lg font-semibold mb-4 text-red-700">Absent / On Leave</h3>
                                    <div className="max-h-60 overflow-y-auto">
                                        <ul className="divide-y divide-gray-100">
                                            {analytics?.attendance?.absent_list?.length > 0 ? (
                                                analytics.attendance.absent_list.map((u, idx) => (
                                                    <li key={idx} className="py-2 flex justify-between items-center">
                                                        <span className="font-medium text-gray-800 text-sm sm:text-base truncate">{u.full_name || u.username}</span>
                                                        <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full capitalize flex-shrink-0 ml-2">{u.role}</span>
                                                    </li>
                                                ))
                                            ) : (
                                                <p className="text-gray-500 text-sm">Everyone is present!</p>
                                            )}
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            {/* Charts Row - Tasks by Priority */}
                            <div className="grid grid-cols-1 gap-4 sm:gap-6">
                                {/* Tasks by Priority */}
                                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-base sm:text-lg font-semibold">Tasks by Priority</h3>
                                        <select
                                            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                                            value={priorityFilter}
                                            onChange={(e) => setPriorityFilter(e.target.value)}
                                            id="priority-filter-dropdown"
                                        >
                                            <option value="all">All Priorities</option>
                                            <option value="high">High</option>
                                            <option value="medium">Medium</option>
                                            <option value="low">Low</option>
                                        </select>
                                    </div>

                                    <div className="mb-3 flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm">
                                        <div className="flex items-center">
                                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-red-500 rounded mr-2"></div>
                                            <span>High Priority</span>
                                        </div>
                                        <div className="flex items-center">
                                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-500 rounded mr-2"></div>
                                            <span>Medium Priority</span>
                                        </div>
                                        <div className="flex items-center">
                                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-green-500 rounded mr-2"></div>
                                            <span>Low Priority</span>
                                        </div>
                                    </div>
                                    <div className="h-56 sm:h-72">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={getPriorityTaskData()}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis
                                                    dataKey="name"
                                                    angle={-45}
                                                    textAnchor="end"
                                                    height={80}
                                                    interval={0}
                                                    tick={{ fontSize: 10 }}
                                                />
                                                <YAxis />
                                                <Tooltip
                                                    content={({ active, payload }) => {
                                                        if (active && payload && payload.length) {
                                                            const data = payload[0].payload;
                                                            return (
                                                                <div className="bg-white p-2 border border-gray-200 rounded shadow text-xs sm:text-sm">
                                                                    <p className="font-semibold">{data.name}</p>
                                                                    <p className="capitalize">Priority: {data.priority}</p>
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    }}
                                                />
                                                <Bar dataKey="value" name="Task">
                                                    {getPriorityTaskData().map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                                    ))}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                                {getProjectCompletionData().length === 0 && (
                                    <p className="text-gray-500 text-center py-4">No projects found</p>
                                )}
                            </div>
                    </div>
                    );
};

                    export default AdminDashboard;
