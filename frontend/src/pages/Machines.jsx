import React, { useState, useEffect, useMemo } from 'react';
import { getMachines, createMachine, updateMachine, deleteMachine } from '../api/services';
import { Plus, Trash2, Monitor, Search, X, Edit2, Building2, Tag } from 'lucide-react';

const Machines = () => {
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    // Search and Filter states
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [unitFilter, setUnitFilter] = useState('all');
    const [categoryFilter, setCategoryFilter] = useState('all');

    const [formData, setFormData] = useState({
        name: '',
        type: '',
        status: 'active',
        location: '',
        hourly_rate: 0
    });

    useEffect(() => {
        fetchMachines();
    }, []);

    const fetchMachines = async () => {
        try {
            setLoading(true);
            const response = await getMachines();
            setMachines(response.data);
        } catch (error) {
            console.error('Failed to fetch machines:', error);
        } finally {
            setLoading(false);
        }
    };

    // Get unique units and categories for filter dropdowns
    const { units, categories } = useMemo(() => {
        const unitSet = new Set();
        const categorySet = new Set();
        machines.forEach(m => {
            if (m.unit_name) unitSet.add(m.unit_name);
            if (m.category_name) categorySet.add(m.category_name);
        });
        return {
            units: Array.from(unitSet).sort(),
            categories: Array.from(categorySet).sort()
        };
    }, [machines]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await createMachine(formData);
            setFormData({ name: '', type: '', status: 'active', location: '', hourly_rate: 0 });
            setShowForm(false);
            fetchMachines();
        } catch (error) {
            console.error('Failed to create machine:', error);
            alert('Failed to create machine');
        }
    };

    const handleDelete = async (machineId) => {
        if (window.confirm('Are you sure you want to delete this machine?')) {
            try {
                await deleteMachine(machineId);
                fetchMachines();
            } catch (error) {
                console.error('Failed to delete machine:', error);
                alert('Failed to delete machine');
            }
        }
    };

    const handleStatusUpdate = async (machineId, newStatus) => {
        try {
            await updateMachine(machineId, { status: newStatus });
            fetchMachines(); // Refresh the list to show updated data
        } catch (error) {
            console.error('Failed to update machine status:', error);
            alert('Failed to update machine status');
        }
    };

    // Filter and search logic
    const getFilteredMachines = () => {
        return machines.filter(machine => {
            // Search filter
            const matchesSearch = searchQuery === '' ||
                machine.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                machine.category_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                machine.unit_name?.toLowerCase().includes(searchQuery.toLowerCase());

            // Status filter
            const matchesStatus = statusFilter === 'all' || machine.status === statusFilter;

            // Unit filter
            const matchesUnit = unitFilter === 'all' || machine.unit_name === unitFilter;

            // Category filter
            const matchesCategory = categoryFilter === 'all' || machine.category_name === categoryFilter;

            return matchesSearch && matchesStatus && matchesUnit && matchesCategory;
        });
    };

    const clearFilters = () => {
        setSearchQuery('');
        setStatusFilter('all');
        setUnitFilter('all');
        setCategoryFilter('all');
    };

    const hasActiveFilters = searchQuery || statusFilter !== 'all' || unitFilter !== 'all' || categoryFilter !== 'all';

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'bg-green-100 text-green-800';
            case 'maintenance': return 'bg-yellow-100 text-yellow-800';
            case 'offline': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="text-center py-8">Loading...</div>;
    }

    const filteredMachines = getFilteredMachines();

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Machines Management</h1>
                    <p className="text-sm sm:text-base text-gray-600">Manage production machines</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2.5 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto text-sm sm:text-base"
                >
                    <Plus size={20} />
                    <span>Add Machine</span>
                </button>
            </div>

            {/* Search and Filters */}
            <div className="bg-white rounded-lg shadow p-3 sm:p-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
                    {/* Search */}
                    <div className="sm:col-span-2 lg:col-span-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                            <input
                                type="text"
                                placeholder="Search machines..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>

                    {/* Unit Filter */}
                    <div>
                        <select
                            value={unitFilter}
                            onChange={(e) => setUnitFilter(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">All Units</option>
                            {units.map(unit => (
                                <option key={unit} value={unit}>{unit}</option>
                            ))}
                        </select>
                    </div>

                    {/* Category Filter */}
                    <div>
                        <select
                            value={categoryFilter}
                            onChange={(e) => setCategoryFilter(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">All Categories</option>
                            {categories.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>

                    {/* Status Filter */}
                    <div>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">All Status</option>
                            <option value="active">Active</option>
                            <option value="maintenance">Maintenance</option>
                            <option value="offline">Offline</option>
                        </select>
                    </div>
                </div>

                {/* Active Filters & Clear */}
                {hasActiveFilters && (
                    <div className="mt-3 flex items-center justify-between">
                        <span className="text-sm text-gray-600">
                            Showing {filteredMachines.length} of {machines.length} machines
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

            {/* Add Machine Form */}
            {showForm && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">Add New Machine</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.type}
                                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., CNC, Lathe, Mill"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Machine ID</label>
                                <input
                                    type="text"
                                    value={formData.location}
                                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                                <select
                                    value={formData.status}
                                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="active">Active</option>
                                    <option value="maintenance">Maintenance</option>
                                    <option value="offline">Offline</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Hourly Rate</label>
                                <input
                                    type="number"
                                    value={formData.hourly_rate}
                                    onChange={(e) => setFormData({ ...formData, hourly_rate: parseFloat(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                        <div className="flex space-x-3">
                            <button
                                type="submit"
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                            >
                                Create Machine
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

            {/* Machines Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {filteredMachines.map((machine) => (
                    <div key={machine.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center space-x-3">
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <Monitor className="text-blue-600" size={24} />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900">{machine.name}</h3>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {machine.unit_name && (
                                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs">
                                                {machine.unit_name}
                                            </span>
                                        )}
                                        {machine.category_name && (
                                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                                                {machine.category_name}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(machine.id)}
                                className="text-red-600 hover:text-red-800"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between text-sm items-center">
                                <span className="text-gray-600">Status:</span>
                                <select
                                    value={machine.status}
                                    onChange={(e) => handleStatusUpdate(machine.id, e.target.value)}
                                    className={`px-2 py-0.5 rounded-full text-xs font-semibold border-none focus:ring-2 focus:ring-blue-500 cursor-pointer ${getStatusColor(machine.status)}`}
                                >
                                    <option value="active" className="bg-white text-gray-900">Active</option>
                                    <option value="maintenance" className="bg-white text-gray-900">Maintenance</option>
                                    <option value="offline" className="bg-white text-gray-900">Offline</option>
                                </select>
                            </div>
                            {machine.hourly_rate > 0 && (
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Hourly Rate:</span>
                                    <span className="text-gray-900 font-semibold">${machine.hourly_rate}/hr</span>
                                </div>
                            )}
                            {machine.current_operator && (
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Current Operator:</span>
                                    <span className="text-gray-900">{machine.current_operator}</span>
                                </div>
                            )}
                            {machine.updated_at && (
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Last Updated:</span>
                                    <span className="text-gray-900">{new Date(machine.updated_at).toLocaleString()}</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Empty State */}
            {filteredMachines.length === 0 && (
                <div className="bg-white rounded-lg shadow p-12 text-center">
                    <Monitor className="mx-auto text-gray-400 mb-4" size={48} />
                    <p className="text-gray-500">
                        {searchQuery || statusFilter !== 'all'
                            ? 'No machines found matching your filters.'
                            : 'No machines found. Add your first machine to get started.'}
                    </p>
                </div>
            )}
        </div>
    );
};

export default Machines;
