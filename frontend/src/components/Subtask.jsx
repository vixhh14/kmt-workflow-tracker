import React, { useState, useEffect } from 'react';
import { getSubtasks, createSubtask, updateSubtask, deleteSubtask } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { Plus, Trash2, Save } from 'lucide-react';

const Subtask = ({ taskId, taskAssigneeId }) => {
    const { user } = useAuth();
    const [subtasks, setSubtasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [newSubtaskTitle, setNewSubtaskTitle] = useState('');

    // State to track edits for each subtask individually
    const [edits, setEdits] = useState({});

    // Roles allowed to edit: Admin, Planning, Supervisor, or the Operator assigned to the task
    const isMaster = ['admin', 'planning', 'supervisor'].includes(user?.role);
    const isAssignedOperator = user?.role === 'operator' && user?.user_id === taskAssigneeId;
    const canEdit = isMaster || isAssignedOperator;

    useEffect(() => {
        if (taskId) {
            fetchSubtasks();
        }
    }, [taskId]);

    const fetchSubtasks = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await getSubtasks(taskId);
            const data = Array.isArray(response.data) ? response.data : [];
            setSubtasks(data);
            // Initialize edit state with current values
            const initialEdits = {};
            data.forEach(st => {
                initialEdits[st.id] = { status: st.status, notes: st.notes || '' };
            });
            setEdits(initialEdits);
        } catch (err) {
            console.error('Failed to fetch subtasks:', err);
            setError('Failed to load subtasks');
            setSubtasks([]); // Set to empty array on error
        } finally {
            setLoading(false);
        }
    };

    const handleAddSubtask = async (e) => {
        e.preventDefault();
        if (!newSubtaskTitle.trim()) return;
        setError('');

        try {
            await createSubtask({
                task_id: taskId,
                title: newSubtaskTitle,
                notes: ''
            });
            setNewSubtaskTitle('');
            await fetchSubtasks();
        } catch (err) {
            console.error('Failed to create subtask:', err);
            const detail = err.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : 'Failed to create subtask');
        }
    };

    const handleEditChange = (subtaskId, field, value) => {
        setEdits(prev => ({
            ...prev,
            [subtaskId]: {
                ...prev[subtaskId],
                [field]: value
            }
        }));
    };

    const handleSave = async (subtaskId) => {
        const dataToUpdate = edits[subtaskId];
        try {
            await updateSubtask(subtaskId, dataToUpdate);
            // Refresh to get updated timestamps or confirm sync
            fetchSubtasks();
            alert('Subtask updated successfully');
        } catch (err) {
            console.error('Failed to update subtask:', err);
            setError(err.response?.data?.detail || 'Failed to update subtask');
        }
    };

    const handleDelete = async (subtaskId) => {
        if (!window.confirm('Are you sure you want to delete this subtask?')) return;
        try {
            await deleteSubtask(subtaskId);
            fetchSubtasks();
        } catch (err) {
            console.error('Failed to delete subtask:', err);
            setError('Failed to delete subtask');
        }
    };

    const getStatusBadgeColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'in_progress': return 'bg-blue-100 text-blue-800';
            case 'pending': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="text-sm text-gray-500 p-4 italic">Loading subtasks...</div>;
    }

    return (
        <div className="bg-gray-50 rounded-lg p-4 mt-2 border border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Subtasks</h4>

            {error && <p className="text-red-500 text-sm mb-2">{error}</p>}

            {/* List Subtasks */}
            <div className="space-y-4">
                {subtasks.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">No subtasks yet.</p>
                ) : (
                    subtasks.map((subtask) => (
                        <div key={subtask.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 flex flex-col sm:flex-row gap-4">
                            {/* Title Section */}
                            <div className="flex-1 min-w-[200px]">
                                <p className="text-sm font-medium text-gray-900">{subtask.title}</p>
                                <p className="text-xs text-gray-500 mt-1">Created: {new Date(subtask.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</p>
                            </div>

                            {/* Status Section */}
                            <div className="w-full sm:w-40">
                                <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
                                {canEdit ? (
                                    <select
                                        value={edits[subtask.id]?.status || 'pending'}
                                        onChange={(e) => handleEditChange(subtask.id, 'status', e.target.value)}
                                        className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="pending">Pending</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="completed">Completed</option>
                                    </select>
                                ) : (
                                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(subtask.status)}`}>
                                        {subtask.status.replace('_', ' ')}
                                    </span>
                                )}
                            </div>

                            {/* Notes Section */}
                            <div className="flex-1">
                                <label className="block text-xs font-medium text-gray-500 mb-1">Notes</label>
                                {canEdit ? (
                                    <textarea
                                        value={edits[subtask.id]?.notes || ''}
                                        onChange={(e) => handleEditChange(subtask.id, 'notes', e.target.value)}
                                        rows="2"
                                        className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        placeholder="Add notes..."
                                    />
                                ) : (
                                    <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded border border-gray-100 min-h-[2.5rem]">
                                        {subtask.notes || <span className="text-gray-400 italic">No notes</span>}
                                    </div>
                                )}
                            </div>

                            {/* Actions Section */}
                            {(isMaster || isAssignedOperator) && (
                                <div className="flex flex-row sm:flex-col justify-center gap-2 mt-2 sm:mt-0">
                                    <button
                                        onClick={() => handleSave(subtask.id)}
                                        className="flex items-center justify-center space-x-1 bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 transition text-xs font-medium"
                                        title="Save Changes"
                                    >
                                        <Save size={14} />
                                        <span>Save</span>
                                    </button>

                                    {isMaster && (
                                        <button
                                            onClick={() => handleDelete(subtask.id)}
                                            className="flex items-center justify-center space-x-1 bg-red-100 text-red-700 px-3 py-1.5 rounded hover:bg-red-200 transition text-xs font-medium"
                                            title="Delete Subtask"
                                        >
                                            <Trash2 size={14} />
                                            <span>Delete</span>
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Add Subtask Form - Only for masters */}
            {isMaster && (
                <form onSubmit={handleAddSubtask} className="mt-6 border-t border-gray-200 pt-4">
                    <div className="flex items-center space-x-2">
                        <input
                            type="text"
                            value={newSubtaskTitle}
                            onChange={(e) => setNewSubtaskTitle(e.target.value)}
                            placeholder="Add a new subtask..."
                            className="flex-1 text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button
                            type="submit"
                            disabled={!newSubtaskTitle.trim()}
                            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition flex items-center space-x-1"
                        >
                            <Plus size={16} />
                            <span className="hidden sm:inline">Add</span>
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
};

export default Subtask;
