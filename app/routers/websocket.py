"""
Main place for routers.

Contains the websocket endpoinds only
"""

from fastapi import APIRouter

websocket_router = APIRouter()

# Endpoinds

@websocket_router.websocket("/echo")
async def echo_chat():
    pass

# Test
@websocket_router.get("/")
async def test():
    """
    Check that the server booted-up properly
    """
    return {"message": "test"}