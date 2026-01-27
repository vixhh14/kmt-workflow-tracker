import React, { useState, useEffect } from 'react';
import { getOperatorTasks, operatorStartTask, operatorCompleteTask, operatorHoldTask, operatorResumeTask, endTask } from '../../api/services';
import { Play, CheckCircle, Pause, Clock, AlertCircle, TrendingUp, ListTodo, Target, ChevronDown, ChevronUp, Save, X, Square } from 'lucide-react';
import Subtask from '../../components/Subtask';

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

const OperatorDashboard = () => {
    const [tasks, setTasks] = useState([]);
    const [stats, setStats] = useState({
        total_tasks: 0,
        completed_tasks: 0,
        in_progress_tasks: 0,
        pending_tasks: 0,
        on_hold_tasks: 0
    });
    const [userInfo, setUserInfo] = useState({ username: '', full_name: '' });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState({});
    const [selectedStatus, setSelectedStatus] = useState('all');
    const [expandedTaskId, setExpandedTaskId] = useState(null);

    // Hold/End Modal State
    const [showModal, setShowModal] = useState(false);
    const [modalType, setModalType] = useState(null); // 'hold' or 'end'
    const [selectedTask, setSelectedTask] = useState(null);
    const [modalReason, setModalReason] = useState('');

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchTasks = async () => {
        try {
            setError(null);
            const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
            const userId = currentUser.user_id;

            if (!userId) {
                setError('User not logged in');
                setLoading(false);
                return;
            }

            const response = await getOperatorTasks(userId);
            const { tasks: taskList, stats: taskStats, user } = response.data;

            setTasks(Array.isArray(taskList) ? taskList : []);
            setStats({
                total_tasks: taskStats?.total_tasks || 0,
                completed_tasks: taskStats?.completed_tasks || 0,
                in_progress_tasks: taskStats?.in_progress_tasks || 0,
                pending_tasks: taskStats?.pending_tasks || 0,
                on_hold_tasks: taskStats?.on_hold_tasks || 0
            });
            setUserInfo({
                username: user?.username || 'Operator',
                full_name: user?.full_name || user?.username || 'Operator'
            });
        } catch (err) {
            console.error('❌ Failed to fetch operator tasks:', err);
            setError(err.response?.data?.detail || 'Failed to load tasks');
            setTasks([]);
        } finally {
            setLoading(false);
        }
    };

    const handleStartTask = async (taskId) => {
        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'starting' }));
            await operatorStartTask(taskId);
            await fetchTasks();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to start task');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (!window.confirm('Are you sure you want to complete this task?')) return;
        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'completing' }));
            await operatorCompleteTask(taskId);
            await fetchTasks();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to complete task');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const openActionModal = (task, type) => {
        setSelectedTask(task);
        setModalType(type);
        setModalReason('');
        setShowModal(true);
    };

    const handleModalSubmit = async () => {
        if (!modalReason.trim()) {
            alert('Please provide a reason');
            return;
        }

        const taskId = selectedTask.id;
        try {
            setActionLoading(prev => ({ ...prev, [taskId]: modalType }));
            if (modalType === 'hold') {
                await operatorHoldTask(taskId, modalReason);
            } else if (modalType === 'end') {
                await endTask(taskId, modalReason);
            }
            setShowModal(false);
            await fetchTasks();
        } catch (err) {
            alert(err.response?.data?.detail || `Failed to ${modalType} task`);
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const handleResumeTask = async (taskId) => {
        try {
            setActionLoading(prev => ({ ...prev, [taskId]: 'resuming' }));
            await operatorResumeTask(taskId);
            await fetchTasks();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to resume task');
        } finally {
            setActionLoading(prev => ({ ...prev, [taskId]: null }));
        }
    };

    const formatDuration = (seconds) => {
        if (!seconds || isNaN(seconds) || seconds <= 0) return '0m';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    const formatMinutesToHHMM = (minutes) => {
        if (!minutes || isNaN(minutes)) return '00:00';
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Not set';
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-IN', {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata'
            });
        } catch (e) { return 'Invalid date'; }
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

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'ended': return 'bg-purple-100 text-purple-800';
            case 'in_progress': return 'bg-blue-100 text-blue-800';
            case 'on_hold': return 'bg-yellow-100 text-yellow-800';
            case 'pending': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getPriorityColor = (priority) => {
        const p = priority?.toLowerCase();
        switch (p) {
            case 'urgent': return 'bg-red-500 text-white';
            case 'high': return 'bg-orange-500 text-white';
            case 'medium': return 'bg-blue-500 text-white';
            case 'low': return 'bg-green-500 text-white';
            default: return 'bg-gray-500 text-white';
        }
    };

    const filteredTasks = selectedStatus === 'all'
        ? tasks
        : tasks.filter(t => t.status === selectedStatus);

    if (loading) return <div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div></div>;

    return (
        <div className="space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900 tracking-tight">Operator Workspace</h1>
                    <p className="text-gray-600 font-medium">Hello, {userInfo.full_name}</p>
                </div>
                <button onClick={fetchTasks} className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition shadow-lg shadow-blue-200 w-full sm:w-auto font-bold uppercase text-xs tracking-wider">
                    <Clock size={16} />
                    <span>Sync Status</span>
                </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
                <StatCard title="Assigned Tasks" value={stats.total_tasks} icon={ListTodo} color="bg-blue-500 shadow-[0_4px_12px_rgba(59,130,246,0.3)]" />
                <StatCard title="Active Now" value={stats.in_progress_tasks} icon={Play} color="bg-indigo-500 shadow-[0_4px_12px_rgba(99,102,241,0.3)]" />
                <StatCard title="Finished Tasks" value={stats.completed_tasks} icon={CheckCircle} color="bg-emerald-500 shadow-[0_4px_12px_rgba(16,185,129,0.3)]" />
                <StatCard title="Pending" value={stats.pending_tasks + stats.on_hold_tasks} icon={Clock} color="bg-amber-500 shadow-[0_4px_12px_rgba(245,158,11,0.3)]" />
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                <div className="flex items-center gap-4">
                    <span className="text-sm font-bold text-gray-500 uppercase tracking-widest">Filter:</span>
                    <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="px-4 py-2 border border-gray-100 rounded-xl focus:ring-4 focus:ring-blue-500/10 text-sm font-medium outline-none">
                        <option value="all">View All Work</option>
                        <option value="pending">Show Pending</option>
                        <option value="in_progress">Show Active</option>
                        <option value="on_hold">Show On Hold</option>
                        <option value="completed">Show Finished</option>
                        <option value="ended">Show Ended</option>
                    </select>
                </div>
            </div>

            <div className="space-y-4">
                {filteredTasks.length === 0 ? (
                    <div className="bg-gray-50 rounded-2xl py-16 text-center border-2 border-dashed border-gray-200">
                        <Target className="mx-auto text-gray-300 mb-4" size={56} />
                        <h3 className="text-xl font-bold text-gray-900 mb-1">Queue is Clear!</h3>
                        <p className="text-gray-500">No tasks match your current filter.</p>
                    </div>
                ) : (
                    filteredTasks.map(task => (
                        <div key={task.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:border-blue-200 transition-colors">
                            <div className="p-5 sm:p-6">
                                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex flex-wrap items-center gap-2 mb-4">
                                            <h3 className="text-xl font-bold text-gray-900 tracking-tight">{task.title || 'General Maintenance'}</h3>
                                            <span className={`px-2.5 py-1 text-[10px] font-black rounded-lg uppercase tracking-widest ${getStatusColor(task.status)}`}>
                                                {(task.status || 'pending').replace('_', ' ')}
                                            </span>
                                            <span className={`px-2.5 py-1 text-[10px] font-black rounded-lg uppercase tracking-widest ${getPriorityColor(task.priority)}`}>
                                                {(task.priority || 'medium')}
                                            </span>
                                        </div>

                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-3 gap-x-8 text-sm">
                                            <div><p className="text-gray-400 font-bold text-[10px] uppercase tracking-wider mb-0.5">Project</p><p className="font-semibold text-gray-800">{task.project || 'Internal'}</p></div>
                                            <div><p className="text-gray-400 font-bold text-[10px] uppercase tracking-wider mb-0.5">Machine</p><p className="font-semibold text-blue-600">{task.machine_name || 'Manual Bench'}</p></div>
                                            <div><p className="text-gray-400 font-bold text-[10px] uppercase tracking-wider mb-0.5">Deadline</p><p className="font-bold text-red-500">{formatDueDateTime(task.due_date)}</p></div>
                                            {task.part_item && <div><p className="text-gray-400 font-bold text-[10px] uppercase tracking-wider mb-0.5">Part/Item</p><p className="font-semibold text-gray-800">{task.part_item}</p></div>}
                                            {task.nos_unit && <div><p className="text-gray-400 font-bold text-[10px] uppercase tracking-wider mb-0.5">Quantity</p><p className="font-semibold text-gray-800">{task.nos_unit}</p></div>}
                                        </div>

                                        <div className="mt-6 flex flex-wrap gap-4 text-xs border-t border-gray-50 pt-5">
                                            <div className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                                <Clock size={14} className="text-blue-500" />
                                                <span className="text-gray-500 font-medium">Runtime:</span>
                                                <span className="font-bold text-gray-900">{formatDuration(task.total_duration_seconds)}</span>
                                            </div>
                                            {task.total_held_seconds > 0 && (
                                                <div className="flex items-center gap-2 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-100 text-amber-900">
                                                    <Pause size={14} />
                                                    <span className="font-medium">Hold Time:</span>
                                                    <span className="font-bold">{formatDuration(task.total_held_seconds)}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex flex-row lg:flex-col gap-3 flex-shrink-0">
                                        {task.status === 'pending' && (
                                            <button onClick={() => handleStartTask(task.id)} className="flex items-center justify-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-xl hover:bg-blue-700 transition font-bold shadow-lg shadow-blue-200 flex-1 lg:flex-none">
                                                <Play size={18} fill="currentColor" />
                                                <span>START WORK</span>
                                            </button>
                                        )}

                                        {task.status === 'in_progress' && (
                                            <>
                                                <button onClick={() => handleCompleteTask(task.id)} className="flex items-center justify-center gap-2 bg-emerald-600 text-white px-8 py-3 rounded-xl hover:bg-emerald-700 transition font-bold shadow-lg shadow-emerald-200 flex-1 lg:flex-none">
                                                    <CheckCircle size={18} />
                                                    <span>FINISH</span>
                                                </button>
                                                <button onClick={() => openActionModal(task, 'hold')} className="flex items-center justify-center gap-2 bg-amber-500 text-white px-8 py-3 rounded-xl hover:bg-amber-600 transition font-bold shadow-lg shadow-amber-200 flex-1 lg:flex-none">
                                                    <Pause size={18} />
                                                    <span>HOLD</span>
                                                </button>
                                                <button onClick={() => openActionModal(task, 'end')} className="flex items-center justify-center gap-2 bg-rose-600 text-white px-8 py-3 rounded-xl hover:bg-rose-700 transition font-bold shadow-lg shadow-rose-200 flex-1 lg:flex-none">
                                                    <Square size={18} />
                                                    <span>END</span>
                                                </button>
                                            </>
                                        )}

                                        {task.status === 'on_hold' && (
                                            <button onClick={() => handleResumeTask(task.id)} className="flex items-center justify-center gap-2 bg-indigo-600 text-white px-8 py-3 rounded-xl hover:bg-indigo-700 transition font-bold shadow-lg shadow-indigo-200 flex-1 lg:flex-none">
                                                <Play size={18} fill="currentColor" />
                                                <span>RESUME</span>
                                            </button>
                                        )}

                                        <button onClick={() => setExpandedTaskId(expandedTaskId === task.id ? null : task.id)} className="flex items-center justify-center px-4 py-3 bg-gray-100 rounded-xl text-gray-600 hover:bg-gray-200 font-bold transition">
                                            {expandedTaskId === task.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                            <span className="ml-2 lg:hidden">DETAILS</span>
                                        </button>
                                    </div>
                                </div>

                                {expandedTaskId === task.id && (
                                    <div className="mt-8 pt-8 border-t border-gray-100 animate-fade-in space-y-8">
                                        <div>
                                            <h4 className="text-lg font-bold text-gray-900 mb-6 flex items-center">
                                                <ListTodo className="mr-3 text-blue-600" size={20} />
                                                Process Sub-checkpoints
                                            </h4>
                                            <Subtask taskId={task.id} taskAssigneeId={task.assigned_to} />
                                        </div>

                                        {task.holds && task.holds.length > 0 && (
                                            <div className="bg-amber-50/50 rounded-2xl p-6 border border-amber-100/50">
                                                <h4 className="text-sm font-black text-amber-800 uppercase tracking-widest mb-4 flex items-center">
                                                    <Pause className="mr-2" size={16} />
                                                    Hold History
                                                </h4>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {task.holds.map((hold, idx) => (
                                                        <div key={idx} className="bg-white p-4 rounded-xl shadow-sm border border-amber-100">
                                                            <div className="flex justify-between items-start mb-2">
                                                                <span className="text-[10px] font-black text-amber-600 uppercase">#{idx + 1} Interval</span>
                                                                <span className="text-xs font-bold text-gray-900">{formatDuration(hold.duration_seconds)}</span>
                                                            </div>
                                                            <p className="text-xs text-gray-600 mb-2">{formatDate(hold.start)} → {hold.end ? formatDate(hold.end) : 'Present'}</p>
                                                            {hold.reason && <p className="text-xs text-gray-500 italic bg-gray-50 p-2 rounded-lg">"{hold.reason}"</p>}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Hold/End Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
                    <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden transform animate-scale-up">
                        <div className={`px-8 py-6 flex items-center justify-between text-white ${modalType === 'hold' ? 'bg-amber-500' : 'bg-rose-600'}`}>
                            <div className="flex items-center gap-3">
                                {modalType === 'hold' ? <Pause size={24} /> : <Square size={24} />}
                                <h3 className="text-xl font-bold uppercase tracking-tight">
                                    {modalType === 'hold' ? 'Pause Production' : 'End Production'}
                                </h3>
                            </div>
                            <button onClick={() => setShowModal(false)} className="bg-white/20 hover:bg-white/30 p-2 rounded-full transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-8">
                            <p className="text-gray-600 font-medium mb-4">
                                Please provide a brief reason for {modalType === 'hold' ? 'putting this task on hold' : 'ending this task early'}.
                            </p>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-1.5 ml-1">Reason / Note</label>
                                    <textarea
                                        autoFocus
                                        value={modalReason}
                                        onChange={(e) => setModalReason(e.target.value)}
                                        placeholder={`e.g. ${modalType === 'hold' ? 'Waiting for tool repair' : 'Part design error detected'}`}
                                        className="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none text-sm transition-all h-32 resize-none"
                                    />
                                </div>
                                <div className="flex gap-3 pt-2">
                                    <button onClick={() => setShowModal(false)} className="flex-1 px-6 py-4 border-2 border-gray-100 rounded-2xl text-gray-500 font-bold hover:bg-gray-50 transition-colors uppercase text-xs tracking-widest">
                                        Cancel
                                    </button>
                                    <button onClick={handleModalSubmit} className={`flex-1 px-6 py-4 text-white rounded-2xl font-bold shadow-lg transition-all flex items-center justify-center gap-2 uppercase text-xs tracking-widest ${modalType === 'hold' ? 'bg-amber-500 shadow-amber-200 hover:bg-amber-600' : 'bg-rose-600 shadow-rose-200 hover:bg-rose-700'}`}>
                                        {actionLoading[selectedTask?.id] ? <Clock className="animate-spin" size={16} /> : <Save size={16} />}
                                        Confirm
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default OperatorDashboard;
