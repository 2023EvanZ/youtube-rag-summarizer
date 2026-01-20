from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import json
import os

class MetricsCollector:
    def __init__(self, data_file="backend/metrics.json"):
        self.data_file = data_file
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        """Load metrics from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "requests": [],
            "transcripts": [],
            "notes_generated": [],
            "errors": [],
            "user_activity": {}
        }
    
    def _save_metrics(self):
        """Save metrics to file"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(self.metrics, f, indent=2)
    
    def log_request(self, username: str, action: str, video_id: str = None):
        """Log a user request"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "action": action,
            "video_id": video_id
        }
        self.metrics["requests"].append(record)
        
        # Update user activity
        if username not in self.metrics["user_activity"]:
            self.metrics["user_activity"][username] = {
                "total_requests": 0,
                "transcripts_generated": 0,
                "notes_generated": 0,
                "last_active": None
            }
        
        self.metrics["user_activity"][username]["total_requests"] += 1
        self.metrics["user_activity"][username]["last_active"] = datetime.now().isoformat()
        
        # Keep only last 1000 requests
        if len(self.metrics["requests"]) > 1000:
            self.metrics["requests"] = self.metrics["requests"][-1000:]
        
        self._save_metrics()
    
    def log_transcript(self, username: str, video_id: str, duration: float):
        """Log transcript generation"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "video_id": video_id,
            "duration_seconds": duration
        }
        self.metrics["transcripts"].append(record)
        
        if username in self.metrics["user_activity"]:
            self.metrics["user_activity"][username]["transcripts_generated"] += 1
        
        self._save_metrics()
    
    def log_notes(self, username: str, video_id: str, chunks_count: int):
        """Log notes generation"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "video_id": video_id,
            "chunks_count": chunks_count
        }
        self.metrics["notes_generated"].append(record)
        
        if username in self.metrics["user_activity"]:
            self.metrics["user_activity"][username]["notes_generated"] += 1
        
        self._save_metrics()
    
    def log_error(self, username: str, error_message: str, context: str = None):
        """Log an error"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "error": error_message,
            "context": context
        }
        self.metrics["errors"].append(record)
        
        # Keep only last 100 errors
        if len(self.metrics["errors"]) > 100:
            self.metrics["errors"] = self.metrics["errors"][-100:]
        
        self._save_metrics()
    
    def get_dashboard_stats(self, hours: int = 24) -> Dict:
        """Get aggregated statistics for dashboard"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Filter by time window
        recent_requests = [
            r for r in self.metrics["requests"]
            if datetime.fromisoformat(r["timestamp"]) > cutoff
        ]
        
        recent_transcripts = [
            t for t in self.metrics["transcripts"]
            if datetime.fromisoformat(t["timestamp"]) > cutoff
        ]
        
        recent_notes = [
            n for n in self.metrics["notes_generated"]
            if datetime.fromisoformat(n["timestamp"]) > cutoff
        ]
        
        recent_errors = [
            e for e in self.metrics["errors"]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        
        # Calculate stats
        total_requests = len(recent_requests)
        unique_users = len(set(r["username"] for r in recent_requests))
        
        avg_transcript_time = (
            sum(t["duration_seconds"] for t in recent_transcripts) / len(recent_transcripts)
            if recent_transcripts else 0
        )
        
        # Action breakdown
        action_counts = defaultdict(int)
        for r in recent_requests:
            action_counts[r["action"]] += 1
        
        # Top users
        user_counts = defaultdict(int)
        for r in recent_requests:
            user_counts[r["username"]] += 1
        
        top_users = sorted(
            [{"username": u, "count": c} for u, c in user_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        return {
            "time_window_hours": hours,
            "total_requests": total_requests,
            "unique_users": unique_users,
            "transcripts_generated": len(recent_transcripts),
            "notes_generated": len(recent_notes),
            "errors": len(recent_errors),
            "avg_transcript_time": avg_transcript_time,
            "action_breakdown": dict(action_counts),
            "top_users": top_users,
            "recent_errors": recent_errors[-10:],
            "user_activity": self.metrics["user_activity"]
        }

# Global metrics collector
metrics_collector = MetricsCollector()