import websockets
import pytest
import json


@pytest.mark.asyncio
async def test_websocket_connection():
    url = "ws://localhost:8000/ws/api/v1/meetings/355fde5e-b9da-4f17-9ab4-b608fbbcc868/"

    async with websockets.connect(url) as websocket:
        message = {
            "type": "chat",
            "message": "Hello world!"
        }
        await websocket.send(json.dumps(message))

        response = await websocket.recv()
        response_data = json.loads(response)

        assert response_data["message"] == "Hello world!"
