import React, { useState, useEffect } from 'react';
import { getRunningTasks, getTaskStatus, getProjectsSummary, getTaskStats, assignTask } from '../../api/supervisor';
import QuickAssign from '../../components/QuickAssign';
import {
    getSupervisorUnifiedDashboard, endTask, completeTask,
    getOperatorTasks, operatorStartTask, operatorCompleteTask, operatorHoldTask, operatorResumeTask
} from '../../api/services';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Folder, CheckCircle, Clock, TrendingUp, RefreshCw, Play, Users, X, Pause, ChevronDown, ChevronUp } from 'lucide-react';
import { resolveMachineName } from '../../utils/machineUtils';

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

const SupervisorDashboard = () => {
    // --- Existing Supervisor State ---
    const [projectSummary, setProjectSummary] = useState({ total: 0, completed: 0, pending: 0, active: 0 });
    const [runningTasks, setRunningTasks] = useState([]);
    const [operatorStatus, setOperatorStatus] = useState([]);
    const [taskStats, setTaskStats] = useState({ total_tasks: 0, pending: 0, in_progress: 0, completed: 0, on_hold: 0, available_projects: [] });
    const [selectedOperator, setSelectedOperator] = useState('all');
    const [selectedProject, setSelectedProject] = useState('all');
    const [operators, setOperators] = useState([]);
    const [machines, setMachines] = useState([]);

    // --- "My Tasks" State ---
    const [myTasks, setMyTasks] = useState([]);
    const [actionLoading, setActionLoading] = useState({});

    // --- Modals ---
    const [selectedTask, setSelectedTask] = useState(null);
    const [showEndModal, setShowEndModal] = useState(false);
    const [endReason, setEndReason] = useState('');

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const isMounted = React.useRef(false);
    const filtersRef = React.useRef({ project: 'all', operator: 'all' });

    useEffect(() => {
        filtersRef.current = { project: selectedProject, operator: selectedOperator };
        fetchDashboard();

        // Polling
        const interval = setInterval(() => {
            fetchRunningTasksOnly();
            fetchMyTasks(); // Also poll my tasks
        }, 15000);
        return () => clearInterval(interval);
    }, [selectedProject, selectedOperator]);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);
            const { project, operator } = filtersRef.current;

            // 1. Fetch Supervisor Data
            const [unifiedRes, runningRes, operatorStatusRes, statsRes] = await Promise.all([
                getSupervisorUnifiedDashboard(project, operator),
                getRunningTasks(project, operator),
                getTaskStatus(operator, project),
                getTaskStats(project, operator)
            ]);

            // 2. Process Supervisor Data
            const unified = unifiedRes?.data || {};
            const overview = unified.overview || {};
            const tStats = overview.tasks || {};
            const pStats = overview.projects || {};

            setProjectSummary({
                total: pStats.total || 0,
                completed: pStats.completed || 0,
                pending: pStats.yet_to_start || 0,
                active: (pStats.in_progress || 0) + (pStats.held || 0)
            });
            setRunningTasks(Array.isArray(runningRes?.data) ? runningRes.data : []);
            setTaskStats({
                total_tasks: tStats.total || 0,
                pending: tStats.pending || 0,
                in_progress: tStats.in_progress || 0,
                completed: (tStats.completed || 0) + (tStats.ended || 0),
                on_hold: tStats.on_hold || 0,
                available_projects: statsRes?.data?.available_projects || []
            });
            setOperatorStatus(Array.isArray(operatorStatusRes?.data) ? operatorStatusRes.data : []);
            setOperators(Array.isArray(unified.operators) ? unified.operators : []);
            setMachines(Array.isArray(unified.machines) ? unified.machines : []);

            // 3. Fetch My Tasks (Assigned to Me)
            await fetchMyTasks();

        } catch (err) {
            console.error('❌ Supervisor Load Error:', err);
            setError(err.response?.data?.detail || 'Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const fetchRunningTasksOnly = async () => {
        try {
            const { project, operator } = filtersRef.current;
            const res = await getRunningTasks(project, operator);
            setRunningTasks(Array.isArray(res?.data) ? res.data : []);
        } catch (e) { console.error(e); }
    };

    const fetchMyTasks = async () => {
        try {
            const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
            // If an operator is selected, fetch THEIR tasks. Otherwise fetch MINE.
            const targetUserId = (selectedOperator && selectedOperator !== 'all') ? selectedOperator : currentUser.user_id;

            if (targetUserId) {
                const res = await getOperatorTasks(targetUserId);
                setMyTasks(Array.isArray(res?.data?.tasks) ? res.data.tasks : []);
            }
        } catch (e) {
            console.error("Failed to load my tasks", e);
        }
    };

    // --- Actions for Running Tasks (Supervisor Admin-Actions) ---
    const handleEndTask = (task) => {
        setSelectedTask(task);
        setEndReason('');
        setShowEndModal(true);
    };

    const confirmEndTask = async () => {
        if (!endReason.trim()) return alert("Reason required");
        if (!confirm("Force END this task?")) return;
        try {
            await endTask(selectedTask.id, endReason);
            setShowEndModal(false);
            setEndReason('');
            setSelectedTask(null);
            fetchDashboard();
        } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
    };

    // --- Actions for My Assigned Tasks (Operator Actions) ---
    const handleMyAction = async (action, taskId, ...args) => {
        try {
            setActionLoading(p => ({ ...p, [taskId]: action }));
            if (action === 'start') await operatorStartTask(taskId);
            if (action === 'complete') await operatorCompleteTask(taskId);
            if (action === 'hold') await operatorHoldTask(taskId, args[0]);
            if (action === 'resume') await operatorResumeTask(taskId);
            await fetchMyTasks();
            await fetchRunningTasksOnly(); // Update running list too
        } catch (err) {
            alert(err.response?.data?.detail || 'Action Failed');
        } finally {
            setActionLoading(p => ({ ...p, [taskId]: null }));
        }
    };

    // --- Helpers ---
    const formatTime = (iso) => iso ? new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'N/A';
    const formatDuration = (sec) => {
        if (!sec) return '0m';
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        return h > 0 ? `${h}h ${m}m` : `${m}m`;
    };

    if (loading) return <div className="text-center py-20">Loading Supervisor Dashboard...</div>;
    if (error) return <div className="text-center py-20 text-red-600">Error: {error} <button onClick={fetchDashboard} className="underline ml-2">Retry</button></div>;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Supervisor Dashboard</h1>
                    <p className="text-gray-600">Overview & Personal Tasks</p>
                </div>
                <div className="flex gap-2">
                    <select
                        value={selectedOperator}
                        onChange={e => setSelectedOperator(e.target.value)}
                        className="p-2 border rounded"
                    >
                        <option value="all">All Operators</option>
                        {operators.map(o => <option key={o.id} value={o.id}>{o.name || o.username}</option>)}
                    </select>
                    <button onClick={fetchDashboard} className="bg-blue-600 text-white px-3 py-2 rounded flex items-center gap-2">
                        <RefreshCw size={16} /> Refresh
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Total Tasks" value={taskStats.total_tasks} icon={TrendingUp} color="bg-indigo-500" />
                <StatCard title="Running Now" value={runningTasks.length} icon={Play} color="bg-blue-500" />
                <StatCard title="Pending" value={taskStats.pending} icon={Clock} color="bg-gray-500" />
                <StatCard title="Completed" value={taskStats.completed} icon={CheckCircle} color="bg-green-500" />
            </div>

            <QuickAssign onAssignSuccess={fetchDashboard} />

            {/* =============== OPERATOR TASKS SECTION ================= */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Users className="text-blue-600" />
                    {selectedOperator !== 'all'
                        ? `Tasks for ${operators.find(o => o.id === selectedOperator)?.name || 'Operator'} (${myTasks.length})`
                        : `My Assigned Tasks (${myTasks.length})`
                    }
                </h2>
                {myTasks.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">
                        {selectedOperator !== 'all' ? 'This operator has no tasks assigned.' : 'No tasks assigned to you right now.'}
                    </p>
                ) : (
                    <div className="space-y-3">
                        {myTasks.map(task => (
                            <div key={task.id} className="border rounded-lg p-4 hover:bg-gray-50">
                                <div className="flex flex-col md:flex-row justify-between gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-bold">{task.title}</h3>
                                            <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                                task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                    task.status === 'on_hold' ? 'bg-yellow-100 text-yellow-800' :
                                                        'bg-gray-100 text-gray-800'
                                                }`}>{task.status.replace('_', ' ')}</span>
                                        </div>
                                        <div className="text-xs text-gray-600 grid grid-cols-2 md:grid-cols-4 gap-2">
                                            <p>Project: <b>{task.project || '-'}</b></p>
                                            <p>Machine: <b>{task.machine_name || '-'}</b></p>
                                            <p>Due: <b>{task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}</b></p>
                                            <p>Part: <b>{task.part_item || '-'}</b></p>
                                        </div>
                                        {task.actual_start_time && (
                                            <div className="mt-2 space-y-1">
                                                <div className="flex flex-wrap gap-3">
                                                    <span className="text-[10px] text-green-700 font-bold uppercase tracking-tight flex items-center gap-1">
                                                        <Play size={10} /> Started: {formatTime(task.actual_start_time)}
                                                    </span>
                                                    <span className="text-[10px] text-blue-700 font-bold uppercase tracking-tight flex items-center gap-1">
                                                        <Clock size={10} /> Net: {formatDuration(task.total_duration_seconds)}
                                                    </span>
                                                    {task.total_held_seconds > 0 && (
                                                        <span className="text-[10px] text-amber-700 font-bold uppercase tracking-tight flex items-center gap-1">
                                                            <Pause size={10} /> Held: {formatDuration(task.total_held_seconds)}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-[9px] text-gray-400 font-black uppercase tracking-widest">
                                                    Total Duration: {
                                                        (() => {
                                                            const start = new Date(task.actual_start_time).getTime();
                                                            const end = task.actual_end_time ? new Date(task.actual_end_time).getTime() : Date.now();
                                                            return formatDuration(Math.floor((end - start) / 1000));
                                                        })()
                                                    }
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Action Buttons for MY tasks */}
                                    <div className="flex items-center gap-2">
                                        {task.status === 'pending' && (
                                            <button
                                                onClick={() => handleMyAction('start', task.id)}
                                                disabled={!!actionLoading[task.id]}
                                                className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-blue-700 disabled:opacity-50"
                                            >
                                                <Play size={14} /> Start
                                            </button>
                                        )}
                                        {task.status === 'in_progress' && (
                                            <>
                                                <button
                                                    onClick={() => handleMyAction('hold', task.id, prompt("Hold Reason:"))}
                                                    disabled={!!actionLoading[task.id]}
                                                    className="bg-yellow-500 text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-yellow-600 disabled:opacity-50"
                                                >
                                                    <Pause size={14} /> Hold
                                                </button>
                                                <button
                                                    onClick={() => handleMyAction('complete', task.id)}
                                                    disabled={!!actionLoading[task.id]}
                                                    className="bg-green-600 text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-green-700 disabled:opacity-50"
                                                >
                                                    <CheckCircle size={14} /> Complete
                                                </button>
                                            </>
                                        )}
                                        {task.status === 'on_hold' && (
                                            <button
                                                onClick={() => handleMyAction('resume', task.id)}
                                                disabled={!!actionLoading[task.id]}
                                                className="bg-purple-600 text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-purple-700 disabled:opacity-50"
                                            >
                                                <Play size={14} /> Resume
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Existing Running Tasks Section (Supervisor View) */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <Play className="text-green-600" />
                        Running Tasks (Everyone)
                    </h2>
                    <span className="text-sm text-gray-500">{runningTasks.length} active</span>
                </div>
                {runningTasks.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No active tasks on shop floor.</p>
                ) : (
                    <div className="space-y-3">
                        {runningTasks.map(task => (
                            <div key={task.id} className="border border-green-100 bg-green-50 rounded-lg p-4">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-bold text-gray-900">{task.title}</h3>
                                        <p className="text-xs text-gray-600 mt-1">
                                            👤 <b>{task.operator_name}</b> | ⚙️ {task.machine_name || 'Handwork'}
                                        </p>
                                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                                            <p className="text-[11px] text-gray-600">
                                                Net Runtime: <b className="text-blue-700">{formatDuration(task.duration_seconds)}</b>
                                            </p>
                                            {task.total_held_seconds > 0 && (
                                                <p className="text-[11px] text-gray-600">
                                                    Hold Time: <b className="text-amber-700">{formatDuration(task.total_held_seconds)}</b>
                                                </p>
                                            )}
                                        </div>
                                        {task.actual_start_time && (
                                            <p className="text-[10px] text-gray-400 font-bold uppercase mt-1 tracking-tighter">
                                                Total Time: {
                                                    (() => {
                                                        const start = new Date(task.actual_start_time).getTime();
                                                        return formatDuration(Math.floor((Date.now() - start) / 1000));
                                                    })()
                                                }
                                            </p>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => handleEndTask(task)}
                                        className="bg-red-100 text-red-700 px-2 py-1 rounded text-[10px] font-bold border border-red-200 hover:bg-red-200"
                                    >
                                        FORCE END
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {showEndModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white p-6 rounded-lg w-full max-w-sm">
                        <h3 className="font-bold text-lg mb-2">Force End Task</h3>
                        <p className="text-sm text-gray-600 mb-4">Stopping: {selectedTask?.title}</p>
                        <textarea
                            className="w-full border p-2 rounded mb-4"
                            placeholder="Reason required..."
                            value={endReason}
                            onChange={e => setEndReason(e.target.value)}
                        />
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setShowEndModal(false)} className="px-4 py-2 bg-gray-100 rounded">Cancel</button>
                            <button onClick={confirmEndTask} className="px-4 py-2 bg-red-600 text-white rounded">End Task</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SupervisorDashboard;
