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
    const [createFormData, setCreateFormData] = useState({
        project_id: '',
        work_order_number: '',
        part_item: '',
        quantity: 1,
        due_date: '',
        due_time: '11:00',
        priority: 'medium',
        remarks: ''
    });
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const canCreate = currentUser?.role === 'admin' || currentUser?.role === 'planning';
    const [projectFilter, setProjectFilter] = useState('all');
    const [projects, setProjects] = useState([]);

    // Masters can assign tasks
    const canAssign = currentUser?.role === 'admin' ||
        (type === 'filing' && (currentUser?.role === 'file_master' || currentUser?.role === 'FILE_MASTER')) ||
        (type === 'fabrication' && (currentUser?.role === 'fab_master' || currentUser?.role === 'FAB_MASTER'));

    useEffect(() => {
        let isMounted = true;
        let timeoutId = null;
        let consecutiveErrors = 0;

        fetchProjects();
        if (canAssign) fetchOperators();

        const pollTasks = async () => {
            if (!isMounted) return;
            if (document.hidden) {
                // If tab hidden, wait longer (30s)
                timeoutId = setTimeout(pollTasks, 30000);
                return;
            }

            try {
                await fetchTasks();
                consecutiveErrors = 0; // Reset on success
                timeoutId = setTimeout(pollTasks, 15000); // 15s normal poll
            } catch (err) {
                consecutiveErrors++;
                const backoff = Math.min(60000, 15000 * Math.pow(1.5, consecutiveErrors));
                console.warn(`Polling failed (${consecutiveErrors}). Retrying in ${Math.round(backoff / 1000)}s...`);
                timeoutId = setTimeout(pollTasks, backoff);
            }
        };

        pollTasks();

        return () => {
            isMounted = false;
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [type]);

    const fetchProjects = async () => {
        try {
            const res = await getProjects();
            setProjects(res.data || []);
            setError(null);
        } catch (e) {
            console.error('Failed to fetch projects:', e);
            const data = e.response?.data;
            const msg = data?.message || data?.detail || 'Failed to load projects.';
            setError(msg);
        }
    };

    const formatDueDateTime = (dtStr) => {
        if (!dtStr) return 'Not set';
        try {
            const date = new Date(dtStr);
            if (isNaN(date.getTime())) return dtStr;
            const options = {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit', hour12: true
            };
            return date.toLocaleString('en-GB', options).replace(',', ' •').toUpperCase();
        } catch (e) { return dtStr; }
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
                filteredData = filteredData.filter(t => String(t.project_id) === String(projectFilter));
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

    const handleCreateTask = async (e) => {
        e.preventDefault();
        try {
            setSubmitting(true);
            const combinedDueDateTime = createFormData.due_date && createFormData.due_time
                ? `${createFormData.due_date}T${createFormData.due_time}:00`
                : createFormData.due_date;

            const payload = {
                project_id: createFormData.project_id,
                work_order_number: createFormData.work_order_number,
                part_item: createFormData.part_item,
                quantity: parseInt(createFormData.quantity),
                due_date: combinedDueDateTime,
                priority: createFormData.priority,
                remarks: createFormData.remarks
            };

            await import('../../api/services').then(mod => mod.createOperationalTask(type, payload));

            setCreateFormData({
                project_id: '',
                work_order_number: '',
                part_item: '',
                quantity: 1,
                due_date: '',
                due_time: '11:00',
                priority: 'medium',
                remarks: ''
            });
            setShowCreateForm(false);
            fetchTasks(); // Refresh tasks
            alert('Task created successfully!');
        } catch (error) {
            console.error('Failed to create task:', error);
            alert(error.response?.data?.detail || 'Failed to create task');
        } finally {
            setSubmitting(false);
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
        const priority = p?.toLowerCase();
        switch (priority) {
            case 'urgent': return 'bg-red-500 text-white shadow-sm ring-1 ring-red-600/20';
            case 'high': return 'bg-orange-500 text-white shadow-sm ring-1 ring-orange-600/20';
            case 'medium': return 'bg-blue-500 text-white shadow-sm ring-1 ring-blue-600/20';
            case 'low': return 'bg-green-500 text-white shadow-sm ring-1 ring-green-600/20';
            default: return 'bg-gray-500 text-white shadow-sm ring-1 ring-gray-600/20';
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
                <div className="flex items-center gap-3">
                    <div className="flex items-center bg-white rounded-xl shadow-sm border p-1 px-3 space-x-2">
                        <div className={`w-2 h-2 rounded-full ${accentBg} animate-pulse`}></div>
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Live Updates</span>
                    </div>
                    {canCreate && (
                        <button
                            onClick={() => setShowCreateForm(!showCreateForm)}
                            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-white font-bold shadow-md transition-all hover:shadow-lg active:scale-95 ${accentBg}`}
                        >
                            <Plus size={18} />
                            <span>Add Task</span>
                        </button>
                    )}
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

            {/* Create Task Form */}
            {showCreateForm && (
                <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6 animate-fade-in mb-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 border-b pb-2">Create New Operational Task</h3>
                    <form onSubmit={handleCreateTask} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* 1. Project */}
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Project *</label>
                            <select
                                required
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                value={createFormData.project_id}
                                onChange={e => setCreateFormData({ ...createFormData, project_id: e.target.value })}
                            >
                                <option value="" disabled hidden>-- Select Project --</option>
                                {projects.map(p => (
                                    <option key={p.id || p.project_id} value={p.id || p.project_id}>{p.name || p.project_name}</option>
                                ))}
                            </select>
                        </div>

                        {/* 2. Work Order Number */}
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Work Order Number *</label>
                            <input
                                required
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                value={createFormData.work_order_number}
                                onChange={e => setCreateFormData({ ...createFormData, work_order_number: e.target.value })}
                            />
                        </div>

                        {/* 3. Part / Item */}
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Part / Item Name *</label>
                            <input
                                required
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                value={createFormData.part_item}
                                onChange={e => setCreateFormData({ ...createFormData, part_item: e.target.value })}
                            />
                        </div>

                        {/* 4. Quantity */}
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Quantity *</label>
                            <input
                                required
                                type="number"
                                min="1"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                value={createFormData.quantity}
                                onChange={e => setCreateFormData({ ...createFormData, quantity: e.target.value })}
                            />
                        </div>

                        {/* 5. Due Date & Time */}
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Due Date *</label>
                                <input
                                    required
                                    type="date"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                    value={createFormData.due_date}
                                    onChange={e => setCreateFormData({ ...createFormData, due_date: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Due Time *</label>
                                <input
                                    required
                                    type="time"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                    value={createFormData.due_time}
                                    onChange={e => setCreateFormData({ ...createFormData, due_time: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* 6. Priority */}
                        <div>
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Priority *</label>
                            <select
                                required
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                value={createFormData.priority}
                                onChange={e => setCreateFormData({ ...createFormData, priority: e.target.value })}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="urgent">Urgent</option>
                            </select>
                        </div>

                        {/* 7. Remarks */}
                        <div className="md:col-span-2">
                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Remarks</label>
                            <textarea
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                                rows="2"
                                value={createFormData.remarks}
                                onChange={e => setCreateFormData({ ...createFormData, remarks: e.target.value })}
                            />
                        </div>

                        <div className="md:col-span-2 flex justify-end space-x-3">
                            <button
                                type="button"
                                onClick={() => setShowCreateForm(false)}
                                className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={submitting}
                                className={`px-6 py-2 text-white font-bold rounded-lg shadow transition hover:opacity-90 ${accentBg}`}
                            >
                                {submitting ? 'Creating...' : 'Create Task'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

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
                            <div key={task.id} className="p-5 hover:bg-gray-50/50 transition-all border-b border-gray-100 last:border-0">
                                <div className="flex flex-col lg:flex-row lg:items-center gap-6">
                                    {/* 1. Primary Info: Title, Priority, WO */}
                                    <div className="lg:w-1/3">
                                        <div className="flex flex-wrap items-center gap-3 mb-2">
                                            <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${getPriorityColor(task.priority)}`}>
                                                {task.priority || 'MEDIUM'}
                                            </span>
                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-100 uppercase tracking-wider">
                                                WO: {task.work_order_number || '00'}
                                            </span>
                                            <h3 className="text-lg font-bold text-gray-900 tracking-tight">
                                                {task.part_item}
                                            </h3>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-x-6 gap-y-1">
                                            <div className="flex items-center text-xs text-gray-400 font-bold">
                                                <Hash size={12} className="mr-1.5 opacity-40" />
                                                <span>{task.machine_name || task.machine_id || 'HANDWORK'}</span>
                                            </div>
                                            <div className="flex items-center text-xs text-gray-400 font-bold">
                                                <Calendar size={12} className="mr-1.5 opacity-40" />
                                                <span>DUE: <span className="text-red-500">{formatDueDateTime(task.due_date).split(' •')[0]}</span></span>
                                            </div>
                                        </div>
                                        {task.remarks && (
                                            <div className="mt-2 flex items-start text-[10px] text-gray-400 font-bold uppercase tracking-tight">
                                                <MessageSquare size={10} className="mr-1.5 mt-0.5 opacity-40" />
                                                <span className="truncate max-w-xs">{task.remarks}</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* 2. Assignment */}
                                    <div className="lg:w-1/6 min-w-[120px]">
                                        <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-1.5 leading-none">Assign To (Manual)</p>
                                        {canAssign ? (
                                            <input
                                                type="text"
                                                defaultValue={task.assignee_name || task.assigned_to || ''}
                                                onBlur={(e) => {
                                                    const val = e.target.value;
                                                    if (val !== (task.assignee_name || task.assigned_to)) {
                                                        handleAssignTask(task.id, val);
                                                    }
                                                }}
                                                className="w-full text-sm font-bold text-gray-800 bg-transparent border-none p-0 focus:ring-0 placeholder:text-gray-300"
                                                placeholder="Enter Name"
                                            />
                                        ) : (
                                            <p className="text-sm font-bold text-gray-700 leading-none">{task.assignee_name || task.assigned_to || 'Unassigned'}</p>
                                        )}
                                    </div>

                                    {/* 3. Action Buttons (HOLD / END) */}
                                    <div className="flex items-center gap-3 lg:w-1/5 shrink-0">
                                        {(task.status?.toLowerCase() === 'pending' || task.status?.toLowerCase() === 'on hold' || task.status?.toLowerCase() === 'onhold') && (
                                            <button
                                                onClick={() => handleUpdateStatus(task.id, 'In Progress')}
                                                className="flex-1 flex items-center justify-center space-x-2 bg-green-600 text-white px-5 py-2.5 rounded-lg font-black text-xs hover:bg-green-700 transition-all shadow-sm active:scale-95 uppercase tracking-wider"
                                            >
                                                <Play size={14} fill="currentColor" />
                                                <span>{task.status?.toLowerCase() === 'pending' ? 'START' : 'RESUME'}</span>
                                            </button>
                                        )}

                                        {(task.status?.toLowerCase() === 'in progress' || task.status?.toLowerCase() === 'inprogress') && (
                                            <>
                                                <button
                                                    onClick={() => handleUpdateStatus(task.id, 'On Hold')}
                                                    className="flex-1 flex items-center justify-center space-x-2 bg-[#b45309] text-white px-5 py-2.5 rounded-lg font-black text-xs hover:bg-[#92400e] transition-all shadow-sm active:scale-95 uppercase tracking-wider"
                                                >
                                                    <Pause size={14} fill="currentColor" />
                                                    <span>HOLD</span>
                                                </button>
                                                <button
                                                    onClick={() => handleUpdateStatus(task.id, 'Completed')}
                                                    className="flex-1 flex items-center justify-center space-x-2 bg-[#0369a1] text-white px-5 py-2.5 rounded-lg font-black text-xs hover:bg-[#075985] transition-all shadow-sm active:scale-95 uppercase tracking-wider"
                                                >
                                                    <Square size={14} fill="currentColor" />
                                                    <span>END</span>
                                                </button>
                                            </>
                                        )}

                                        {task.status?.toLowerCase() === 'completed' && (
                                            <div className="flex-1 flex items-center justify-center space-x-2 bg-green-50 text-green-700 border border-green-100 px-5 py-2.5 rounded-lg font-black text-xs uppercase tracking-wider">
                                                <CheckCircle size={14} />
                                                <span>FINISHED</span>
                                            </div>
                                        )}
                                    </div>

                                    {/* 4. Progress Tracking */}
                                    <div className="lg:flex-1 flex items-center gap-6">
                                        <div className="flex-1">
                                            <div className="flex justify-between items-end mb-2">
                                                <span className={`text-[11px] font-black uppercase tracking-[0.2em] ${task.status?.toLowerCase() === 'in progress' ? 'text-green-600' : 'text-gray-400'}`}>
                                                    {task.status === 'InProgress' ? 'IN PROGRESS' : task.status}
                                                </span>
                                                <div className="flex items-baseline gap-2">
                                                    <span className="text-base font-black text-gray-900 leading-none">{task.completed_quantity}</span>
                                                    <span className="text-xs text-gray-400 font-bold leading-none">/ {task.quantity}</span>
                                                </div>
                                            </div>
                                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden shadow-inner border border-gray-100">
                                                <div
                                                    className={`h-full transition-all duration-1000 cubic-bezier(0.4, 0, 0.2, 1) ${accentBg}`}
                                                    style={{ width: `${(task.completed_quantity / task.quantity) * 100}%` }}
                                                />
                                            </div>
                                        </div>

                                        {/* Precision Controls */}
                                        <div className="flex flex-col gap-1.5 shrink-0">
                                            <button
                                                onClick={() => handleUpdateQuantity(task, task.completed_quantity + 1)}
                                                disabled={task.completed_quantity >= task.quantity}
                                                className={`p-1.5 rounded-lg ${accentBg} text-white hover:scale-110 active:scale-90 transition-all shadow-sm disabled:opacity-20`}
                                            >
                                                <ArrowUpCircle size={20} />
                                            </button>
                                            <button
                                                onClick={() => handleUpdateQuantity(task, task.completed_quantity - 1)}
                                                disabled={task.completed_quantity <= 0}
                                                className="p-1.5 rounded-lg bg-white border border-gray-200 text-gray-300 hover:text-red-500 hover:border-red-200 transition-all disabled:opacity-20"
                                            >
                                                <ArrowDownCircle size={20} />
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
