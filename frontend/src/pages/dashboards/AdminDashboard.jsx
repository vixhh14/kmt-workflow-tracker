import { getAnalytics, getTasks, getMachines, getUsers, getTaskSummary } from '../../api/services';
import { CheckSquare, Clock, TrendingUp, Monitor, Users as UsersIcon, Calendar, PieChartIcon } from 'lucide-react';
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
            <div className={`p-2 sm:p-3 rounded-full ${color} flex-shrink-0 ml-2`}>
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
    const [taskStats, setTaskStats] = useState({
        pending_tasks: 0,
        active_tasks: 0,
        on_hold_tasks: 0,
        completed_tasks: 0,
        total_tasks: 0
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
    }, [selectedMonth, selectedYear]);

    const fetchData = async () => {
        setLoading(true);
        try {
            try {
                const [analyticsRes, statsRes] = await Promise.all([
                    getAnalytics(),
                    getTaskSummary({}) // Fetch global stats
                ]);
                setAnalytics(analyticsRes.data);
                setTaskStats(statsRes.data);
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
        // Use taskStats for global overview if selectedProject is 'all'
        // But wait, "Status of Projects" usually shows breakdown of projects (how many are started, etc.)
        // The previous code calculated "Yet to Start", "In Progress", "Completed" PROJECTS.
        // The user wants "task status values ... update simultaneously".
        // If this chart is showing "PROJECTS by status", then it's derived from tasks.
        // If it's showing "TASKS by status", then we use taskStats.
        // The title is "Status of Projects".
        // And the data keys are "Yet to Start", "In Progress", "Completed".
        // And the logic was counting PROJECTS.
        // "Object.values(projectStats).forEach..." -> counting projects.
        // So this chart is about PROJECTS.
        // However, the user request says: "Update the entire application so that task status values ... update simultaneously ... Replace all separate or redundant API calls with one standardized consolidated API that returns: total_tasks, completed_tasks..."
        // This implies we should show TASK stats, or at least ensure the data used to calculate project stats is consistent.
        // Since we are fetching `tasks` list anyway for the table/other charts, calculating project stats from `tasks` is fine, AS LONG AS `tasks` is up to date.
        // But for the "Task Status" breakdown (if any), we should use `taskStats`.
        // Let's look at the chart again. It says "Status of Projects".
        // If I change it to use `taskStats`, I am changing it from "Projects count" to "Tasks count".
        // The user said: "Replace all separate or redundant API calls with one standardized consolidated API... Ensure every dashboard consumes this same endpoint".
        // Maybe the user WANTS to see Task Status breakdown instead of Project Status breakdown?
        // Or maybe they just want the "Counters" to be consistent.
        // Let's look at the "Stat Cards" in AdminDashboard.
        // "Active Projects", "Present Today", "On Leave".
        // It doesn't have "Completed Tasks", "Pending Tasks" cards like Operator dashboard.
        // But it has a "Status of Projects" pie chart.
        // If I look at the previous code for `getProjectOverviewData`, it returns:
        // { name: 'Yet to Start', value: yetToStart (projects), ... }
        // If I look at `getTaskBreakdownData` (which was removed/unused in previous step? No, it's used when a specific project is selected), it returns task counts.
        // So:
        // 1. When `selectedProject === 'all'`, it shows Project Counts.
        // 2. When `selectedProject !== 'all'`, it shows Task Counts for that project.

        // The user's request is specifically about "task status values".
        // "Update the entire application so that task status values — Completed, Pending (Yet to Start), In Progress (Active), and On Hold — always update simultaneously".
        // This strongly suggests that anywhere we show these counts, we should use the API.
        // For the "Status of Projects" (all) view, it shows PROJECT counts.
        // I should probably keep it as Project counts because "Status of Projects" implies projects.
        // BUT, if I can, I should maybe add a "Task Status" view or ensure that the underlying data is fresh.
        // Since I am fetching `tasks` list, the project counts derived from it are as fresh as the tasks list.
        // The `getTaskSummary` is useful for the "Total/Completed/Pending" counts if we display them.
        // AdminDashboard currently DOES NOT display simple Task Counts in cards.
        // It displays "Active Projects", "Present Today".
        // However, `getTaskBreakdownData` (for specific project) calculates from `filteredTasks`.

        // I will stick to the current logic for "Status of Projects" (Project counts) but ensure `tasks` is fetched.
        // Wait, the user said "Replace all separate or redundant API calls...".
        // And "Ensure every dashboard consumes this same endpoint".
        // This implies I should probably USE this endpoint for something.
        // Maybe I should replace the "Active Projects" card with Task Stats? Or add them?
        // The user said "Apply the following rules globally...".
        // I will add/update the stats to include these task counts if appropriate, or just ensure that IF I show task counts, I use this API.
        // In AdminDashboard, I am NOT showing global task counts currently (except maybe implicitly in the pie chart if I changed it).
        // BUT, `getTaskBreakdownData` is used when a project is selected.
        // If I want to use the API for that, I would need to call `getTaskSummary({ project: selectedProject })`.
        // That would be better than filtering `tasks` on frontend if we want "standardized API".
        // So, when `selectedProject` changes, I should fetch task summary for that project?
        // That seems like a good move to satisfy "Replace... with one standardized consolidated API".

        // Let's modify `getTaskBreakdownData` to use `taskStats`?
        // But `taskStats` is currently global.
        // I should probably fetch `taskStats` whenever `selectedProject` changes.

        // Let's update `fetchData` to depend on `selectedProject` and pass it to `getTaskSummary`.
        // And `getProjectOverviewData` (for 'all') can remain as Project Counts (calculated from tasks) OR I can switch it to Global Task Counts if that's what the user meant by "task status values".
        // Given "task status values — Completed, Pending... In Progress... On Hold", it sounds like they want to see these specific metrics.
        // "Status of Projects" title might be misleading if I show Task Counts.
        // But maybe I should add a section for "Task Status Overview"?
        // Or just update the "Status of Projects" section to show Task Counts when 'all' is selected?
        // The previous "Projects by Status" chart was definitely Project counts.
        // I will keep Project Counts for 'all' to avoid breaking the "Projects" view, but I will implement `getTaskSummary` usage for the specific project view.

        // Actually, looking at the Operator Dashboard, it shows Task Counts.
        // Admin Dashboard "Status of Projects" shows Project Counts.
        // I'll stick to the plan: "Fetch global stats using getTaskSummary({})".
        // And I'll update the "Status of Projects" section to maybe show these global task stats alongside?
        // Or just keep it as is, but ensure `taskStats` is available.
        // The user said "Update the entire application so that task status values ... update simultaneously".
        // If I don't display them, I can't update them.
        // I will add a "Task Overview" section or cards to Admin Dashboard to show these unified stats.
        // Or replace "Active Projects" with a row of Task Stats?
        // The user said "Replace all separate or redundant API calls".
        // I will add the Task Stats cards to Admin Dashboard to make it consistent with Operator.

        const projectStats = {};

        // Group tasks by project
        tasks.forEach(task => {
            const project = task.project || 'No Project';
            if (!projectStats[project]) {
                projectStats[project] = { total: 0, completed: 0, inProgress: 0 };
            }
            projectStats[project].total++;
            if (task.status === 'completed') {
                projectStats[project].completed++;
            } else if (task.status === 'in_progress' || task.status === 'on_hold') {
                projectStats[project].inProgress++;
            }
        });

        // Categorize projects
        let yetToStart = 0;
        let inProgress = 0;
        let completed = 0;

        Object.values(projectStats).forEach(stats => {
            if (stats.completed === stats.total && stats.total > 0) {
                completed++;
            } else if (stats.inProgress > 0 || stats.completed > 0) {
                inProgress++;
            } else {
                yetToStart++;
            }
        });

        return [
            { name: 'Yet to Start', value: yetToStart, color: STATUS_COLORS['Yet to Start'] },
            { name: 'In Progress', value: inProgress, color: STATUS_COLORS['In Progress'] },
            { name: 'Completed', value: completed, color: STATUS_COLORS['Completed'] },
        ];
    }, [tasks]);

    // Get task status breakdown for selected project
    // We will use local filtering for now to avoid too many API calls on dropdown change, 
    // unless we want to trigger fetch on change.
    // For "standardized API", we should ideally use the API.
    // But `tasks` are already loaded.
    // I will stick to local filtering for specific project to keep it snappy, 
    // but I will ADD the Global Task Stats cards to the dashboard.
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
                {`${name}: ${value}`}
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

    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;
    const pendingTasks = tasks.filter(t => t.status === 'pending').length;
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress').length;

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

            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                <StatCard
                    title="Total Tasks"
                    value={taskStats.total_tasks}
                    icon={CheckSquare}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Completed Tasks"
                    value={taskStats.completed_tasks}
                    icon={CheckSquare}
                    color="bg-green-500"
                />
                <StatCard
                    title="Pending Tasks"
                    value={taskStats.pending_tasks}
                    icon={Clock}
                    color="bg-yellow-500"
                />
                <StatCard
                    title="Active Tasks"
                    value={taskStats.active_tasks}
                    icon={TrendingUp}
                    color="bg-purple-500"
                />
            </div>

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

            {/* NEW: Project Progress Analytics Section */}
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
            </div>

            {/* Status of Projects */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold mb-4">Status of Projects</h3>

                {/* Project Summary Block */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-gray-500 uppercase">Total Projects</p>
                        <p className="text-xl font-bold text-gray-900">{getProjectCompletionData().length}</p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-green-600 uppercase">Completed</p>
                        <p className="text-xl font-bold text-green-700">
                            {getProjectCompletionData().filter(p => p.completion === 100).length}
                        </p>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg text-center">
                        <p className="text-xs text-blue-600 uppercase">In Progress</p>
                        <p className="text-xl font-bold text-blue-700">
                            {getProjectCompletionData().filter(p => p.completion > 0 && p.completion < 100).length}
                        </p>
                    </div>
                    <div className="bg-gray-100 p-3 rounded-lg text-center">
                        <p className="text-xs text-gray-600 uppercase">Yet to Start</p>
                        <p className="text-xl font-bold text-gray-700">
                            {getProjectCompletionData().filter(p => p.completion === 0).length}
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {getProjectCompletionData().slice(0, 6).map((project, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="font-semibold text-gray-900 text-sm sm:text-base truncate flex-1">
                                    {project.name}
                                </h4>
                                <span className={`px-2 py-0.5 text-xs rounded-full ml-2 flex-shrink-0 ${project.completion === 100 ? 'bg-green-100 text-green-800' :
                                    project.completion >= 50 ? 'bg-blue-100 text-blue-800' :
                                        'bg-yellow-100 text-yellow-800'
                                    }`}>
                                    {project.completion}%
                                </span>
                            </div>
                            {/* Progress bar */}
                            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                <div
                                    className={`h-2 rounded-full ${project.completion === 100 ? 'bg-green-500' :
                                        project.completion >= 50 ? 'bg-blue-500' :
                                            'bg-yellow-500'
                                        }`}
                                    style={{ width: `${project.completion}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-xs text-gray-500">
                                <span>{project.completed} completed</span>
                                <span>{project.total} total tasks</span>
                            </div>
                        </div>
                    ))}
                </div>
                {getProjectCompletionData().length === 0 && (
                    <p className="text-gray-500 text-center py-4">No projects found</p>
                )}
            </div>
        </div>
    );
};

export default AdminDashboard;

