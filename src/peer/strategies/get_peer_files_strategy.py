import socket
import os
import json
from .command_strategy import CommandStrategy
from src.utils.config import Config
from src.utils.commands_enum import Commands
class GetPeerFilesStrategy(CommandStrategy):
    """Handles the command to list files available on this peer."""

    def execute(self, client_socket: socket.socket, **kwargs):
        """Lists files in the shared directory and sends the list to the client."""
        shared_files_path = Config.SHARED_FILES_DIR
        files_list = []

        print(f"Peer (GetPeerFiles): Listing files in '{shared_files_path}' for connected client.")

        try:
            
            if os.path.exists(shared_files_path) and os.path.isdir(shared_files_path):
                
                files = [f for f in os.listdir(shared_files_path) if os.path.isfile(os.path.join(shared_files_path, f)) and not f.startswith('.')]
                
                for filename in sorted(files): # sort for consistent order
                    filepath = os.path.join(shared_files_path, filename)
                    try:
                        filesize = os.path.getsize(filepath)
                        files_list.append({"filename": filename, "size": filesize})
                    except Exception as size_e:
                        print(f"Peer (GetPeerFiles): Could not get size for {filename}: {size_e}")
                        files_list.append({"filename": filename, "size": "N/A"}) 


            # send the list as a JSON response
            response = {"status": "OK", "files": files_list}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            print(f"Peer (GetPeerFiles): Sent file list ({len(files_list)} files) to client.")

        except Exception as e:
            print(f"Peer (GetPeerFiles): Error listing or sending files: {e}")
            error_response = {"status": "ERROR", "message": f"Error listing files: {e}"}
            client_socket.sendall(json.dumps(error_response).encode('utf-8'))

