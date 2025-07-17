"""
Main place for routers.

Contains the websocket endpoinds only
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

websocket_router = APIRouter()

# Endpoinds

@websocket_router.websocket("/echo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"{data}")

    except WebSocketDisconnect:
        print("Connection closed by client")
        return
# Test
@websocket_router.get("/")
async def test():
    """
    Check that the server booted-up properly
    """
    return {"message": "test"}