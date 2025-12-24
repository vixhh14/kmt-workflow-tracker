import React, { useState, useEffect } from 'react';
import { getPendingUsers, getUnits, approveUser, rejectUser } from '../../api/services';
import { Check, X, UserCheck, AlertCircle, Briefcase, User } from 'lucide-react';
import { ROLE_LABELS } from '../../constants/roles';

const UserApprovals = () => {
    const [users, setUsers] = useState([]);
    const [units, setUnits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');
    const [selectedRoles, setSelectedRoles] = useState({});
    const [selectedUnits, setSelectedUnits] = useState({});
    const [processing, setProcessing] = useState({});

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (users.length > 0) {
            const initialRoles = {};
            users.forEach(u => {
                initialRoles[u.username] = u.role || 'operator';
            });
            setSelectedRoles(initialRoles);
        }
    }, [users]);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError('');

            const [usersRes, unitsRes] = await Promise.all([
                getPendingUsers(),
                getUnits()
            ]);

            setUsers(Array.isArray(usersRes?.data) ? usersRes.data : []);
            setUnits(Array.isArray(unitsRes?.data) ? unitsRes.data : []);
        } catch (err) {
            console.error('Error fetching approval data:', err);
            setError(err.response?.data?.detail || 'Failed to load pending users or units.');
            setUsers([]);
            setUnits([]);
        } finally {
            setLoading(false);
        }
    };

    const handleUnitChange = (username, unitId) => {
        setSelectedUnits(prev => ({
            ...prev,
            [username]: unitId
        }));
    };


    const handleRoleChange = (username, role) => {
        setSelectedRoles(prev => ({
            ...prev,
            [username]: role
        }));
    };

    const handleApprove = async (username) => {
        const unitId = selectedUnits[username];
        const role = selectedRoles[username];

        if (!unitId) {
            setError(`Please select a unit for ${username} before approving.`);
            return;
        }

        if (!role) {
            setError(`Please select a role for ${username} before approving.`);
            return;
        }

        setProcessing(prev => ({ ...prev, [username]: 'approving' }));
        setError('');
        setSuccessMsg('');

        try {
            await approveUser(username, unitId, role);
            setSuccessMsg(`User ${username} approved successfully as ${role}.`);
            // Remove user from list
            setUsers(prev => prev.filter(u => u.username !== username));
            // Clear selection
            const newUnits = { ...selectedUnits };
            delete newUnits[username];
            setSelectedUnits(newUnits);

            const newRoles = { ...selectedRoles };
            delete newRoles[username];
            setSelectedRoles(newRoles);

        } catch (err) {
            console.error('Approval error:', err);
            setError(err.response?.data?.detail || `Failed to approve ${username}`);
        } finally {
            setProcessing(prev => ({ ...prev, [username]: null }));
        }
    };

    // ... handleReject ...

    // ... render ...

    const handleReject = async (username) => {
        if (!window.confirm(`Are you sure you want to reject ${username}?`)) return;

        setProcessing(prev => ({ ...prev, [username]: 'rejecting' }));
        setError('');
        setSuccessMsg('');

        try {
            await rejectUser(username);
            setSuccessMsg(`User ${username} rejected.`);
            setUsers(prev => prev.filter(u => u.username !== username));
        } catch (err) {
            console.error('Rejection error:', err);
            setError(err.response?.data?.detail || `Failed to reject ${username}`);
        } finally {
            setProcessing(prev => ({ ...prev, [username]: null }));
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="p-4 sm:p-6 max-w-7xl mx-auto">
            <div className="flex items-center space-x-3 mb-6">
                <div className="p-3 bg-blue-100 rounded-full">
                    <UserCheck className="text-blue-600" size={24} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Pending Approvals</h1>
                    <p className="text-gray-500 text-sm">Review and assign units to new signups</p>
                </div>
            </div>

            {error && (
                <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start animate-fade-in">
                    <AlertCircle className="text-red-500 mt-0.5 mr-2 flex-shrink-0" size={20} />
                    <p className="text-red-700 font-medium">{error}</p>
                </div>
            )}

            {successMsg && (
                <div className="mb-4 p-4 bg-green-50 border-l-4 border-green-500 rounded-lg flex items-start animate-fade-in">
                    <Check className="text-green-500 mt-0.5 mr-2 flex-shrink-0" size={20} />
                    <p className="text-green-700 font-medium">{successMsg}</p>
                </div>
            )}

            {users.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
                    <UserCheck className="mx-auto text-gray-300 mb-4" size={48} />
                    <h3 className="text-lg font-medium text-gray-900">No Pending Requests</h3>
                    <p className="text-gray-500 mt-1">All caught up! There are no new signups waiting for approval.</p>
                </div>
            ) : (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User Details</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role & Skills</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assign Unit</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {users.map((user) => (
                                    <tr key={user.username} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                                                    <User className="text-blue-600" size={20} />
                                                </div>
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                                                    <div className="text-sm text-gray-500">@{user.username}</div>
                                                    <div className="text-xs text-gray-400">{user.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col space-y-2">
                                                <select
                                                    value={selectedRoles[user.username] || user.role || 'operator'}
                                                    onChange={(e) => handleRoleChange(user.username, e.target.value)}
                                                    className="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 border p-1"
                                                >
                                                    {Object.entries(ROLE_LABELS).map(([value, label]) => (
                                                        <option key={value} value={value}>{label}</option>
                                                    ))}
                                                </select>

                                                {user.machine_types && String(user.machine_types).length > 0 && (
                                                    <div className="flex flex-wrap gap-1">
                                                        {String(user.machine_types).split(',').map((skill, idx) => (
                                                            <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                                                {skill.trim()}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center space-x-2">
                                                <Briefcase size={16} className="text-gray-400" />
                                                <select
                                                    value={selectedUnits[user.username] || ''}
                                                    onChange={(e) => handleUnitChange(user.username, e.target.value)}
                                                    className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md border"
                                                >
                                                    <option value="" disabled>Select Unit</option>
                                                    {units.map((unit) => (
                                                        <option key={unit.id} value={unit.id}>
                                                            {unit.name}
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex justify-end space-x-3">
                                                <button
                                                    onClick={() => handleReject(user.username)}
                                                    disabled={processing[user.username]}
                                                    className="text-red-600 hover:text-red-900 disabled:opacity-50 transition-colors flex items-center"
                                                    title="Reject"
                                                >
                                                    {processing[user.username] === 'rejecting' ? (
                                                        <span className="animate-spin h-4 w-4 border-2 border-red-600 border-t-transparent rounded-full mr-1"></span>
                                                    ) : (
                                                        <X size={18} className="mr-1" />
                                                    )}
                                                    Reject
                                                </button>
                                                <button
                                                    onClick={() => handleApprove(user.username)}
                                                    disabled={processing[user.username] || !selectedUnits[user.username]}
                                                    className={`
                                                        flex items-center px-3 py-1.5 rounded-md text-white transition-colors
                                                        ${!selectedUnits[user.username]
                                                            ? 'bg-gray-300 cursor-not-allowed'
                                                            : 'bg-green-600 hover:bg-green-700 shadow-sm'}
                                                    `}
                                                    title={!selectedUnits[user.username] ? "Select a unit first" : "Approve"}
                                                >
                                                    {processing[user.username] === 'approving' ? (
                                                        <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-1"></span>
                                                    ) : (
                                                        <Check size={18} className="mr-1" />
                                                    )}
                                                    Approve
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserApprovals;
