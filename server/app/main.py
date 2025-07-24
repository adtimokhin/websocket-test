"""
Main FastAPI application module.
"""
import uvicorn

from fastapi import FastAPI
from routers.websocket import websocket_router
from routers.human_handover import ws_hh_router

app = FastAPI(
    title='Test Websocket',
    description='Test Websocket Endpoint - Simple echo server',
)
@app.on_event("startup")
async def startup():
    # Initialize the connection list on startup
    app.state.connections = [] # WS connections

# Adding the endpoinds
app.include_router(websocket_router)
app.include_router(ws_hh_router, prefix='/hh')

if __name__ == "__main__":
    uvicorn.run(app, port=8080, log_level="info")