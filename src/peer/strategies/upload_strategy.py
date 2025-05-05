import socket
import os
from .command_strategy import CommandStrategy
from src.utils.config import Config 
from src.utils.commands_enum import Commands 

class UploadStrategy(CommandStrategy):
    """Handles the file upload command."""

    def execute(self, client_socket: socket.socket, **kwargs):
        
        filename = kwargs.get('filename')
        if not filename:
            print("Peer (Upload): Filename not provided.")
            # Optionally send an error back to the client
            return

        filepath = os.path.join(Config.SHARED_FILES_DIR, filename)
        print(f"Peer (Upload): Receiving file '{filename}' to '{filepath}'...")
        try:
            with open(filepath, 'wb') as f:
                while True:
                    chunk = client_socket.recv(Config.CHUNK_SIZE)
                    # Check for DONE signal
                    if not chunk or chunk.decode('utf-8', errors='ignore').strip() == str(Commands.DONE):
                        break
                    f.write(chunk)
            print(f"Peer (Upload): File '{filename}' received successfully.")
        except Exception as e:
            print(f"Peer (Upload): Error receiving file '{filename}': {e}")
            # Clean up potentially incomplete file
            if os.path.exists(filepath):
                os.remove(filepath)