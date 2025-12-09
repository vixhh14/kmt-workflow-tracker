import React, { useState } from 'react';
import { changePassword } from '../../api/services';
import { Lock, AlertCircle, CheckCircle } from 'lucide-react';
import { validatePasswordFull } from '../../utils/passwordValidation';
import PasswordStrengthMeter from '../../components/PasswordStrengthMeter';
import PasswordInput from '../../components/PasswordInput';

const ChangePassword = () => {
    const [formData, setFormData] = useState({
        oldPassword: '',
        newPassword: '',
        confirmNewPassword: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        // Clear errors when user types
        if (error) setError('');
    };

    // Check if passwords match and are valid for button state
    const isFormValid = () => {
        if (!formData.oldPassword || !formData.newPassword || !formData.confirmNewPassword) {
            return false;
        }
        if (formData.newPassword !== formData.confirmNewPassword) {
            return false;
        }
        const validation = validatePasswordFull(formData.newPassword);
        return validation.isValid;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // Strong password validation
        const passwordValidation = validatePasswordFull(formData.newPassword);
        if (!passwordValidation.isValid) {
            setError(passwordValidation.errors[0]);
            return;
        }

        if (formData.newPassword !== formData.confirmNewPassword) {
            setError('New passwords do not match');
            return;
        }

        setLoading(true);

        try {
            await changePassword({
                current_password: formData.oldPassword,
                new_password: formData.newPassword,
                confirm_new_password: formData.confirmNewPassword
            });
            setSuccess('Password updated successfully');
            setFormData({
                oldPassword: '',
                newPassword: '',
                confirmNewPassword: ''
            });
        } catch (err) {
            console.error('Change password error:', err);
            setError(err.response?.data?.detail || 'Failed to update password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-xl shadow-md">
            <div className="flex items-center space-x-3 mb-6">
                <div className="p-3 bg-blue-100 rounded-full">
                    <Lock className="text-blue-600" size={24} />
                </div>
                <h2 className="text-2xl font-bold text-gray-800">Change Password</h2>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 rounded flex items-start">
                    <AlertCircle className="text-red-500 mt-0.5 mr-2 flex-shrink-0" size={18} />
                    <p className="text-sm text-red-700">{error}</p>
                </div>
            )}

            {success && (
                <div className="mb-4 p-3 bg-green-50 border-l-4 border-green-500 rounded flex items-start">
                    <CheckCircle className="text-green-500 mt-0.5 mr-2 flex-shrink-0" size={18} />
                    <p className="text-sm text-green-700">{success}</p>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <PasswordInput
                    label="Current Password"
                    name="oldPassword"
                    value={formData.oldPassword}
                    onChange={handleChange}
                    placeholder="Enter current password"
                />

                <div>
                    <PasswordInput
                        label="New Password"
                        name="newPassword"
                        value={formData.newPassword}
                        onChange={handleChange}
                        placeholder="Enter strong password"
                    />
                    <PasswordStrengthMeter password={formData.newPassword} />
                </div>

                <div>
                    <PasswordInput
                        label="Confirm New Password"
                        name="confirmNewPassword"
                        value={formData.confirmNewPassword}
                        onChange={handleChange}
                        placeholder="Re-enter new password"
                    />
                    {formData.confirmNewPassword && formData.newPassword !== formData.confirmNewPassword && (
                        <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={loading || !isFormValid()}
                    className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition shadow-md disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center"
                >
                    {loading ? (
                        <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Updating...
                        </>
                    ) : 'Update Password'}
                </button>
            </form>
        </div>
    );
};

export default ChangePassword;

