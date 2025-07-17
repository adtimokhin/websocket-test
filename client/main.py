"""
Very simple python-based client to talk to the websocket

Websocket connection exists on:
http://127.0.0.1:8080/echo

In order to start the server, you will need to start the appropriate project
"""

import asyncio
import websockets # type: ignore
import sys
import threading

ECHO_URI = "ws://127.0.0.1:8080/echo"
BROADCAST_URI = "ws://127.0.0.1:8080/broadcast"

class BroadcastClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.running = True
        
    async def listen_for_messages(self):
        """
        Continuously listen for incoming messages from the server
        """
        try:
            while self.running:
                try:
                    response = await self.websocket.recv() # type: ignore
                    print(f"\n[RECEIVED]: {response}")
                    print("Enter message: ", end="", flush=True)  # Prompt user again
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by server")
                    break
                except Exception as e:
                    print(f"\nError receiving message: {e}")
                    break
        except Exception as e:
            print(f"Error in message listener: {e}")
    
    async def send_messages(self):
        """
        Handle user input and send messages to the server
        """
        import queue
        
        # Create a queue to communicate between threads
        message_queue = queue.Queue()
        
        def get_input():
            """Get input in a separate thread to avoid blocking"""
            try:
                while self.running:
                    message = input("Enter message: ")
                    if message.lower() in ['quit', 'exit', 'q']:
                        self.running = False
                        break
                    message_queue.put(message)
            except KeyboardInterrupt:
                self.running = False
        
        # Run input in a separate thread
        input_thread = threading.Thread(target=get_input, daemon=True)
        input_thread.start()
        
        # Process messages from the queue in the main async loop
        while self.running:
            try:
                # Check for messages in the queue (non-blocking)
                message = message_queue.get_nowait()
                await self.send_message(message)
            except queue.Empty:
                # No messages in queue, continue
                pass
            
            await asyncio.sleep(0.1)
    
    async def send_message(self, message: str):
        """
        Send a single message to the server
        """
        try:
            await self.websocket.send(message) # type: ignore
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def connect_and_run(self):
        """
        Main connection and message handling loop
        """
        try:
            print("Connecting to server...")
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                print("Connected! Type messages to send (type 'quit' or Ctrl+C to exit)")
                
                # Run both listening and sending concurrently
                await asyncio.gather(
                    self.listen_for_messages(),
                    self.send_messages(),
                    return_exceptions=True
                )
                
        except ConnectionRefusedError:
            print(f"Could not connect to server. Make sure the server is running on {self.uri}")
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.running = False
            print("Connection terminated. Goodbye!")

async def main(connection_uri: str):
    """
    Main program loop.
    To exit you'll need to do KeyBoard Interrupt or type 'quit'
    """
    client = BroadcastClient(connection_uri)
    await client.connect_and_run()

if __name__ == "__main__":
    # Simple argument parsing
    if len(sys.argv) > 1:
        if sys.argv[1] == "echo":
            uri = ECHO_URI
        elif sys.argv[1] == "broadcast":
            uri = BROADCAST_URI
        else:
            print("Usage: python client.py [echo|broadcast]")
            sys.exit(1)
    else:
        uri = BROADCAST_URI  # Default to broadcast
    
    print(f"Connecting to: {uri}")
    asyncio.run(main(uri))