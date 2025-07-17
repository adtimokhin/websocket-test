"""
Connection manager that allows to keep track of all connections open
"""
import asyncio

from fastapi import WebSocket
from typing import List 


class ConnectionManager():
    def __init__(self) -> None:
        self.active_connections: List[WebSocket]

    async def connect(self, websocket: WebSocket) -> None:
        """
        Add the new websocket connection to the list of active connections
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a websocket connection from the list of active connections.

        Check before calling this function that the websocket was added to the
        list of active connections
        """
        self.active_connections.remove(websocket)

    async def broadcast(self, message:str) -> None:
        """
        Sends the message to all active connections
        """
        # Using task buffer for better asynchronous code
        tasks = []
        for connection in self.active_connections.copy():
            tasks.append(connection.send_text(message))

        await asyncio.gather(*tasks, return_exceptions=True)


