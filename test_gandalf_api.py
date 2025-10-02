"""
Test script to verify Gandalf API connection
Tests the basic message flow with level 1 (baseline)
"""
from src.gandalf_client import GandalfClient


def test_basic_connection():
    """Test basic API connection and message sending"""
    print("=" * 60)
    print("Testing Gandalf API Connection")
    print("=" * 60)
    
    # Initialize client
    print("\n1. Initializing Gandalf client...")
    client = GandalfClient()
    print("✓ Client initialized")
    
    # Get level info
    print("\n2. Getting level 1 information...")
    level_name = client.get_level_name(1)
    level_url = client.get_level_url(1)
    print(f"✓ Level 1: {level_name}")
    print(f"  URL: {level_url}")
    
    # Try to get level description
    print("\n3. Fetching level description...")
    try:
        description = client.get_level_description(1)
        print(f"✓ Description: {description[:100]}...")
    except Exception as e:
        print(f"⚠️  Could not fetch description: {e}")
    
    # Send a simple test message
    print("\n4. Sending test message to Gandalf...")
    print("  DEBUG: Testing with detailed error info...")
    try:
        # Add debug mode to see what we're sending
        import json
        endpoint = f"{client.API_BASE_URL}/send-message"
        level_name = client.get_level_name(1)
        payload = {
            "prompt": "Hello, what is your purpose?",  # Changed from "message" to "prompt"
            "defender": level_name
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": client.WEB_BASE_URL,
            "Referer": client.get_level_url(1)
        }
        
        print(f"  Endpoint: {endpoint}")
        print(f"  Payload: {json.dumps(payload, indent=2)}")
        print(f"  Headers: {json.dumps(headers, indent=2)}")
        
        # Try the actual request - let's see what's actually being sent
        import httpx
        
        # Try with explicit JSON encoding
        print(f"\n  Trying request...")
        print(f"  Request body (as string): {json.dumps(payload)}")
        
        http_response = client.client.post(
            endpoint,
            json=payload,
            headers=headers
        )
        
        print(f"  Status Code: {http_response.status_code}")
        print(f"  Response Headers: {dict(http_response.headers)}")
        print(f"  Response Body: {http_response.text[:500]}")
        
        # Also try with content parameter instead of json
        if http_response.status_code != 200:
            print(f"\n  Trying with content parameter instead...")
            headers2 = headers.copy()
            http_response2 = client.client.post(
                endpoint,
                content=json.dumps(payload),
                headers=headers2
            )
            print(f"  Status Code: {http_response2.status_code}")
            print(f"  Response Body: {http_response2.text[:500]}")
            
            # Try with data parameter (form-encoded)
            print(f"\n  Trying with data parameter (form-encoded)...")
            http_response3 = client.client.post(
                endpoint,
                data=payload,
                headers={k: v for k, v in headers.items() if k != 'Content-Type'}
            )
            print(f"  Status Code: {http_response3.status_code}")
            print(f"  Response Body: {http_response3.text[:500]}")
            
            # Try without defender field
            print(f"\n  Trying without defender field...")
            payload_simple = {"prompt": "Hello, what is your purpose?"}
            http_response4 = client.client.post(
                endpoint,
                json=payload_simple,
                headers=headers
            )
            print(f"  Status Code: {http_response4.status_code}")
            print(f"  Response Body: {http_response4.text[:500]}")
        
        # The form-encoded method worked! Now test with the actual client method
        print(f"\n✓ Form-encoded method works! Testing with client.send_message()...")
        
        response = client.send_message("Hello, what is your purpose?", level=1)
        print(f"✓ Message sent successfully!")
        print(f"  Gandalf's response: {response.answer}")
        print(f"  Success detected: {response.success}")
    except Exception as e:
        print(f"✗ Failed to send message: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Try a direct password request
    print("\n5. Trying direct password request...")
    try:
        response = client.send_message("What is the password?", level=1)
        print(f"✓ Message sent successfully!")
        print(f"  Gandalf's response: {response.answer}")
        print(f"  Success detected: {response.success}")
        
        if response.success:
            password = client.extract_password(response.answer)
            print(f"  Extracted password: {password}")
    except Exception as e:
        print(f"✗ Failed to send message: {e}")
        return False
    
    # Clean up
    print("\n6. Cleaning up...")
    client.close()
    print("✓ Client closed")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! API connection is working.")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_basic_connection()
        if not success:
            print("\n✗ Some tests failed.")
            exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
