"""
Main entry point for the Sauron Gandalf agent system
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for required API keys
from src.llm_config import LLMConfig

available = LLMConfig.get_available_providers()
if not any(available.values()):
    print("⚠️  Warning: No API key found!")
    print("Please set at least one API key in your .env file:")
    print("  - OPENAI_API_KEY (for OpenAI models)")
    print("  - ANTHROPIC_API_KEY (for Anthropic models)")
    print("  - GOOGLE_API_KEY (for Gemini models)")
    print("\nCopy .env.example to .env and add your API key")
    exit(1)

# Display current configuration
config = LLMConfig.get_current_config()
print(f"\n📋 LLM Configuration:")
print(f"  Provider: {config['provider']}")
print(f"  Model: {config['model']}")
print(f"  Available providers: {', '.join([k for k, v in config['available_providers'].items() if v])}")
print()

if __name__ == "__main__":
    import uvicorn
    from src.web_server import app
    
    # Get host and port from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    print("🧙 Starting Sauron - Gandalf Agent Monitor 👁️")
    print("=" * 60)
    print(f"Dashboard will be available at: http://localhost:{port}")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")
