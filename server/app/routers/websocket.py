"""
Main place for routers.

Contains the websocket endpoinds only

Note:
/broadcast and /echo are functionally very similar. The difference is that the
/echo will only reply with the message to the same connection, whilst /broadcast
will retranslate the message to all connections.
"""
import uuid
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

from utils.connections import ConnectionManager

websocket_router = APIRouter()
manager = ConnectionManager()
connected_users: Dict[str, WebSocket] = {}
user_chat_states: Dict[str, Dict] = {}  # user_id -> {"receiver_id": str, "pending_requests": list}

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

# Global storage for user connections and chat states

@websocket_router.websocket("/chat/{receiver_id}")
async def chat_endpoint(websocket: WebSocket, receiver_id: str | None):
    # Generate unique user ID
    user_id = str(uuid.uuid4())[:8]
    
    try:
        # 1. Establish connection with the new user
        await websocket.accept()
        connected_users[user_id] = websocket
        
        # 2. Get their websocket data to be stored into a hash-map
        user_chat_states[user_id] = {
            "receiver_id": None,
            "pending_requests": [],
            "chat_active": False
        }
        
        # 3. Handle receiver_id logic
        if receiver_id == "none" or receiver_id is None:
            # User wants to chat to the first available user
            await handle_no_receiver(websocket, user_id)
        else:
            # 3.1. Check that the provided receiver_id is in the hashmap
            if receiver_id in connected_users:
                await handle_chat_request(websocket, user_id, receiver_id)
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"User {receiver_id} is not online"
                }))
        
        # 4. Wait for messages and handle them
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                await handle_message(user_id, message_data)
                
            except json.JSONDecodeError:
                # Handle plain text messages
                await handle_message(user_id, {"type": "text", "content": data})
                
    except WebSocketDisconnect:
        await handle_disconnect(user_id)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        await handle_disconnect(user_id)

async def handle_no_receiver(websocket: WebSocket, user_id: str):
    """Handle user who wants to chat with any available user"""
    # Send welcome message with user ID
    await websocket.send_text(json.dumps({
        "type": "welcome",
        "message": f"Welcome! Your ID is {user_id}. Looking for available users...",
        "user_id": user_id
    }))
    
    # Find first available user (not in active chat)
    available_user = None
    for uid, state in user_chat_states.items():
        if uid != user_id and not state["chat_active"]:
            available_user = uid
            break
    
    if available_user:
        await handle_chat_request(websocket, user_id, available_user)
    else:
        await websocket.send_text(json.dumps({
            "type": "info",
            "message": "No available users right now. Your messages will be queued until someone connects."
        }))

async def handle_chat_request(websocket: WebSocket, sender_id: str, receiver_id: str):
    """Handle chat request between two users"""
    receiver_websocket = connected_users.get(receiver_id)
    
    if not receiver_websocket:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"User {receiver_id} is not available"
        }))
        return
    
    # Send chat request to receiver
    await receiver_websocket.send_text(json.dumps({
        "type": "chat_request",
        "message": f"User {sender_id} wants to start a chat with you. Reply 'accept' or 'decline'",
        "sender_id": sender_id
    }))
    
    # Add to pending requests
    user_chat_states[receiver_id]["pending_requests"].append(sender_id)
    
    # Notify sender
    await websocket.send_text(json.dumps({
        "type": "info",
        "message": f"Chat request sent to {receiver_id}. Waiting for response..."
    }))

async def handle_message(user_id: str, message_data: dict):
    """Handle incoming messages from users"""
    websocket = connected_users[user_id]
    user_state = user_chat_states[user_id]
    
    message_type = message_data.get("type", "text")
    content = message_data.get("content", "")
    
    if message_type == "accept":
        # Handle chat acceptance
        if user_state["pending_requests"]:
            sender_id = user_state["pending_requests"].pop(0)
            await establish_chat(user_id, sender_id)
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "No pending chat requests"
            }))
    
    elif message_type == "decline":
        # Handle chat decline
        if user_state["pending_requests"]:
            sender_id = user_state["pending_requests"].pop(0)
            sender_websocket = connected_users.get(sender_id)
            if sender_websocket:
                await sender_websocket.send_text(json.dumps({
                    "type": "info",
                    "message": f"User {user_id} declined your chat request"
                }))
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "No pending chat requests"
            }))
    
    elif message_type == "text":
        # Handle regular chat messages
        if user_state["chat_active"] and user_state["receiver_id"]:
            # 5. Send the message to the receiver using the receiver_id and the hash_map
            receiver_websocket = connected_users.get(user_state["receiver_id"])
            if receiver_websocket:
                await receiver_websocket.send_text(json.dumps({
                    "type": "message",
                    "sender_id": user_id,
                    "content": content
                }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Receiver is no longer available"
                }))
        else:
            # User not in active chat - queue message or inform them
            await websocket.send_text(json.dumps({
                "type": "info",
                "message": "You're not in an active chat. Messages will be queued until you connect with someone."
            }))

async def establish_chat(user1_id: str, user2_id: str):
    """Establish active chat between two users"""
    # Set up chat state for both users
    user_chat_states[user1_id]["receiver_id"] = user2_id
    user_chat_states[user1_id]["chat_active"] = True
    
    user_chat_states[user2_id]["receiver_id"] = user1_id
    user_chat_states[user2_id]["chat_active"] = True
    
    # Notify both users
    user1_websocket = connected_users[user1_id]
    user2_websocket = connected_users[user2_id]
    
    await user1_websocket.send_text(json.dumps({
        "type": "chat_started",
        "message": f"Chat started with {user2_id}. You can now send messages!",
        "partner_id": user2_id
    }))
    
    await user2_websocket.send_text(json.dumps({
        "type": "chat_started",
        "message": f"Chat started with {user1_id}. You can now send messages!",
        "partner_id": user1_id
    }))

async def handle_disconnect(user_id: str):
    """Handle user disconnection"""
    if user_id in connected_users:
        # Notify chat partner if in active chat
        user_state = user_chat_states.get(user_id, {})
        if user_state.get("chat_active") and user_state.get("receiver_id"):
            partner_id = user_state["receiver_id"]
            partner_websocket = connected_users.get(partner_id)
            if partner_websocket:
                await partner_websocket.send_text(json.dumps({
                    "type": "info",
                    "message": f"User {user_id} has disconnected"
                }))
                # Reset partner's chat state
                user_chat_states[partner_id]["receiver_id"] = None
                user_chat_states[partner_id]["chat_active"] = False
        
        # Clean up
        del connected_users[user_id]
        if user_id in user_chat_states:
            del user_chat_states[user_id]
        
        print(f"User {user_id} disconnected")

# Helper endpoint to get connected users (for debugging)
@websocket_router.get("/chat/users")
async def get_connected_users():
    return {
        "connected_users": list(connected_users.keys()),
        "user_count": len(connected_users),
        "chat_states": {uid: {
            "receiver_id": state["receiver_id"],
            "chat_active": state["chat_active"],
            "pending_requests": len(state["pending_requests"])
        } for uid, state in user_chat_states.items()}
    }

# @websocket_router.websocket("/chat/{receiver_id}")
# async def chat_endpoint(websocket: WebSocket, receiver_id:str | None):
#     # 1. Establish connection with the new user
#     # 2. Get their websocket data to be stored into a hash-map
#     # 3. If the receiver_id is not set - this user wants to chat to the first
#     #    user that does not chat to anyone yet.
#     #    In this case - server will simply dump the messages until the valid receiver_id is set to the appropriate data structure
#     #    But the user will also get an initial message from the server that will welcome them + say their id
#     # 3.1. Check that the provided receiver_id is in the hashmap
#     # When the user tries to send a message to someone, that someone will get a message asking them if they want to enter a chat room with that person
#     # If yes - the receiver_id will be set
#     # 4. Wait for the message
#     # 5. Send the message to the receiver using the receiver_id and the hash_map
#     pass