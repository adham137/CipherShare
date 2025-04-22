import socket
import os
from .command_strategy import CommandStrategy
from src.utils.config import Config
from src.utils.commands_enum import Commands 


class DownloadStrategy(CommandStrategy):
    """Handles the file download command."""

    def get_file_path(self, file_id_str: str, shared_files_path: str):
        """Looks up the file path based on a simple index (file_id)."""
        try:
            file_id = int(file_id_str)
            # Ensure the shared directory exists
            if not os.path.exists(shared_files_path) or not os.path.isdir(shared_files_path):
                 print(f"Peer (Download): Shared directory '{shared_files_path}' not found.")
                 return None

            files = sorted([f for f in os.listdir(shared_files_path) if os.path.isfile(os.path.join(shared_files_path, f))]) # List only files and sort

            if 0 <= file_id < len(files):
                return os.path.join(shared_files_path, files[file_id])
            else:
                print(f"Peer (Download): Invalid file ID {file_id}. Max index is {len(files)-1}.")
                return None
        except ValueError:
            print(f"Peer (Download): Invalid file ID format: '{file_id_str}'. Must be an integer.")
            return None
        except Exception as e:
            print(f"Peer (Download): Error accessing shared files directory '{shared_files_path}': {e}")
            return None


    def execute(self, client_socket: socket.socket, **kwargs):
        """Handles sending a requested file."""
        file_id_str = kwargs.get('file_id_str')
        if not file_id_str:
            print("Peer (Download): File ID not provided.")
            # Optionally send an error back to the client
            return

        filepath = self.get_file_path(file_id_str, Config.SHARED_FILES_DIR)
        if filepath and os.path.exists(filepath):
            filename = os.path.basename(filepath)
            print(f"Peer (Download): Sending file '{filename}' (ID: {file_id_str})...")
            try:
                with open(filepath, 'rb') as f:
                    while True:
                        chunk = f.read(Config.CHUNK_SIZE)
                        if not chunk:
                            break
                        client_socket.sendall(chunk) # Use sendall for reliability
                # Send DONE signal
                client_socket.sendall(str(Commands.DONE).encode('utf-8'))
                print(f"Peer (Download): File '{filename}' sent successfully.")
            except FileNotFoundError:
                 print(f"Peer (Download): Error: File '{filename}' not found at path '{filepath}' (should not happen after check).")
                 # Consider sending an error signal
            except Exception as e:
                print(f"Peer (Download): Error sending file '{filename}': {e}")
                # Consider sending an error signal
        else:
            print(f"Peer (Download): Error: File with ID {file_id_str} not found or path is invalid.")
            # Send an error signal or specific message back to the client
            