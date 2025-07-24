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
        self.connection_lock = asyncio.Lock()

    async def add_connection(self, websocket: WebSocket) -> None:
        """
        Add the new websocket connection to the list of current connections
        """
        websocket.app.state.connections.append(websocket)
        print(f"there are {len(websocket.app.state.connections)} connections")


    async def remove_connection(self, websocket: WebSocket):
        """
        Removes connection
        """
        try:
            websocket.app.state.connections.remove(websocket)
        except ValueError as e:
            print(f"Could not remove websocket - it does not exist on app.state.connections, {e}")
        finally:
            print(f"there are {len(websocket.app.state.connections)} connections")

    async def establish_connection(self, agent_websocket: WebSocket, connections) -> Optional[WebSocket]:
        """
        Attempts to connect two websockets together.

        If the system finds a user for the agent, they will be linked.
        The return value will be that user's Websocket.

        If no link was established, agent recieves None.
        """
        #TODO: Not sure of the type for the connection objecy
        if agent_websocket.receipient_websocket:
            # Already in conversation
            return None
        
        async with self.connection_lock:
            for client in connections:
                if client == agent_websocket:
                    continue

                if client.connection_type == ConnectionType.AGENT:
                    continue

                if client.chat_mode is ChatMode.USER_AGENT and \
                    client.receipient_websocket is None:
                    # This should be atomic
                    client.receipient_websocket = agent_websocket
                    agent_websocket.receipient_websocket = client
                    return client
            return None

