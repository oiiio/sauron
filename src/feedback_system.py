"""
Global feedback system for human judging
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime


class FeedbackSystem:
    """Global feedback system for coordinating human feedback between routes and graph"""
    
    def __init__(self):
        self.feedback_queue: Dict[str, Dict] = {}  # session_id -> feedback_result
        self.pending_requests: Dict[str, Dict] = {}  # session_id -> request_data
    
    def store_feedback(self, session_id: str, success: bool) -> None:
        """Store human feedback for a session"""
        self.feedback_queue[session_id] = {
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_feedback(self, session_id: str) -> Optional[Dict]:
        """Get and remove feedback for a session"""
        return self.feedback_queue.pop(session_id, None)
    
    def has_feedback(self, session_id: str) -> bool:
        """Check if feedback is available for a session"""
        return session_id in self.feedback_queue
    
    def store_request(self, session_id: str, request_data: Dict) -> None:
        """Store a pending feedback request"""
        self.pending_requests[session_id] = request_data
    
    def clear_request(self, session_id: str) -> None:
        """Clear a pending feedback request"""
        self.pending_requests.pop(session_id, None)
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up all data for a session"""
        self.feedback_queue.pop(session_id, None)
        self.pending_requests.pop(session_id, None)


# Global feedback system instance
feedback_system = FeedbackSystem()
