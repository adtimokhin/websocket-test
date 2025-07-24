"""
This is the module for the in-memory managers that will be needed for the
human handover feature
"""
import asyncio
import uuid

from fastapi import WebSocket
from typing import Optional
from utils.connection_pool import Connection


class ConnectionManager():
    def __init__(self) -> None:
        self.connection_lock = asyncio.Lock()

    def _generate_connection_id(self) -> str:
        """
        Generate a unique connection ID.
        """
        return str(uuid.uuid4())

    async def add_connection(self, websocket: WebSocket, tenant_id:str = "tenant_123") -> None:
        """
        Add the new websocket connection to the list of current connections.
        Now, this method connection to an active wait list.
        """
        pool = websocket.app.state.connections
        conn_id = self._generate_connection_id()

        websocket.conn_id = conn_id
        websocket.tenant_id = tenant_id
        pool.add_connection(Connection(conn_id, tenant_id, websocket))



    async def remove_connection(self, connections, websocket: WebSocket):
        """
        Removes connection from a list of waiting connections.
        Make sure that it was initially added to the manager!
        """
        pool = connections
        if websocket.conn_id:
            # In a queue
            conn_id = websocket.conn_id
            tenant_id = websocket.tenant_id
            if conn_id:
                 pool.remove_connection(tenant_id, conn_id)

    async def establish_connection(self, agent_websocket: WebSocket, connections, tenant_id:str = "tenant_123") -> Optional[WebSocket]:
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
        
        pool = connections
        next_conn = pool.get_next_connection(tenant_id)
        if next_conn:
            user_websocket = next_conn.data

            user_websocket.receipient_websocket = agent_websocket
            agent_websocket.receipient_websocket = user_websocket

            await self.remove_connection(connections=connections,\
                                         websocket=user_websocket)
            return user_websocket
        return None