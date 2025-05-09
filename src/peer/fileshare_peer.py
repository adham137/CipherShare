# src/peer/fileshare_peer.py
import socket
import threading
import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.config import Config 
from src.utils.commands_enum import Commands 
from src.peer.command_factory import CommandFactory 

# from utils import crypto_utils


PEER_HOST = Config.PEER_HOST
CHUNK_SIZE = Config.CHUNK_SIZE
SHARED_FILES_PATH = Config.SHARED_FILES_DIR # Directory to store shared files



class FileSharePeer:
    def __init__(self, requested_port=0): # Allow requesting port 0 for dynamic assignment
        self.host = PEER_HOST
        self.port = requested_port 
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        try:
             
             self.peer_socket.bind((self.host, self.port))
             self.port = self.peer_socket.getsockname()[1] # Get the actual port (if port was 0)
        except OSError as e:
             print(f"Peer: Error binding socket to {self.host}:{self.port} - {e}")
             raise # Re-raise the exception to signal failure


    def start_peer(self):
        try:
            self.peer_socket.listen(5)
            print(f"Peer: Listening on {self.host}:{self.port}")
            while True:
                try:
                    client_socket, client_address = self.peer_socket.accept()
                    print(f"Peer: Accepted connection from {client_address}")
                    # Start a new thread for each client connection
                    client_thread = threading.Thread(target=self.handle_client_connection,
                                                     args=(client_socket, client_address),
                                                     daemon=True) 
                    client_thread.start()
                except Exception as e:
                    print(f"Peer: Error accepting connection: {e}")
                    # Decide if the loop should continue or break based on the error

        except KeyboardInterrupt:
             print("\nPeer: Shutting down...")
        except Exception as e:
            print(f"Peer: Server loop error: {e}")
        finally:
            self.peer_socket.close()
            print("Peer: Server socket closed.")

    def handle_client_connection(self, client_socket: socket.socket, client_address):
        print(f"Peer: Handling connection from {client_address}")
        command_str = None
        try:
            # Read the first line for the command
            command_line = b""
            while b"\n" not in command_line:
                 chunk = client_socket.recv(1)
                 if not chunk: # Connection closed prematurely
                      print(f"Peer: Connection from {client_address} closed before command received.")
                      return
                 command_line += chunk
            
            
            command_str = command_line.decode('utf-8').strip()
            command = Commands.from_string(command_str) # Convert string to Enum
            
            print(f"Peer: Received command '{command_str}' from {client_address}")

            if command:
                handler = CommandFactory.get_command_handler(command)
                if handler:
                    # Prepare arguments for the handler
                    handler_args = {'client_socket': client_socket}

                   
                    if command == Commands.UPLOAD:
                   
                        filename_line = b""
                        while b"\n" not in filename_line:
                             chunk = client_socket.recv(1)
                             if not chunk: break
                             filename_line += chunk
                        handler_args['filename'] = filename_line.decode('utf-8').strip()

                    elif command == Commands.DOWNLOAD:
                        
                        file_id_line = b""
                        while b"\n" not in file_id_line:
                             chunk = client_socket.recv(1)
                             if not chunk: break
                             file_id_line += chunk
                        handler_args['file_id_str'] = file_id_line.decode('utf-8').strip()

                    elif command == Commands.GET_PEER_FILES:
                        # for GET_PEER_FILES, the command line is the entire request for now
                        pass 

                    # Execute the command using the strategy
                    print(f"Peer: Executing handler for command {command} with args: { {k:v for k,v in handler_args.items() if k!='client_socket'} }")
                    handler.execute(**handler_args)
                else:
                    print(f"Peer: No handler found for command '{command_str}'")
                    # Optionally send an error response to the client
            else:
                print(f"Peer: Received unknown command: '{command_str}'")
                # Optionally send an error response to the client

        except ConnectionResetError:
             print(f"Peer: Connection from {client_address} reset.")
        except socket.timeout:
             print(f"Peer: Socket timeout handling client {client_address}.")
        except UnicodeDecodeError:
             print(f"Peer: Error decoding command '{command_str or '?'}' from {client_address}. Ensure UTF-8 encoding.")
        except Exception as e:
            print(f"Peer: Error handling client {client_address} (Command: {command_str or 'N/A'}): {type(e).__name__} - {e}")
        finally:
            print(f"Peer: Closing connection from {client_address}")
            client_socket.close()

