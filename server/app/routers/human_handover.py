"""
module that will try to simulate the human handover solution we are
trying to intergrate into the Chat API
"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, FastAPI
from utils.enums import ConnectionType, ChatMode
from utils.human_handover.managers import ConnectionManager
from typing import Optional

ws_hh_router = APIRouter() # WebSocket, Human Handover Router :)
connection_manager = ConnectionManager() # Now just a wrapper for app.state

@ws_hh_router.websocket("/user")
async def user_endpoint(websocket: WebSocket):
    """
    This endpoint is the endpoint for the regular user.

    The endpoint will manage the state of the chat
    The endpoint will redirect messages to AI / human, depending on the state
    The endpoint will manage the websocket manager
    """
    
    await websocket.accept()
    
    # Initial setup
    _add_user_websocket_attributes(websocket)
    await connection_manager.add_connection(websocket)

    try:
        while True:
            incomming_message = await websocket.receive_text()

            # Conversation manager logic
            _check_modify_current_conversation_state(incomming_message, websocket)

            if websocket.chat_mode is ChatMode.USER_AI:
                await _ai_conversation_handler(incomming_message, websocket)
            else:
                await _agent_conversation_handler(incomming_message, websocket)
            
    except WebSocketDisconnect:
        print("User closed connection")
        if websocket.receipient_websocket:
            await _close_receipient_websocket_connection(websocket.receipient_websocket)
        await _user_disconnect_cleanup(websocket)
    except Exception as e:
        print(f"Error in websocket connection: {e}")
    finally:
        if websocket.receipient_websocket:
            await _close_receipient_websocket_connection(websocket.receipient_websocket)
        await _user_disconnect_cleanup(websocket)

@ws_hh_router.websocket("/agent")
async def agent_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Initial setup
    _add_agent_websocket_attributes(websocket)
    await connection_manager.add_connection(websocket)

    try:
        # Connection establishing
        await websocket.send_text("Looking for a connection...")
        app = websocket.app
        receipient_websocket = await _agent_establish_connection(websocket, app)
        if receipient_websocket:
            await websocket.send_text("Connection found")
        else:
            await websocket.send_text("Connection Search Timeout. Goodbye")
            await websocket.close(code=1000, reason="Connection Search Timeout.")
        
        # Main loop
        while True:
            incomming_message = await websocket.receive_text()
            await _agent_conversation_handler(incomming_message, websocket)

    except WebSocketDisconnect:
        print("Agent closed connection")
        if websocket.receipient_websocket:
            await _notify_user_about_agent_disconnect(websocket.receipient_websocket)
        await _agent_disconnect_cleanup(websocket)
    except Exception as e:
        print(f"Error in websocket connection: {e}")
    finally:
        if websocket.receipient_websocket:
            await _notify_user_about_agent_disconnect(websocket.receipient_websocket)
        await _agent_disconnect_cleanup(websocket)

################################################################################
#                          Conversation Handlers
################################################################################
async def _ai_conversation_handler(incomming_message:str, websocket: WebSocket):
    """
    This is a function that should have the logic of conversation with
    AI. This is called when you expect to pass message to ai and to get
    a response back, also form AI.

    It fully handles the logic of AI conversation.

    Note: in this example AI is replaced with simple echoing of a message

    Args:
        incomming_message (str) - the message received from user
        websocket (WebSocket) - websocket connection
    """
    await websocket.send_text(incomming_message)

async def _agent_conversation_handler(incomming_message:str, sender: WebSocket):
    """
    This is a funnction that is responsible for relaying messages between two
    connections. It can be called by either user or agent
    """
    please_wait_msg = "Please wait - we are waiting on an agent to pick up a conversation with you ..." if sender.connection_type is ConnectionType.USER else "Please wait - we are waiting on an idle user..."
    receipient = sender.receipient_websocket
    if receipient is None:
        # Relay message that the connection is not yet established
        await sender.send_text(please_wait_msg)
    else:
        await receipient.send_text(incomming_message)

################################################################################
#                          User-Related Helper Functions
################################################################################
def _add_user_websocket_attributes(websocket: WebSocket):
    """
    This funciton will add special new fields to the websocket instance.

    Here are the fields that will be added:
        websocket.connection_type: ConnectionType = ConnectionType.USER
        websocket.chat_mode: ChatMode = ChatMode.USER_AI
        websocket.receipient_websocket: Websocket = None
    """
    websocket.connection_type = ConnectionType.USER
    websocket.chat_mode  = ChatMode.USER_AI
    websocket.receipient_websocket = None

def _check_modify_current_conversation_state(incomming_message:str, websocket: WebSocket):
    """
    This function is the place where the user connection will switch from
    USER-AI to USER-AGENT states. The logic of whether that must happen will
    take place in this function, switching the state if needed.

    The decision of actual switching is based on receiving a message of a
    certain format: "SWITCH" is a special message we are expecing.

    Note: After the state was switched incomming message will have no effect on
    the state
    """
    if websocket.chat_mode is ChatMode.USER_AGENT:
        return
    
    if incomming_message == "SWITCH":
        websocket.chat_mode = ChatMode.USER_AGENT # From now on the user should talk to Agent

async def _user_disconnect_cleanup(websocket: WebSocket):
    """
    Perform cleanup for user connection
    """
    if websocket.receipient_websocket:
        websocket.receipient_websocket.receipient_websocket = None
        websocket.receipient_websocket = None
    await connection_manager.remove_connection(websocket)

async def _notify_user_about_agent_disconnect(websocket: WebSocket):
    """
    Will be shown if an agent closed the connection
    """
    await websocket.send_text("Agent terminated conversation. You will be connected to the next available agent") # System message

################################################################################
#                          Agent-Related Helper Functions
################################################################################
def _add_agent_websocket_attributes(websocket: WebSocket):
    """
    This funciton will add special new fields to the websocket instance.

    Here are the fields that will be added:
        websocket.connection_type: ConnectionType = ConnectionType.AGENT
        websocket.receipient_websocket: Websocket = None
    """
    websocket.connection_type = ConnectionType.AGENT
    websocket.receipient_websocket = None

async def _agent_establish_connection(websocket: WebSocket,  app: FastAPI,  timeout_seconds: int = 60) -> Optional[WebSocket]:
    """
    Only agents can establish connections. We will try to establish connection,
    by waiting for some time to get an idle user. We stop trying after some timeout
    """
    interval = 2 # Time in seconds
    total_waited = 0
    # All connections
    connections = app.state.connections

    while total_waited < timeout_seconds:
        result = await connection_manager.establish_connection(websocket, connections)
        if result is not None:
            return result

        await asyncio.sleep(interval)
        total_waited += interval

    # Timed out
    return None

async def _close_receipient_websocket_connection(websocket: WebSocket):
    """
    Should be called to trigger closure of agent's websocket connection
    when agent did not directly close the connection, but that is the result of
    user's actions.
    """
    await websocket.send_text("User disconnected. Goodbye") # System message
    await websocket.close(code=1000, reason="User disconnected")

async def _agent_disconnect_cleanup(websocket: WebSocket):
    """
    Perform cleanup for agent connection
    """
    if websocket.receipient_websocket:
        websocket.receipient_websocket.receipient_websocket = None
        websocket.receipient_websocket = None
    await connection_manager.remove_connection(websocket)
