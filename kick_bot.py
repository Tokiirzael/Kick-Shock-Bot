import flask
import threading
import asyncio
import json
import hmac
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from multishock_client import MultiShockClient

# --- Configuration ---
MULTISHOCK_AUTH_KEY = "your_auth_key_here"
KICK_API_TOKEN = "your_kick_api_token_here"
KICK_BROADCASTER_ID = "your_kick_broadcaster_id_here"
DEFAULT_SUB_TIER = "1000"  # Default to Tier 1

# Kick's public key for webhook signature verification
KICK_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq/+l1WnlRrGSolDMA+A8
6rAhMbQGmQ2SapVcGM3zq8ANXjnhDWocMqfWcTd95btDydITa10kDvHzw9WQOqp2
MZI7ZyrfzJuz5nhTPCiJwTwnEtWft7nV14BYRDHvlfqPUaZ+1KR4OCaO/wWIk/rQ
L/TjY0M70gse8rlBkbo2a8rKhu69RQTRsoaf4DVhDPEeSeI5jVrRDGAMGL3cGuyY
6CLKGdjVEM78g3JfYOvDU/RvfqD7L89TZ3iN94jrmWdGz34JNlEI5hqK8dd7C5EF
BEbZ5jgB8s8ReQV8H+MkuffjdAj3ajDDX3DOJMIut1lBrUVD1AaSrGCKHooWoL2e
twIDAQAB
-----END PUBLIC KEY-----
"""

app = flask.Flask(__name__)
multishock_client = MultiShockClient(MULTISHOCK_AUTH_KEY)
kick_public_key = serialization.load_pem_public_key(KICK_PUBLIC_KEY.encode())

def verify_signature(request):
    """
    Verifies the signature of a webhook request from Kick.
    """
    signature_header = request.headers.get('Kick-Event-Signature')
    message_id = request.headers.get('Kick-Event-Message-Id')
    timestamp = request.headers.get('Kick-Event-Message-Timestamp')

    if not signature_header or not message_id or not timestamp:
        return False

    signature_body = f"{message_id}.{timestamp}.{request.data.decode('utf-8')}"

    try:
        kick_public_key.verify(
            bytes.fromhex(signature_header),
            signature_body.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False

@app.route('/kick/webhook', methods=['POST'])
def kick_webhook():
    """
    This endpoint receives webhook events from Kick.
    """
    if not verify_signature(flask.request):
        return 'Signature verification failed', 401

    event_type = flask.request.headers.get('Kick-Event-Type')
    event_data = flask.request.json

    if event_type == 'channel.followed':
        handle_follow(event_data)
    elif event_type == 'channel.subscription.new':
        handle_subscription(event_data)
    elif event_type == 'channel.subscription.gifts':
        handle_gifted_subscription(event_data)
    elif event_type == 'channel.subscription.renewal':
        handle_resubscription(event_data)

    return '', 200

def handle_follow(data):
    """
    Handles a channel.followed event.
    """
    print(f"New follower: {data['follower']['username']}")
    payload = {
        "cmd": "channel.follow",
        "value": {
            "user_id": str(data['follower']['user_id']),
            "user_login": data['follower']['channel_slug'],
            "user_name": data['follower']['username'],
            "broadcaster_user_id": str(data['broadcaster']['user_id']),
            "broadcaster_user_login": data['broadcaster']['channel_slug'],
            "broadcaster_user_name": data['broadcaster']['username'],
            "followed_at": data['created_at']
        },
        "auth_key": MULTISHOCK_AUTH_KEY
    }
    asyncio.run(multishock_client.websocket.send(json.dumps(payload)))


def handle_subscription(data):
    """
    Handles a channel.subscription.new event.
    """
    print(f"New subscription from {data['subscriber']['username']}")
    payload = {
        "cmd": "channel.subscribe",
        "value": {
            "user_id": str(data['subscriber']['user_id']),
            "user_login": data['subscriber']['channel_slug'],
            "user_name": data['subscriber']['username'],
            "broadcaster_user_id": str(data['broadcaster']['user_id']),
            "broadcaster_user_login": data['broadcaster']['channel_slug'],
            "broadcaster_user_name": data['broadcaster']['username'],
            "tier": DEFAULT_SUB_TIER,
            "is_gift": False
        },
        "auth_key": MULTISHOCK_AUTH_KEY
    }
    asyncio.run(multishock_client.websocket.send(json.dumps(payload)))


def handle_gifted_subscription(data):
    """
    Handles a channel.subscription.gifts event.
    """
    gifter = data['gifter']['username'] or 'Anonymous'
    giftee_count = len(data['giftees'])
    print(f"{gifter} gifted {giftee_count} subs!")

    payload = {
        "cmd": "channel.subscription.gift",
        "value": {
            "user_id": str(data['gifter']['user_id']) if data['gifter']['user_id'] else None,
            "user_login": data['gifter']['channel_slug'],
            "user_name": gifter,
            "broadcaster_user_id": str(data['broadcaster']['user_id']),
            "broadcaster_user_login": data['broadcaster']['channel_slug'],
            "broadcaster_user_name": data['broadcaster']['username'],
            "total": giftee_count,
            "tier": DEFAULT_SUB_TIER,
            "is_anonymous": data['gifter']['username'] is None
        },
        "auth_key": MULTISHOCK_AUTH_KEY
    }
    asyncio.run(multishock_client.websocket.send(json.dumps(payload)))


def handle_resubscription(data):
    """
    Handles a channel.subscription.renewal event.
    """
    print(f"{data['subscriber']['username']} resubscribed for {data['duration']} months!")
    payload = {
        "cmd": "channel.subscription.message",
        "value": {
            "user_id": str(data['subscriber']['user_id']),
            "user_login": data['subscriber']['channel_slug'],
            "user_name": data['subscriber']['username'],
            "broadcaster_user_id": str(data['broadcaster']['user_id']),
            "broadcaster_user_login": data['broadcaster']['channel_slug'],
            "broadcaster_user_name": data['broadcaster']['username'],
            "message": {
                "text": "",
                "emotes": None
            },
            "tier": DEFAULT_SUB_TIER,
            "cumulative_months": data['duration'],
            "streak_months": None, # Not provided by Kick API
            "duration_months": data['duration']
        },
        "auth_key": MULTISHOCK_AUTH_KEY
    }
    asyncio.run(multishock_client.websocket.send(json.dumps(payload)))


def run_flask_app():
    """
    Runs the Flask app in a separate thread.
    """
    # Note: When running this script, you will need to use a tool like ngrok
    # to expose this local endpoint to the public internet. For example:
    # ngrok http 5000
    # Then, you will need to configure the generated public URL (e.g.,
    # https://xxxx-xxxx-xxxx.ngrok.io/kick/webhook) in your Kick developer
    # settings.
    app.run(port=5000)

import requests

def subscribe_to_kick_events():
    """
    Subscribes to the necessary Kick events.
    """
    events = [
        {'name': 'channel.followed', 'version': 1},
        {'name': 'channel.subscription.new', 'version': 1},
        {'name': 'channel.subscription.gifts', 'version': 1},
        {'name': 'channel.subscription.renewal', 'version': 1}
    ]
    headers = {
        'Authorization': f'Bearer {KICK_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'broadcaster_user_id': KICK_BROADCASTER_ID,
        'events': events,
        'method': 'webhook'
    }
    response = requests.post('https://api.kick.com/public/v1/events/subscriptions', headers=headers, json=data)
    if response.status_code == 200:
        print("Successfully subscribed to events")
    else:
        print(f"Failed to subscribe to events: {response.text}")

async def main():
    """
    Main function to connect to the Multishock server and start the Flask app.
    """
    await multishock_client.connect()

    subscribe_to_kick_events()

    # Start the Flask app in a background thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    print("Kick to Multishock bridge is running.")
    # The main thread will continue to run, keeping the script alive.
    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
        asyncio.run(multishock_client.close())
