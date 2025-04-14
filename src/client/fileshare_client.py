import socket
import os
import sys
import json
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.config import Config 
from src.utils.commands_enum import Commands 

from src.utils import crypto_utils

from src.peer.fileshare_peer import FileSharePeer


REGISTRY_ADDRESS = Config.REGISTRY_IP
REGISTRY_PORT = Config.REGISTRY_PORT
CHUNK_SIZE = Config.CHUNK_SIZE 



class FileShareClient:
    def __init__(self, username):
        self.username = username
        self.peer_address = None
        self.peer_listening_port = None # Store the port the peer thread is listening on
        self.shared_files = [] # Keep track of files this client's peer is sharing (IDs, names)

    def _connect_socket(self, address, port):
        """Helper to create and connect a socket."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((address, port))
            return sock
        except socket.error as e:
            print(f"Client: Socket error connecting to {address}:{port}: {e}")
            return None

    def register_with_registry(self):
        if not self.peer_address:
             print("Client: Cannot register with registry, peer address not set.")
             return False
        
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return False

        try:
            request = {"command": str(Commands.REGISTER_PEER),
                       "username": self.username,
                       "peer_address": self.peer_address} 
            sock.sendall(json.dumps(request).encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            if response == "OK":
                print(f"Client: Registered '{self.username}' with registry successfully.")
                return True
            else:
                print(f"Client: Registry registration failed. Response: {response}")
                return False
        except Exception as e:
            print(f"Client: Error during registry registration: {e}")
            return False
        finally:
            sock.close()

    def get_peers(self):
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return []
        try:
            request = {"command": str(Commands.GET_PEERS)}
            sock.sendall(json.dumps(request).encode('utf-8'))
            response_data = sock.recv(4096).decode('utf-8')
            peer_list = json.loads(response_data)
            # Filter out self
            peer_list = [tuple(p) for p in peer_list if tuple(p) != self.peer_address]
            return peer_list
        except json.JSONDecodeError:
             print("Client: Error decoding peer list JSON from registry.")
             return []
        except Exception as e:
            print(f"Client: Error getting peers from registry: {e}")
            return []
        finally:
            sock.close()

    def upload_file(self, filepath, peer_address):
        if not os.path.isfile(filepath):
            print(f"Client: Error - File not found at '{filepath}'")
            return False

        filename = os.path.basename(filepath)
        sock = self._connect_socket(peer_address[0], peer_address[1]) # Use tuple elements
        if not sock:
            return False

        try:
            # Send command and filename together, separated by newline, REVISE THIS
            command_msg = f"{str(Commands.UPLOAD)}\n{filename}\n"
            sock.sendall(command_msg.encode('utf-8'))
            print(f"Client: Sending command '{Commands.UPLOAD}' and filename '{filename}' to {peer_address}")

            # Send the file in chunks
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk) 
            
            # Send DONE signal separately
            sock.sendall(str(Commands.DONE).encode('utf-8')) 
            print(f"Client: File '{filename}' uploaded to peer {peer_address}.")
            
            # Register file with registry AFTER successful upload
            file_id = self.register_file_with_registry(filename)
            if file_id is not None:
                 print(f"Client: File '{filename}' registered with registry (ID: {file_id}).")
                 # Optionally add to local list: self.shared_files.append({'id': file_id, 'name': filename})
                 return True
            else:
                 print(f"Client: Warning - File '{filename}' uploaded but failed to register with registry.")
                 return False # Indicate partial success/failure

        except Exception as e:
            print(f"Client: Error uploading file '{filename}' to {peer_address}: {e}")
            return False
        finally:
            sock.close()

    def download_file(self, file_id_str, destination_path, peer_address, filename):
         # Ensure destination directory exists
         os.makedirs(destination_path, exist_ok=True)

         sock = self._connect_socket(peer_address[0], peer_address[1]) 
         if not sock:
             return False

         try:
             # Send command and file ID together, separated by newline, REVISE THIS
             command_msg = f"{str(Commands.DOWNLOAD)}\n{file_id_str}\n"
             sock.sendall(command_msg.encode('utf-8'))
             print(f"Client: Requesting file ID '{file_id_str}' ({filename}) from {peer_address}")

             filepath = os.path.join(destination_path, filename)
             with open(filepath, 'wb') as f:
                 while True:
                     chunk = sock.recv(CHUNK_SIZE)
                     # Check for DONE signal - assumes DONE signal is sent alone and reliably
                     if not chunk or chunk.decode(errors='ignore').strip() == str(Commands.DONE):
                         break
                     # Check for ERROR signal (Optional, requires peer to send it)
                     # if chunk.decode(errors='ignore').strip() == str(Commands.ERROR):
                     #     print(f"Client: Peer {peer_address} reported an error downloading file ID {file_id_str}.")
                     #     # Clean up potentially incomplete file
                     #     f.close()
                     #     if os.path.exists(filepath): os.remove(filepath)
                     #     return False
                     f.write(chunk)

             print(f"Client: File '{filename}' (ID: {file_id_str}) downloaded to '{destination_path}'.")
             return True
         except Exception as e:
             print(f"Client: Error downloading file ID {file_id_str} from {peer_address}: {e}")
             # Clean up potentially incomplete file
             if 'f' in locals() and not f.closed: f.close()
             if os.path.exists(filepath): os.remove(filepath)
             return False
         finally:
             sock.close()

    def register_file_with_registry(self, filename):
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return None

        try:
            request = {"command": str(Commands.REGISTER_FILE), 
                       "filename": filename,
                       "owner": self.username}
            sock.sendall(json.dumps(request).encode('utf-8'))
            response_data = sock.recv(1024).decode('utf-8')
            response = json.loads(response_data)
            file_id = response.get("file_id")
            if file_id is not None:
                 return file_id
            else:
                 print(f"Client: Error registering file '{filename}' - Registry did not return file_id. Response: {response_data}")
                 return None
        except json.JSONDecodeError:
             print("Client: Error decoding file registration JSON from registry.")
             return None
        except Exception as e:
            print(f"Client: Error registering file '{filename}' with registry: {e}")
            return None
        finally:
            sock.close()

    def get_files_from_registry(self):
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return {}
        try:
            request = {"command": str(Commands.GET_FILES)}
            sock.sendall(json.dumps(request).encode('utf-8'))
            response_data = sock.recv(4096).decode('utf-8')
            file_list = json.loads(response_data)
            return file_list # Returns dict {file_id_str: {filename: name, owner: user}}
        except json.JSONDecodeError:
            print("Client: Error decoding file list JSON from registry.")
            return {}
        except Exception as e:
            print(f"Client: Error getting file list from registry: {e}")
            return {}
        finally:
            sock.close()

    def start_peer_thread(self, requested_port=0):
        """Starts the peer functionality in a separate thread."""
        try:
            peer = FileSharePeer(requested_port) # Pass 0 for OS to choose port
            self.peer_listening_port = peer.port # Get the actual port chosen
            self.peer_address = (Config.PEER_HOST, self.peer_listening_port) 

            peer_thread = threading.Thread(target=peer.start_peer, daemon=True)
            peer_thread.start()
            print(f"Client: Peer thread started listening on {self.peer_address}")
            return True
        except Exception as e:
            print(f"Client: Failed to start peer thread: {e}")
            self.peer_address = None
            self.peer_listening_port = None
            return False


# --- Basic UI ---
def client_ui(client: FileShareClient):
    while True:
        print("\n--- CipherShare Client ---")
        print("1. List Peers")
        print("2. Upload File")
        print("3. List Available Files (from Registry)")
        print("4. Download File")
        # print("5. List My Shared Files") # Future
        print("6. Exit")
        print("------------------------")

        choice = input("Enter choice: ")

        if choice == '1':
            peers = client.get_peers()
            if peers:
                print("Available Peers (excluding self):")
                for i, peer in enumerate(peers):
                    print(f"{i}: {peer}")
            else:
                print("No other peers found.")
        elif choice == '2':
            filepath = input("Enter full file path to upload: ")
            if not os.path.isfile(filepath):
                 print(f"Error: File not found at '{filepath}'")
                 continue

            peers = client.get_peers()
            if not peers:
                print("No other peers available to upload to.")
                continue

            print("Choose a peer to upload to:")
            for i, peer in enumerate(peers):
                print(f"{i}: {peer}")
            try:
                 peer_index_str = input(f"Enter peer index (0 to {len(peers)-1}): ")
                 peer_index = int(peer_index_str)
                 if 0 <= peer_index < len(peers):
                     selected_peer_address = peers[peer_index]
                     client.upload_file(filepath, selected_peer_address)
                 else:
                     print("Invalid peer index.")
            except ValueError:
                 print("Invalid input. Please enter a number.")

        elif choice == '3':
            files = client.get_files_from_registry()
            if files:
                print("Available Files on the Network:")
                # Sort by file_id for consistent display
                sorted_file_ids = sorted(files.keys(), key=int)
                for file_id in sorted_file_ids:
                    file_info = files[file_id]
                    print(f"ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']}")
            else:
                print("No files found in the registry.")

        elif choice == '4':
            files = client.get_files_from_registry()
            if not files:
                print("No files available to download. Try listing files first (option 3).")
                continue
            
            # Display files again for convenience
            print("Available Files on the Network:")
            sorted_file_ids = sorted(files.keys(), key=int)
            for file_id in sorted_file_ids:
                file_info = files[file_id]
                print(f"ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']}")
            
            file_id_str = input("Enter file ID to download: ")
            
            # Validate file_id
            if file_id_str not in files:
                print(f"Error: Invalid file ID '{file_id_str}'.")
                continue

            destination_path = input("Enter destination directory path (e.g., ./downloads): ")
            if not os.path.isdir(destination_path):
                 create_dest = input(f"Directory '{destination_path}' does not exist. Create it? (y/n): ")
                 if create_dest.lower() == 'y':
                     try:
                         os.makedirs(destination_path)
                         print(f"Created directory: {destination_path}")
                     except OSError as e:
                         print(f"Error creating directory: {e}")
                         continue
                 else:
                     print("Download cancelled.")
                     continue


            # Find the peer address of the owner
            owner_username = files[file_id_str]["owner"]
            all_peers_incl_self = client.get_peers() # Get all peers again
            # Add self address if known
            if client.peer_address:
                 # Need to get full list including self from somewhere, registry might not have it updated instantly
                 # For simplicity, assume registry is mostly up-to-date or client knows peer address
                 # A better approach might involve querying the registry for the owner's specific address
                 
                 # Let's try to find the owner in the list returned by registry
                 owner_address = None
                 registry_peers = client.get_peers() # Call registry again for updated list
                 # Also check against known registered peers (requires client to store this)
                 # We need a reliable way to map username to current address. Registry is the source.
                 
                 # Attempt to fetch owner address from registry based on username
                 # This requires enhancing the registry to allow lookup by username,
                 # or enhancing the GET_PEERS/GET_FILES response to include addresses.
                 
                 # **Simplification:** Assume the owner is one of the peers returned by get_peers().
                 # This is NOT robust. A direct lookup mechanism is needed.
                 # Let's iterate through known peers (this relies on the client having called get_peers previously)
                 
                 # **Revised Simplification for Phase 1:** Connect to *any* peer that *might* have the file.
                 # Since Phase 1 doesn't enforce that only the owner serves the file,
                 # we can *try* downloading from any known peer. This is inefficient and insecure.
                 # A better Phase 1 might involve the registry returning the owner's address with GET_FILES.

                 # **Workaround for current structure:** Find the owner's *expected* address.
                 # This assumes the peer list from get_peers is somewhat accurate and contains the owner.
                 # This requires the peer list from get_peers to map usernames to addresses, which it currently doesn't explicitly.
                 # The current `get_peers` returns only list of addresses.
                 
                 # **Let's stick to the original logic flaw for now, assuming peer address can be found**
                 # (This needs fixing in a real system - the registry needs to provide owner address)
                 
                 print(f"Client: Attempting to find address for owner '{owner_username}'...")
                 # Problem: get_peers only returns addresses, not usernames.
                 # We need the registry to return {username: address} or enhance GET_FILES.
                 
                 # **Temporary Fix:** Ask user to select peer (like upload) - less ideal but works with current limitations.
                 peers_for_download = client.get_peers()
                 if not peers_for_download:
                      print("No peers available to download from.")
                      continue

                 print(f"Select a peer likely to have the file (owned by '{owner_username}'):")
                 for i, peer in enumerate(peers_for_download):
                      print(f"{i}: {peer}")
                 try:
                     peer_index_str = input(f"Enter peer index (0 to {len(peers_for_download)-1}): ")
                     peer_index = int(peer_index_str)
                     if 0 <= peer_index < len(peers_for_download):
                         selected_peer_address = peers_for_download[peer_index]
                         client.download_file(file_id_str, destination_path, selected_peer_address, files[file_id_str]["filename"])
                     else:
                         print("Invalid peer index.")
                 except ValueError:
                      print("Invalid input. Please enter a number.")

            else:
                print("Could not determine own peer address. Cannot proceed.")


        # elif choice == '5':
        #     shared_files = client.list_shared_files()
        #     print("Locally Tracked Shared Files:", shared_files)
        elif choice == '6':
            print("Exiting CipherShare Client.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # Ensure necessary directories exist relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shared_files_dir = os.path.join(script_dir, '..', Config.SHARED_FILES_DIR) # Adjust path as needed
    os.makedirs(shared_files_dir, exist_ok=True)
    
    username = input("Enter your username: ")
    client = FileShareClient(username)
    
    # Start peer thread first to get listening address
    if client.start_peer_thread():
        # Register with registry only after peer is listening
        if not client.register_with_registry():
             print("!!! Warning: Failed to register with registry. Peer discovery may fail.")
        
        # Start the UI thread
        client_ui_thread = threading.Thread(target=client_ui, args=(client,))
        client_ui_thread.start()
        client_ui_thread.join() # Wait for UI thread to finish (on exit)
    else:
         print("!!! Error: Could not start peer listener. Client cannot operate.")