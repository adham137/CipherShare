import socket
import os
import sys
import json
import threading

from colorama import Fore, Style
from Crypto.Cipher import AES

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
        self.key = None
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

    # def register_with_registry(self):
    #     if not self.peer_address:
    #          print("Client: Cannot register with registry, peer address not set.")
    #          return False
        
    #     sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
    #     if not sock:
    #         return False

    #     try:
    #         request = {"command": str(Commands.REGISTER_PEER),
    #                    "username": self.username,
    #                    "peer_address": self.peer_address} 
    #         sock.sendall(json.dumps(request).encode('utf-8'))
    #         response = sock.recv(1024).decode('utf-8')
    #         if response == "OK":
    #             print(f"Client: Registered '{self.username}' with registry successfully.")
    #             return True
    #         else:
    #             print(f"Client: Registry registration failed. Response: {response}")
    #             return False
    #     except Exception as e:
    #         print(f"Client: Error during registry registration: {e}")
    #         return False
    #     finally:
    #         sock.close()
    def register_user(self, username, password):
        if not self.peer_address:
             print("Client: Cannot register with registry, peer address not set.")
             return False
        
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return False
        try:
            request = {"command": "REGISTER_USER", "username": username, "password": password, "peer_address": self.peer_address}
            sock.sendall(json.dumps(request).encode())
            response = sock.recv(1024).decode()
            response_data = json.loads(response)
            if response_data["status"] == "OK":
                print(Fore.GREEN + "Client: Registration successful!" + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + f"Client: Registration failed: {response_data['message']}" + Style.RESET_ALL)
                return False
        except Exception as e:
            print(Fore.RED + f"Client: Registration error: {e}" + Style.RESET_ALL)
            return False
    def login_user(self, username, password):
        if not self.peer_address:
             print("Client: Cannot login with registry, peer address not set.")
             return False
        
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return False
        try:
            request = {"command": "LOGIN_USER", "username": username, "password": password, "peer_address": self.peer_address}
            sock.sendall(json.dumps(request).encode())
            response = sock.recv(1024).decode()
            response_data = json.loads(response)
            if response_data["status"] == "OK":
                # recieve your sessionId and key
                self.username = username
                self.session_id = response_data["session_id"]
                self.key = response_data["key"]
                print(f"Recieved sessionId: ({self.session_id})\nRecieved key: ({self.key})")
                print(Fore.GREEN + "Client: Login successful!" + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + f"Client: Login failed: {response_data['message']}" + Style.RESET_ALL)
                return False
        except Exception as e:
            print(Fore.RED + f"Client: Login error: {e}" + Style.RESET_ALL)
            return False

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
    def request_key(self, file_id):
        key=""
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return None
        try:
            request = {"command": "REQUEST_KEY", "file_id": file_id}
            sock.sendall(json.dumps(request).encode())
            response = sock.recv(1024).decode()
            response_data = json.loads(response)
            if response_data["status"] == "OK":
                # recieve the key for the file
                key = response_data["key"]
                print(f"Recieved key: ({key})")
                return key
            else:
                print(Fore.RED + f"Client: Access for the file is prohibted: {response_data['message']}" + Style.RESET_ALL)
                return None
        except Exception as e:
            print(Fore.RED + f"Client: error while trying to retrieve the key: {e}" + Style.RESET_ALL)
            return None
        
    def upload_file(self, filepath, peer_address):
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot upload file." + Style.RESET_ALL)
            return False
        
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

            # Compute integrity hash over plaintext
            file_hash = crypto_utils.compute_file_hash(filepath)

            # Encrypt entire file
            with open(filepath, 'rb') as f:
                plaintext = f.read()
            ciphertext = crypto_utils.encrypt_data(plaintext, self.key)
            # assert len(ciphertext) % AES.block_size == 0, "Blob length must be multiple of 16"

            # Send encrypted bytes in chunks
            for i in range(0, len(ciphertext), CHUNK_SIZE):
                sock.sendall(ciphertext[i:i+CHUNK_SIZE]) 
            
            # Send DONE signal separately
            # sock.sendall(str(Commands.DONE).encode('utf-8')) 
            print(f"Client: Encrypted File '{filename}' uploaded to peer {peer_address}.")
            
            # Register file with registry AFTER successful upload
            file_id = self.register_file_with_registry(filename, file_hash)
            if file_id is not None:
                 print(f"Client: File '{filename}' registered with registry (ID: {file_id}, hash {file_hash}).")
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

    def download_file(self, file_id_str, destination_path, peer_address, filename, expected_hash, key):
        if not self.session_id:
            print(Fore.RED + "Client: Not logged in. Cannot download file." + Style.RESET_ALL)
            return False
        
        # # Fetch expected hash from registry
        # all_files = self.get_files_from_registry()
        # meta = all_files.get(file_id_str) or {}
        # expected_hash = meta.get("file_hash")
        
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

            # Receive all encrypted data
            encrypted = b''
            while True:
                chunk = sock.recv(CHUNK_SIZE)
                if not chunk or chunk.decode(errors='ignore').strip() == str(Commands.DONE):
                    break
                encrypted += chunk

            # Decrypt
            print("We will begin decrypting now")

            plaintext = crypto_utils.decrypt_data(encrypted, key)

            with open(filepath, 'wb') as f:
                    f.write(plaintext)
            print(Fore.GREEN + f"Client: Decrypted file saved to {filepath}" + Style.RESET_ALL)

             # 5) Verify integrity
            actual_hash = crypto_utils.compute_hash(plaintext)
            if expected_hash and actual_hash == expected_hash:
                print(Fore.GREEN + "Client: Integrity check passed ✔" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"Client: WARNING—integrity check failed (expected {expected_hash}, got {actual_hash})" + Style.RESET_ALL)
                

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

    def register_file_with_registry(self, filename, file_hash):
        sock = self._connect_socket(REGISTRY_ADDRESS, REGISTRY_PORT)
        if not sock:
            return None

        try:
            request = {"command": str(Commands.REGISTER_FILE), 
                       "filename": filename,
                       "owner": self.username,
                       "owner_address": self.peer_address,
                       "file_hash":     file_hash}
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
    def list_shared_files(self):
        return self.shared_files

if __name__ == "__main__":
    # Ensure necessary directories exist relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shared_files_dir = os.path.join(script_dir, '..', Config.SHARED_FILES_DIR) # Adjust path as needed
    os.makedirs(shared_files_dir, exist_ok=True)
    

    client = FileShareClient()
    
    # Start peer thread first to get listening address
    if client.start_peer_thread():
        # Start the UI thread
        client_ui_thread = threading.Thread(target=client_ui, args=(client,))
        client_ui_thread.start()
        client_ui_thread.join() 
    else:
         print("!!! Error: Could not start peer listener. Client cannot operate.")