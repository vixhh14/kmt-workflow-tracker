import React, { useState, useEffect } from 'react';
import { getOutsource } from '../../api/services';
import { useAuth } from '../../context/AuthContext';
import { Briefcase, Clock, Truck, Package, CheckCircle } from 'lucide-react';

const OutsourceVendorDashboard = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();

    useEffect(() => {
        fetchItems();
    }, []);

    const fetchItems = async () => {
        try {
            setLoading(true);
            const response = await getOutsource();
            // In a real app, filter by vendor name matching the logged-in user
            // For now, show all items
            setItems(response.data);
        } catch (error) {
            console.error('Failed to fetch outsource items:', error);
        } finally {
            setLoading(false);
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

    const pendingItems = items.filter(i => i.status === 'pending');
    const inProgressItems = items.filter(i => i.status === 'in_progress');
    const completedItems = items.filter(i => i.status === 'completed');

    // New tracking stats
    const dcGenerated = items.filter(i => i.dc_generated).length;
    const inTransit = items.filter(i => i.transport_status === 'in_transit').length;
    const readyForPickup = items.filter(i => i.pickup_status === 'scheduled' || i.pickup_status === 'completed').length;

    // Group items by project
    const projectGroups = items.reduce((acc, item) => {
        const project = item.project || 'No Project';
        if (!acc[project]) {
            acc[project] = {
                total: 0,
                pending: 0,
                inProgress: 0,
                completed: 0
            };
        }
        acc[project].total++;
        if (item.status === 'pending') acc[project].pending++;
        if (item.status === 'in_progress') acc[project].inProgress++;
        if (item.status === 'completed') acc[project].completed++;
        return acc;
    }, {});

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Vendor Dashboard</h1>
                <p className="text-gray-600">Welcome, {user?.full_name || user?.username}!</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Total Items</p>
                            <p className="text-3xl font-bold text-gray-900">{items.length}</p>
                        </div>
                        <Briefcase className="text-blue-500" size={32} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">In Progress</p>
                            <p className="text-3xl font-bold text-blue-600">{inProgressItems.length}</p>
                        </div>
                        <Clock className="text-blue-500" size={32} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">DC Generated</p>
                            <p className="text-3xl font-bold text-purple-600">{dcGenerated}</p>
                        </div>
                        <CheckCircle className="text-purple-500" size={32} />
                    </div>
                </div>
            </div>

            {/* Tracking Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">In Transit</p>
                            <p className="text-2xl font-bold text-blue-600">{inTransit}</p>
                        </div>
                        <Truck className="text-blue-500" size={28} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Ready for Pickup</p>
                            <p className="text-2xl font-bold text-orange-600">{readyForPickup}</p>
                        </div>
                        <Package className="text-orange-500" size={28} />
                    </div>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">Completed</p>
                            <p className="text-2xl font-bold text-green-600">{completedItems.length}</p>
                        </div>
                        <CheckCircle className="text-green-500" size={28} />
                    </div>
                </div>
            </div>

            {/* Project-wise Overview */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Project-wise Overview</h3>
                <div className="space-y-3">
                    {Object.entries(projectGroups).map(([project, stats]) => (
                        <div key={project} className="p-4 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="font-semibold text-gray-900">{project}</h4>
                                <span className="text-2xl font-bold text-blue-600">{stats.total}</span>
                            </div>
                            <div className="flex items-center space-x-4 text-sm">
                                <div className="flex items-center space-x-1">
                                    <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                                    <span className="text-gray-600">Pending: {stats.pending}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                    <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                                    <span className="text-gray-600">In Progress: {stats.inProgress}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                                    <span className="text-gray-600">Completed: {stats.completed}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                    {items.length === 0 && (
                        <p className="text-gray-500 text-sm text-center py-4">No items to display</p>
                    )}
                </div>
            </div>

            {/* My Outsource Items */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                    <h3 className="text-lg font-semibold">My Outsource Items</h3>
                </div>
                <div className="divide-y">
                    {items.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                            No outsource items assigned yet.
                        </div>
                    ) : (
                        items.map((item) => (
                            <div key={item.id} className="p-6 hover:bg-gray-50">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-3 mb-2">
                                            <h4 className="font-semibold text-gray-900">{item.title}</h4>
                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(item.status)}`}>
                                                {item.status.replace('_', ' ')}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-3">{item.description}</p>

                                        {/* Tracking Information */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                            <div>
                                                <span className="text-gray-500">Vendor:</span>
                                                <p className="font-medium text-gray-900">{item.vendor}</p>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Cost:</span>
                                                <p className="font-semibold text-gray-900">${item.cost}</p>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">DC Generated:</span>
                                                <p className={`font-medium ${item.dc_generated ? 'text-green-600' : 'text-gray-400'}`}>
                                                    {item.dc_generated ? 'Yes' : 'No'}
                                                </p>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Transport:</span>
                                                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getTransportColor(item.transport_status)}`}>
                                                    {item.transport_status || 'pending'}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Additional Info */}
                                        <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                                            {item.pickup_status && (
                                                <>
                                                    <span>Pickup: <span className="font-medium text-gray-700">{item.pickup_status}</span></span>
                                                    <span>•</span>
                                                </>
                                            )}
                                            {item.follow_up_time && (
                                                <span>Follow-up: <span className="font-medium text-gray-700">{new Date(item.follow_up_time).toLocaleDateString()}</span></span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default OutsourceVendorDashboard;
