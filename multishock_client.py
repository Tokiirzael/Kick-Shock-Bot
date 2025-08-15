import asyncio
import json
import socket
from zeroconf import Zeroconf, ServiceBrowser

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

        import websockets
        self.websocket = await websockets.connect(self.uri)
        await self.authenticate()

    async def authenticate(self):
        """
        Authenticates with the MultiShock WebSocket server.
        """
        payload = {
            "cmd": "identify",
            "value": "Kick",
            "auth_key": self.auth_key
        }
        await self.websocket.send(json.dumps(payload))
        response = await self.websocket.recv()
        print(f"Authentication response: {response}")

    async def send_operate_command(self, intensity, duration, shocker_option, action, shocker_ids=[], device_ids=[], warning=False, held=False):
        """
        Sends an operate command to the MultiShock WebSocket server.
        """
        payload = {
            "cmd": "operate",
            "value": {
                "intensity": intensity,
                "duration": duration,
                "shocker_option": shocker_option,
                "action": action,
                "shocker_ids": shocker_ids,
                "device_ids": device_ids,
                "warning": warning,
                "held": held
            },
            "auth_key": self.auth_key
        }
        await self.websocket.send(json.dumps(payload))

    async def close(self):
        """
        Closes the WebSocket connection.
        """
        if self.websocket:
            await self.websocket.close()
