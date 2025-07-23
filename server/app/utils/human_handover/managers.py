"""
This is the module for the in-memory managers that will be needed for the
human handover feature
"""
import asyncio

from fastapi import WebSocket
from collections import defaultdict
from typing import Dict, List, Optional

from utils.enums import ConnectionType, ChatMode

class ConnectionManager():
    def __init__(self) -> None:
        self.connections: Dict[ConnectionType, List[WebSocket]] = defaultdict(list)
        self.connection_lock = asyncio.Lock()

    def add_connection(self, connection_type: ConnectionType, websocket: WebSocket) -> None:
        """
        Add the new websocket connection to the list of current connections
        """
        self.connections[connection_type].append(websocket)

    def remove_connection(self, connection_type: ConnectionType, websocket: WebSocket):
        """
        Removes connection
        """
        # TODO: Add lock-protection
        if websocket in self.connections[connection_type]:
            self.connections[connection_type].remove(websocket)

    async def establish_connection(self, agent_websocket: WebSocket) -> Optional[WebSocket]:
        """
        Attempts to connect two websockets together.

        If the system finds a user for the agent, they will be linked.
        The return value will be that user's Websocket.

        If no link was established, agent recieves None.
        """
        if agent_websocket.receipient_websocket:
            # Already in conversation
            return None
        
        async with self.connection_lock:
            for user_connection in self.connections[ConnectionType.USER]:
                # We take the first connection that awaits agent connection
                if user_connection.chat_mode is ChatMode.USER_AGENT and \
                    user_connection.receipient_websocket is None:
                    # This should be atomic
                    user_connection.receipient_websocket = agent_websocket
                    agent_websocket.receipient_websocket = user_connection
                    return user_connection
            
            return None

