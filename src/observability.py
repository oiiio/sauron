"""
Observability and logging system for the Gandalf agent
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog


class ObservabilityManager:
    """Manages logging and observability for the agent system"""
    
    def __init__(self, log_file: str = "logs/gandalf_agent.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure structured logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ]
        )
        
        self.logger = structlog.get_logger()
        
        # In-memory storage for web interface
        self.events: List[Dict[str, Any]] = []
        self.attempts: List[Dict[str, Any]] = []
        
    def log_event(
        self,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a general event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        
        self.events.append(event)
        self.logger.info(event_type, **event)
        
        # Write to file
        self._write_to_file(event)
    
    def log_attempt(
        self,
        attempt_number: int,
        prompt: str,
        response: str,
        reasoning: str,
        success: bool,
        level: int
    ) -> None:
        """Log an attempt to extract the password"""
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "attempt_number": attempt_number,
            "level": level,
            "prompt": prompt,
            "response": response,
            "reasoning": reasoning,
            "success": success
        }
        
        self.attempts.append(attempt)
        self.logger.info("attempt", **attempt)
        
        # Write to file
        self._write_to_file(attempt)
    
    def _write_to_file(self, data: Dict[str, Any]) -> None:
        """Write data to log file"""
        with open(self.log_file, "a") as f:
            f.write(json.dumps(data) + "\n")
    
    def get_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent events"""
        if limit:
            return self.events[-limit:]
        return self.events
    
    def get_attempts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent attempts"""
        if limit:
            return self.attempts[-limit:]
        return self.attempts
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        total_attempts = len(self.attempts)
        successful_attempts = sum(1 for a in self.attempts if a["success"])
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "latest_attempt": self.attempts[-1] if self.attempts else None,
            "total_events": len(self.events)
        }
    
    def clear(self) -> None:
        """Clear in-memory logs"""
        self.events.clear()
        self.attempts.clear()
