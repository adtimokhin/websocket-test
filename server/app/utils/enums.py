"""
Enums module
"""

from enum import Enum

class ConnectionType(Enum):
    USER = "USER"
    AGENT = "AGENT"

class ChatMode(Enum):
    USER_AI = "USER_AI"
    USER_AGENT = "USER_AGENT"