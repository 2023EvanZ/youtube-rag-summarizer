"""
Supabase database connection and helpers
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_database():
    """
    Create tables if they don't exist.
    Run this SQL in your Supabase SQL Editor (Dashboard > SQL Editor):
    
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_login TIMESTAMP WITH TIME ZONE,
        CONSTRAINT username_length CHECK (char_length(username) >= 3),
        CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
    );
    
    -- Create index for faster lookups
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    
    -- Metrics table
    CREATE TABLE IF NOT EXISTS metrics (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        video_id TEXT,
        duration REAL,
        error TEXT,
        context TEXT
    );
    
    -- Create index for faster queries
    CREATE INDEX IF NOT EXISTS idx_metrics_username ON metrics(username);
    CREATE INDEX IF NOT EXISTS idx_metrics_action ON metrics(action);
    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC);
    """
    print("⚠️ Please run the SQL schema in your Supabase dashboard")
    print("Dashboard URL:", SUPABASE_URL)

class SupabaseUserDB:
    """Handle user operations with Supabase"""
    
    @staticmethod
    def create_user(username: str, email: str, hashed_password: str, is_admin: bool = False):
        """Create a new user"""
        try:
            data = {
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "is_admin": is_admin,
                "created_at": datetime.utcnow().isoformat()
            }
            response = supabase.table("users").insert(data).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_user_by_username(username: str):
        """Get user by username"""
        try:
            response = supabase.table("users").select("*").eq("username", username).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str):
        """Get user by email"""
        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    
    @staticmethod
    def update_last_login(username: str):
        """Update user's last login time"""
        try:
            data = {"last_login": datetime.utcnow().isoformat()}
            supabase.table("users").update(data).eq("username", username).execute()
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    @staticmethod
    def get_all_users():
        """Get all users (admin only)"""
        try:
            response = supabase.table("users").select("username, email, is_admin, created_at, last_login").execute()
            return response.data
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
    
    @staticmethod
    def update_user(username: str, updates: dict):
        """Update user data"""
        try:
            supabase.table("users").update(updates).eq("username", username).execute()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    @staticmethod
    def delete_user(username: str):
        """Delete user"""
        try:
            supabase.table("users").delete().eq("username", username).execute()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

class SupabaseMetricsDB:
    """Handle metrics operations with Supabase"""
    
    @staticmethod
    def log_metric(username: str, action: str, video_id: str = None, 
                   duration: float = None, error: str = None, context: str = None):
        """Log a metric"""
        try:
            data = {
                "username": username,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                "video_id": video_id,
                "duration": duration,
                "error": error,
                "context": context
            }
            supabase.table("metrics").insert(data).execute()
        except Exception as e:
            print(f"Error logging metric: {e}")
    
    @staticmethod
    def get_metrics(hours: int = 24):
        """Get metrics from last N hours"""
        try:
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            response = supabase.table("metrics")\
                .select("*")\
                .gte("timestamp", cutoff)\
                .order("timestamp", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return []