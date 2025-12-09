import React, { useState, useEffect } from 'react';
import { getCurrentUser } from '../api/services';
import { User, Mail, Briefcase, Calendar } from 'lucide-react';

const Profile = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const response = await getCurrentUser();
            setUser(response.data);
        } catch (err) {
            setError('Failed to load profile');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-center">Loading profile...</div>;

    if (error) return <div className="p-8 text-center text-red-600">{error}</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>

            {/* Profile Info Card */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center space-x-4 mb-6">
                    <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-2xl font-bold text-blue-600">
                            {user?.full_name?.charAt(0) || user?.username?.charAt(0)}
                        </span>
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold">{user?.full_name || 'User'}</h2>
                        <p className="text-gray-500">@{user?.username}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-500">Email</label>
                        <div className="mt-1 flex items-center space-x-2 text-gray-900">
                            <Mail size={18} className="text-gray-400" />
                            <span>{user?.email || 'N/A'}</span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-500">Role</label>
                        <div className="mt-1 flex items-center space-x-2 text-gray-900 capitalize">
                            <Briefcase size={18} className="text-gray-400" />
                            <span>{user?.role}</span>
                        </div>
                    </div>
                    {user?.unit_id && (
                        <div>
                            <label className="block text-sm font-medium text-gray-500">Unit ID</label>
                            <div className="mt-1 text-gray-900">{user.unit_id}</div>
                        </div>
                    )}
                    <div>
                        <label className="block text-sm font-medium text-gray-500">Member Since</label>
                        <div className="mt-1 flex items-center space-x-2 text-gray-900">
                            <Calendar size={18} className="text-gray-400" />
                            <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Info Note */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-700">
                    💡 To change your password, use the <strong>"Change Password"</strong> option in the sidebar menu.
                </p>
            </div>
        </div>
    );
};

export default Profile;
