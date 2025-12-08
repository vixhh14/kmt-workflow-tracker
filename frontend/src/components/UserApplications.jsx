import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { Check, X, User, Calendar, MapPin, Phone, Mail, Shield } from 'lucide-react';

const UserApplications = () => {
    const [pendingUsers, setPendingUsers] = useState([]);
    const [units, setUnits] = useState([]);
    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState(null);
    const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);

    // Form state for approval
    const [selectedUnit, setSelectedUnit] = useState('');
    const [selectedMachines, setSelectedMachines] = useState([]);
    const [processing, setProcessing] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [usersRes, unitsRes, machinesRes] = await Promise.all([
                api.get('/admin/pending-users'),
                api.get('/api/units'),
                api.get('/machines/')
            ]);
            setPendingUsers(usersRes.data);
            setUnits(unitsRes.data);
            setMachines(machinesRes.data);
        } catch (error) {
            console.error("Error fetching data:", error);
            setMessage({ type: 'error', text: 'Failed to load data' });
        } finally {
            setLoading(false);
        }
    };

    const handleApproveClick = (user) => {
        setSelectedUser(user);
        setSelectedUnit('');
        setSelectedMachines([]);
        setIsApproveModalOpen(true);
        setMessage({ type: '', text: '' });
    };

    const handleRejectClick = async (user) => {
        if (!window.confirm(`Are you sure you want to reject ${user.username}?`)) return;

        try {
            setProcessing(true);
            await api.post(`/admin/users/${user.username}/reject`);
            setMessage({ type: 'success', text: `User ${user.username} rejected` });
            fetchData(); // Refresh list
        } catch (error) {
            console.error("Error rejecting user:", error);
            setMessage({ type: 'error', text: 'Failed to reject user' });
        } finally {
            setProcessing(false);
        }
    };

    const handleConfirmApprove = async () => {
        if (!selectedUnit) {
            setMessage({ type: 'error', text: 'Please select a unit' });
            return;
        }

        try {
            setProcessing(true);
            const machineTypesStr = selectedMachines.join(',');

            await api.post(`/admin/users/${selectedUser.username}/approve`, {
                unit_id: selectedUnit,
                machine_types: machineTypesStr
            });

            setMessage({ type: 'success', text: `User ${selectedUser.username} approved successfully` });
            setIsApproveModalOpen(false);
            fetchData(); // Refresh list
        } catch (error) {
            console.error("Error approving user:", error);
            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to approve user' });
        } finally {
            setProcessing(false);
        }
    };

    const toggleMachineSelection = (machineName) => {
        if (selectedMachines.includes(machineName)) {
            setSelectedMachines(selectedMachines.filter(m => m !== machineName));
        } else {
            setSelectedMachines([...selectedMachines, machineName]);
        }
    };

    if (loading) return <div className="p-4 text-center">Loading applications...</div>;

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
                <User className="mr-2" /> User Applications
                <span className="ml-2 bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                    {pendingUsers.length} Pending
                </span>
            </h2>

            {message.text && (
                <div className={`mb-4 p-3 rounded ${message.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {message.text}
                </div>
            )}

            {pendingUsers.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No pending applications.</p>
            ) : (
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User Details</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact Info</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registered At</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {pendingUsers.map((user) => (
                                <tr key={user.user_id}>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center">
                                            <div>
                                                <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                                                <div className="text-sm text-gray-500">@{user.username}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm text-gray-900 flex items-center"><Mail size={14} className="mr-1" /> {user.email}</div>
                                        <div className="text-sm text-gray-500 flex items-center"><Phone size={14} className="mr-1" /> {user.contact_number || 'N/A'}</div>
                                        <div className="text-sm text-gray-500 flex items-center"><MapPin size={14} className="mr-1" /> {user.address || 'N/A'}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => handleApproveClick(user)}
                                            className="text-green-600 hover:text-green-900 mr-4 inline-flex items-center"
                                        >
                                            <Check size={16} className="mr-1" /> Approve
                                        </button>
                                        <button
                                            onClick={() => handleRejectClick(user)}
                                            className="text-red-600 hover:text-red-900 inline-flex items-center"
                                        >
                                            <X size={16} className="mr-1" /> Reject
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Approval Modal */}
            {isApproveModalOpen && selectedUser && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-lg w-full p-6">
                        <h3 className="text-lg font-bold mb-4">Approve User: {selectedUser.full_name}</h3>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Assign Unit *</label>
                            <select
                                value={selectedUnit}
                                onChange={(e) => setSelectedUnit(e.target.value)}
                                className="w-full border border-gray-300 rounded-md shadow-sm p-2"
                            >
                                <option value="">Select a Unit</option>
                                {units.map(unit => (
                                    <option key={unit.id} value={unit.id}>{unit.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Assign Machines/Skills</label>
                            <div className="border border-gray-300 rounded-md p-2 max-h-48 overflow-y-auto">
                                {machines.map(machine => (
                                    <label key={machine.id} className="flex items-center p-1 hover:bg-gray-50">
                                        <input
                                            type="checkbox"
                                            checked={selectedMachines.includes(machine.name)}
                                            onChange={() => toggleMachineSelection(machine.name)}
                                            className="mr-2"
                                        />
                                        <span className="text-sm">{machine.name}</span>
                                    </label>
                                ))}
                            </div>
                            <p className="text-xs text-gray-500 mt-1">Selected: {selectedMachines.join(', ') || 'None'}</p>
                        </div>

                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={() => setIsApproveModalOpen(false)}
                                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                                disabled={processing}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmApprove}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                                disabled={processing}
                            >
                                {processing ? 'Processing...' : 'Confirm Approval'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserApplications;
