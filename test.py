import socketio
import requests
import json
import sys
import time

# Create a Socket.IO client
sio = socketio.Client()

# Socket.IO event handlers
@sio.event
def connect():
    print("✅ Connected to server")
    # Join user room based on user_id
    user_id = sys.argv[1] if len(sys.argv) > 1 else "1"  # Default to user_id 1
    sio.emit('join', {'room': user_id})
    print(f"Joined room for user_id: {user_id}")

@sio.event
def disconnect():
    print("❌ Disconnected from server")

@sio.on('notification')
def on_notification(data):
    print("\n📩 Notification received:")
    print(f"Title: {data['title']}")
    print(f"Content: {data['content']}")
    print(f"Timestamp: {data['timestamp']}")
    print(f"User ID: {data['user_id']}")

def send_test_notification_direct(user_id):
    """Send a test notification using the direct endpoint"""
    notification_data = {
        "user_id": int(user_id),
        "type": "in-app",
        "title": "Test Direct In-App Notification",
        "content": "This is a test in-app notification sent directly at " + time.strftime("%H:%M:%S")
    }
    
    response = requests.post(
        "http://localhost:5000/send-direct-notification", 
        json=notification_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        print(f"✅ Test notification sent directly: {response.json()}")
    else:
        print(f"❌ Failed to send notification: {response.text}")

if __name__ == "__main__":
    # Connect to the Socket.IO server
    try:
        sio.connect("http://localhost:5000")
        
        # Get user_id from command line argument or default to 1
        user_id = sys.argv[1] if len(sys.argv) > 1 else "1"
        
        # Wait for connection to establish
        time.sleep(1)
        
        # Send a test notification
        send_test_notification_direct(user_id)
        
        # Keep the client running to receive notifications
        print("\nListening for notifications. Press Ctrl+C to exit...")
        sio.wait()
        
    except Exception as e:
        print(f"Error: {e}")
        if sio.connected:
            sio.disconnect()