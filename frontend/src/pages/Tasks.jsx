import React, { useState, useEffect } from 'react';
import { getTasks, createTask, deleteTask, getMachines, getUsers, updateTask, getProjects, endTask } from '../api/services';
import { Plus, Trash2, CheckSquare, Search, Filter, X, ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Clock, Square } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Subtask from '../components/Subtask';
import { minutesToHHMM, hhmmToMinutes, validateHHMM } from '../utils/timeFormat';
import { resolveMachineName } from '../utils/machineUtils';

const Tasks = () => {
    const { user: currentUser } = useAuth();

    // Helper to format due_datetime (supports legacy due_date)
    const formatDueDateTime = (isoString, fallbackDate) => {
        if (!isoString) {
            if (!fallbackDate) return '-';
            try {
                const [year, month, day] = fallbackDate.split('-');
                if (!year || !month || !day) return fallbackDate;
                const date = new Date(year, month - 1, day, 9, 0); // Default to 09:00 AM
                const options = { day: '2-digit', month: 'short', year: 'numeric' };
                return date.toLocaleDateString('en-GB', options) + " • 09:00 AM";
            } catch (e) { return fallbackDate; }
        }

        try {
            // isoString from backend is like "2023-12-23T14:30:00" (Naive)
            // Parsing it directly as naive depends on browser, but usually works as local.
            // If it ends in Z, it's UTC, which we want to avoid but handle if present.
            const date = new Date(isoString);
            if (isNaN(date.getTime())) return isoString;

            const options = {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
                hour12: true
            };
            const formatted = date.toLocaleString('en-GB', options);
            return formatted.replace(',', ' •').toUpperCase();
        } catch (e) { return isoString; }
    };

    const [tasks, setTasks] = useState([]);
    const [machines, setMachines] = useState([]);
    const [users, setUsers] = useState([]);
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [expandedTaskId, setExpandedTaskId] = useState(null);

    // Search and Filter states
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [priorityFilter, setPriorityFilter] = useState('all');
    const [operatorFilter, setOperatorFilter] = useState('all');

    // Pagination states
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);

    // Bulk action states
    const [selectedTasks, setSelectedTasks] = useState([]);
    const [showBulkActions, setShowBulkActions] = useState(false);

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        project: '',
        project_id: '',
        part_item: '',
        nos_unit: '',
        status: 'pending',
        priority: 'medium',
        assigned_to: '',
        assigned_by: '',
        machine_id: '',
        due_date: '',
        due_time: '09:00',
        expected_completion_time: ''
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            console.log('🔄 Fetching dropdown data...');

            const [tasksRes, machinesRes, usersRes, projectsRes] = await Promise.all([
                getTasks(),
                getMachines(),
                getUsers(),
                getProjects()
            ]);

            // Debug API responses
            console.log('📡 API Responses:', {
                tasks: tasksRes?.data?.length,
                machines: machinesRes?.data?.length,
                users: usersRes?.data?.length,
                projects: projectsRes?.data?.length
            });

            // Ensure data is always an array
            const tasksData = Array.isArray(tasksRes?.data) ? tasksRes.data : [];
            const machinesData = Array.isArray(machinesRes?.data) ? machinesRes.data : [];
            const usersData = Array.isArray(usersRes?.data) ? usersRes.data : [];
            const projectsData = Array.isArray(projectsRes?.data) ? projectsRes.data : [];

            console.log('✅ Data loaded:', {
                tasks: tasksData.length,
                machines: machinesData.length,
                users: usersData.length,
                projects: projectsData.length
            });

            // Log sample data for verification
            if (machinesData.length > 0) {
                console.log('Sample machine:', machinesData[0]);
            } else {
                console.warn('⚠️ No machines loaded');
            }

            if (usersData.length > 0) {
                console.log('Sample user:', usersData[0]);
            } else {
                console.warn('⚠️ No users loaded');
            }

            setTasks(tasksData);
            setMachines(machinesData);
            setUsers(usersData);
            setProjects(projectsData);
        } catch (error) {
            console.error('❌ Failed to fetch data:', error);
            console.error('Error details:', error.response?.data || error.message);
            // Set empty arrays on error to prevent crashes
            setTasks([]);
            setMachines([]);
            setUsers([]);
            setProjects([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (!validateHHMM(formData.expected_completion_time)) {
                alert('Invalid duration format. Please use HH:MM (e.g. 02:30)');
                return;
            }

            const durationMinutes = hhmmToMinutes(formData.expected_completion_time);
            if (durationMinutes <= 0) {
                alert('Expected duration must be greater than 0');
                return;
            }

            // Combine Date and Time for due_datetime
            let due_datetime = null;
            if (formData.due_date) {
                // Use selected time or default to 09:00
                const timeStr = formData.due_time || '09:00';
                due_datetime = `${formData.due_date}T${timeStr}:00`;
            }

            const payload = {
                ...formData,
                due_datetime: due_datetime,
                expected_completion_time: durationMinutes
            };

            await createTask(payload);
            setFormData({
                title: '',
                description: '',
                project: '',
                project_id: '',
                part_item: '',
                nos_unit: '',
                status: 'pending',
                priority: 'medium',
                assigned_to: '',
                assigned_by: '',
                machine_id: '',
                due_date: '',
                due_time: '09:00',
                expected_completion_time: ''
            });
            setShowForm(false);
            fetchData();
        } catch (error) {
            console.error('Failed to create task:', error);
            alert(error.response?.data?.detail || 'Failed to create task');
        }
    };

    const handleEndTask = async (taskId) => {
        if (window.confirm('Are you sure you want to end this task? It will be closed and cannot be resumed by operators.')) {
            try {
                await endTask(taskId);
                fetchData();
            } catch (error) {
                console.error('Failed to end task:', error);
                alert(error.response?.data?.detail || 'Failed to end task');
            }
        }
    };

    const handleDelete = async (taskId) => {
        if (window.confirm('Are you sure you want to delete this task?')) {
            try {
                await deleteTask(taskId);
                fetchData();
            } catch (error) {
                console.error('Failed to delete task:', error);
                alert(error.response?.data?.detail || 'Failed to delete task');
            }
        }
    };

    const toggleExpand = (taskId) => {
        setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
    };

    // Filter and search logic
    const getFilteredTasks = () => {
        return tasks.filter(task => {
            // Search filter
            const matchesSearch = searchQuery === '' ||
                task.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                task.project?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                task.part_item?.toLowerCase().includes(searchQuery.toLowerCase());

            // Status filter
            const matchesStatus = statusFilter === 'all' || task.status === statusFilter;

            // Priority filter
            const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter;

            // Operator filter
            const matchesOperator = operatorFilter === 'all' || task.assigned_to === operatorFilter;

            return matchesSearch && matchesStatus && matchesPriority && matchesOperator;
        });
    };

    // Pagination logic
    const filteredTasks = getFilteredTasks();
    const totalPages = Math.ceil(filteredTasks.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedTasks = filteredTasks.slice(startIndex, endIndex);

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery, statusFilter, priorityFilter, operatorFilter]);

    // Bulk actions
    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedTasks(paginatedTasks.map(t => t.id));
        } else {
            setSelectedTasks([]);
        }
    };

    const handleSelectTask = (taskId) => {
        setSelectedTasks(prev =>
            prev.includes(taskId)
                ? prev.filter(id => id !== taskId)
                : [...prev, taskId]
        );
    };

    const handleBulkAssign = async (operatorId) => {
        try {
            await Promise.all(
                selectedTasks.map(taskId =>
                    updateTask(taskId, { assigned_to: operatorId })
                )
            );
            setSelectedTasks([]);
            setShowBulkActions(false);
            fetchData();
        } catch (error) {
            console.error('Failed to bulk assign:', error);
            alert(error.response?.data?.detail || 'Failed to assign tasks');
        }
    };

    const handleBulkDelete = async () => {
        if (window.confirm(`Are you sure you want to delete ${selectedTasks.length} tasks?`)) {
            try {
                await Promise.all(selectedTasks.map(taskId => deleteTask(taskId)));
                setSelectedTasks([]);
                fetchData();
            } catch (error) {
                console.error('Failed to bulk delete:', error);
                alert(error.response?.data?.detail || 'Failed to delete tasks');
            }
        }
    };

    const clearFilters = () => {
        setSearchQuery('');
        setStatusFilter('all');
        setPriorityFilter('all');
        setOperatorFilter('all');
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
        switch (priority) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-yellow-100 text-yellow-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Tasks Management</h1>
                    <p className="text-sm sm:text-base text-gray-600">Manage and track tasks</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2.5 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto text-sm sm:text-base"
                >
                    <Plus size={20} />
                    <span>Add Task</span>
                </button>
            </div>

            {/* Search and Filters */}
            <div className="bg-white rounded-lg shadow p-3 sm:p-4">
                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-2 sm:gap-4">
                    {/* Search */}
                    <div className="col-span-2 lg:col-span-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                            <input
                                type="text"
                                placeholder="Search tasks..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>

                    {/* Status Filter */}
                    <div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">Status</option>
                            <option value="pending">Pending</option>
                            <option value="in_progress">In Progress</option>
                            <option value="on_hold">On Hold</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>

                    {/* Priority Filter */}
                    <div>
                        <select
                            value={priorityFilter}
                            onChange={(e) => setPriorityFilter(e.target.value)}
                            className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">Priority</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                    </div>

                    {/* Operator Filter */}
                    <div className="col-span-2 sm:col-span-1">
                        <select
                            value={operatorFilter}
                            onChange={(e) => setOperatorFilter(e.target.value)}
                            className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">All Operators</option>
                            {Array.isArray(users) && users
                                .filter(u => u?.role === 'operator')
                                .map(user => (
                                    <option key={user?.user_id || Math.random()} value={user?.user_id || ''}>
                                        {user?.full_name || user?.username || 'Unknown'}
                                    </option>
                                ))}
                        </select>
                    </div>
                </div>

                {/* Active Filters & Clear */}
                {(searchQuery || statusFilter !== 'all' || priorityFilter !== 'all' || operatorFilter !== 'all') && (
                    <div className="mt-3 flex items-center justify-between">
                        <span className="text-sm text-gray-600">
                            Showing {filteredTasks.length} of {tasks.length} tasks
                        </span>
                        <button
                            onClick={clearFilters}
                            className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                        >
                            <X size={16} />
                            <span>Clear Filters</span>
                        </button>
                    </div>
                )}
            </div>

            {/* Bulk Actions */}
            {selectedTasks.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <span className="text-sm font-medium text-blue-900">
                            {selectedTasks.length} task(s) selected
                        </span>
                        <div className="flex flex-wrap items-center gap-2">
                            <select
                                onChange={(e) => {
                                    if (e.target.value) {
                                        handleBulkAssign(e.target.value);
                                        e.target.value = '';
                                    }
                                }}
                                className="flex-1 sm:flex-none px-3 py-1.5 text-sm border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Assign to...</option>
                                {Array.isArray(users) && users
                                    .filter(u => u?.role === 'operator')
                                    .map(user => (
                                        <option key={user?.user_id || Math.random()} value={user?.user_id || ''}>
                                            {user?.full_name || user?.username || 'Unknown'}
                                        </option>
                                    ))}
                            </select>
                            <button
                                onClick={handleBulkDelete}
                                className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"
                            >
                                Delete
                            </button>
                            <button
                                onClick={() => setSelectedTasks([])}
                                className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Task Form */}
            {showForm && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">Add New Task</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Project *</label>
                                <select
                                    required
                                    value={formData.project_id || ''}
                                    onChange={(e) => {
                                        const selectedProject = projects.find(p => p.project_id === e.target.value);
                                        setFormData({
                                            ...formData,
                                            project_id: e.target.value,
                                            project: selectedProject ? selectedProject.project_name : ''
                                        });
                                    }}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    disabled={loading || projects.length === 0}
                                >
                                    <option value="">Select Project</option>
                                    {projects.map((p) => (
                                        <option key={p.project_id} value={p.project_id}>
                                            {p.project_name} ({p.project_code})
                                        </option>
                                    ))}
                                </select>
                                {projects.length === 0 && !loading && (
                                    <p className="text-xs text-red-600 mt-1">⚠️ No projects available. Please add projects first.</p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Part / Item *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.part_item}
                                    onChange={(e) => setFormData({ ...formData, part_item: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Nos / Unit *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.nos_unit}
                                    onChange={(e) => setFormData({ ...formData, nos_unit: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Priority *</label>
                                <select
                                    required
                                    value={formData.priority}
                                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Machine *</label>
                                <select
                                    required
                                    value={formData.machine_id}
                                    onChange={(e) => setFormData({ ...formData, machine_id: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    disabled={loading || machines.length === 0}
                                >
                                    <option value="">
                                        {loading ? 'Loading machines...' : machines.length === 0 ? 'No machines available' : 'Select Machine'}
                                    </option>
                                    {Array.isArray(machines) && machines.map((machine) => (
                                        <option key={machine?.id || Math.random()} value={machine?.id || ''}>
                                            {resolveMachineName(machine)}
                                        </option>
                                    ))}
                                </select>
                                {machines.length === 0 && !loading && (
                                    <p className="text-xs text-red-600 mt-1">⚠️ No machines available. Please add machines in the Machines page.</p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Assign To *</label>
                                <select
                                    required
                                    value={formData.assigned_to}
                                    onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Select User</option>
                                    {users.filter(u => u?.role !== 'admin').map((user) => (
                                        <option key={user?.user_id || Math.random()} value={user?.user_id || ''}>
                                            {user?.full_name || user?.username || 'Unknown User'} ({user?.role})
                                        </option>
                                    ))}
                                </select>
                                {users.filter(u => u?.role !== 'admin').length === 0 && !loading && (
                                    <p className="text-xs text-red-600 mt-1">⚠️ No available users to assign.</p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Assigned By *</label>
                                <select
                                    required
                                    value={formData.assigned_by}
                                    onChange={(e) => setFormData({ ...formData, assigned_by: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    disabled={loading || users.length === 0}
                                >
                                    <option value="">
                                        {loading ? 'Loading users...' : users.filter(u => ['admin', 'supervisor', 'planning'].includes(u?.role)).length === 0 ? 'No assigners available' : 'Select User'}
                                    </option>
                                    {Array.isArray(users) && users
                                        .filter(u => ['admin', 'supervisor', 'planning'].includes(u?.role))
                                        .map((user) => (
                                            <option key={user?.user_id || Math.random()} value={user?.user_id || ''}>
                                                {user?.full_name || user?.username || 'Unknown'} ({user?.role || 'unknown'})
                                            </option>
                                        ))}
                                    {users.filter(u => ['admin', 'supervisor', 'planning'].includes(u?.role)).length === 0 && !loading && (
                                        <p className="text-xs text-gray-500 mt-1">⚠️ No admin/supervisor/planning users available</p>
                                    )}
                                </select>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Due Date *</label>
                                    <input
                                        type="date"
                                        required
                                        value={formData.due_date}
                                        onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Expected Time of Completion *</label>
                                    <input
                                        type="time"
                                        required
                                        value={formData.due_time}
                                        onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Task Completion Duration (HH:MM) *</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="e.g. 02:30"
                                    value={formData.expected_completion_time}
                                    onChange={(e) => setFormData({ ...formData, expected_completion_time: e.target.value })}
                                    className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                                <p className="text-xs text-gray-400 mt-1">Enter hours and minutes (e.g. 02:30 = 150 mins). Total: {hhmmToMinutes(formData.expected_completion_time)}m</p>
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                                <textarea
                                    required
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    rows="3"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                        <div className="flex space-x-3">
                            <button
                                type="submit"
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                            >
                                Create Task
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
                </div >
            )}

            {/* Tasks Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-2 sm:px-4 py-3 text-left">
                                    <input
                                        type="checkbox"
                                        checked={selectedTasks.length === paginatedTasks.length && paginatedTasks.length > 0}
                                        onChange={handleSelectAll}
                                        className="rounded border-gray-300"
                                    />
                                </th>
                                <th className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Project</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Part/Item</th>
                                <th className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Priority</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Assigned To</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Deadline</th>
                                <th className="px-2 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {paginatedTasks.map((task) => (
                                <React.Fragment key={task.id}>
                                    <tr className="hover:bg-gray-50">
                                        <td className="px-2 sm:px-4 py-3 sm:py-4">
                                            <input
                                                type="checkbox"
                                                checked={selectedTasks.includes(task.id)}
                                                onChange={() => handleSelectTask(task.id)}
                                                className="rounded border-gray-300"
                                            />
                                        </td>
                                        <td className="px-2 sm:px-6 py-3 sm:py-4">
                                            <div className="flex items-center">
                                                <button
                                                    onClick={() => toggleExpand(task.id)}
                                                    className="mr-1 sm:mr-2 text-gray-400 hover:text-gray-600 flex-shrink-0"
                                                >
                                                    {expandedTaskId === task.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                                </button>
                                                <div className="min-w-0">
                                                    <div className="text-xs sm:text-sm font-medium text-gray-900 truncate max-w-[100px] sm:max-w-[200px]">{task.title}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900 truncate max-w-[150px]">{task.project || '-'}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">{task.part_item || '-'}</div>
                                            {task.nos_unit && <div className="text-xs text-gray-500">({task.nos_unit})</div>}
                                        </td>
                                        <td className="px-2 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                                            <span className={`px-1.5 sm:px-2 py-0.5 sm:py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(task.status)}`}>
                                                {task.status.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getPriorityColor(task.priority)}`}>
                                                {task.priority}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {users.find(u => u.user_id === task.assigned_to)?.username || 'Unassigned'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-[11px] font-bold text-gray-700 bg-gray-50 px-2 py-1 rounded inline-block">
                                                {formatDueDateTime(task.due_datetime, task.due_date)}
                                            </div>
                                        </td>
                                        <td className="px-2 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-sm font-medium">
                                            <div className="flex items-center space-x-2">
                                                {currentUser?.role === 'admin' && task.status !== 'ended' && task.status !== 'completed' && (
                                                    <button
                                                        onClick={() => handleEndTask(task.id)}
                                                        className="text-purple-600 hover:text-purple-900 p-1 flex items-center space-x-1 border border-purple-200 rounded hover:bg-purple-50"
                                                        title="End Task (Admin Only)"
                                                    >
                                                        <Square size={14} fill="currentColor" />
                                                        <span className="text-[10px] uppercase font-bold">End</span>
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => handleDelete(task.id)}
                                                    className="text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded"
                                                    title="Delete Task"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                    {expandedTaskId === task.id && (
                                        <tr>
                                            <td colSpan="8" className="px-3 sm:px-6 py-4 bg-gray-50 border-t border-gray-200">
                                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                                    {/* Subtasks Section */}
                                                    <div>
                                                        <Subtask taskId={task.id} />
                                                    </div>

                                                    {/* Timing Analytics Section */}
                                                    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                                                        <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide flex items-center">
                                                            <Clock size={16} className="mr-2 text-blue-600" />
                                                            Timing Analytics
                                                        </h4>

                                                        <div className="space-y-4">
                                                            <div className="grid grid-cols-2 gap-4">
                                                                <div className="bg-blue-50 p-3 rounded-lg">
                                                                    <p className="text-[10px] text-blue-600 font-bold uppercase mb-1">Task Lifecycle</p>
                                                                    <div className="space-y-1 text-xs">
                                                                        <p className="flex justify-between">
                                                                            <span className="text-gray-500">Started:</span>
                                                                            <span className="font-medium text-gray-900">{task.actual_start_time ? new Date(task.actual_start_time).toLocaleString('en-IN') : 'N/A'}</span>
                                                                        </p>
                                                                        <p className="flex justify-between">
                                                                            <span className="text-gray-500">Completed:</span>
                                                                            <span className="font-medium text-gray-900">{task.actual_end_time ? new Date(task.actual_end_time).toLocaleString('en-IN') : 'N/A'}</span>
                                                                        </p>
                                                                    </div>
                                                                </div>

                                                                <div className="bg-purple-50 p-3 rounded-lg">
                                                                    <p className="text-[10px] text-purple-600 font-bold uppercase mb-1">Duration Analysis</p>
                                                                    <div className="space-y-1 text-xs">
                                                                        <p className="flex justify-between">
                                                                            <span className="text-gray-500">Deadline:</span>
                                                                            <span className="font-bold text-red-600">{formatDueDateTime(task.due_datetime, task.due_date)}</span>
                                                                        </p>
                                                                        <p className="flex justify-between">
                                                                            <span className="text-gray-500">Task Completion Duration:</span>
                                                                            <span className="font-medium text-gray-900">{minutesToHHMM(task.expected_completion_time)} ({task.expected_completion_time || '0'}m)</span>
                                                                        </p>
                                                                        <p className="flex justify-between">
                                                                            <span className="text-gray-500">Actual (Net):</span>
                                                                            <span className={`font-bold ${task.expected_completion_time && (task.total_duration_seconds / 60) > task.expected_completion_time
                                                                                ? 'text-red-600'
                                                                                : 'text-green-600'
                                                                                }`}>
                                                                                {Math.floor(task.total_duration_seconds / 60)} mins
                                                                            </span>
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            <div className="border-t pt-3">
                                                                <p className="text-[10px] text-gray-400 font-bold uppercase mb-2 flex justify-between items-center">
                                                                    <span>Hold History</span>
                                                                    <span className="text-amber-600">Total Held: {Math.floor((task.total_held_seconds || 0) / 60)} mins</span>
                                                                </p>

                                                                {task.holds && task.holds.length > 0 ? (
                                                                    <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                                                                        {task.holds.map((hold, idx) => (
                                                                            <div key={idx} className="flex justify-between items-center bg-gray-50 p-2 rounded text-[11px] border-l-2 border-amber-400">
                                                                                <div>
                                                                                    <div className="flex items-center text-gray-700 font-medium">
                                                                                        <span>{new Date(hold.start).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</span>
                                                                                        <span className="mx-1">→</span>
                                                                                        <span>{hold.end ? new Date(hold.end).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'Present'}</span>
                                                                                    </div>
                                                                                    {hold.reason && <p className="text-[10px] text-gray-500 italic mt-0.5">Reason: {hold.reason}</p>}
                                                                                </div>
                                                                                <span className="font-bold text-gray-900 bg-white px-1.5 py-0.5 rounded border border-gray-100">
                                                                                    {Math.ceil(hold.duration_seconds / 60)}m
                                                                                </span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <p className="text-xs text-gray-400 italic py-2">No hold intervals recorded for this task.</p>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {filteredTasks.length > 0 && (
                    <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                        <div className="flex-1 flex justify-between sm:hidden">
                            <button
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                disabled={currentPage === totalPages}
                                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                            >
                                Next
                            </button>
                        </div>
                        <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                            <div className="flex items-center space-x-4">
                                <p className="text-sm text-gray-700">
                                    Showing <span className="font-medium">{startIndex + 1}</span> to <span className="font-medium">{Math.min(endIndex, filteredTasks.length)}</span> of{' '}
                                    <span className="font-medium">{filteredTasks.length}</span> results
                                </p>
                                <select
                                    value={itemsPerPage}
                                    onChange={(e) => {
                                        setItemsPerPage(Number(e.target.value));
                                        setCurrentPage(1);
                                    }}
                                    className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                                >
                                    <option value={10}>10 per page</option>
                                    <option value={25}>25 per page</option>
                                    <option value={50}>50 per page</option>
                                    <option value={100}>100 per page</option>
                                </select>
                            </div>
                            <div>
                                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                    <button
                                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                        disabled={currentPage === 1}
                                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        <ChevronLeft size={20} />
                                    </button>
                                    {[...Array(totalPages)].map((_, i) => (
                                        <button
                                            key={i + 1}
                                            onClick={() => setCurrentPage(i + 1)}
                                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${currentPage === i + 1
                                                ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                                }`}
                                        >
                                            {i + 1}
                                        </button>
                                    ))}
                                    <button
                                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                                        disabled={currentPage === totalPages}
                                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        <ChevronRight size={20} />
                                    </button>
                                </nav>
                            </div>
                        </div>
                    </div>
                )}

                {filteredTasks.length === 0 && (
                    <div className="text-center py-12">
                        <CheckSquare className="mx-auto text-gray-400 mb-4" size={48} />
                        <p className="text-gray-500">No tasks found matching your filters.</p>
                    </div>
                )}
            </div>
        </div >
    );
};

export default Tasks;
