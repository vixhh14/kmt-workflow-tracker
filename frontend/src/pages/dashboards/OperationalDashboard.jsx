import React, { useState, useEffect } from 'react';
import { getOperationalTasks, updateOperationalTask } from '../../api/services';
import {
    Plus, CheckCircle, Clock, AlertCircle, TrendingUp, ListTodo,
    Target, User, Hash, MessageSquare, Calendar, ChevronRight,
    ArrowUpCircle, ArrowDownCircle, Info
} from 'lucide-react';
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
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        pending: 0,
        inProgress: 0,
        completed: 0,
        totalQty: 0,
        completedQty: 0
    });

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 15000);
        return () => clearInterval(interval);
    }, [type]);

    const fetchTasks = async () => {
        try {
            const res = await getOperationalTasks(type);
            const data = res.data || [];

            // Filter by assigned user
            // Admin and Masters see all tasks of the given type
            // Operators see only their assigned tasks or unassigned ones
            const canSeeAll = currentUser?.role === 'admin' ||
                (type === 'filing' && currentUser?.role === 'file_master') ||
                (type === 'fabrication' && currentUser?.role === 'fab_master');

            const filteredData = canSeeAll
                ? data
                : data.filter(t => t.assigned_to === currentUser?.user_id || t.assigned_to === null);

            setTasks(filteredData);

            // Calculate stats
            const newStats = filteredData.reduce((acc, t) => {
                acc[t.status.toLowerCase().replace(' ', '')] = (acc[t.status.toLowerCase().replace(' ', '')] || 0) + 1;
                acc.totalQty += t.quantity;
                acc.completedQty += t.completed_quantity;
                return acc;
            }, { pending: 0, inprogress: 0, completed: 0, totalQty: 0, completedQty: 0 });

            setStats({
                pending: newStats.pending || 0,
                inProgress: newStats.inprogress || 0,
                completed: newStats.completed || 0,
                totalQty: newStats.totalQty,
                completedQty: newStats.completedQty
            });
        } catch (error) {
            console.error('Failed to fetch tasks:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateQuantity = async (task, delta) => {
        try {
            const newQty = Math.max(0, Math.min(task.quantity, task.completed_quantity + delta));
            if (newQty === task.completed_quantity) return;

            await updateOperationalTask(type, task.id, { completed_quantity: newQty });
            fetchTasks();
        } catch (error) {
            console.error('Failed to update quantity:', error);
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

            {/* Tasks Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-4 sm:p-6 border-b border-gray-100 flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-900 flex items-center">
                        <ListTodo className={`mr-2 ${accentText}`} size={20} />
                        Job Queue
                    </h2>
                    <div className="flex space-x-2">
                        <span className="text-xs font-bold bg-gray-100 text-gray-600 px-3 py-1 rounded-full border">
                            {tasks.length} Total Jobs
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
                                        {task.remarks && (
                                            <div className="mt-3 bg-gray-50 border border-gray-100 rounded-lg p-2 flex items-start">
                                                <MessageSquare size={14} className="mr-2 text-gray-400 mt-1 shrink-0" />
                                                <p className="text-xs text-gray-600 italic">"{task.remarks}"</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Task Execution / Progress */}
                                    <div className="flex flex-col sm:flex-row items-center gap-6 shrink-0 lg:w-[400px]">
                                        <div className="w-full flex-1">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs font-bold text-gray-500 uppercase tracking-tighter">Production Completion</span>
                                                <span className="text-sm font-black text-gray-900">{task.completed_quantity} <span className="text-gray-400 font-medium">/ {task.quantity}</span></span>
                                            </div>
                                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden border border-gray-100 shadow-inner">
                                                <div
                                                    className={`h-full transition-all duration-500 ease-out shadow-sm ${accentBg}`}
                                                    style={{ width: `${(task.completed_quantity / task.quantity) * 100}%` }}
                                                />
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleUpdateQuantity(task, -1)}
                                                disabled={task.completed_quantity === 0}
                                                className="p-2 rounded-xl border border-gray-200 hover:border-red-500 hover:text-red-500 transition-all bg-white shadow-sm disabled:opacity-30 disabled:hover:border-gray-200 disabled:hover:text-gray-400"
                                            >
                                                <ArrowDownCircle size={20} />
                                            </button>
                                            <button
                                                onClick={() => handleUpdateQuantity(task, 1)}
                                                disabled={task.completed_quantity >= task.quantity}
                                                className={`p-3 rounded-2xl ${accentBg} text-white shadow-md hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:hover:scale-100`}
                                            >
                                                <ArrowUpCircle size={24} />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Machine Info */}
                                    <div className="shrink-0 flex flex-col justify-center border-l border-gray-100 pl-6 hidden xl:flex">
                                        <div className="text-[10px] font-bold text-gray-400 uppercase mb-1">Assigned Station</div>
                                        <div className="flex items-center space-x-2 text-sm font-bold text-gray-800">
                                            <Info size={14} className={accentText} />
                                            <span>{task.machine_name || 'General Station'}</span>
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
