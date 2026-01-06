import React, { useState, useEffect } from 'react';
import { getCurrentUser, updateProfile } from '../api/services';
import { User, Mail, Briefcase, Calendar, Phone, Edit2, Check, X, Shield, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Profile = () => {
    const { user: authUser, setUser: setAuthUser } = useAuth();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isEditing, setIsEditing] = useState(false);
    const [saving, setSaving] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        username: '',
        contact_number: '',
        security_question: '',
        security_answer: ''
    });

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            setLoading(true);
            const response = await getCurrentUser();
            const data = response.data;
            setUser(data);
            setFormData({
                full_name: data.full_name || '',
                email: data.email || '',
                username: data.username || '',
                contact_number: data.contact_number || '',
                security_question: data.security_question || '',
                security_answer: '' // Don't show existing answer for security
            });
        } catch (err) {
            setError('Failed to load profile. Please refresh the page.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        setSuccess('');

        try {
            // Prepare payload - only send security answer if it's filled
            const payload = { ...formData };
            if (!payload.security_answer) {
                delete payload.security_answer;
            }

            const response = await updateProfile(payload);
            setSuccess(response.data.message || 'Profile updated successfully!');

            // Refresh local user state
            const updatedProfile = await getCurrentUser();
            setUser(updatedProfile.data);

            // Sync with AuthContext if username or full_name changed
            if (setAuthUser) {
                setAuthUser({
                    ...authUser,
                    username: updatedProfile.data.username,
                    full_name: updatedProfile.data.full_name,
                    email: updatedProfile.data.email
                });
            }

            setIsEditing(false);
        } catch (err) {
            console.error('Profile update failed:', err);
            setError(err.response?.data?.detail || 'Failed to update profile. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const handleCancel = () => {
        // Reset form data to current user data
        setFormData({
            full_name: user?.full_name || '',
            email: user?.email || '',
            username: user?.username || '',
            contact_number: user?.contact_number || '',
            security_question: user?.security_question || '',
            security_answer: ''
        });
        setIsEditing(false);
        setError('');
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
    );

    return (
        <div className="max-w-4xl mx-auto space-y-6 pb-12 animate-fade-in">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">My Profile</h1>
                {!isEditing && (
                    <button
                        onClick={() => setIsEditing(true)}
                        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow-sm font-medium"
                    >
                        <Edit2 size={18} />
                        <span>Edit Profile</span>
                    </button>
                )}
            </div>

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-3">
                    <AlertCircle size={20} className="flex-shrink-0" />
                    <p className="text-sm font-medium">{error}</p>
                </div>
            )}

            {success && (
                <div className="p-4 bg-green-50 border border-green-200 text-green-700 rounded-xl flex items-center gap-3">
                    <CheckCircle size={20} className="flex-shrink-0" />
                    <p className="text-sm font-medium">{success}</p>
                </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                {/* Header/Cover aspect */}
                <div className="h-32 bg-gradient-to-r from-blue-500 to-blue-700"></div>

                <div className="px-6 pb-8">
                    {/* Profile Avatar */}
                    <div className="relative -mt-12 mb-6 flex justify-center sm:justify-start">
                        <div className="h-24 w-24 bg-white p-1 rounded-full shadow-md">
                            <div className="h-full w-full bg-blue-100 rounded-full flex items-center justify-center text-3xl font-bold text-blue-600">
                                {user?.full_name?.charAt(0) || user?.username?.charAt(0)}
                            </div>
                        </div>
                    </div>

                    {!isEditing ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <section className="space-y-6">
                                <div>
                                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Basic Information</h3>
                                    <div className="space-y-4">
                                        <div className="flex items-start gap-3">
                                            <User className="text-gray-400 mt-0.5" size={20} />
                                            <div>
                                                <p className="text-xs text-gray-500 font-medium">Full Name</p>
                                                <p className="text-gray-900 font-semibold text-lg">{user?.full_name || 'N/A'}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-3">
                                            <Mail className="text-gray-400 mt-0.5" size={20} />
                                            <div>
                                                <p className="text-xs text-gray-500 font-medium">Email Address</p>
                                                <p className="text-gray-900 font-medium">{user?.email || 'N/A'}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-3">
                                            <Phone className="text-gray-400 mt-0.5" size={20} />
                                            <div>
                                                <p className="text-xs text-gray-500 font-medium">Contact Number</p>
                                                <p className="text-gray-900 font-medium">{user?.contact_number || 'N/A'}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>

                            <section className="space-y-6">
                                <div>
                                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">System Details</h3>
                                    <div className="space-y-4">
                                        <div className="flex items-start gap-3">
                                            <Briefcase className="text-gray-400 mt-0.5" size={20} />
                                            <div>
                                                <p className="text-xs text-gray-500 font-medium">System Role</p>
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 uppercase tracking-wide mt-1">
                                                    {(user?.role || 'user').replace('_', ' ')}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-3">
                                            <Calendar className="text-gray-400 mt-0.5" size={20} />
                                            <div>
                                                <p className="text-xs text-gray-500 font-medium">Member Since</p>
                                                <p className="text-gray-900 font-medium">
                                                    {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' }) : 'N/A'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-start gap-3">
                                            <Shield className="text-gray-400 mt-0.5" size={20} />
                                            <div>
                                                <p className="text-xs text-gray-500 font-medium">Security Question</p>
                                                <p className="text-gray-700 italic">{user?.security_question ? `"${user.security_question}"` : 'Not set (Required for password recovery)'}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        </div>
                    ) : (
                        <form onSubmit={handleSave} className="space-y-8 max-w-2xl">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="block text-sm font-bold text-gray-700">Full Name</label>
                                    <input
                                        type="text"
                                        name="full_name"
                                        value={formData.full_name}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-sm font-bold text-gray-700">Username</label>
                                    <input
                                        type="text"
                                        name="username"
                                        value={formData.username}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-sm font-bold text-gray-700">Email Address</label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-sm font-bold text-gray-700">Contact Number</label>
                                    <input
                                        type="text"
                                        name="contact_number"
                                        value={formData.contact_number}
                                        onChange={handleInputChange}
                                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all outline-none"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="p-6 bg-blue-50 rounded-2xl border border-blue-100 space-y-6">
                                <h4 className="text-blue-800 font-bold flex items-center gap-2">
                                    <Shield size={18} />
                                    Security Credentials (Password Recovery)
                                </h4>
                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="block text-sm font-bold text-blue-700">Security Question</label>
                                        <input
                                            type="text"
                                            name="security_question"
                                            placeholder="e.g., What was your first pet's name?"
                                            value={formData.security_question}
                                            onChange={handleInputChange}
                                            className="w-full px-4 py-3 bg-white border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-sm font-bold text-blue-700">Security Answer</label>
                                        <input
                                            type="password"
                                            name="security_answer"
                                            placeholder="Leave blank to keep current answer"
                                            value={formData.security_answer}
                                            onChange={handleInputChange}
                                            className="w-full px-4 py-3 bg-white border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 transition-all outline-none"
                                        />
                                        <p className="text-[10px] text-blue-500 font-medium">This answer is required to reset your password if you forget it.</p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col sm:flex-row gap-4 pt-4">
                                <button
                                    type="submit"
                                    disabled={saving}
                                    className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition font-bold disabled:opacity-50"
                                >
                                    {saving ? 'Saving...' : (
                                        <>
                                            <Check size={20} />
                                            <span>Update Profile</span>
                                        </>
                                    )}
                                </button>
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    className="flex-1 flex items-center justify-center gap-2 bg-gray-100 text-gray-700 px-6 py-3 rounded-xl hover:bg-gray-200 transition font-bold"
                                >
                                    <X size={20} />
                                    <span>Cancel</span>
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>

            {/* Info Note */}
            {!isEditing && (
                <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 flex items-start gap-4">
                    <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                        <Shield size={20} />
                    </div>
                    <div>
                        <p className="text-sm text-indigo-900 font-medium">Keep your profile updated</p>
                        <p className="text-xs text-indigo-700 mt-1 leading-relaxed">
                            Updating your email and contact number ensures the administration can reach you. Setting your security question is mandatory for self-service password recovery.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Profile;
