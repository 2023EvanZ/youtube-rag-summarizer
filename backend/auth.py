import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime
from typing import Optional, Dict
import os
from dotenv import load_dotenv

from .supabase_db import SupabaseUserDB

load_dotenv()

# Use Argon2 for password hashing
ph = PasswordHasher()

# Get default admin credentials from environment variables
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")

def init_default_admin():
    """Create default admin user if it doesn't exist"""
    user = SupabaseUserDB.get_user_by_username(DEFAULT_ADMIN_USERNAME)
    if not user:
        hashed = ph.hash(DEFAULT_ADMIN_PASSWORD)
        success, result = SupabaseUserDB.create_user(
            DEFAULT_ADMIN_USERNAME,
            DEFAULT_ADMIN_EMAIL,
            hashed,
            is_admin=True
        )
        if success:
            print(f"✅ Default admin user created: {DEFAULT_ADMIN_USERNAME}")
        else:
            print(f"⚠️ Failed to create admin user: {result}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def hash_password(password: str) -> str:
    """Hash a password"""
    return ph.hash(password)

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user info"""
    user = SupabaseUserDB.get_user_by_username(username)
    
    if user and verify_password(password, user["hashed_password"]):
        # Update last login
        SupabaseUserDB.update_last_login(username)
        
        return {
            "username": user["username"],
            "email": user["email"],
            "is_admin": user["is_admin"]
        }
    return None

def create_user(username: str, email: str, password: str, is_admin: bool = False) -> tuple[bool, str]:
    """Create a new user account"""
    
    # Validate username
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    # Check if username exists
    if SupabaseUserDB.get_user_by_username(username):
        return False, "Username already exists"
    
    # Validate email
    if not email or "@" not in email:
        return False, "Invalid email address"
    
    # Check if email exists
    if SupabaseUserDB.get_user_by_email(email):
        return False, "Email already registered"
    
    # Validate password
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Create user
    hashed = hash_password(password)
    success, result = SupabaseUserDB.create_user(username, email, hashed, is_admin)
    
    if success:
        return True, "Account created successfully!"
    else:
        return False, f"Error creating account: {result}"

def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Change user password"""
    user = SupabaseUserDB.get_user_by_username(username)
    
    if not user:
        return False, "User not found"
    
    # Verify old password
    if not verify_password(old_password, user["hashed_password"]):
        return False, "Current password is incorrect"
    
    # Validate new password
    if not new_password or len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    
    # Update password
    hashed = hash_password(new_password)
    success = SupabaseUserDB.update_user(username, {"hashed_password": hashed})
    
    if success:
        return True, "Password changed successfully!"
    else:
        return False, "Error changing password"

def get_all_users() -> Dict:
    """Get all users (admin only)"""
    users = SupabaseUserDB.get_all_users()
    
    # Convert to dict format for compatibility
    users_dict = {}
    for user in users:
        users_dict[user["username"]] = {
            "username": user["username"],
            "email": user["email"],
            "is_admin": user["is_admin"],
            "created_at": user.get("created_at", ""),
            "last_login": user.get("last_login", "")
        }
    
    return users_dict

def delete_user(username: str) -> tuple[bool, str]:
    """Delete a user account (admin only)"""
    if username == DEFAULT_ADMIN_USERNAME:
        return False, "Cannot delete default admin account"
    
    success = SupabaseUserDB.delete_user(username)
    
    if success:
        return True, f"User {username} deleted successfully"
    else:
        return False, "Error deleting user"

def make_admin(username: str) -> tuple[bool, str]:
    """Promote user to admin"""
    success = SupabaseUserDB.update_user(username, {"is_admin": True})
    
    if success:
        return True, f"User {username} is now an admin"
    else:
        return False, "Error updating user"

def revoke_admin(username: str) -> tuple[bool, str]:
    """Revoke admin privileges"""
    if username == DEFAULT_ADMIN_USERNAME:
        return False, "Cannot revoke admin from default admin account"
    
    success = SupabaseUserDB.update_user(username, {"is_admin": False})
    
    if success:
        return True, f"Admin privileges revoked from {username}"
    else:
        return False, "Error updating user"

def init_session_state():
    """Initialize session state for authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.email = None
    st.session_state.is_admin = False
    st.session_state.page = "user"
    st.rerun()

def require_auth():
    """Require authentication to access page"""
    return st.session_state.authenticated

def require_admin():
    """Require admin privileges"""
    if not st.session_state.authenticated:
        return False
    return st.session_state.is_admin

def get_admin_info() -> Dict[str, str]:
    """Get default admin credentials info"""
    return {
        "username": DEFAULT_ADMIN_USERNAME,
        "email": DEFAULT_ADMIN_EMAIL
    }

# Initialize default admin on module import
init_default_admin()