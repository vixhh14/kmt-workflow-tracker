import React, { useState, useEffect } from 'react';
import { getOutsource, createOutsource, deleteOutsource } from '../api/services';
import { Plus, Trash2, Briefcase, Search, X, ChevronLeft, ChevronRight } from 'lucide-react';

const Outsource = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    // Search and Filter states
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [transportFilter, setTransportFilter] = useState('all');

    // Pagination states
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);

    const [formData, setFormData] = useState({
        title: '',
        vendor: '',
        description: '',
        status: 'pending',
        cost: 0,
        due_date: '',
        dc_generated: false,
        transport_status: 'pending',
        follow_up_time: '',
        pickup_status: 'pending'
    });

    useEffect(() => {
        fetchItems();
    }, []);

    const fetchItems = async () => {
        try {
            setLoading(true);
            const response = await getOutsource();
            setItems(response.data);
        } catch (error) {
            console.error('Failed to fetch outsource items:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await createOutsource(formData);
            setFormData({
                title: '',
                vendor: '',
                description: '',
                status: 'pending',
                cost: 0,
                due_date: '',
                dc_generated: false,
                transport_status: 'pending',
                follow_up_time: '',
                pickup_status: 'pending'
            });
            setShowForm(false);
            fetchItems();
        } catch (error) {
            console.error('Failed to create outsource item:', error);
            alert('Failed to create outsource item');
        }
    };

    const handleDelete = async (itemId) => {
        if (window.confirm('Are you sure you want to delete this outsource item?')) {
            try {
                await deleteOutsource(itemId);
                fetchItems();
            } catch (error) {
                console.error('Failed to delete outsource item:', error);
                alert('Failed to delete outsource item');
            }
        }
    };

    // Filter and search logic
    const getFilteredItems = () => {
        return items.filter(item => {
            // Search filter
            const matchesSearch = searchQuery === '' ||
                item.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.vendor?.toLowerCase().includes(searchQuery.toLowerCase());

            // Status filter
            const matchesStatus = statusFilter === 'all' || item.status === statusFilter;

            // Transport filter
            const matchesTransport = transportFilter === 'all' || item.transport_status === transportFilter;

            return matchesSearch && matchesStatus && matchesTransport;
        });
    };

    // Pagination logic
    const filteredItems = getFilteredItems();
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = filteredItems.slice(startIndex, endIndex);

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery, statusFilter, transportFilter]);

    const clearFilters = () => {
        setSearchQuery('');
        setStatusFilter('all');
        setTransportFilter('all');
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'in_progress': return 'bg-blue-100 text-blue-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getTransportColor = (status) => {
        switch (status) {
            case 'delivered': return 'bg-green-100 text-green-800';
            case 'in_transit': return 'bg-blue-100 text-blue-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
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
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Outsource Management</h1>
                    <p className="text-sm sm:text-base text-gray-600">Manage outsourced items and vendors</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2.5 rounded-lg hover:bg-blue-700 transition w-full sm:w-auto text-sm sm:text-base"
                >
                    <Plus size={20} />
                    <span>Add Outsource</span>
                </button>
            </div>

            {/* Search and Filters */}
            <div className="bg-white rounded-lg shadow p-3 sm:p-4">
                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
                    {/* Search */}
                    <div className="col-span-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                            <input
                                type="text"
                                placeholder="Search..."
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
                            <option value="completed">Completed</option>
                        </select>
                    </div>

                    {/* Transport Filter */}
                    <div>
                        <select
                            value={transportFilter}
                            onChange={(e) => setTransportFilter(e.target.value)}
                            className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">Transport</option>
                            <option value="pending">Pending</option>
                            <option value="in_transit">In Transit</option>
                            <option value="delivered">Delivered</option>
                        </select>
                    </div>
                </div>

                {/* Active Filters & Clear */}
                {(searchQuery || statusFilter !== 'all' || transportFilter !== 'all') && (
                    <div className="mt-3 flex items-center justify-between">
                        <span className="text-sm text-gray-600">
                            Showing {filteredItems.length} of {items.length} items
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

            {/* Add Outsource Form */}
            {showForm && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">Add New Outsource Item</h3>
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
                                <label className="block text-sm font-medium text-gray-700 mb-1">Vendor *</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.vendor}
                                    onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Cost</label>
                                <input
                                    type="number"
                                    value={formData.cost}
                                    onChange={(e) => setFormData({ ...formData, cost: parseFloat(e.target.value) })}
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
                                    <option value="pending">Pending</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Transport Status</label>
                                <select
                                    value={formData.transport_status}
                                    onChange={(e) => setFormData({ ...formData, transport_status: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="pending">Pending</option>
                                    <option value="in_transit">In Transit</option>
                                    <option value="delivered">Delivered</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Pickup Status</label>
                                <select
                                    value={formData.pickup_status}
                                    onChange={(e) => setFormData({ ...formData, pickup_status: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="pending">Pending</option>
                                    <option value="scheduled">Scheduled</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
                                <input
                                    type="date"
                                    value={formData.due_date}
                                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Follow Up Time</label>
                                <input
                                    type="datetime-local"
                                    value={formData.follow_up_time}
                                    onChange={(e) => setFormData({ ...formData, follow_up_time: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    id="dc_generated"
                                    checked={formData.dc_generated}
                                    onChange={(e) => setFormData({ ...formData, dc_generated: e.target.checked })}
                                    className="rounded border-gray-300 mr-2"
                                />
                                <label htmlFor="dc_generated" className="text-sm font-medium text-gray-700">DC Generated</label>
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                <textarea
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
                                Create Item
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

            {/* Outsource Items Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transport</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DC</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {paginatedItems.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{item.title}</div>
                                        {item.description && (
                                            <div className="text-xs text-gray-500">{item.description.substring(0, 50)}...</div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">{item.vendor}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-semibold text-gray-900">${item.cost}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(item.status)}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getTransportColor(item.transport_status)}`}>
                                            {item.transport_status || 'pending'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${item.dc_generated ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                            }`}>
                                            {item.dc_generated ? 'Yes' : 'No'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button
                                            onClick={() => handleDelete(item.id)}
                                            className="text-red-600 hover:text-red-900"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {filteredItems.length > 0 && (
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
                                    Showing <span className="font-medium">{startIndex + 1}</span> to <span className="font-medium">{Math.min(endIndex, filteredItems.length)}</span> of{' '}
                                    <span className="font-medium">{filteredItems.length}</span> results
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
                                    {[...Array(Math.min(totalPages, 5))].map((_, i) => {
                                        let pageNum;
                                        if (totalPages <= 5) {
                                            pageNum = i + 1;
                                        } else if (currentPage <= 3) {
                                            pageNum = i + 1;
                                        } else if (currentPage >= totalPages - 2) {
                                            pageNum = totalPages - 4 + i;
                                        } else {
                                            pageNum = currentPage - 2 + i;
                                        }
                                        return (
                                            <button
                                                key={i}
                                                onClick={() => setCurrentPage(pageNum)}
                                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${currentPage === pageNum
                                                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                                    }`}
                                            >
                                                {pageNum}
                                            </button>
                                        );
                                    })}
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

                {filteredItems.length === 0 && (
                    <div className="text-center py-12">
                        <Briefcase className="mx-auto text-gray-400 mb-4" size={48} />
                        <p className="text-gray-500">No outsource items found matching your filters.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Outsource;
