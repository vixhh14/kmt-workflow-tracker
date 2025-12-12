import React, { useState, useEffect } from 'react';
import { getTasks, getUsers, updateTask, getAnalytics, getTaskSummary } from '../../api/services';
import { Users, CheckSquare, TrendingUp, AlertTriangle, Briefcase, UserPlus, Monitor, Clock, Pause, Folder } from 'lucide-react';
import {
    BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
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

const SupervisorDashboard = () => {
    const [tasks, setTasks] = useState([]);
    const [users, setUsers] = useState([]);
    const [analytics, setAnalytics] = useState(null);
    const [projectStats, setProjectStats] = useState({
        total: 0,
        completed: 0,
        in_progress: 0,
        yet_to_start: 0,
        held: 0
    });
    const [loading, setLoading] = useState(true);
    const [selectedOperator, setSelectedOperator] = useState('all');

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // Real-time updates
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            // setLoading(true); // Don't show loading on refresh
            const [tasksRes, usersRes, analyticsRes, statsRes] = await Promise.all([
                getTasks(),
                getUsers(),
                getAnalytics(),
                getTaskSummary({})
            ]);
            setTasks(tasksRes.data);
            setUsers(usersRes.data.filter(u => u.role === 'operator').sort((a, b) => a.username.localeCompare(b.username)));
            setAnalytics(analyticsRes.data);

            if (statsRes.data.project_stats) {
                setProjectStats(statsRes.data.project_stats);
            }
            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch data:', error);
            setLoading(false);
        }
    };

    const filteredTasks = selectedOperator === 'all'
        ? tasks
        : tasks.filter(t => t.assigned_to === selectedOperator);

    const getOperatorStatus = () => {
        const operatorsToShow = selectedOperator === 'all'
            ? users
            : users.filter(u => u.user_id === selectedOperator);

        return operatorsToShow.map(user => {
            const userTasks = tasks.filter(t => t.assigned_to === user.user_id);
            const completed = userTasks.filter(t => t.status === 'completed').length;
            const inProgress = userTasks.filter(t => t.status === 'in_progress').length;
            const pending = userTasks.filter(t => t.status === 'pending').length;
            const onHold = userTasks.filter(t => t.status === 'on_hold').length;

            return {
                name: user.username.length > 10 ? user.username.substring(0, 10) + '...' : user.username,
                completed,
                inProgress,
                pending,
                onHold,
                total: userTasks.length
            };
        }).sort((a, b) => b.total - a.total);
    };

    const getPriorityTaskStatus = () => {
        const taskPriorities = filteredTasks.slice(0, 10).map(task => ({
            name: task.title.length > 15 ? task.title.substring(0, 15) + '...' : task.title,
            priority: task.priority,
            value: 1
        }));

        return taskPriorities;
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return '#ef4444';
            case 'medium': return '#eab308';
            case 'low': return '#22c55e';
            default: return '#6b7280';
        }
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    return (
        <div className="space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Supervisor Dashboard</h1>
                    <p className="text-sm sm:text-base text-gray-600">Team oversight and task management</p>
                </div>

                {/* Operator Filter Dropdown */}
                <div className="flex items-center gap-2">
                    <label className="text-xs sm:text-sm font-medium text-gray-700 whitespace-nowrap">Filter:</label>
                    <select
                        value={selectedOperator}
                        onChange={(e) => setSelectedOperator(e.target.value)}
                        className="block w-full sm:w-40 pl-2 sm:pl-3 pr-8 py-2 text-sm border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                    >
                        <option value="all">All Operators</option>
                        {users.map(user => (
                            <option key={user.user_id} value={user.user_id}>
                                {user.username}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Stats Cards - Updated to Project Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
                <StatCard
                    title="Total Projects"
                    value={projectStats.total}
                    icon={Folder}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Completed Projects"
                    value={projectStats.completed}
                    icon={CheckSquare}
                    color="bg-green-500"
                />
                <StatCard
                    title="Pending Projects"
                    value={projectStats.yet_to_start}
                    icon={Clock}
                    color="bg-yellow-500"
                />
                <StatCard
                    title="Active Projects"
                    value={projectStats.in_progress}
                    icon={TrendingUp}
                    color="bg-purple-500"
                />
            </div>

            {/* Quick Assign - Pending Tasks */}
            <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold mb-4 flex items-center">
                    <UserPlus className="mr-2 flex-shrink-0" size={20} />
                    <span className="truncate">Quick Assign - Pending Tasks</span>
                </h3>
                <div className="space-y-3">
                    {tasks.filter(t => t.status === 'pending' || !t.assigned_to).slice(0, 5).map((task) => (
                        <div key={task.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 bg-gray-50 rounded-lg gap-3">
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-gray-900 text-sm sm:text-base truncate">{task.title}</p>
                                <div className="flex flex-wrap items-center gap-2 mt-1">
                                    {task.project && (
                                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded truncate max-w-[100px]">
                                            {task.project}
                                        </span>
                                    )}
                                    <span className={`text-xs px-2 py-0.5 rounded ${task.priority === 'high' ? 'bg-red-100 text-red-800' :
                                        task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                            'bg-green-100 text-green-800'
                                        }`}>
                                        {task.priority}
                                    </span>
                                </div>
                            </div>
                            <div className="flex-shrink-0">
                                <select
                                    onChange={async (e) => {
                                        if (e.target.value) {
                                            try {
                                                await updateTask(task.id, { assigned_to: e.target.value, status: 'pending' });
                                                fetchData();
                                            } catch (error) {
                                                console.error('Failed to assign task:', error);
                                                alert('Failed to assign task');
                                            }
                                        }
                                    }}
                                    className="w-full sm:w-auto px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Assign to...</option>
                                    {users.map(user => (
                                        <option key={user.user_id} value={user.user_id}>
                                            {user.username}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    ))}
                    {tasks.filter(t => t.status === 'pending' || !t.assigned_to).length === 0 && (
                        <p className="text-gray-500 text-sm">No pending tasks to assign</p>
                    )}
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                {/* Operator-wise Status */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-2">Operator-wise Task Status</h3>
                    <p className="text-xs sm:text-sm text-gray-600 mb-4">Track each operator's work progress</p>
                    <div className="h-64 sm:h-80">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={getOperatorStatus()}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                                <YAxis />
                                <Tooltip />
                                <Legend wrapperStyle={{ fontSize: '12px' }} />
                                <Bar dataKey="completed" stackId="a" fill="#10b981" name="Completed" />
                                <Bar dataKey="inProgress" stackId="a" fill="#3b82f6" name="In Progress" />
                                <Bar dataKey="pending" stackId="a" fill="#f59e0b" name="Pending" />
                                <Bar dataKey="onHold" stackId="a" fill="#ef4444" name="On Hold" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Priority Task Status */}
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4">Priority Task Status</h3>
                    <div className="mb-3 flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm">
                        <div className="flex items-center">
                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-red-500 rounded mr-2"></div>
                            <span>High</span>
                        </div>
                        <div className="flex items-center">
                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-yellow-500 rounded mr-2"></div>
                            <span>Medium</span>
                        </div>
                        <div className="flex items-center">
                            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-green-500 rounded mr-2"></div>
                            <span>Low</span>
                        </div>
                    </div>
                    <div className="h-52 sm:h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={getPriorityTaskStatus()}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 10 }} />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="value" name="Task">
                                    {getPriorityTaskStatus().map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={getPriorityColor(entry.priority)} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Team Overview and Recent Tasks */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4 flex items-center">
                        <Users className="mr-2 flex-shrink-0" size={20} />
                        Team Members
                    </h3>
                    <div className="space-y-3 max-h-80 overflow-y-auto">
                        {users.map((user) => {
                            const userTasks = tasks.filter(t => t.assigned_to === user.user_id);
                            const userCompleted = userTasks.filter(t => t.status === 'completed').length;
                            const userInProgress = userTasks.filter(t => t.status === 'in_progress').length;
                            const userPending = userTasks.filter(t => t.status === 'pending').length;
                            return (
                                <div key={user.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <div className="min-w-0 flex-1">
                                        <p className="font-medium text-gray-900 text-sm sm:text-base truncate">{user.username}</p>
                                        <p className="text-xs sm:text-sm text-gray-500 truncate">{user.full_name}</p>
                                    </div>
                                    <div className="text-right flex-shrink-0 ml-2">
                                        <p className="text-xs sm:text-sm font-semibold text-gray-900">{userTasks.length} tasks</p>
                                        <div className="flex flex-wrap justify-end gap-1 text-xs mt-1">
                                            <span className="text-green-600">{userCompleted} done</span>
                                            <span className="text-blue-600">{userInProgress} active</span>
                                            <span className="text-yellow-600">{userPending} pending</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                        {users.length === 0 && (
                            <p className="text-gray-500 text-sm">No operators found</p>
                        )}
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold mb-4">Recent Tasks</h3>
                    <div className="space-y-3 max-h-80 overflow-y-auto">
                        {tasks.slice(0, 5).map((task) => (
                            <div key={task.id} className="p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-start justify-between gap-2 mb-2">
                                    <p className="font-medium text-gray-900 text-sm sm:text-base truncate flex-1">{task.title}</p>
                                    <span className={`px-2 py-0.5 text-xs rounded-full flex-shrink-0 ${task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                        task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                            task.status === 'on_hold' ? 'bg-red-100 text-red-800' :
                                                'bg-yellow-100 text-yellow-800'
                                        }`}>
                                        {task.status.replace('_', ' ')}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between text-xs sm:text-sm text-gray-500">
                                    <span className="truncate">{users.find(u => u.user_id === task.assigned_to)?.username || 'Unassigned'}</span>
                                    <span className={`px-2 py-0.5 text-xs rounded-full flex-shrink-0 ml-2 ${task.priority === 'high' ? 'bg-red-100 text-red-800' :
                                        task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                            'bg-green-100 text-green-800'
                                        }`}>
                                        {task.priority}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {tasks.length === 0 && (
                            <p className="text-gray-500 text-sm">No recent tasks</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SupervisorDashboard;
