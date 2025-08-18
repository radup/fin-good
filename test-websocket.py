#!/usr/bin/env python3
"""
Test script for WebSocket upload progress tracking.
"""

import asyncio
import websockets
import json
import requests
import time

# Configuration
BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000"

# Demo credentials - update these to match your test account
DEMO_EMAIL = "demo@fingood.com"
DEMO_PASSWORD = "demo123"

async def test_websocket_connection():
    """Test WebSocket connection for upload progress tracking."""
    
    print("🔧 Testing WebSocket Upload Progress Tracking")
    print("=" * 50)
    
    # Step 1: Login to get authentication cookies
    print("1. Authenticating user...")
    session = requests.Session()
    
    login_data = {
        "username": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    }
    
    try:
        response = session.post(f"{BACKEND_URL}/api/v1/auth/login", data=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return
        
        print("✅ Login successful")
        
        # Step 2: Get WebSocket token
        print("2. Getting WebSocket token...")
        token_response = session.post(f"{BACKEND_URL}/api/v1/auth/websocket-token")
        if token_response.status_code != 200:
            print(f"❌ Failed to get WebSocket token: {token_response.status_code} - {token_response.text}")
            return
        
        token_data = token_response.json()
        websocket_token = token_data["websocket_token"]
        print("✅ WebSocket token obtained")
        
        # Step 3: Test WebSocket connection
        print("3. Testing WebSocket connection...")
        batch_id = f"test_batch_{int(time.time())}"
        websocket_url = f"{WEBSOCKET_URL}/ws/upload-progress/{batch_id}?token={websocket_token}"
        
        print(f"   Connecting to: {websocket_url}")
        
        try:
            async with websockets.connect(websocket_url) as websocket:
                print("✅ WebSocket connected successfully")
                
                # Wait for initial connection message
                try:
                    initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message_data = json.loads(initial_message)
                    print(f"   Initial message: {message_data}")
                    
                    # Send a ping to test bidirectional communication
                    await websocket.send("ping")
                    pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"   Ping response: {pong_response}")
                    
                    if pong_response == "pong":
                        print("✅ Bidirectional communication working")
                    
                    print("4. Testing progress message simulation...")
                    # In a real scenario, upload would trigger progress messages
                    # For now, we'll just listen for any messages
                    
                    # Keep connection alive for a few seconds
                    await asyncio.sleep(2)
                    
                except asyncio.TimeoutError:
                    print("⚠️  No initial message received (timeout)")
                
        except websockets.exceptions.ConnectionClosed as e:
            print(f"❌ WebSocket connection closed: {e}")
        except Exception as e:
            print(f"❌ WebSocket connection error: {e}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request error: {e}")
    
    print("\n✅ WebSocket test completed")

async def test_upload_progress_simulation():
    """Simulate upload progress messages."""
    print("\n🚀 Testing Upload Progress Simulation")
    print("=" * 50)
    
    # This would require a running backend with the WebSocket manager
    # For now, just test the connection mechanism
    
    # You can extend this to actually upload a file and watch the progress
    batch_id = f"upload_test_{int(time.time())}"
    print(f"Generated batch ID: {batch_id}")
    
    # In a real test, you would:
    # 1. Start WebSocket connection with the batch_id
    # 2. Upload a CSV file with the same batch_id
    # 3. Monitor progress messages
    
    print("📋 To test full upload progress:")
    print("   1. Start the backend server (python main.py)")
    print("   2. Use the frontend upload form")
    print("   3. Monitor WebSocket messages in browser dev tools")

if __name__ == "__main__":
    print("🧪 FinGood WebSocket Test Suite")
    print("================================")
    
    # Run the tests
    try:
        asyncio.run(test_websocket_connection())
        asyncio.run(test_upload_progress_simulation())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")