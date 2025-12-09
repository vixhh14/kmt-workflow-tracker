import React, { useState, useEffect } from 'react';
import { getCurrentUser, changePassword } from '../api/services';
import { User, Mail, Briefcase, Calendar, Lock, AlertCircle, Check } from 'lucide-react';
import PasswordStrengthMeter from '../components/PasswordStrengthMeter';
import PasswordInput from '../components/PasswordInput';

const Profile = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Password form state
    const [passwords, setPasswords] = useState({
        current_password: '',
        new_password: '',
        confirm_new_password: ''
    });
    const [changingPassword, setChangingPassword] = useState(false);

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

    const handlePasswordInputChange = (e) => {
        setPasswords({ ...passwords, [e.target.name]: e.target.value });
        if (error) setError('');
    };

    // Check if passwords match for button state
    const isPasswordFormValid = () => {
        if (!passwords.current_password || !passwords.new_password || !passwords.confirm_new_password) {
            return false;
        }
        return passwords.new_password === passwords.confirm_new_password;
    };

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (passwords.new_password !== passwords.confirm_new_password) {
            setError('New passwords do not match');
            return;
        }

        setChangingPassword(true);
        try {
            await changePassword(passwords);
            setSuccess('Password changed successfully');
            setPasswords({ current_password: '', new_password: '', confirm_new_password: '' });
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to change password');
        } finally {
            setChangingPassword(false);
        }
    };

    if (loading) return <div className="p-8 text-center">Loading profile...</div>;

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

            {/* Change Password Card */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center space-x-2 mb-4">
                    <Lock className="text-gray-900" size={20} />
                    <h2 className="text-lg font-semibold text-gray-900">Change Password</h2>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center">
                        <AlertCircle size={18} className="mr-2" />
                        {error}
                    </div>
                )}
                {success && (
                    <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-lg flex items-center">
                        <Check size={18} className="mr-2" />
                        {success}
                    </div>
                )}

                <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
                    <PasswordInput
                        label="Current Password"
                        name="current_password"
                        value={passwords.current_password}
                        onChange={handlePasswordInputChange}
                        placeholder="Enter current password"
                    />
                    <div>
                        <PasswordInput
                            label="New Password"
                            name="new_password"
                            value={passwords.new_password}
                            onChange={handlePasswordInputChange}
                            placeholder="Enter new password"
                        />
                        <div className="mt-2">
                            <PasswordStrengthMeter password={passwords.new_password} />
                        </div>
                    </div>
                    <div>
                        <PasswordInput
                            label="Confirm New Password"
                            name="confirm_new_password"
                            value={passwords.confirm_new_password}
                            onChange={handlePasswordInputChange}
                            placeholder="Re-enter new password"
                        />
                        {passwords.confirm_new_password && passwords.new_password !== passwords.confirm_new_password && (
                            <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                        )}
                    </div>
                    <button
                        type="submit"
                        disabled={changingPassword || !isPasswordFormValid()}
                        className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                    >
                        {changingPassword ? 'Updating...' : 'Update Password'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Profile;

