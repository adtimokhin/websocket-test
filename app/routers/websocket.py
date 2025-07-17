"""
Main place for routers.

Contains the websocket endpoinds only

Note:
/broadcast and /echo are functionally very similar. The difference is that the
/echo will only reply with the message to the same connection, whilst /broadcast
will retranslate the message to all connections.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from utils.connections import ConnectionManager

websocket_router = APIRouter()
manager = ConnectionManager()

# Endpoinds
@websocket_router.websocket("/broadcast")
async def broadcast_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Broadcast the message to all connected clients
            broadcast_message = f"Broadcast: {data}"
            await manager.broadcast(broadcast_message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error in websocket connection: {e}")
        manager.disconnect(websocket)

@websocket_router.websocket("/echo")
async def echo_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)

    except WebSocketDisconnect:
        print("Connection closed by client")
        return
