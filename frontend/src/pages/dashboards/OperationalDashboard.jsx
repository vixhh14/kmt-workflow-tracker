import React, { useState, useEffect } from 'react';
import {
    Plus, CheckCircle, Clock, AlertCircle, TrendingUp, ListTodo,
    Target, User, Hash, MessageSquare, Calendar, ChevronRight,
    ArrowUpCircle, ArrowDownCircle, Info, Play, Pause, Square, Filter
} from 'lucide-react';
import { getOperationalTasks, updateOperationalTask, getAssignableUsers, getProjects } from '../../api/services';
import { useAuth } from '../../context/AuthContext';

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 transition-all hover:shadow-md">
        <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm font-semibold text-gray-500 mb-1 uppercase tracking-wider">{title}</p>
                <div className="flex items-baseline space-x-2">
                    <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value}</p>
                    {subtitle && <span className="text-xs text-green-500 font-medium">{subtitle}</span>}
                </div>
            </div>
            <div className={`p-3 rounded-2xl ${color} flex-shrink-0 ml-4 shadow-sm`}>
                <Icon className="text-white" size={24} />
            </div>
        </div>
    </div>
);

const OperationalDashboard = ({ type }) => {
    const { user: currentUser } = useAuth();
    const isFileMaster = type === 'filing';
    const accentColor = isFileMaster ? 'blue' : 'orange';
    const accentBg = isFileMaster ? 'bg-blue-600' : 'bg-orange-600';
    const accentText = isFileMaster ? 'text-blue-600' : 'text-orange-600';

    const [tasks, setTasks] = useState([]);
    const [operators, setOperators] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState({
        pending: 0,
        inProgress: 0,
        completed: 0,
        totalQty: 0,
        completedQty: 0
    });
    const [projectFilter, setProjectFilter] = useState('all');
    const [projects, setProjects] = useState([]);

    // Masters can assign tasks
    const canAssign = currentUser?.role === 'admin' ||
        (type === 'filing' && (currentUser?.role === 'file_master' || currentUser?.role === 'FILE_MASTER')) ||
        (type === 'fabrication' && (currentUser?.role === 'fab_master' || currentUser?.role === 'FAB_MASTER'));

    useEffect(() => {
        fetchTasks();
        fetchProjects();
        if (canAssign) fetchOperators();
        const interval = setInterval(fetchTasks, 15000);
        return () => clearInterval(interval);
    }, [type]);

    const fetchProjects = async () => {
        try {
            const res = await getProjects();
            setProjects(res.data || []);
            setError(null);
        } catch (e) {
            console.error('Failed to fetch projects:', e);
            if (!e.response) setError('Connection Error: Could not load projects.');
        }
    };

    const fetchOperators = async () => {
        try {
            const res = await getAssignableUsers();
            setOperators(res.data.filter(u => u.role === 'operator'));
        } catch (e) {
            console.error('Failed to fetch operators:', e);
        }
    }

    const fetchTasks = async () => {
        try {
            const res = await getOperationalTasks(type);
            const data = res.data || [];

            // Admin and Masters see all tasks of the given type
            // Operators see only their assigned tasks or unassigned ones
            const canSeeAll = currentUser?.role === 'admin' ||
                (type === 'filing' && (currentUser?.role === 'file_master' || currentUser?.role === 'FILE_MASTER')) ||
                (type === 'fabrication' && (currentUser?.role === 'fab_master' || currentUser?.role === 'FAB_MASTER'));

            let filteredData = canSeeAll
                ? data
                : data.filter(t => t.assigned_to === currentUser?.user_id || t.assigned_to === null || t.assigned_to === '');

            if (projectFilter !== 'all') {
                filteredData = filteredData.filter(t => t.project_id === parseInt(projectFilter));
            }

            setTasks(filteredData);

            // Calculate stats
            const newStats = filteredData.reduce((acc, t) => {
                const status = (t.status || 'pending').toLowerCase().replace(/\s/g, '');
                acc[status] = (acc[status] || 0) + 1;
                acc.totalQty += (t.quantity || 0);
                acc.completedQty += (t.completed_quantity || 0);
                return acc;
            }, { pending: 0, inprogress: 0, completed: 0, totalQty: 0, completedQty: 0 });

            setStats({
                pending: newStats.pending || 0,
                inProgress: newStats.inprogress || 0,
                completed: newStats.completed || 0,
                totalQty: newStats.totalQty,
                completedQty: newStats.completedQty
            });
            setError(null);
        } catch (error) {
            console.error('Failed to fetch tasks:', error);
            const isNetworkError = !error.response;
            const message = isNetworkError
                ? `Connection Error: Failed to reach backend. Please check your internet or server status.`
                : (error.response?.data?.detail || "Failed to load dashboard data");
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateStatus = async (taskId, newStatus) => {
        try {
            await updateOperationalTask(type, taskId, { status: newStatus });
            fetchTasks();
        } catch (error) {
            console.error('Failed to update status:', error);
            alert(error.response?.data?.detail || 'Failed to update status');
        }
    };

    const handleAssignTask = async (taskId, userId) => {
        try {
            await updateOperationalTask(type, taskId, { assigned_to: userId });
            fetchTasks();
        } catch (error) {
            console.error('Failed to assign task:', error);
            alert(error.response?.data?.detail || 'Failed to assign task');
        }
    };

    const handleUpdateQuantity = async (task, newValue) => {
        try {
            const qty = parseInt(newValue);
            if (isNaN(qty)) return;

            const newQty = Math.max(0, Math.min(task.quantity, qty));
            if (newQty === task.completed_quantity) return;

            await updateOperationalTask(type, task.id, { completed_quantity: newQty });
            fetchTasks();
        } catch (error) {
            console.error('Failed to update quantity:', error);
            alert(error.response?.data?.detail || 'Failed to update quantity');
        }
    };

    const getPriorityColor = (p) => {
        switch (p?.toLowerCase()) {
            case 'urgent': return 'bg-red-100 text-red-700 border-red-200';
            case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
            case 'medium': return 'bg-blue-100 text-blue-700 border-blue-200';
            default: return 'bg-gray-100 text-gray-700 border-gray-200';
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className={`animate-spin rounded-full h-12 w-12 border-b-2 border-${accentColor}-600`}></div>
        </div>
    );

    return (
        <div className="space-y-6 animate-fade-in pb-10">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                        {isFileMaster ? '🟦 File Master Dashboard' : '🟧 Fab Master Dashboard'}
                    </h1>
                    <p className="text-gray-500 mt-1 font-medium">Monitoring and executing {type} operations</p>
                </div>
                <div className="flex items-center bg-white rounded-xl shadow-sm border p-1 px-3 space-x-2">
                    <div className={`w-2 h-2 rounded-full ${accentBg} animate-pulse`}></div>
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Live Updates</span>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                <StatCard
                    title="Active Tasks"
                    value={stats.pending + stats.inProgress}
                    icon={ListTodo}
                    color={isFileMaster ? 'bg-blue-500' : 'bg-orange-500'}
                />
                <StatCard
                    title="Completed"
                    value={stats.completed}
                    icon={CheckCircle}
                    color="bg-green-500"
                />
                <StatCard
                    title="Progress"
                    value={`${stats.totalQty > 0 ? Math.round((stats.completedQty / stats.totalQty) * 100) : 0}%`}
                    icon={TrendingUp}
                    color="bg-purple-500"
                    subtitle={`${stats.completedQty}/${stats.totalQty} Units`}
                />
                <StatCard
                    title="In Queue"
                    value={stats.pending}
                    icon={Clock}
                    color="bg-indigo-500"
                />
            </div>

            {error && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg flex items-center justify-between">
                    <div className="flex items-center">
                        <AlertCircle className="text-red-500 mr-3" size={20} />
                        <p className="text-sm text-red-700 font-medium">{error}</p>
                    </div>
                    <button
                        onClick={() => { setError(null); fetchTasks(); fetchProjects(); }}
                        className="text-xs bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200 font-bold"
                    >
                        RETRY
                    </button>
                </div>
            )}

            {/* Tasks Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-4 sm:p-6 border-b border-gray-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <h2 className="text-lg font-bold text-gray-900 flex items-center">
                        <ListTodo className={`mr-2 ${accentText}`} size={20} />
                        Job Queue
                    </h2>
                    <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                        <div className="relative flex-1 sm:flex-initial">
                            <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                            <select
                                value={projectFilter}
                                onChange={(e) => setProjectFilter(e.target.value)}
                                className="pl-8 pr-4 py-1.5 text-xs border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-500 w-full"
                            >
                                <option value="all">All Projects</option>
                                {projects.map(p => (
                                    <option key={p.id || p.project_id} value={p.id || p.project_id}>{p.name || p.project_name}</option>
                                ))}
                            </select>
                        </div>
                        <span className="text-xs font-bold bg-gray-50 text-gray-600 px-3 py-1.5 rounded-lg border whitespace-nowrap">
                            {tasks.length} Jobs
                        </span>
                    </div>
                </div>

                <div className="divide-y divide-gray-100">
                    {tasks.length === 0 ? (
                        <div className="p-12 text-center text-gray-400">
                            <Target size={48} className="mx-auto mb-4 opacity-20" />
                            <p className="font-medium">No tasks assigned to you yet.</p>
                        </div>
                    ) : (
                        tasks.map(task => (
                            <div key={task.id} className="p-4 sm:p-6 hover:bg-gray-50/50 transition-colors group">
                                <div className="flex flex-col lg:flex-row gap-6">
                                    {/* Task Identifiers */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex flex-wrap items-center gap-2 mb-2">
                                            <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase border ${getPriorityColor(task.priority)}`}>
                                                {task.priority || 'Medium'}
                                            </span>
                                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-100 uppercase">
                                                WO: {task.work_order_number}
                                            </span>
                                            <h3 className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                                                {task.part_item}
                                            </h3>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-2 gap-x-4">
                                            <div className="flex items-center text-sm text-gray-600">
                                                <Hash size={14} className="mr-2 text-gray-400" />
                                                <span className="font-medium">{task.project_name || 'Generic Project'}</span>
                                            </div>
                                            <div className="flex items-center text-sm text-gray-600">
                                                <Calendar size={14} className="mr-2 text-gray-400" />
                                                <span>Due: <span className="font-bold text-red-600">{task.due_date || 'ASAP'}</span></span>
                                            </div>
                                        </div>

                                        {/* Assignee / Master Actions */}
                                        <div className="mt-4 flex flex-col sm:flex-row gap-3">
                                            <div className="flex-1">
                                                <label className="text-[10px] font-bold text-gray-400 uppercase mb-1 block">Notes / Remarks</label>
                                                <input
                                                    type="text"
                                                    placeholder="Add notes..."
                                                    defaultValue={task.remarks || ''}
                                                    onBlur={(e) => {
                                                        if (e.target.value !== task.remarks) {
                                                            updateOperationalTask(type, task.id, { remarks: e.target.value })
                                                                .then(() => fetchTasks());
                                                        }
                                                    }}
                                                    className={`w-full text-xs border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-500 ${(!canAssign && task.assigned_to !== currentUser?.user_id) ? 'bg-gray-50' : ''}`}
                                                    disabled={!canAssign && task.assigned_to !== currentUser?.user_id}
                                                    readOnly={!canAssign && task.assigned_to !== currentUser?.user_id}
                                                />
                                            </div>

                                            {canAssign && (
                                                <div className="sm:w-48">
                                                    <label className="text-[10px] font-bold text-gray-400 uppercase mb-1 block">Assign To</label>
                                                    <select
                                                        value={task.assigned_to || ''}
                                                        onChange={(e) => handleAssignTask(task.id, e.target.value)}
                                                        className="w-full text-xs border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-500 py-1.5"
                                                    >
                                                        <option value="">Unassigned</option>
                                                        {operators.map(op => (
                                                            <option key={op.id || op.user_id} value={op.user_id}>
                                                                {op.full_name || op.username}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            )}

                                            {!canAssign && task.assignee_name && (
                                                <div className="sm:w-48">
                                                    <label className="text-[10px] font-bold text-gray-400 uppercase mb-1 block">Assigned To</label>
                                                    <div className="text-xs font-semibold text-gray-700 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                                        {task.assignee_name}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Task Execution / Progress */}
                                    <div className="flex flex-col sm:flex-row items-center gap-4 shrink-0 lg:w-[450px]">
                                        {/* Status Controls */}
                                        <div className="flex items-center gap-2 pr-4 border-r border-gray-100">
                                            {(task.status === 'Pending' || task.status === 'On Hold' || task.status === 'onhold') && (
                                                <button
                                                    onClick={() => handleUpdateStatus(task.id, 'In Progress')}
                                                    className="flex items-center space-x-1.5 bg-green-500 text-white px-3 py-2 rounded-lg font-bold text-xs hover:bg-green-600 transition-all shadow-sm"
                                                >
                                                    <Play size={14} fill="currentColor" />
                                                    <span>{task.status === 'Pending' ? 'START' : 'RESUME'}</span>
                                                </button>
                                            )}

                                            {(task.status === 'In Progress' || task.status === 'inprogress') && (
                                                <>
                                                    <button
                                                        onClick={() => handleUpdateStatus(task.id, 'On Hold')}
                                                        className="flex items-center space-x-1.5 bg-orange-500 text-white px-3 py-2 rounded-lg font-bold text-xs hover:bg-orange-600 transition-all shadow-sm"
                                                    >
                                                        <Pause size={14} fill="currentColor" />
                                                        <span>HOLD</span>
                                                    </button>
                                                    <button
                                                        onClick={() => handleUpdateStatus(task.id, 'Completed')}
                                                        className="flex items-center space-x-1.5 bg-blue-600 text-white px-3 py-2 rounded-lg font-bold text-xs hover:bg-blue-700 transition-all shadow-sm"
                                                    >
                                                        <Square size={14} fill="currentColor" />
                                                        <span>END</span>
                                                    </button>
                                                </>
                                            )}

                                            {task.status === 'Completed' && (
                                                <div className="flex flex-col items-center text-green-600">
                                                    <CheckCircle size={20} />
                                                    <span className="text-[10px] font-black uppercase mt-1">Done</span>
                                                </div>
                                            )}
                                        </div>

                                        <div className="w-full flex-1">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className={`text-[10px] font-black uppercase tracking-wider ${task.status === 'In Progress' ? 'text-green-600' : 'text-gray-400'}`}>
                                                    {task.status}
                                                </span>
                                                <div className="flex items-center space-x-2">
                                                    <input
                                                        type="number"
                                                        value={task.completed_quantity}
                                                        onChange={(e) => handleUpdateQuantity(task, e.target.value)}
                                                        className="w-14 text-center text-sm font-black text-gray-900 border-gray-200 rounded-lg p-1 focus:ring-1 focus:ring-blue-500"
                                                        min="0"
                                                        max={task.quantity}
                                                    />
                                                    <span className="text-gray-400 font-medium">/ {task.quantity}</span>
                                                </div>
                                            </div>
                                            <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden border border-gray-100 shadow-inner">
                                                <div
                                                    className={`h-full transition-all duration-500 ease-out shadow-sm ${accentBg}`}
                                                    style={{ width: `${(task.completed_quantity / task.quantity) * 100}%` }}
                                                />
                                            </div>
                                            {task.completed_at && (
                                                <p className="text-[9px] text-gray-400 mt-1 font-medium italic">
                                                    Finished: {new Date(task.completed_at).toLocaleString()}
                                                </p>
                                            )}
                                            {task.total_active_duration > 0 && (
                                                <p className="text-[10px] text-gray-500 mt-1 font-bold">
                                                    ⏱ Active Time: {Math.floor(task.total_active_duration / 3600)}h {Math.floor((task.total_active_duration % 3600) / 60)}m {task.total_active_duration % 60}s
                                                </p>
                                            )}
                                        </div>

                                        <div className="flex flex-col items-center justify-center gap-1 min-w-[60px]">
                                            <button
                                                onClick={() => handleUpdateQuantity(task, task.completed_quantity + 1)}
                                                disabled={task.completed_quantity >= task.quantity}
                                                className={`p-1.5 rounded-lg ${accentBg} text-white shadow-sm hover:scale-110 active:scale-90 transition-all disabled:opacity-30`}
                                            >
                                                <ArrowUpCircle size={18} />
                                            </button>
                                            <button
                                                onClick={() => handleUpdateQuantity(task, task.completed_quantity - 1)}
                                                disabled={task.completed_quantity === 0}
                                                className="p-1.5 rounded-lg border border-gray-200 text-gray-500 hover:text-red-500 transition-all bg-white disabled:opacity-30"
                                            >
                                                <ArrowDownCircle size={18} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default OperationalDashboard;
