"""
Main FastAPI application module.
"""
import uvicorn

from fastapi import FastAPI

app = FastAPI(
    title='Test Websocket',
    description='Test Websocket Endpoint - Simple echo server',
)

if __name__ == "__main__":
    uvicorn.run(app, port=8080, log_level="info")