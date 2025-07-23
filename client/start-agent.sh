#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Run the main Python script with the WebSocket URL argument
python main.py "ws://127.0.0.1:8080/hh/agnet"