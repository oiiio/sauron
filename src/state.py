"""
State management for the Gandalf agent system
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AttemptRecord(BaseModel):
    """Record of a single attempt to extract the password"""
    attempt_number: int
    prompt: str
    gandalf_response: str
    reasoning: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    level: int


class AgentState(BaseModel):
    """State for the LangGraph agent system"""
    level: int = 1
    max_attempts: int = 20
    current_attempt: int = 0
    attempts_history: List[AttemptRecord] = Field(default_factory=list)
    success: bool = False
    extracted_password: Optional[str] = None
    
    # Current iteration data
    current_prompt: Optional[str] = None
    current_response: Optional[str] = None
    current_reasoning: Optional[str] = None
    
    # Strategy tracking
    strategies_tried: List[str] = Field(default_factory=list)
    
    # New fields for Xezbeth integration
    mode: str = "xezbeth"  # or "standalone"
    sauron_session_id: Optional[str] = None  # Our internal session ID
    xezbeth_session_id: Optional[str] = None  # Xezbeth session ID
    attack_family: Optional[str] = None
    template_id: Optional[str] = None
    current_telemetry: Optional[Dict] = None
    current_attempt_id: Optional[str] = None  # For Xezbeth recording
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_attempt(
        self,
        prompt: str,
        response: str,
        reasoning: str,
        success: bool
    ) -> None:
        """Add an attempt to the history"""
        self.current_attempt += 1
        
        record = AttemptRecord(
            attempt_number=self.current_attempt,
            prompt=prompt,
            gandalf_response=response,
            reasoning=reasoning,
            success=success,
            level=self.level
        )
        
        self.attempts_history.append(record)
        
        if success:
            self.success = True
            # Try to extract the password from the response
            self.extracted_password = self._extract_password(response)
    
    def _extract_password(self, response: str) -> Optional[str]:
        """Extract the password from Gandalf's response"""
        import re
        
        # Look for quoted words
        quoted = re.findall(r'"([^"]+)"', response)
        if quoted:
            return quoted[0]
        
        # Look for all-caps words
        caps = re.findall(r'\b[A-Z]{4,}\b', response)
        if caps:
            return caps[0]
        
        # Look for "password is X" patterns
        patterns = [
            r'password is (\w+)',
            r'password: (\w+)',
            r'secret is (\w+)',
            r'secret: (\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_recent_attempts(self, n: int = 5) -> List[AttemptRecord]:
        """Get the n most recent attempts"""
        return self.attempts_history[-n:] if self.attempts_history else []
    
    def should_continue(self) -> bool:
        """Check if the agent should continue trying"""
        return not self.success and self.current_attempt < self.max_attempts
