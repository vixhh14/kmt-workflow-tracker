"""
Password Validation Utility for Backend
Enforces strong password requirements to prevent breached password warnings
"""
import re
from typing import Tuple, List

# Password Requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Common breached passwords to reject
COMMON_BREACHED_PASSWORDS = {
    'password', 'password1', 'password123', '123456', '12345678', '123456789',
    'qwerty', 'abc123', 'monkey', 'master', 'dragon', 'letmein', 'login',
    'admin', 'admin123', 'welcome', 'welcome1', 'shadow', 'sunshine',
    'princess', 'football', 'baseball', 'iloveyou', 'trustno1', 'hello123',
    'operator', 'operator123', 'supervisor', 'supervisor123', 'planning123',
    'test', 'test123', 'guest', 'guest123', 'changeme', 'changeme123',
}


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength against security requirements.
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    if not password:
        return False, ['Password is required']
    
    # Check minimum length
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f'Password must be at least {PASSWORD_MIN_LENGTH} characters')
    
    # Check maximum length
    if len(password) > PASSWORD_MAX_LENGTH:
        errors.append(f'Password must not exceed {PASSWORD_MAX_LENGTH} characters')
    
    # Check for uppercase
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter (A-Z)')
    
    # Check for lowercase
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter (a-z)')
    
    # Check for number
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one number (0-9)')
    
    # Check for special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append('Password must contain at least one special character (!@#$%^&*...)')
    
    # Check against common breached passwords
    if password.lower() in COMMON_BREACHED_PASSWORDS:
        errors.append('This password is commonly used and may be in data breaches')
    
    return len(errors) == 0, errors


def is_password_valid(password: str) -> bool:
    """Quick check if password meets all requirements."""
    is_valid, _ = validate_password_strength(password)
    return is_valid


def get_password_errors(password: str) -> List[str]:
    """Get list of password validation errors."""
    _, errors = validate_password_strength(password)
    return errors
