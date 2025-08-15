import requests
import json
import websocket
import threading
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global variable to hold the WebSocketApp instance
ws_app = None

def subscribe_to_events(authorization_header, broadcaster_id, webhook_url):
    """
    Subscribes to Kick events via webhooks.
    """
    url = "https://api.kick.com/public/v1/events/subscriptions"

    headers = {
        "Authorization": authorization_header,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # A list of all events we want to subscribe to.
    events = [
        {"name": "chat.message.sent"},
        {"name": "channel.followed"},
        {"name": "channel.subscription.new"},
        {"name": "channel.subscription.renewal"},
        {"name": "channel.subscription.gifts"}
    ]

    for event in events:
        payload = {
            "broadcaster_user_id": broadcaster_id,
            "events": [event],
            "method": "webhook",
            "webhook_url": webhook_url
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            print(f"Successfully subscribed to {event['name']}.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while subscribing to {event['name']}: {e}")

@app.route('/webhook', methods=['POST'])
def kick_webhook():
    """
    Receives webhook events from Kick.
    """
    event_type = request.headers.get("Kick-Event-Type")
    data = request.json

    print(f"Received event: {event_type}")
    print("Data:", json.dumps(data, indent=2))

    formatted_payload = format_event(event_type, data)

    if formatted_payload and ws_app and ws_app.sock and ws_app.sock.connected:
        try:
            ws_app.send(json.dumps(formatted_payload))
            print(f"Sent event to MultiShock: {formatted_payload['cmd']}")
        except Exception as e:
            print(f"Error sending to MultiShock: {e}")

    return '', 200

def format_event(event_type, data):
    """
    Formats the event data into the structure expected by MultiShock.
    """
    if event_type == "chat.message.sent":
        return {
            "cmd": "chat_message",
            "value": {
                "username": data["sender"]["username"],
                "message": data["content"]
            }
        }
    elif event_type == "channel.followed":
        return {
            "cmd": "follow",
            "value": {
                "username": data["follower"]["username"]
            }
        }
    elif event_type == "channel.subscription.new":
        return {
            "cmd": "subscribe",
            "value": {
                "username": data["subscriber"]["username"],
                "months": 1
            }
        }
    elif event_type == "channel.subscription.renewal":
        return {
            "cmd": "resubscribe",
            "value": {
                "username": data["subscriber"]["username"],
                "months": data["duration"]
            }
        }
    elif event_type == "channel.subscription.gifts":
        # MultiShock expects a separate event for each gifted sub
        # We will handle this in the future if needed
        return {
            "cmd": "gift_subscribe",
            "value": {
                "gifter": data["gifter"]["username"],
                "count": len(data["giftees"])
            }
        }
    # We don't have a direct equivalent for "redeems" yet.
    # This will be implemented if Kick adds a similar feature.
    return None

def start_multishock_ws():
    global ws_app
    ws_app = websocket.WebSocketApp("ws://localhost:8765/",
                                     on_open=on_open,
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close)
    ws_thread = threading.Thread(target=ws_app.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

def on_open(ws):
    print("Connected to MultiShock WebSocket.")
    identify_payload = {
        "cmd": "identify",
        "value": "Kick"
    }
    ws.send(json.dumps(identify_payload))

def on_message(ws, message):
    print(f"Received from MultiShock: {message}")

def on_error(ws, error):
    print(f"MultiShock WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("MultiShock WebSocket connection closed.")

if __name__ == "__main__":
    start_multishock_ws()

    print("This script now runs a web server to receive webhooks from Kick.")
    print("You will need to use a tool like ngrok to expose this server to the internet.")
    print("Run ngrok with the command: ngrok http 5000")
    print("Then, provide the ngrok URL (e.g., https://xxxx-xxxx.ngrok.io) to subscribe to events.")

    webhook_url = input("Enter your ngrok webhook URL (e.g., https://xxxx-xxxx.ngrok.io/webhook): ")
    authorization_header = input("Enter your Authorization header value (including 'Bearer '): ")
    broadcaster_id = input("Enter your Kick broadcaster ID: ")

    if webhook_url and authorization_header and broadcaster_id:
        subscribe_to_events(authorization_header, int(broadcaster_id), webhook_url)
        app.run(port=5000)
    else:
        print("Missing required information. Exiting.")
