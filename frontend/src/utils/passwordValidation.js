/**
 * Password Validation Utility
 * Enforces strong password requirements to prevent breached password warnings
 */

// Password Requirements
export const PASSWORD_REQUIREMENTS = {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumber: true,
    requireSpecial: true,
};

// Regex patterns for validation
const PATTERNS = {
    uppercase: /[A-Z]/,
    lowercase: /[a-z]/,
    number: /[0-9]/,
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/,
};

/**
 * Validate password strength
 * @param {string} password - The password to validate
 * @returns {Object} - { isValid: boolean, errors: string[], strength: number }
 */
export const validatePassword = (password) => {
    const errors = [];
    let strength = 0;

    if (!password) {
        return { isValid: false, errors: ['Password is required'], strength: 0 };
    }

    // Check minimum length
    if (password.length < PASSWORD_REQUIREMENTS.minLength) {
        errors.push(`Password must be at least ${PASSWORD_REQUIREMENTS.minLength} characters`);
    } else {
        strength += 20;
    }

    // Check maximum length
    if (password.length > PASSWORD_REQUIREMENTS.maxLength) {
        errors.push(`Password must not exceed ${PASSWORD_REQUIREMENTS.maxLength} characters`);
    }

    // Check for uppercase
    if (PASSWORD_REQUIREMENTS.requireUppercase && !PATTERNS.uppercase.test(password)) {
        errors.push('Password must contain at least one uppercase letter (A-Z)');
    } else if (PATTERNS.uppercase.test(password)) {
        strength += 20;
    }

    // Check for lowercase
    if (PASSWORD_REQUIREMENTS.requireLowercase && !PATTERNS.lowercase.test(password)) {
        errors.push('Password must contain at least one lowercase letter (a-z)');
    } else if (PATTERNS.lowercase.test(password)) {
        strength += 20;
    }

    // Check for number
    if (PASSWORD_REQUIREMENTS.requireNumber && !PATTERNS.number.test(password)) {
        errors.push('Password must contain at least one number (0-9)');
    } else if (PATTERNS.number.test(password)) {
        strength += 20;
    }

    // Check for special character
    if (PASSWORD_REQUIREMENTS.requireSpecial && !PATTERNS.special.test(password)) {
        errors.push('Password must contain at least one special character (!@#$%^&*...)');
    } else if (PATTERNS.special.test(password)) {
        strength += 20;
    }

    // Bonus for extra length
    if (password.length >= 12) {
        strength = Math.min(strength + 10, 100);
    }

    return {
        isValid: errors.length === 0,
        errors,
        strength,
    };
};

/**
 * Get password strength label and color
 * @param {number} strength - Strength value 0-100
 * @returns {Object} - { label: string, color: string, bgColor: string }
 */
export const getPasswordStrengthInfo = (strength) => {
    if (strength < 40) {
        return { label: 'Weak', color: 'text-red-600', bgColor: 'bg-red-500' };
    } else if (strength < 60) {
        return { label: 'Fair', color: 'text-orange-600', bgColor: 'bg-orange-500' };
    } else if (strength < 80) {
        return { label: 'Good', color: 'text-yellow-600', bgColor: 'bg-yellow-500' };
    } else {
        return { label: 'Strong', color: 'text-green-600', bgColor: 'bg-green-500' };
    }
};

/**
 * Check if password appears in common breached password lists
 * This is a basic check for the most commonly breached passwords
 * @param {string} password - The password to check
 * @returns {boolean} - True if password is commonly breached
 */
export const isCommonlyBreachedPassword = (password) => {
    const commonBreached = [
        'password', 'password1', 'password123', '123456', '12345678', '123456789',
        'qwerty', 'abc123', 'monkey', 'master', 'dragon', 'letmein', 'login',
        'admin', 'admin123', 'welcome', 'welcome1', 'shadow', 'sunshine',
        'princess', 'football', 'baseball', 'iloveyou', 'trustno1', 'hello123',
        'operator', 'operator123', 'supervisor', 'supervisor123', 'planning123',
        'test', 'test123', 'guest', 'guest123', 'changeme', 'changeme123',
    ];
    
    return commonBreached.includes(password.toLowerCase());
};

/**
 * Full password validation including breach check
 * @param {string} password - The password to validate
 * @returns {Object} - Complete validation result
 */
export const validatePasswordFull = (password) => {
    const result = validatePassword(password);
    
    // Add breach check
    if (result.isValid && isCommonlyBreachedPassword(password)) {
        result.isValid = false;
        result.errors.push('This password is commonly used and may be in data breaches. Please choose a unique password.');
        result.strength = Math.min(result.strength, 20);
    }
    
    return result;
};

export default {
    validatePassword,
    validatePasswordFull,
    getPasswordStrengthInfo,
    isCommonlyBreachedPassword,
    PASSWORD_REQUIREMENTS,
};
