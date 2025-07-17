"""
Main FastAPI application module.
"""
import uvicorn

from fastapi import FastAPI
from routers.websocket import websocket_router

app = FastAPI(
    title='Test Websocket',
    description='Test Websocket Endpoint - Simple echo server',
)

# Adding the endpoinds
app.include_router(websocket_router)

if __name__ == "__main__":
    uvicorn.run(app, port=8080, log_level="info")