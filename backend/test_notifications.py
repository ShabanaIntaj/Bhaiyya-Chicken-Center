
import asyncio
import getpass
import websockets


async def test_notifications():
    token = getpass.getpass("Paste owner access token (hidden): ")

    url = f"ws://127.0.0.1:8000/notifications/ws?token={token}"

    print("\nConnecting to owner notifications...")

    try:
        async with websockets.connect(url) as websocket:
            print("Connected successfully!")
            print("Waiting for a new order notification...")
            print("Keep this terminal open.\n")

            async for message in websocket:
                print("NEW NOTIFICATION:")
                print(message)
                print("-" * 40)

    except Exception as error:
        print(f"\nConnection failed: {error}")


if __name__ == "__main__":
    asyncio.run(test_notifications())
