import asyncio
import websockets

async def test_connection():
    uri = "ws://localhost:8765"
    print(f"Attempting to connect to {uri}...")
    try:
        # Using open_timeout for compatibility with older Python versions
        async with websockets.connect(uri, open_timeout=10) as websocket:
            print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
