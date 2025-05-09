import socket
import os
import sys
import json
import threading

from colorama import Fore, Style

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.ui_utils import client_ui
from src.utils.config import Config
from src.utils.commands_enum import Commands

from src.utils import crypto_utils

from src.peer.fileshare_peer import FileSharePeer


REGISTRY_ADDRESS = Config.REGISTRY_IP
REGISTRY_PORT = Config.REGISTRY_PORT
CHUNK_SIZE = Config.CHUNK_SIZE


class FileShareClient:
    def __init__(self):
        self.username = None
        self.session_id = None
        self.key = None # this is the user's symmetric key derived from their password
        self.peer_address = None
        self.peer_listening_port = None # store the port the peer thread is listening on
        # self.shared_files = [] # Keep track of files this client's peer is sharing (IDs, names) - Registry is the source of truth now

    def _connect_socket(self, address, port):
        """Helper to create and connect a socket."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((address, port))
            return sock
        except socket.error as e:
            print(Fore.RED + f"Client: Socket error connecting to {address}:{port}: {e}" + Style.RESET_ALL)
            return None

    def _send_registry_request(self, request):
        """Helper to send a request to the registry and receive the response."""
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return {"status": "ERROR", "message": "Could not connect to registry"}
        try:
            sock.sendall(json.dumps(request).encode())
            response = sock.recv(4096).decode() # Increased buffer size
            return json.loads(response)
        except json.JSONDecodeError:
            print(Fore.RED + "Client: Error decoding JSON response from registry." + Style.RESET_ALL)
            return {"status": "ERROR", "message": "Invalid response from registry"}
        except Exception as e:
            print(Fore.RED + f"Client: Error communicating with registry: {e}" + Style.RESET_ALL)
            return {"status": "ERROR", "message": f"Registry communication error: {e}"}
        finally:
            sock.close()
    def get_files_from_peers(self):
        """Fetches file lists from all active peers."""
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot discover files from peers." + Style.RESET_ALL)
            return {}

        print(Fore.YELLOW + "Client: Discovering files from active peers..." + Style.RESET_ALL)
        active_peers = self.get_peers() # Get active peers from the registry
        all_peer_files = {} # {peer_address: [{filename, size}, ...]}

        if not active_peers:
            print(Fore.YELLOW + "Client: No other active peers found to query." + Style.RESET_ALL)
            return all_peer_files

        for peer_addr in active_peers:
            print(f"Client: Querying peer {peer_addr} for file list...")
            sock = self._connect_socket(peer_addr[0], peer_addr[1])
            if not sock:
                print(Fore.RED + f"Client: Could not connect to peer {peer_addr}." + Style.RESET_ALL)
                continue

            try:
                # Send the GET_PEER_FILES command
                command_msg = f"{str(Commands.GET_PEER_FILES)}\n"
                sock.sendall(command_msg.encode('utf-8'))


                response_data = b''
                # Set a shorter timeout for receiving from peer after sending command
                sock.settimeout(10) # e.g., 10 seconds to get the file list response

                while True:
                    chunk = sock.recv(4096) # Read in chunks
                    if not chunk:
                        break # Connection closed by peer
                    response_data += chunk

                if not response_data:
                    print(Fore.RED + f"Client: No response received from peer {peer_addr}." + Style.RESET_ALL)
                    continue

                try:
                    response = json.loads(response_data.decode('utf-8'))
                    if response.get("status") == "OK":
                        all_peer_files[peer_addr] = response.get("files", [])
                        print(Fore.GREEN + f"Client: Successfully received file list from {peer_addr}." + Style.RESET_ALL)
                    else:
                         print(Fore.RED + f"Client: Error response from peer {peer_addr}: {response.get('message', 'Unknown error')}" + Style.RESET_ALL)

                except json.JSONDecodeError:
                    print(Fore.RED + f"Client: Error decoding JSON response from peer {peer_addr}." + Style.RESET_ALL)
                except Exception as response_e:
                    print(Fore.RED + f"Client: Error processing response from peer {peer_addr}: {response_e}" + Style.RESET_ALL)


            except Exception as e:
                print(Fore.RED + f"Client: Error communicating with peer {peer_addr}: {e}" + Style.RESET_ALL)
            finally:
                sock.close()

        return all_peer_files

    def register_user(self, username, password):
        if not self.peer_address:
             print(Fore.RED + "Client: Cannot register with registry, peer address not set." + Style.RESET_ALL)
             return False

        request = {"command": str(Commands.REGISTER_USER), "username": username, "password": password, "peer_address": self.peer_address}
        response_data = self._send_registry_request(request)

        if response_data["status"] == "OK":
            print(Fore.GREEN + "Client: Registration successful!" + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"Client: Registration failed: {response_data['message']}" + Style.RESET_ALL)
            return False

    def login_user(self, username, password):
        if not self.peer_address:
             print(Fore.RED + "Client: Cannot login with registry, peer address not set." + Style.RESET_ALL)
             return False

        request = {"command": str(Commands.LOGIN_USER), "username": username, "password": password, "peer_address": self.peer_address}
        response_data = self._send_registry_request(request)

        if response_data["status"] == "OK":
            self.username = username
            self.session_id = response_data["session_id"]
            self.key = response_data["key"] # User's own key
            # print(f"Recieved sessionId: ({self.session_id})\nRecieved key: ({self.key})") # Avoid printing sensitive info
            print(Fore.GREEN + "Client: Login successful!" + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"Client: Login failed: {response_data['message']}" + Style.RESET_ALL)
            self.username = None
            self.session_id = None
            self.key = None
            return False
    def logout(self):
        self.username = None
        self.session_id = None
        self.key = None
    def get_peers(self):
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot get peers." + Style.RESET_ALL)
            return []

        request = {"command": str(Commands.GET_PEERS), "session_id": self.session_id}
        response_data = self._send_registry_request(request)

        peer_list = response_data # assuming response_data is the list of peers
        # filter out self
        peer_list = [tuple(p) for p in peer_list if tuple(p) != self.peer_address]
        return peer_list

    def get_files_from_registry(self):
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot get file list." + Style.RESET_ALL)
            return {}

        request = {"command": str(Commands.GET_FILES), "session_id": self.session_id}
        response_data = self._send_registry_request(request)

        if response_data.get("status") == "ERROR": # Handle potential errors from _send_registry_request
             print(Fore.RED + f"Client: Error getting file list: {response_data['message']}" + Style.RESET_ALL)
             return {}

        return response_data # assuming response_data is the dictionary of files

    def register_file_with_registry(self, filename, file_hash):
        if not self.session_id or not self.username or not self.peer_address:
            print(Fore.RED + "Client: Not logged in or peer address not set. Cannot register file." + Style.RESET_ALL)
            return None

        request = {"command": str(Commands.REGISTER_FILE),
                   "session_id": self.session_id,
                   "filename": filename,
                   # "owner": self.username, # Owner is determined by the registry from session_id
                   "owner_address": self.peer_address,
                   "file_hash":     file_hash}
        response_data = self._send_registry_request(request)

        if response_data.get("status") == "OK":
            file_id = response_data.get("file_id")
            if file_id is not None:
                 print(Fore.GREEN + f"Client: File '{filename}' registered with registry (ID: {file_id}, hash {file_hash})." + Style.RESET_ALL)
                 return file_id
            else:
                 print(Fore.RED + f"Client: Error registering file '{filename}' - Registry did not return file_id. Response: {response_data}" + Style.RESET_ALL)
                 return None
        else:
             print(Fore.RED + f"Client: Error registering file '{filename}': {response_data.get('message', 'Unknown error')}" + Style.RESET_ALL)
             return None

    def request_key(self, file_id):
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot request key." + Style.RESET_ALL)
            return None

        request = {"command": str(Commands.REQUEST_KEY),
                   "session_id": self.session_id,
                   "file_id": file_id}
        response_data = self._send_registry_request(request)

        if response_data.get("status") == "OK":
            key = response_data.get("key")
            if key:
                # print(f"Recieved key: ({key})") # Avoid printing sensitive info
                print(Fore.GREEN + f"Client: Successfully retrieved key for file ID {file_id}." + Style.RESET_ALL)
                return key
            else:
                 print(Fore.RED + f"Client: Registry did not return a key for file ID {file_id}. Response: {response_data}" + Style.RESET_ALL)
                 return None
        else:
            print(Fore.RED + f"Client: Failed to retrieve key for file ID {file_id}: {response_data.get('message', 'Unknown error')}" + Style.RESET_ALL)
            return None

    def check_access(self, file_id):
        """Checks with the registry if the current user has access to a file."""
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot check access." + Style.RESET_ALL)
            return False

        request = {"command": str(Commands.CHECK_ACCESS),
                   "session_id": self.session_id,
                   "file_id": file_id}
        response_data = self._send_registry_request(request)

        if response_data.get("status") == "OK":
            print(Fore.GREEN + f"Client: Access granted for file ID {file_id}." + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"Client: Access denied for file ID {file_id}: {response_data.get('message', 'Unknown error')}" + Style.RESET_ALL)
            return False

    def share_file(self, file_id, target_username):
        """Shares a file (by ID) with another user."""
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot share file." + Style.RESET_ALL)
            return False

        request = {"command": str(Commands.SHARE_FILE),
                   "session_id": self.session_id,
                   "file_id": file_id,
                   "target_username": target_username}
        response_data = self._send_registry_request(request)

        if response_data.get("status") == "OK":
            print(Fore.GREEN + f"Client: Successfully shared file ID {file_id} with '{target_username}'." + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"Client: Failed to share file ID {file_id} with '{target_username}': {response_data.get('message', 'Unknown error')}" + Style.RESET_ALL)
            return False

    def revoke_access(self, file_id, target_username):
        """Revokes access to a file (by ID) for another user."""
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot revoke access." + Style.RESET_ALL)
            return False

        request = {"command": str(Commands.REVOKE_ACCESS),
                   "session_id": self.session_id,
                   "file_id": file_id,
                   "target_username": target_username}
        response_data = self._send_registry_request(request)

        if response_data.get("status") == "OK":
            print(Fore.GREEN + f"Client: Successfully revoked access to file ID {file_id} for '{target_username}'." + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"Client: Failed to revoke access to file ID {file_id} for '{target_username}': {response_data.get('message', 'Unknown error')}" + Style.RESET_ALL)
            return False


    def upload_file(self, filepath): # simplified upload - always upload to your own peer
        if not self.session_id or not self.peer_address or not self.key:
            print(Fore.RED + "Client: Not logged in or peer address/key not set. Cannot upload file." + Style.RESET_ALL)
            return False

        if not os.path.isfile(filepath):
            print(Fore.RED + f"Client: Error - File not found at '{filepath}'" + Style.RESET_ALL)
            return False

        filename = os.path.basename(filepath)
        sock = self._connect_socket(self.peer_address[0], self.peer_address[1]) # Connect to own peer
        if not sock:
            return False

        try:
            # Send command and filename
            command_msg = f"{str(Commands.UPLOAD)}\n{filename}\n"
            sock.sendall(command_msg.encode('utf-8'))
            print(f"Client: Sending command '{Commands.UPLOAD}' and filename '{filename}' to own peer {self.peer_address}")

            # Compute integrity hash over plaintext
            file_hash = crypto_utils.compute_file_hash(filepath)

            # Encrypt entire file using the user's key
            with open(filepath, 'rb') as f:
                plaintext = f.read()
            ciphertext = crypto_utils.encrypt_data(plaintext, self.key)

            # Send encrypted bytes in chunks
            for i in range(0, len(ciphertext), CHUNK_SIZE):
                sock.sendall(ciphertext[i:i+CHUNK_SIZE])



            print(Fore.GREEN + f"Client: Encrypted File '{filename}' uploaded to own peer {self.peer_address}." + Style.RESET_ALL)

            # Register file with registry AFTER successful upload
            file_id = self.register_file_with_registry(filename, file_hash)
            if file_id is not None:
                 print(Fore.GREEN + f"Client: File '{filename}' registered with registry (ID: {file_id})." + Style.RESET_ALL)
                 return True
            else:
                 print(Fore.RED + f"Client: Warning - File '{filename}' uploaded but failed to register with registry." + Style.RESET_ALL)
                 return False # Indicate partial success/failure

        except Exception as e:
            print(Fore.RED + f"Client: Error uploading file '{filename}' to own peer {self.peer_address}: {e}" + Style.RESET_ALL)
            return False
        finally:
            sock.close()


    def download_file(self, file_id_str, destination_path, peer_address, filename, expected_hash):
        """
        Handles the download process including access check and key retrieval.
        Note: The key is now retrieved dynamically via request_key after access check.
        """
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot download file." + Style.RESET_ALL)
            return False

        # 1) check access with the registry
        if not self.check_access(file_id_str):
             print(Fore.RED + f"Client: Access denied for file ID {file_id_str}. Cannot download." + Style.RESET_ALL)
             return False

        # 2) if access is granted, request the decryption key from the registry
        decryption_key = self.request_key(file_id_str)
        if not decryption_key:
             print(Fore.RED + f"Client: Failed to retrieve decryption key for file ID {file_id_str}. Cannot download." + Style.RESET_ALL)
             return False


        # ensure destination directory exists
        os.makedirs(destination_path, exist_ok=True)

        sock = self._connect_socket(peer_address[0], peer_address[1])
        if not sock:
            return False

        filepath = os.path.join(destination_path, filename)

        try:
             # send command and file ID to the peer
            command_msg = f"{str(Commands.DOWNLOAD)}\n{file_id_str}\n"
            sock.sendall(command_msg.encode('utf-8'))
            print(f"Client: Requesting file ID '{file_id_str}' ({filename}) from peer {peer_address}")

            # receive all encrypted data
            encrypted = b''
            print(f"Client: Receiving encrypted data for file ID {file_id_str}...")
            while True:
                chunk = sock.recv(CHUNK_SIZE)
                if not chunk or chunk.decode(errors='ignore').strip() == str(Commands.DONE):
                    break
                encrypted += chunk
            print(f"Client: Finished receiving encrypted data for file ID {file_id_str}.")

            # decrypt
            print("Client: Beginning decryption...")
            plaintext = crypto_utils.decrypt_data(encrypted, decryption_key) # use the retrieved key 

            with open(filepath, 'wb') as f:
                    f.write(plaintext)
            print(Fore.GREEN + f"Client: Decrypted file saved to {filepath}" + Style.RESET_ALL)

             # verify integrity
            actual_hash = crypto_utils.compute_hash(plaintext)
            if expected_hash and actual_hash == expected_hash:
                print(Fore.GREEN + "Client: Integrity check passed ✔" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"Client: WARNING—integrity check failed (expected {expected_hash}, got {actual_hash})" + Style.RESET_ALL)


            print(Fore.GREEN + f"Client: File '{filename}' (ID: {file_id_str}) downloaded to '{destination_path}'." + Style.RESET_ALL)
            return True
        except Exception as e:
            print(Fore.RED + f"Client: Error downloading file ID {file_id_str} from {peer_address}: {e}" + Style.RESET_ALL)
            # Clean up potentially incomplete file
            if 'f' in locals() and not f.closed: f.close()
            if os.path.exists(filepath): os.remove(filepath)
            return False
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
            print(Fore.RED + f"Client: Failed to start peer thread: {e}" + Style.RESET_ALL)
            self.peer_address = None
            self.peer_listening_port = None
            return False


if __name__ == "__main__":
    # Ensure necessary directories exist relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shared_files_dir = os.path.join(script_dir, '..', '..', Config.SHARED_FILES_DIR) # Adjust path as needed
    os.makedirs(shared_files_dir, exist_ok=True)

    client = FileShareClient()

    # Start peer thread first to get listening address
    if client.start_peer_thread():
        # Start the UI thread
        client_ui_thread = threading.Thread(target=client_ui, args=(client,))
        client_ui_thread.start()
        client_ui_thread.join()
    else:
         print(Fore.RED + "!!! Error: Could not start peer listener. Client cannot operate." + Style.RESET_ALL)

