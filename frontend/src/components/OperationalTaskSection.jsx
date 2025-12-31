import React, { useState, useEffect, useMemo } from 'react';
import {
    getOperationalTasks,
    createOperationalTask,
    updateOperationalTask,
    deleteOperationalTask,
    getProjectsDropdown,
    getAssignableUsers,
    getUserOperationalTasks
} from '../api/services';
import { Plus, Trash2, Edit2, CheckCircle, Clock, AlertCircle, User, MessageSquare, Hash, Calendar, Play, Pause, Square, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const OperationalTaskSection = ({ type, machineId, machineName, userId, userName, initialProjects, initialUsers }) => {
    const { user: currentUser } = useAuth();
    const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'planning';

    const [tasks, setTasks] = useState([]);
    const [projects, setProjects] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingTask, setEditingTask] = useState(null);

    const [formData, setFormData] = useState({
        project_id: '',
        work_order_number: '',
        part_item: '',
        quantity: 1,
        due_date: '',
        priority: 'medium',
        assigned_to: '',
        remarks: ''
    });

    useEffect(() => {
        fetchData();
    }, [type, machineId, userId, initialProjects, initialUsers]);

    const fetchData = async () => {
        try {
            setLoading(true);
            console.log(`🔄 Fetching operational data for ${type}...`);

            if (userId) {
                const [tasksRes, projectsRes, usersRes] = await Promise.all([
                    getUserOperationalTasks(userId),
                    (Array.isArray(initialProjects) && initialProjects.length > 0) ? Promise.resolve({ data: initialProjects }) : getProjectsDropdown(),
                    (Array.isArray(initialUsers) && initialUsers.length > 0) ? Promise.resolve({ data: initialUsers }) : getAssignableUsers()
                ]);

                const tasksData = Array.isArray(tasksRes?.data) ? tasksRes.data : [];
                const projectsData = Array.isArray(projectsRes?.data) ? projectsRes.data : [];
                const usersData = Array.isArray(usersRes?.data) ? usersRes.data : [];

                console.log(`✅ Data loaded for user ${userId}:`, {
                    tasks: tasksData.length,
                    projects: projectsData.length,
                    users: usersData.length,
                    source: initialProjects ? 'props' : 'api'
                });

                setTasks(tasksData);
                setProjects(projectsData);
                setUsers(usersData);
            } else {
                const [tasksRes, projectsRes, usersRes] = await Promise.all([
                    getOperationalTasks(type),
                    (Array.isArray(initialProjects) && initialProjects.length > 0) ? Promise.resolve({ data: initialProjects }) : getProjectsDropdown(),
                    (Array.isArray(initialUsers) && initialUsers.length > 0) ? Promise.resolve({ data: initialUsers }) : getAssignableUsers()
                ]);

                const allTasks = Array.isArray(tasksRes?.data) ? tasksRes.data : [];
                const projectsData = Array.isArray(projectsRes?.data) ? projectsRes.data : [];
                const usersData = Array.isArray(usersRes?.data) ? usersRes.data : [];

                console.log(`✅ Data loaded for ${type}:`, {
                    allTasks: allTasks.length,
                    projects: projectsData.length,
                    users: usersData.length,
                    source: initialProjects ? 'props' : 'api'
                });

                // Filter tasks by machineId if provided
                const filteredTasks = machineId
                    ? allTasks.filter(t => String(t.machine_id) === String(machineId))
                    : allTasks;

                setTasks(filteredTasks);
                setProjects(projectsData);
                setUsers(usersData);
            }
        } catch (error) {
            console.error(`❌ Failed to fetch operational data:`, error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Validate required fields explicitly if needed
            if (!formData.project_id) {
                alert('Please select a project');
                return;
            }

            const payload = {
                project_id: formData.project_id,
                work_order_number: formData.work_order_number,
                part_item: formData.part_item,
                quantity: parseInt(formData.quantity),
                due_date: formData.due_date,
                priority: formData.priority,
                assigned_to: formData.assigned_to || null, // Ensure empty string becomes null
                remarks: formData.remarks
            };

            if (editingTask) {
                await updateOperationalTask(type, editingTask.id, payload);
            } else {
                await createOperationalTask(type, payload);
            }

            setShowForm(false);
            setEditingTask(null);
            setFormData({
                project_id: '',
                work_order_number: '',
                part_item: '',
                quantity: 1,
                due_date: '',
                priority: 'medium',
                assigned_to: '',
                remarks: ''
            });
            fetchData();
        } catch (error) {
            console.error('Failed to save task:', error);
            const detail = error.response?.data?.detail;
            alert(
                typeof detail === 'string'
                    ? detail
                    : (detail ? JSON.stringify(detail, null, 2) : 'Failed to save task. Please check all required fields.')
            );
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this task?')) return;
        try {
            await deleteOperationalTask(type, id);
            fetchData();
        } catch (error) {
            console.error('Failed to delete task:', error);
        }
    };

    const handleUpdateProgress = async (task, newValue) => {
        try {
            const qty = parseInt(newValue);
            if (isNaN(qty)) return;

            const newQty = Math.max(0, Math.min(task.quantity, qty));
            if (newQty === task.completed_quantity) return;

            await updateOperationalTask(type, task.id, { completed_quantity: newQty });
            fetchData();
        } catch (error) {
            console.error('Failed to update progress:', error);
        }
    };

    const handleUpdateStatus = async (taskId, newStatus) => {
        try {
            await updateOperationalTask(type, taskId, { status: newStatus });
            fetchData();
        } catch (error) {
            console.error('Failed to update status:', error);
            alert(error.response?.data?.detail || 'Failed to update status');
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'completed': return 'bg-green-100 text-green-700';
            case 'in progress': return 'bg-blue-100 text-blue-700';
            case 'on hold': return 'bg-yellow-100 text-yellow-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    if (loading && tasks.length === 0) return <div className="p-4 text-center">Loading...</div>;

    return (
        <div className="mt-4 space-y-4 border-t pt-4">
            <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wider flex items-center">
                    {userId
                        ? `👤 Tasks for ${userName || userId}`
                        : (type === 'filing' ? '🔹 Filing Tasks' : '🔸 Fabrication Tasks')
                    }
                    <span className="ml-2 bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-[10px]">
                        {tasks.length}
                    </span>
                </h4>
                {isAdmin && !userId && (
                    <button
                        onClick={() => {
                            setEditingTask(null);
                            setShowForm(!showForm);
                        }}
                        className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 flex items-center space-x-1"
                    >
                        <Plus size={14} />
                        <span>Add Task</span>
                    </button>
                )}
            </div>

            {showForm && (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 animate-fade-in shadow-inner">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {/* Project Field */}
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Project *</label>
                                <select
                                    required
                                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm bg-white"
                                    value={formData.project_id || ''}
                                    onChange={e => {
                                        const pId = e.target.value;
                                        setFormData({
                                            ...formData,
                                            project_id: pId || ''
                                        });
                                    }}
                                >
                                    <option value="" disabled hidden>
                                        {loading ? '-- Loading Projects --' : (initialProjects?.length || projects.length) === 0 ? '-- No Projects Available --' : '-- Select Project --'}
                                    </option>
                                    {(initialProjects?.length > 0 ? initialProjects : projects).map(p => (
                                        <option key={p?.id || p?.project_id || Math.random()} value={p?.id || p?.project_id || ''}>
                                            {p?.name || p?.project_name || 'Unknown Project'}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Work Order Field */}
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Work Order Number *</label>
                                <input
                                    required
                                    placeholder="Enter Work Order #"
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                                    value={formData.work_order_number}
                                    onChange={e => setFormData({ ...formData, work_order_number: e.target.value })}
                                />
                            </div>

                            {/* Part / Item Field */}
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Part / Item *</label>
                                <input
                                    required
                                    placeholder="Enter Part or Item Name"
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                                    value={formData.part_item}
                                    onChange={e => setFormData({ ...formData, part_item: e.target.value })}
                                />
                            </div>

                            {/* Quantity Field */}
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Quantity *</label>
                                <input
                                    type="number"
                                    required
                                    min="1"
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                                    value={formData.quantity}
                                    onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                                />
                            </div>

                            {/* Due Date Field */}
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Due Date *</label>
                                <input
                                    type="date"
                                    required
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                                    value={formData.due_date}
                                    onChange={e => setFormData({ ...formData, due_date: e.target.value })}
                                />
                            </div>

                            {/* Priority Field */}
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Priority *</label>
                                <select
                                    required
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                                    value={formData.priority}
                                    onChange={e => setFormData({ ...formData, priority: e.target.value })}
                                >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                    <option value="urgent">Urgent</option>
                                </select>
                            </div>

                            {/* Assign To (Dropdown) */}
                            <div className="sm:col-span-2">
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Assign To</label>
                                <select
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500 bg-white"
                                    value={formData.assigned_to}
                                    onChange={e => setFormData({ ...formData, assigned_to: e.target.value })}
                                >
                                    <option value="">-- Auto-assign to Master --</option>
                                    {users.filter(u => u.role !== 'admin').map((u) => (
                                        <option key={u.user_id || u.id} value={u.user_id || u.id}>
                                            {u.full_name || u.username} ({u.role})
                                        </option>
                                    ))}
                                </select>
                                <p className="text-[9px] text-gray-400 mt-1">Select an operator or leave default for auto-assignment</p>
                            </div>

                            {/* Remarks Field */}
                            <div className="sm:col-span-2">
                                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">Remarks</label>
                                <textarea
                                    className="w-full text-sm border rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
                                    rows="2"
                                    value={formData.remarks}
                                    onChange={e => setFormData({ ...formData, remarks: e.target.value })}
                                    placeholder="Add any additional instructions..."
                                />
                            </div>
                        </div>

                        {/* Form Actions */}
                        <div className="flex justify-end space-x-3 pt-2">
                            <button
                                type="button"
                                onClick={() => {
                                    setShowForm(false);
                                    setEditingTask(null);
                                }}
                                className="px-4 py-2 border rounded-lg text-sm bg-white hover:bg-gray-50 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold shadow-sm hover:bg-blue-700 transition-all flex items-center space-x-1"
                            >
                                <CheckCircle size={16} />
                                <span>{editingTask ? 'Update Task' : 'Create Task'}</span>
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="overflow-x-auto rounded-lg border">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-3 py-2 text-left text-[10px] font-bold text-gray-500 uppercase">Task / Project</th>
                            <th className="px-3 py-2 text-center text-[10px] font-bold text-gray-500 uppercase">Qty</th>
                            <th className="px-3 py-2 text-center text-[10px] font-bold text-gray-500 uppercase">Status</th>
                            <th className="px-3 py-2 text-left text-[10px] font-bold text-gray-500 uppercase">Assignee</th>
                            <th className="px-3 py-2 text-right text-[10px] font-bold text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {tasks.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="px-3 py-10 text-center text-xs text-gray-500 italic">
                                    {userId ? "No tasks found for this user." : (machineId ? `No ${type} tasks assigned to this machine.` : `No ${type} tasks found.`)}
                                </td>
                            </tr>
                        ) : (
                            tasks.map(task => (
                                <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-3 py-2">
                                        <div className="text-[10px] font-bold text-blue-600 uppercase">WO: {task.work_order_number}</div>
                                        <div className="text-xs font-bold text-gray-900">{task.part_item}</div>
                                        <div className="text-[10px] text-gray-500">{task.project_name || 'No Project'}</div>
                                    </td>
                                    <td className="px-3 py-2">
                                        <div className="flex flex-col items-center">
                                            <div className="flex items-center space-x-1 mb-1">
                                                <input
                                                    type="number"
                                                    value={task.completed_quantity}
                                                    onChange={(e) => handleUpdateProgress(task, e.target.value)}
                                                    className="w-12 text-center text-xs font-bold border rounded p-0.5 focus:ring-1 focus:ring-blue-500"
                                                    min="0"
                                                    max={task.quantity}
                                                />
                                                <span className="text-xs text-gray-400">/ {task.quantity}</span>
                                            </div>
                                            <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden border">
                                                <div
                                                    className="h-full bg-green-500 transition-all"
                                                    style={{ width: `${(task.completed_quantity / task.quantity) * 100}%` }}
                                                />
                                            </div>
                                            {task.completed_at && (
                                                <span className="text-[8px] text-gray-400 mt-0.5 whitespace-nowrap">
                                                    End: {new Date(task.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <div className="flex flex-col items-center gap-1">
                                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${getStatusColor(task.status)}`}>
                                                {task.status}
                                            </span>
                                            {/* Minimal Quick Status Controls for Admin and Assignee */}
                                            {(isAdmin || (task.assigned_to === currentUser?.user_id)) && (
                                                <div className="flex items-center gap-1">
                                                    {(task.status === 'Pending' || task.status === 'On Hold') && (
                                                        <button onClick={() => handleUpdateStatus(task.id, 'In Progress')} className="p-0.5 text-green-600 hover:bg-green-50 rounded">
                                                            <Play size={10} fill="currentColor" />
                                                        </button>
                                                    )}
                                                    {task.status === 'In Progress' && (
                                                        <>
                                                            <button onClick={() => handleUpdateStatus(task.id, 'On Hold')} className="p-0.5 text-orange-600 hover:bg-orange-50 rounded">
                                                                <Pause size={10} fill="currentColor" />
                                                            </button>
                                                            <button onClick={() => handleUpdateStatus(task.id, 'Completed')} className="p-0.5 text-blue-600 hover:bg-blue-50 rounded">
                                                                <Square size={10} fill="currentColor" />
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2">
                                        <div className="flex flex-col">
                                            <div className="flex items-center space-x-1 text-xs text-gray-600">
                                                <User size={12} className="text-gray-400" />
                                                <span className="truncate max-w-[80px]">{task.assignee_name || 'Unassigned'}</span>
                                            </div>
                                            {task.total_active_duration > 0 && (
                                                <span className="text-[9px] text-gray-400 font-medium">
                                                    ⏱ {Math.floor(task.total_active_duration / 60)}m {task.total_active_duration % 60}s
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-3 py-2 text-right">
                                        <div className="flex justify-end space-x-1">
                                            {isAdmin && (
                                                <>
                                                    <button
                                                        onClick={() => {
                                                            setEditingTask(task);
                                                            setFormData({
                                                                project_id: task.project_id || '',
                                                                work_order_number: task.work_order_number || '',
                                                                part_item: task.part_item || '',
                                                                quantity: task.quantity,
                                                                due_date: task.due_date || '',
                                                                priority: task.priority || 'medium',
                                                                assigned_to: task.assigned_to || '',
                                                                remarks: task.remarks || ''
                                                            });
                                                            setShowForm(true);
                                                        }}
                                                        className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                                                    >
                                                        <Edit2 size={14} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(task.id)}
                                                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            )
                            ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default OperationalTaskSection;
