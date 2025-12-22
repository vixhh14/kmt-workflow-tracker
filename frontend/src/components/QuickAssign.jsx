import React, { useState, useEffect } from 'react';
import { UserPlus, X, Clock, Play, CheckCircle, AlertCircle, Calendar } from 'lucide-react';
import { getPendingTasks, assignTask, getOperators } from '../api/supervisor';
import { getMachines, getUnits } from '../api/services';
import { minutesToHHMM, hhmmToMinutes, validateHHMM } from '../utils/timeFormat';
import { resolveMachineName } from '../utils/machineUtils';

const QuickAssign = ({ onAssignSuccess }) => {
    const [pendingTasks, setPendingTasks] = useState([]);
    const [operators, setOperators] = useState([]);
    const [machines, setMachines] = useState([]);
    const [units, setUnits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [selectedTask, setSelectedTask] = useState(null);

    // Modal Form State
    const [assigningData, setAssigningData] = useState({
        operator_id: '',
        machine_id: '',
        priority: 'medium',
        expected_duration_hhmm: '00:00',
        due_date: ''
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [tasksRes, operatorsRes, machinesRes, unitsRes] = await Promise.all([
                getPendingTasks(),
                getOperators(),
                getMachines(),
                getUnits()
            ]);
            setPendingTasks(Array.isArray(tasksRes?.data) ? tasksRes.data : []);
            setOperators(Array.isArray(operatorsRes?.data) ? operatorsRes.data : []);
            setMachines(Array.isArray(machinesRes?.data) ? machinesRes.data : []);
            setUnits(Array.isArray(unitsRes?.data) ? unitsRes.data : []);
        } catch (err) {
            console.error('Failed to fetch Quick Assign data:', err);
            setPendingTasks([]);
            setOperators([]);
            setMachines([]);
            setUnits([]);
        } finally {
            setLoading(false);
        }
    };

    const handleAssignClick = (task) => {
        setSelectedTask(task);
        setAssigningData({
            operator_id: task.assigned_to || '',
            machine_id: task.machine_id || '',
            priority: task.priority || 'medium',
            expected_duration_hhmm: minutesToHHMM(task.expected_completion_time || 0),
            due_date: task.due_date || ''
        });
        setShowModal(true);
    };

    const handleSubmit = async () => {
        if (!assigningData.operator_id || !selectedTask) return;

        if (!validateHHMM(assigningData.expected_duration_hhmm)) {
            alert('Invalid duration format. Please use HH:MM (e.g., 02:30)');
            return;
        }

        const durationMinutes = hhmmToMinutes(assigningData.expected_duration_hhmm);
        if (durationMinutes <= 0) {
            alert('Expected duration must be greater than 0');
            return;
        }

        try {
            await assignTask(selectedTask.id, {
                ...assigningData,
                expected_completion_time: durationMinutes
            });

            // Optimistic update: remove from local list before refresh
            setTasks(prev => prev.filter(t => t.id !== selectedTask.id));

            setShowModal(false);
            setSelectedTask(null);

            // Global refresh
            if (onAssignSuccess) onAssignSuccess();
            fetchData();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to assign task');
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading && pendingTasks.length === 0) {
        return <div className="p-8 text-center text-gray-500">Loading pending tasks...</div>;
    }

    return (
        <div className="bg-white rounded-lg shadow p-4 sm:p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                    <UserPlus className="text-blue-600 mr-2" size={24} />
                    <h2 className="text-lg font-semibold text-gray-900">Quick Assign – Pending Tasks</h2>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">{pendingTasks.length} task(s)</span>
                    <button onClick={fetchData} className="text-xs text-blue-600 hover:underline">Refresh</button>
                </div>
            </div>

            {pendingTasks.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {pendingTasks.map(task => (
                        <div key={task.id} className="border rounded-lg p-4 hover:shadow-md transition bg-gray-50">
                            <div className="flex items-start justify-between mb-2">
                                <h3 className="font-medium text-gray-900 flex-1 truncate">{task.title || 'Untitled Task'}</h3>
                                {task.priority && (
                                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${getPriorityColor(task.priority)}`}>
                                        {task.priority}
                                    </span>
                                )}
                            </div>
                            <div className="space-y-1 mb-3">
                                {task.project && (
                                    <p className="text-xs text-gray-600 truncate">📁 <span className="font-medium text-gray-800">{task.project}</span></p>
                                )}
                                <p className="text-xs text-gray-600">⚙️ {task.machine_name || (task.machine_id ? `Machine-${task.machine_id}` : 'Handwork')}</p>
                                {task.due_date && (
                                    <p className="text-xs text-gray-600">📅 Due: {task.due_date}</p>
                                )}
                            </div>
                            <button
                                onClick={() => handleAssignClick(task)}
                                className="w-full bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-medium flex items-center justify-center gap-2"
                            >
                                <UserPlus size={16} />
                                <span>Assign Task</span>
                            </button>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                    <CheckCircle className="mx-auto mb-2 text-gray-300" size={32} />
                    <p className="text-sm">No pending tasks to assign</p>
                </div>
            )}

            {/* Modal */}
            {showModal && selectedTask && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden">
                        <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between">
                            <h3 className="text-lg font-bold text-gray-900">Task Assignment</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
                                <p className="text-sm text-blue-800"><span className="font-bold">Task:</span> {selectedTask.title}</p>
                                <p className="text-xs text-blue-600 mt-1">📁 Project: {selectedTask.project || 'N/A'}</p>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Operator</label>
                                    <select
                                        value={assigningData.operator_id}
                                        onChange={(e) => setAssigningData({ ...assigningData, operator_id: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="">-- Choose Operator --</option>
                                        {operators.map(op => (
                                            <option key={op.user_id} value={op.user_id}>{op.full_name || op.username}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Machine</label>
                                    <select
                                        value={assigningData.machine_id}
                                        onChange={(e) => setAssigningData({ ...assigningData, machine_id: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="">-- Choose Machine --</option>
                                        {machines.map(m => (
                                            <option key={m.id} value={m.id}>{resolveMachineName(m)}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Priority</label>
                                    <select
                                        value={assigningData.priority}
                                        onChange={(e) => setAssigningData({ ...assigningData, priority: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                    </select>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Task Completion Duration (HH:MM)</label>
                                    <input
                                        type="text"
                                        placeholder="02:30"
                                        value={assigningData.expected_duration_hhmm}
                                        onChange={(e) => setAssigningData({ ...assigningData, expected_duration_hhmm: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                    <p className="text-[10px] text-gray-400">Total Minutes: {hhmmToMinutes(assigningData.expected_duration_hhmm)}</p>
                                </div>
                                <div className="space-y-1 sm:col-span-2">
                                    <label className="text-xs font-bold text-gray-500 uppercase">Due Date</label>
                                    <input
                                        type="date"
                                        value={assigningData.due_date}
                                        onChange={(e) => setAssigningData({ ...assigningData, due_date: e.target.value })}
                                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="bg-gray-50 px-6 py-4 flex gap-3">
                            <button
                                onClick={() => setShowModal(false)}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 text-gray-700 font-medium"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={!assigningData.operator_id}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                            >
                                Confirm Assignment
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuickAssign;
