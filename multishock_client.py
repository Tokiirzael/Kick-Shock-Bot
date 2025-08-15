import asyncio
import json
import socket
from zeroconf import Zeroconf, ServiceBrowser
import websockets

class MultiShockClient:
    def __init__(self, auth_key):
        self.auth_key = auth_key
        self.uri = None
        self.websocket = None

    def discover_service(self):
        """
        Discovers the MultiShock WebSocket service on the local network.
        """
        class MyServiceListener:
            def __init__(self):
                self.info = None

            def add_service(self, zeroconf, type, name):
                self.info = zeroconf.get_service_info(type, name)
                zeroconf.close()

            def remove_service(self, zeroconf, type, name):
                pass

            def update_service(self, zeroconf, type, name):
                pass

        zeroconf = Zeroconf()
        listener = MyServiceListener()
        ServiceBrowser(zeroconf, "_ws._tcp.local.", listener)

        try:
            # Wait for the service to be discovered
            import time
            time.sleep(5)
        finally:
            if listener.info:
                address = socket.inet_ntoa(listener.info.addresses[0])
                port = listener.info.port
                self.uri = f"ws://{address}:{port}"
                print(f"Discovered MultiShock service at {self.uri}")
            else:
                print("Could not find MultiShock service. Defaulting to ws://localhost:8765")
                self.uri = "ws://localhost:8765"


    async def connect(self):
        """
        Connects to the MultiShock WebSocket server.
        """
        if not self.uri:
            self.discover_service()

        print(f"Attempting to connect to {self.uri}...")
        try:
            # The API documentation doesn't mention an identify/auth step,
            # so we will just connect and assume the auth_key is validated on each command.
            self.websocket = await websockets.connect(self.uri, open_timeout=10)
            print("Connection established. Waiting for Kick events...")
        except asyncio.TimeoutError:
            print("Connection timed out. Please ensure the Multishock server is running and accessible.")
            self.websocket = None
        except Exception as e:
            print(f"An error occurred during connection: {e}")
            self.websocket = None

    async def send_command(self, payload):
        """
        Sends a command to the MultiShock WebSocket server.
        """
        if not self.websocket:
            print("Cannot send command, no WebSocket connection.")
            return

        # Add the auth key to every command, as per the documentation
        payload['auth_key'] = self.auth_key
        await self.websocket.send(json.dumps(payload))

    async def close(self):
        """
        Closes the WebSocket connection.
        """
        if self.websocket:
            await self.websocket.close()
