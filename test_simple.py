"""
Simple test script to verify the Gandalf agent system works
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from src.gandalf_client import GandalfClient, GandalfResponse
        from src.state import AgentState, AttemptRecord
        from src.agents import ReasoningAgent, GandalfInteractionAgent
        from src.observability import ObservabilityManager
        from src.graph import GandalfGraph
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_gandalf_client():
    """Test the Gandalf client (without actually calling the API)"""
    print("\nTesting Gandalf client...")
    try:
        from src.gandalf_client import GandalfClient
        client = GandalfClient()
        print("✓ Gandalf client initialized")
        client.close()
        return True
    except Exception as e:
        print(f"✗ Gandalf client test failed: {e}")
        return False


def test_state_management():
    """Test state management"""
    print("\nTesting state management...")
    try:
        from src.state import AgentState
        state = AgentState(level=1, max_attempts=5)
        
        # Add a test attempt
        state.add_attempt(
            prompt="Test prompt",
            response="Test response with password TESTPASS",
            reasoning="Test reasoning",
            success=True
        )
        
        assert state.current_attempt == 1
        assert len(state.attempts_history) == 1
        assert state.success == True
        
        print("✓ State management working")
        return True
    except Exception as e:
        print(f"✗ State management test failed: {e}")
        return False


def test_observability():
    """Test observability system"""
    print("\nTesting observability...")
    try:
        from src.observability import ObservabilityManager
        obs = ObservabilityManager(log_file="logs/test.log")
        
        obs.log_event("test", "Test event")
        obs.log_attempt(
            attempt_number=1,
            prompt="Test",
            response="Response",
            reasoning="Reasoning",
            success=False,
            level=1
        )
        
        summary = obs.get_summary()
        assert summary["total_attempts"] == 1
        
        print("✓ Observability working")
        return True
    except Exception as e:
        print(f"✗ Observability test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Sauron - Gandalf Agent System Tests")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  Warning: No API key found!")
        print("Some tests may fail without an API key.")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
    
    tests = [
        test_imports,
        test_gandalf_client,
        test_state_management,
        test_observability,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All tests passed! System is ready to use.")
        print("\nTo start the web interface, run:")
        print("  python main.py")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        print("\nMake sure you have installed all dependencies:")
        print("  pip install -r requirements.txt")


if __name__ == "__main__":
    main()
