# Common utility functions for the Urban Mobility Backend System

import random
import string
import bcrypt

def generate_id(length=8):
    """Generate a random alphanumeric ID of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, password):
    """Check a hashed password against a plain password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Note: For encryption/decryption, use EncryptionHandler from encryption.py
# Note: For validation, use validation functions from validation.py
# Note: For logging, use EncryptedLogger from logging_handler.py

