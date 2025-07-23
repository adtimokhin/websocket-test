# WebSocket Client

A simple Python-based WebSocket client that supports both echo and broadcast messaging modes.

## Features

- **Real-time Communication**: Send and receive messages simultaneously
- **Two Connection Modes**: Echo mode for simple request-response and broadcast mode for multi-user chat
- **Non-blocking Input**: Type messages while receiving broadcasts from other users


## Set Up a Virtual Environment (venv)

A **virtual environment** keeps your project's dependencies isolated from other Python projects on your computer.

### 💡 Create and activate the environment:

```bash
# Create venv folder
python3 -m venv venv

# Activate it
source venv/bin/activate
```

```bash
# Create venv folder
python -m venv venv

# Activate it
venv\Scripts\activate
```

> ✅ When activated, your terminal prompt will show `(venv)`.

## Installation

1. Install the required dependency:
```bash
pip install -r requirements.txt
```
Make sure to install the correct requirements file. It might help to move the client into a separate folder completely.

## Usage

### Basic Usage

```bash
# Connect to broadcast mode (default)
python main.py

# Connect to broadcast mode explicitly
python main.py broadcast

# Connect to echo mode
python main.py echo

# Connect to echo mode
python main.py [`endpoint`]
```

### Human Handover Feature Setup
You can start a client to take on a role of an end-user (or user) or a human agent (or agent)
This client has two scripts that will setup both of user types. Notes, these bash files will also
start the venv for you

#### To Compile Bash Scripts
```bash
chmod +x start-user.sh
chmod +x start-agent.sh
```

#### To Run Bash Scripts
```bash
./start-user.sh
./start-agent.sh
```

## Server Endpoints

The client expects the following WebSocket endpoints to be available:

- **Echo Mode**: `ws://127.0.0.1:8080/echo`
- **Broadcast Mode**: `ws://127.0.0.1:8080/broadcast`

## How It Works

### Echo Mode
- Send a message → Server echoes it back
- Simple request-response pattern
- Suitable for testing basic WebSocket functionality

### Broadcast Mode
- Send a message → Server broadcasts it to all connected clients
- Real-time multi-user communication
- Perfect for chat applications

## Features in Detail

### Concurrent Message Handling
The client uses Python's `asyncio` and `threading` to handle:
- **Receiving messages**: Continuously listens for incoming messages
- **Sending messages**: Handles user input without blocking message reception
- **Thread-safe communication**: Uses `queue.Queue()` to safely pass messages between threads

### User Interface
- **Clear message display**: Incoming messages are prefixed with `[RECEIVED]:`
- **Persistent input prompt**: Input prompt reappears after receiving messages
- **Multiple exit options**: Type `quit`, `exit`, `q`, or press `Ctrl+C` to exit