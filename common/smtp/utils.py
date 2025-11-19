"""
SMTP Encryption Utilities
Encrypts/decrypts SMTP passwords using user-specific keys
"""

import hashlib
import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import User


def generate_user_key(user: User) -> bytes:
    """
    Generate a unique encryption key for a specific user
    Uses a combination of user ID, username, and Django SECRET_KEY
    to create a deterministic but secure key
    
    Args:
        user: Django User object
        
    Returns:
        bytes: 32-byte key suitable for Fernet encryption
    """
    # Create a unique string for this user
    user_string = f"{user.id}_{user.username}_{settings.SECRET_KEY}"
    
    # Hash it to get a consistent 32-byte key
    key_hash = hashlib.sha256(user_string.encode('utf-8')).digest()
    
    # Convert to base64 for Fernet (Fernet needs URL-safe base64)
    key = base64.urlsafe_b64encode(key_hash)
    
    return key


def encrypt_password(password: str, user: User) -> str:
    """
    Encrypt a password using user-specific key
    
    Args:
        password: Plain text password
        user: Django User object (for key generation)
        
    Returns:
        str: Encrypted password (base64 encoded)
    """
    if not password:
        return ""
    
    try:
        key = generate_user_key(user)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(password.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        # If encryption fails, log error but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error encrypting password: {e}")
        return password  # Return original if encryption fails


def decrypt_password(encrypted_password: str, user: User) -> str:
    """
    Decrypt a password using user-specific key
    
    Args:
        encrypted_password: Encrypted password (base64 encoded)
        user: Django User object (for key generation)
        
    Returns:
        str: Decrypted password
        
    Note:
        If decryption fails, assumes password is unencrypted (backward compatibility)
    """
    if not encrypted_password:
        return ""
    
    try:
        key = generate_user_key(user)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        # If decryption fails, it might be an old unencrypted password
        # Try to detect if it's encrypted or not
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if it looks like Fernet encrypted (base64, starts with gAAAA)
        if encrypted_password.startswith('gAAAA'):
            # It's encrypted but decryption failed - might be wrong user
            logger.error(f"Failed to decrypt password for user {user.username}: {e}")
            raise ValueError("Password decryption failed. Password may have been encrypted by a different user.")
        else:
            # It's probably unencrypted (backward compatibility)
            logger.warning(f"Password appears to be unencrypted, returning as-is: {e}")
            return encrypted_password

