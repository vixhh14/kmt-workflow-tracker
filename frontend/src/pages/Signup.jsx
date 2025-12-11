import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Lock, Phone, MapPin, Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react';
import { validatePasswordFull } from '../utils/passwordValidation';
import PasswordStrengthMeter from '../components/PasswordStrengthMeter';
import api from '../api/axios';

const Signup = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        full_name: '',
        contact_number: '+91 ',
    });
    const [errors, setErrors] = useState({});
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitSuccess, setSubmitSuccess] = useState(false);
    const [submitError, setSubmitError] = useState('');

    const validate = () => {
        const newErrors = {};

        if (!formData.full_name) newErrors.full_name = 'Full Name is required';

        // Phone validation: +91 followed by 10 digits
        const phoneRegex = /^\+91 \d{5} \d{5}$/;
        // Or just 10 digits if we strip spaces. The user asked for "+91 XXXXX XXXXX" format.
        // Let's enforce the length. +91 + space + 10 digits = 14 chars (if space after 91)
        // Or +91 + 10 digits = 13 chars.
        // The user said "Placeholder: +91 XXXXX XXXXX".
        // "Validate 10 digits after +91".

        const cleanPhone = formData.contact_number.replace(/\D/g, '');
        // +91 is 2 digits. So total digits should be 12.
        if (!formData.contact_number) {
            newErrors.contact_number = 'Phone Number is required';
        } else if (cleanPhone.length !== 12 || !formData.contact_number.startsWith('+91')) {
            newErrors.contact_number = 'Phone number must be 10 digits after +91';
        }

        if (!formData.email) newErrors.email = 'Email is required';
        if (!formData.username) newErrors.username = 'Username is required';

        // Strong password validation
        const passwordValidation = validatePasswordFull(formData.password);
        if (!passwordValidation.isValid) {
            newErrors.password = passwordValidation.errors[0];
        }

        if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitError('');

        if (validate()) {
            setIsSubmitting(true);
            try {
                // Call API directly instead of storing in session
                const response = await api.post('/auth/signup', {
                    username: formData.username,
                    email: formData.email,
                    password: formData.password,
                    full_name: formData.full_name,
                    contact_number: formData.contact_number
                });

                if (response.data) {
                    setSubmitSuccess(true);
                }
            } catch (error) {
                console.error('Signup error:', error);
                setSubmitError(error.response?.data?.detail || 'Registration failed. Please try again.');
            } finally {
                setIsSubmitting(false);
            }
        }
    };

    if (submitSuccess) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 text-center">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6">
                        <CheckCircle className="text-green-600" size={40} />
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-4">Registration Successful!</h2>
                    <p className="text-gray-600 mb-8 text-lg">
                        Your account has been created and is currently <strong>Pending Approval</strong>.
                        <br /><br />
                        Please wait for an administrator to approve your account. You will receive an email notification once approved.
                    </p>
                    <button
                        onClick={() => navigate('/login')}
                        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition shadow-md"
                    >
                        Return to Login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4 sm:p-6 lg:p-8">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-6 sm:p-8">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                        <User className="text-blue-600" size={32} />
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900">Create Account</h1>
                    <p className="text-gray-600 mt-2">Join the workflow tracker system</p>
                </div>

                {submitError && (
                    <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 flex items-start">
                        <AlertCircle className="text-red-500 mt-0.5 mr-3" size={20} />
                        <p className="text-red-700">{submitError}</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

                        {/* Full Name */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                            <div className="relative">
                                <User className="absolute left-3 top-3 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.full_name}
                                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    className={`block w-full pl-10 pr-3 py-2.5 border ${errors.full_name ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                                    placeholder="John Doe"
                                />
                            </div>
                            {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name}</p>}
                        </div>

                        {/* Phone Number */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
                            <div className="relative">
                                <Phone className="absolute left-3 top-3 text-gray-400" size={20} />
                                <input
                                    type="tel"
                                    value={formData.contact_number}
                                    onChange={(e) => {
                                        let val = e.target.value;
                                        // Ensure +91 prefix
                                        if (!val.startsWith('+91 ')) {
                                            val = '+91 ' + val.replace(/^\+91\s?/, '').replace(/^\+91/, '');
                                        }

                                        // Allow only digits after prefix
                                        const suffix = val.substring(4).replace(/\D/g, '');

                                        // Limit to 10 digits
                                        if (suffix.length <= 10) {
                                            // Optional: Add space after 5 digits for "XXXXX XXXXX" look?
                                            // The user asked for placeholder "+91 XXXXX XXXXX".
                                            // Let's just keep it simple digits for now to avoid cursor jumping issues, 
                                            // or implement simple formatting if easy.
                                            // Let's just stick to digits for robustness.
                                            setFormData({ ...formData, contact_number: '+91 ' + suffix });
                                        }
                                    }}
                                    className={`block w-full pl-10 pr-3 py-2.5 border ${errors.contact_number ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                                    placeholder="+91 XXXXX XXXXX"
                                />
                            </div>
                            {errors.contact_number && <p className="text-red-500 text-xs mt-1">{errors.contact_number}</p>}
                        </div>

                        {/* Email */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className={`block w-full pl-10 pr-3 py-2.5 border ${errors.email ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                                    placeholder="john@example.com"
                                />
                            </div>
                            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
                        </div>

                        {/* Username */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
                            <div className="relative">
                                <User className="absolute left-3 top-3 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    className={`block w-full pl-10 pr-3 py-2.5 border ${errors.username ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                                    placeholder="johndoe123"
                                />
                            </div>
                            {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username}</p>}
                        </div>

                        {/* Password */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className={`block w-full pl-10 pr-10 py-2.5 border ${errors.password ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                                    placeholder="••••••••"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
                            <PasswordStrengthMeter password={formData.password} />
                        </div>

                        {/* Confirm Password */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password *</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                                <input
                                    type={showConfirmPassword ? "text" : "password"}
                                    value={formData.confirmPassword}
                                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                    className={`block w-full pl-10 pr-10 py-2.5 border ${errors.confirmPassword ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                                    placeholder="••••••••"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                                >
                                    {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                            {errors.confirmPassword && <p className="text-red-500 text-xs mt-1">{errors.confirmPassword}</p>}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className={`w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition shadow-md hover:shadow-lg transform active:scale-[0.98] ${isSubmitting ? 'opacity-70 cursor-not-allowed' : ''}`}
                    >
                        {isSubmitting ? 'Creating Account...' : 'Create Account'}
                    </button>

                    <div className="text-center text-sm text-gray-600">
                        Already have an account?{' '}
                        <a href="/login" className="text-blue-600 hover:text-blue-800 font-semibold transition-colors">
                            Sign In
                        </a>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Signup;
