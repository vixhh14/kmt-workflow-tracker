import React, { useState, useEffect, useMemo } from 'react';
import {
    getOperationalTasks,
    createOperationalTask,
    updateOperationalTask,
    deleteOperationalTask,
    getProjects,
    getUsers
} from '../api/services';
import { Plus, Trash2, Edit2, CheckCircle, Clock, AlertCircle, User, MessageSquare, Hash, Calendar } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const OperationalTaskSection = ({ type, machineId, machineName }) => {
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
        part_item: '',
        quantity: 1,
        due_date: '',
        priority: 'medium',
        assigned_to: '',
        remarks: ''
    });

    useEffect(() => {
        fetchData();
    }, [type, machineId]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [tasksRes, projectsRes, usersRes] = await Promise.all([
                getOperationalTasks(type),
                getProjects(),
                getUsers()
            ]);

            // Filter tasks by machineId if provided
            const allTasks = tasksRes.data || [];
            const filteredTasks = machineId
                ? allTasks.filter(t => t.machine_id === machineId)
                : allTasks;

            setTasks(filteredTasks);
            setProjects(projectsRes.data || []);
            setUsers(usersRes.data || []);
        } catch (error) {
            console.error(`Failed to fetch ${type} tasks:`, error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                machine_id: machineId,
                quantity: parseInt(formData.quantity)
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
            alert('Failed to save task');
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

    const handleUpdateProgress = async (task, increment) => {
        try {
            const newQty = Math.max(0, Math.min(task.quantity, task.completed_quantity + increment));
            if (newQty === task.completed_quantity) return;

            await updateOperationalTask(type, task.id, { completed_quantity: newQty });
            fetchData();
        } catch (error) {
            console.error('Failed to update progress:', error);
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
                    {type === 'filing' ? '🔹 Filing Tasks' : '🔸 Fabrication Tasks'}
                    <span className="ml-2 bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-[10px]">
                        {tasks.length}
                    </span>
                </h4>
                {isAdmin && (
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
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 animate-fade-in">
                    <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="sm:col-span-2">
                            <label className="block text-[10px] font-bold text-gray-500 uppercase">Project / Item *</label>
                            <div className="flex gap-2">
                                <select
                                    required
                                    className="flex-1 text-sm border rounded p-1.5"
                                    value={formData.project_id}
                                    onChange={e => setFormData({ ...formData, project_id: e.target.value })}
                                >
                                    <option value="">Select Project</option>
                                    {projects.map(p => (
                                        <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
                                    ))}
                                </select>
                                <input
                                    required
                                    placeholder="Part / Item"
                                    className="flex-1 text-sm border rounded p-1.5"
                                    value={formData.part_item}
                                    onChange={e => setFormData({ ...formData, part_item: e.target.value })}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase">Quantity *</label>
                            <input
                                type="number"
                                required
                                min="1"
                                className="w-full text-sm border rounded p-1.5"
                                value={formData.quantity}
                                onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase">Due Date *</label>
                            <input
                                type="date"
                                required
                                className="w-full text-sm border rounded p-1.5"
                                value={formData.due_date}
                                onChange={e => setFormData({ ...formData, due_date: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase">Priority</label>
                            <select
                                className="w-full text-sm border rounded p-1.5"
                                value={formData.priority}
                                onChange={e => setFormData({ ...formData, priority: e.target.value })}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="urgent">Urgent</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-gray-500 uppercase">Assign To</label>
                            <select
                                className="w-full text-sm border rounded p-1.5"
                                value={formData.assigned_to}
                                onChange={e => setFormData({ ...formData, assigned_to: e.target.value })}
                            >
                                <option value="">Auto-Assign Later</option>
                                {users.filter(u => u.role === (type === 'filing' ? 'file_master' : 'fab_master') || u.role === 'operator').map(u => (
                                    <option key={u.user_id} value={u.user_id}>{u.full_name || u.username}</option>
                                ))}
                            </select>
                        </div>
                        <div className="sm:col-span-2">
                            <label className="block text-[10px] font-bold text-gray-500 uppercase">Remarks</label>
                            <textarea
                                className="w-full text-sm border rounded p-1.5"
                                rows="2"
                                value={formData.remarks}
                                onChange={e => setFormData({ ...formData, remarks: e.target.value })}
                            />
                        </div>
                        <div className="sm:col-span-2 flex justify-end space-x-2">
                            <button
                                type="button"
                                onClick={() => setShowForm(false)}
                                className="text-xs px-3 py-1.5 border rounded hover:bg-gray-100"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 font-bold"
                            >
                                {editingTask ? 'Update Task' : 'Create Task'}
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
                                <td colSpan="5" className="px-3 py-4 text-center text-xs text-gray-400 italic">
                                    No {type} tasks assigned to this machine.
                                </td>
                            </tr>
                        ) : (
                            tasks.map(task => (
                                <tr key={task.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-3 py-2">
                                        <div className="text-xs font-bold text-gray-900">{task.part_item}</div>
                                        <div className="text-[10px] text-gray-500">{task.project_name || 'No Project'}</div>
                                    </td>
                                    <td className="px-3 py-2">
                                        <div className="flex flex-col items-center">
                                            <div className="text-xs font-bold">{task.completed_quantity} / {task.quantity}</div>
                                            <div className="w-16 h-1 bg-gray-100 rounded-full mt-1 overflow-hidden">
                                                <div
                                                    className="h-full bg-green-500 transition-all"
                                                    style={{ width: `${(task.completed_quantity / task.quantity) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${getStatusColor(task.status)}`}>
                                            {task.status}
                                        </span>
                                    </td>
                                    <td className="px-3 py-2">
                                        <div className="flex items-center space-x-1 text-xs text-gray-600">
                                            <User size={12} className="text-gray-400" />
                                            <span>{task.assignee_name || 'Unassigned'}</span>
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
