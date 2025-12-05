import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPlanningTasks, createPlanningTask, deletePlanningTask, getUsers, getTasks } from '../api/services';
import { Plus, Trash2, Calendar, Users } from 'lucide-react';

const PlanningDashboard = () => {
    const [planningTasks, setPlanningTasks] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        task_id: '',
        project_name: '',
        task_sequence: 1,
        assigned_supervisor: '',
        status: 'pending'
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [planningRes, tasksRes, usersRes] = await Promise.all([
                getPlanningTasks(),
                getTasks(),
                getUsers()
            ]);
            setPlanningTasks(planningRes.data);
            setTasks(tasksRes.data);
            setUsers(usersRes.data);
        } catch (error) {
            console.error('Failed to fetch planning data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await createPlanningTask(formData);
            setFormData({
                task_id: '',
                project_name: '',
                task_sequence: 1,
                assigned_supervisor: '',
                status: 'pending'
            });
            setShowForm(false);
            fetchData();
        } catch (error) {
            console.error('Failed to create planning task:', error);
            alert('Failed to create planning task');
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this planning task?')) {
            try {
                await deletePlanningTask(id);
                fetchData();
            } catch (error) {
                console.error('Failed to delete planning task:', error);
                alert('Failed to delete planning task');
            }
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'in_progress': return 'bg-blue-100 text-blue-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Planning Department</h1>
                    <p className="text-gray-600">Manage project planning and task sequences</p>
                </div>
                <div className="flex items-center space-x-3">
                    <Link
                        to="/workflow-tracker"
                        className="flex items-center space-x-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
                    >
                        <Users size={20} />
                        <span>Workflow Tracker</span>
                    </Link>
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                    >
                        <Plus size={20} />
                        <span>Add Plan</span>
                    </button>
                </div>
            </div>

            {/* Add Planning Task Form */}
            {showForm && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">Add New Planning Task</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.project_name}
                                    onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Linked Task</label>
                                <select
                                    value={formData.task_id}
                                    onChange={(e) => setFormData({ ...formData, task_id: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Select Task</option>
                                    {tasks.map((task) => (
                                        <option key={task.id} value={task.id}>
                                            {task.title}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Sequence Number</label>
                                <input
                                    type="number"
                                    min="1"
                                    value={formData.task_sequence}
                                    onChange={(e) => setFormData({ ...formData, task_sequence: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Assigned Supervisor</label>
                                <select
                                    value={formData.assigned_supervisor}
                                    onChange={(e) => setFormData({ ...formData, assigned_supervisor: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Select Supervisor</option>
                                    {users.filter(u => u.role === 'supervisor' || u.role === 'admin').map((user) => (
                                        <option key={user.user_id} value={user.user_id}>
                                            {user.username}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                                <select
                                    value={formData.status}
                                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="pending">Pending</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex space-x-3">
                            <button
                                type="submit"
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                            >
                                Create Plan
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowForm(false)}
                                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Planning Tasks Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {planningTasks.map((item) => (
                    <div key={item.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center space-x-3">
                                <div className="p-3 bg-indigo-100 rounded-lg">
                                    <Calendar className="text-indigo-600" size={24} />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900">{item.project_name}</h3>
                                    <p className="text-sm text-gray-500">Seq: {item.task_sequence}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(item.id)}
                                className="text-red-600 hover:text-red-900"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Status:</span>
                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(item.status)}`}>
                                    {item.status.replace('_', ' ')}
                                </span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Supervisor:</span>
                                <span className="text-gray-900">
                                    {users.find(u => u.user_id === item.assigned_supervisor)?.username || 'Unassigned'}
                                </span>
                            </div>
                            {item.updated_at && (
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Last Updated:</span>
                                    <span className="text-gray-900">{new Date(item.updated_at).toLocaleString()}</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {planningTasks.length === 0 && (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                    <Calendar className="mx-auto text-gray-400 mb-4" size={48} />
                    <p className="text-gray-500">No planning tasks found. Add your first plan above.</p>
                </div>
            )}
        </div>
    );
};

export default PlanningDashboard;
