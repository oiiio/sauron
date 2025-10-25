"""
Client for Xezbeth API interactions
"""
import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime


class XezbethClient:
    """Client for Xezbeth API interactions"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = httpx.AsyncClient(timeout=30.0)
        
        # Set up headers
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    async def test_connection(self) -> bool:
        """Test if Xezbeth API is reachable"""
        try:
            response = await self.session.get(f"{self.api_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def create_session(
        self,
        objective: str,
        level: int,
        max_attempts: int
    ) -> str:
        """Create Xezbeth session, returns session_id"""
        # Map Gandalf level to target descriptor - using the correct format
        target_descriptor = {
            "model_name": "gandalf",
            "has_system_prompt": True,
            "conversational_interface": True,
            "capabilities": ["text_generation"]
        }
        
        payload = {
            "objective": objective,
            "target_descriptor": target_descriptor,
            "max_attempts": max_attempts
        }
        
        try:
            response = await self.session.post(
                f"{self.api_url}/v1/sessions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["session_id"]
        except httpx.HTTPError as e:
            raise Exception(f"Failed to create Xezbeth session: {e}")
    
    async def get_next_prompt(
        self,
        session_id: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """Get next prompt with telemetry"""
        payload = {
            "conversation_history": conversation_history
        }
        
        try:
            response = await self.session.post(
                f"{self.api_url}/v1/sessions/{session_id}/step",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get next prompt: {e}")
    
    async def record_attempt(
        self,
        session_id: str,
        attempt_id: str,
        model_response: str,
        aux_signals: Optional[Dict] = None
    ) -> Dict:
        """Record attempt result and get updated metrics"""
        payload = {
            "attempt_id": attempt_id,
            "model_response": model_response
        }
        
        if aux_signals:
            payload["aux_signals"] = aux_signals
        
        try:
            response = await self.session.post(
                f"{self.api_url}/v1/sessions/{session_id}/record",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to record attempt: {e}")
    
    async def get_report(self, session_id: str) -> Dict:
        """Get final session report"""
        try:
            response = await self.session.get(
                f"{self.api_url}/v1/sessions/{session_id}/report",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get session report: {e}")
    
    async def get_analytics(self, session_id: str) -> Dict:
        """Get comprehensive session analytics"""
        try:
            response = await self.session.get(
                f"{self.api_url}/v1/sessions/{session_id}/analytics",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get session analytics: {e}")
    
    def format_conversation_history(self, attempts: List[Dict]) -> List[Dict]:
        """Format Sauron attempts into Xezbeth conversation history format"""
        history = []
        
        for attempt in attempts:
            # Add user message (the prompt we sent)
            history.append({
                "role": "user",
                "content": attempt["prompt"],
                "timestamp": attempt["timestamp"]
            })
            
            # Add assistant response (Gandalf's response)
            history.append({
                "role": "assistant", 
                "content": attempt["response"],
                "timestamp": attempt["timestamp"]
            })
        
        return history
    
    def extract_attempt_id(self, step_response: Dict) -> str:
        """Extract attempt ID from step response for recording"""
        # Xezbeth should provide an attempt_id in the step response
        # If not provided, generate one based on session and timestamp
        if "attempt_id" in step_response:
            return step_response["attempt_id"]
        else:
            # Fallback: create attempt ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            return f"attempt_{timestamp}"
    
    async def close(self):
        """Close HTTP client"""
        await self.session.aclose()


class XezbethError(Exception):
    """Custom exception for Xezbeth API errors"""
    pass


def create_xezbeth_client() -> Optional[XezbethClient]:
    """Factory function to create XezbethClient from environment"""
    api_url = os.getenv("XEZBETH_API_URL", "http://localhost:8000")
    api_key = os.getenv("XEZBETH_API_KEY")
    
    return XezbethClient(api_url, api_key)
