import React from 'react';
import { validatePassword, getPasswordStrengthInfo, PASSWORD_REQUIREMENTS } from '../utils/passwordValidation';
import { Check, X, Shield } from 'lucide-react';

/**
 * Password Strength Meter Component
 * Displays real-time password strength feedback with requirements checklist
 */
const PasswordStrengthMeter = ({ password, showRequirements = true }) => {
    const validation = validatePassword(password);
    const strengthInfo = getPasswordStrengthInfo(validation.strength);

    // Individual requirement checks
    const requirements = [
        {
            label: `At least ${PASSWORD_REQUIREMENTS.minLength} characters`,
            met: password.length >= PASSWORD_REQUIREMENTS.minLength
        },
        {
            label: 'One uppercase letter (A-Z)',
            met: /[A-Z]/.test(password)
        },
        {
            label: 'One lowercase letter (a-z)',
            met: /[a-z]/.test(password)
        },
        {
            label: 'One number (0-9)',
            met: /[0-9]/.test(password)
        },
        {
            label: 'One special character (!@#$%^&*)',
            met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
        },
    ];

    if (!password) {
        return null;
    }

    return (
        <div className="mt-2 space-y-2">
            {/* Strength Bar */}
            <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${strengthInfo.bgColor} transition-all duration-300`}
                        style={{ width: `${validation.strength}%` }}
                    />
                </div>
                <span className={`text-xs font-medium ${strengthInfo.color} min-w-[50px]`}>
                    {strengthInfo.label}
                </span>
            </div>

            {/* Requirements Checklist */}
            {showRequirements && (
                <div className="bg-gray-50 rounded-lg p-3 space-y-1">
                    <div className="flex items-center gap-1 text-xs text-gray-600 mb-2">
                        <Shield size={14} />
                        <span>Password Requirements:</span>
                    </div>
                    {requirements.map((req, index) => (
                        <div
                            key={index}
                            className={`flex items-center gap-2 text-xs ${req.met ? 'text-green-600' : 'text-gray-500'}`}
                        >
                            {req.met ? (
                                <Check size={14} className="text-green-600" />
                            ) : (
                                <X size={14} className="text-gray-400" />
                            )}
                            <span>{req.label}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default PasswordStrengthMeter;
