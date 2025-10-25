"""
Determines and manages Xezbeth vs Standalone mode
"""
import os
import asyncio
from typing import Dict, Optional
from .xezbeth_client import XezbethClient


class ModeSelector:
    """Determines and manages Xezbeth vs Standalone mode"""
    
    @staticmethod
    def should_use_xezbeth() -> bool:
        """Check if Xezbeth mode should be used"""
        # Check environment variable first
        xezbeth_enabled = os.getenv("XEZBETH_ENABLED", "true").lower()
        if xezbeth_enabled in ["false", "0", "no", "off"]:
            return False
        
        # If enabled, we'll test connection during initialization
        return True
    
    @staticmethod
    async def test_xezbeth_connection(url: Optional[str] = None) -> bool:
        """Test if Xezbeth API is reachable"""
        if url is None:
            url = os.getenv("XEZBETH_API_URL", "http://localhost:8000")
        
        try:
            api_key = os.getenv("XEZBETH_API_KEY")
            client = XezbethClient(url, api_key)
            
            # Test connection with timeout
            is_connected = await asyncio.wait_for(
                client.test_connection(),
                timeout=5.0
            )
            
            await client.close()
            return is_connected
            
        except Exception:
            return False
    
    @staticmethod
    async def determine_mode() -> str:
        """Determine which mode to use based on configuration and connectivity"""
        # First check if Xezbeth is enabled
        if not ModeSelector.should_use_xezbeth():
            return "standalone"
        
        # Test connection to Xezbeth
        if await ModeSelector.test_xezbeth_connection():
            return "xezbeth"
        else:
            # Fallback to standalone if Xezbeth is not reachable
            return "standalone"
    
    @staticmethod
    def get_mode_config() -> Dict:
        """Get current mode configuration"""
        xezbeth_enabled = ModeSelector.should_use_xezbeth()
        xezbeth_url = os.getenv("XEZBETH_API_URL", "http://localhost:8000")
        has_api_key = bool(os.getenv("XEZBETH_API_KEY"))
        
        return {
            "xezbeth_enabled": xezbeth_enabled,
            "xezbeth_url": xezbeth_url,
            "has_api_key": has_api_key,
            "fallback_available": True  # Standalone mode always available
        }
    
    @staticmethod
    async def get_mode_status() -> Dict:
        """Get detailed mode status including connectivity"""
        config = ModeSelector.get_mode_config()
        
        if config["xezbeth_enabled"]:
            # Test connection
            is_connected = await ModeSelector.test_xezbeth_connection()
            determined_mode = "xezbeth" if is_connected else "standalone"
            
            return {
                **config,
                "xezbeth_connected": is_connected,
                "determined_mode": determined_mode,
                "status": "connected" if is_connected else "fallback_to_standalone"
            }
        else:
            return {
                **config,
                "xezbeth_connected": False,
                "determined_mode": "standalone",
                "status": "disabled"
            }


class ModeManager:
    """Manages mode state and transitions"""
    
    def __init__(self):
        self.current_mode: Optional[str] = None
        self.xezbeth_client: Optional[XezbethClient] = None
    
    async def initialize(self) -> str:
        """Initialize and determine mode"""
        self.current_mode = await ModeSelector.determine_mode()
        
        if self.current_mode == "xezbeth":
            # Initialize Xezbeth client
            api_url = os.getenv("XEZBETH_API_URL", "http://localhost:8000")
            api_key = os.getenv("XEZBETH_API_KEY")
            self.xezbeth_client = XezbethClient(api_url, api_key)
        
        return self.current_mode
    
    def get_mode(self) -> str:
        """Get current mode"""
        return self.current_mode or "standalone"
    
    def is_xezbeth_mode(self) -> bool:
        """Check if currently in Xezbeth mode"""
        return self.current_mode == "xezbeth"
    
    def get_xezbeth_client(self) -> Optional[XezbethClient]:
        """Get Xezbeth client if in Xezbeth mode"""
        return self.xezbeth_client if self.is_xezbeth_mode() else None
    
    async def switch_to_standalone(self):
        """Force switch to standalone mode"""
        if self.xezbeth_client:
            await self.xezbeth_client.close()
            self.xezbeth_client = None
        
        self.current_mode = "standalone"
    
    async def try_switch_to_xezbeth(self) -> bool:
        """Try to switch to Xezbeth mode"""
        if not ModeSelector.should_use_xezbeth():
            return False
        
        if await ModeSelector.test_xezbeth_connection():
            # Close existing client if any
            if self.xezbeth_client:
                await self.xezbeth_client.close()
            
            # Create new client
            api_url = os.getenv("XEZBETH_API_URL", "http://localhost:8000")
            api_key = os.getenv("XEZBETH_API_KEY")
            self.xezbeth_client = XezbethClient(api_url, api_key)
            self.current_mode = "xezbeth"
            return True
        
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.xezbeth_client:
            await self.xezbeth_client.close()
            self.xezbeth_client = None
