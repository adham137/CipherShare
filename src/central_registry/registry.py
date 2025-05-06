import socket
import threading
import json
import sys, os
# Add parent directory to sys.path to import modules from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.utils.config import Config
from src.utils.commands_enum import Commands
from src.utils.crypto_utils import *

REGISTRY_ADDRESS = Config.REGISTRY_IP
REGISTRY_PORT = Config.REGISTRY_PORT

REGISTERED_PEERS = {}  # {username: (host, port)}
USER_CREDENTIALS = {}  # {username: {hashed_password, salt, key}}
USER_SESSIONS = {}  # {session_id: username}

# new SHARED_FILES structure to include 'allowed_users'
# {file_id: {filename: , owner: , owner_addr: , file_hash: , allowed_users: []}}
SHARED_FILES = {}
FILE_ID_COUNTER = 0


def handle_client(client_socket):
    global FILE_ID_COUNTER
    # print("Registry: A client has connected") # Keep logging minimal unless debugging
    try:
        data = client_socket.recv(1024).decode()
        request = json.loads(data)
        command_str = request.get("command")
        command = Commands.from_string(command_str)

        # --- Authentication Check for commands requiring login ---
        # these commands require a valid session_id
        commands_requiring_auth = [
            Commands.REGISTER_FILE, Commands.GET_FILES, Commands.REQUEST_KEY,
            Commands.SHARE_FILE, Commands.REVOKE_ACCESS, Commands.CHECK_ACCESS
        ]
        session_id = request.get("session_id")
        username = None
        if command in commands_requiring_auth:
            if session_id not in USER_SESSIONS:
                client_socket.send(json.dumps({"status": "ERROR", "message": "Authentication required"}).encode())
                print(f"Registry: Authentication failed for command {command_str} (Invalid session ID: {session_id})")
                return # Close connection after sending error
            username = USER_SESSIONS[session_id]
            print(f"Registry: Authenticated user '{username}' for command {command_str}")
        # --- End Authentication Check ---


        if command == Commands.REGISTER_USER:
            username_reg = request["username"]
            password = request["password"]
            peer_address = tuple(request["peer_address"])
            if username_reg not in USER_CREDENTIALS:
                hashed_password , salt = hash_password_argon2(password)
                key = derive_key_from_password(password, salt)
                # print(f"The hash is ({hashed_password})\n the salt is ({salt})\n the key is ({key})") # Avoid printing sensitive info
                USER_CREDENTIALS[username_reg] = {"hashed_password": hashed_password, "salt": salt, "key": key}
                REGISTERED_PEERS[username_reg] = peer_address
                client_socket.send(json.dumps({"status": "OK"}).encode())
                print(f"Registry: User {username_reg} registered")
            else:
                client_socket.send(json.dumps({"status": "ERROR", "message": "Username already exists"}).encode())


        elif command == Commands.LOGIN_USER:
            username_login = request["username"]
            password = request["password"]
            peer_address = tuple(request["peer_address"])

            if username_login in USER_CREDENTIALS:
                stored_salt = USER_CREDENTIALS[username_login]["salt"]
                stored_hashed_password = USER_CREDENTIALS[username_login]["hashed_password"]
                is_valid_login = verify_password_argon2(password, stored_hashed_password, stored_salt)

                if is_valid_login:
                    session_id = generate_session_id()
                    stored_key = USER_CREDENTIALS[username_login]["key"]
                    USER_SESSIONS[session_id] = username_login
                    REGISTERED_PEERS[username_login] = peer_address # Update peer address on login
                    client_socket.send(json.dumps({"status": "OK", "session_id": session_id, "key": stored_key}).encode())
                    print(f"Registry: User {username_login} logged in, Session ID: {session_id}")
                else:
                    client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid credentials"}).encode())
            else:
                client_socket.send(json.dumps({"status": "ERROR", "message": "Username not found"}).encode())

        # not used 
        elif command == Commands.VERIFY_SESSION:
            session_id_verify = request["session_id"]
            if session_id_verify in USER_SESSIONS:
                client_socket.send(json.dumps({"status": "OK", "username": USER_SESSIONS[session_id_verify]}).encode())
            else:
                client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid session"}).encode())

        # REGISTER_PEER command is redundant now with peer address updated on login/register
        # elif command == Commands.REGISTER_PEER:
        #     username_peer = request["username"]
        #     peer_address = tuple(request["peer_address"])
        #     REGISTERED_PEERS[username_peer] = peer_address
        #     client_socket.send(b"OK")
        #     print(f"Registry: Peer '{username_peer}' registered: {peer_address}")

        elif command == Commands.GET_PEERS:
            # only return peers that are currently logged in (have a session)
            active_peers = [REGISTERED_PEERS[u] for u in USER_SESSIONS.values() if u in REGISTERED_PEERS]
            client_socket.send(json.dumps(active_peers).encode())
            print(f"Registry: Sent active peer list: {active_peers}")

        elif command == Commands.REGISTER_FILE:
            filename = request["filename"]
            # owner is determined from the session
            owner_address = request["owner_address"] 
            file_hash = request["file_hash"]

            if username is None: # should not happen due to auth check but safety first
                 client_socket.send(json.dumps({"status": "ERROR", "message": "User not authenticated"}).encode())
                 return

            # ensure the owner_address matches the registered peer address for the user
            if username in REGISTERED_PEERS and REGISTERED_PEERS[username] != tuple(owner_address):
                 print(f"Registry: WARNING - Registered file owner address mismatch! User: {username}, Sent: {owner_address}, Registered: {REGISTERED_PEERS[username]}")
            

            file_id = FILE_ID_COUNTER
            SHARED_FILES[file_id] = {
                "filename": filename,
                "owner": username, 
                "owner_address": tuple(owner_address),
                "file_hash": file_hash,
                "allowed_users": [username] # owner has access by default
            }
            FILE_ID_COUNTER += 1
            client_socket.send(json.dumps({"status": "OK", "file_id": file_id}).encode())
            print(f"Registry: File '{filename}' (Owner: {username}) registered with ID: {file_id}")

        elif command == Commands.GET_FILES:
            # filter files to only include those the requesting user is allowed to access
            accessible_files = {
                file_id: file_info
                for file_id, file_info in SHARED_FILES.items()
                if username in file_info.get("allowed_users", [])
            }

            client_socket.send(json.dumps(accessible_files).encode())
            print(f"Registry: Sent accessible file list for user '{username}': {accessible_files}")



        elif command == Commands.REQUEST_KEY:
            file_id_str = request.get("file_id")
            if file_id_str is None:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "File ID not provided"}).encode())
                 return

            try:
                file_id = int(file_id_str)
            except ValueError:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid File ID format"}).encode())
                 return

            if file_id in SHARED_FILES:
                file_info = SHARED_FILES[file_id]
                # --- Access Control Check ---
                if username in file_info.get("allowed_users", []):
                    owner_username = file_info["owner"]
                    # Retrieve the key for the file owner
                    if owner_username in USER_CREDENTIALS:
                         key = USER_CREDENTIALS[owner_username]["key"]
                         # print(f"Registry: Sending key for file ID {file_id} to user {username}") 
                         client_socket.send(json.dumps({"status": "OK", "key": key}).encode())
                    else:
                         # this case indicates an internal inconsistency (file registered but owner credentials missing)
                         print(f"Registry ERROR: File ID {file_id} registered to user '{owner_username}', but credentials not found.")
                         client_socket.send(json.dumps({"status": "ERROR", "message": "Internal error retrieving key"}).encode())
                else:
                    print(f"Registry: Access denied for user '{username}' to file ID {file_id}.")
                    client_socket.send(json.dumps({"status": "ERROR", "message": "Access denied"}).encode())
                # --- End Access Control Check ---
            else:
                print(f"Registry: File with ID {file_id} not found.")
                client_socket.send(json.dumps({"status": "ERROR", "message": "File not found"}).encode())

        elif command == Commands.SHARE_FILE:
            file_id_str = request.get("file_id")
            target_username = request.get("target_username")

            if file_id_str is None or target_username is None:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "File ID or target username not provided"}).encode())
                 return

            try:
                file_id = int(file_id_str)
            except ValueError:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid File ID format"}).encode())
                 return

            if file_id in SHARED_FILES:
                file_info = SHARED_FILES[file_id]
                # check if the requesting user is the owner of the file
                if username == file_info["owner"]:
                    # check if the target user exists
                    if target_username in USER_CREDENTIALS:
                        if target_username not in file_info.get("allowed_users", []):
                            file_info.setdefault("allowed_users", []).append(target_username)
                            client_socket.send(json.dumps({"status": "OK", "message": f"File shared with {target_username}"}).encode())
                            print(f"Registry: User '{username}' shared file ID {file_id} with '{target_username}'.")
                        else:
                            client_socket.send(json.dumps({"status": "ERROR", "message": f"File already shared with {target_username}"}).encode())
                            print(f"Registry: File ID {file_id} already shared with '{target_username}'.")
                    else:
                        client_socket.send(json.dumps({"status": "ERROR", "message": f"Target user '{target_username}' not found"}).encode())
                        print(f"Registry: Share failed - Target user '{target_username}' not found.")
                else:
                    client_socket.send(json.dumps({"status": "ERROR", "message": "Only the file owner can share the file"}).encode())
                    print(f"Registry: Share failed - User '{username}' is not the owner of file ID {file_id}.")
            else:
                client_socket.send(json.dumps({"status": "ERROR", "message": "File not found"}).encode())
                print(f"Registry: Share failed - File with ID {file_id} not found.")

        elif command == Commands.REVOKE_ACCESS:
            file_id_str = request.get("file_id")
            target_username = request.get("target_username")

            if file_id_str is None or target_username is None:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "File ID or target username not provided"}).encode())
                 return

            try:
                file_id = int(file_id_str)
            except ValueError:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid File ID format"}).encode())
                 return

            if file_id in SHARED_FILES:
                file_info = SHARED_FILES[file_id]
                # check if the requesting user is the owner of the file
                if username == file_info["owner"]:
                    # prevent owner from revoking their own access (unless specific logic is needed)
                    if target_username == username:
                        client_socket.send(json.dumps({"status": "ERROR", "message": "Cannot revoke access for the file owner"}).encode())
                        print(f"Registry: Revoke failed - Owner '{username}' tried to revoke their own access for file ID {file_id}.")
                        return

                    if target_username in file_info.get("allowed_users", []):
                        file_info["allowed_users"].remove(target_username)
                        client_socket.send(json.dumps({"status": "OK", "message": f"Access revoked for {target_username}"}).encode())
                        print(f"Registry: User '{username}' revoked access for '{target_username}' to file ID {file_id}.")
                    else:
                        client_socket.send(json.dumps({"status": "ERROR", "message": f"User {target_username} does not have access to this file"}).encode())
                        print(f"Registry: Revoke failed - User '{target_username}' does not have access to file ID {file_id}.")
                else:
                    client_socket.send(json.dumps({"status": "ERROR", "message": "Only the file owner can revoke access"}).encode())
                    print(f"Registry: Revoke failed - User '{username}' is not the owner of file ID {file_id}.")
            else:
                client_socket.send(json.dumps({"status": "ERROR", "message": "File not found"}).encode())
                print(f"Registry: Revoke failed - File with ID {file_id} not found.")

        elif command == Commands.CHECK_ACCESS:        
            file_id_str = request.get("file_id")
            if file_id_str is None:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "File ID not provided"}).encode())
                 return

            try:
                file_id = int(file_id_str)
            except ValueError:
                 client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid File ID format"}).encode())
                 return

            if file_id in SHARED_FILES:
                file_info = SHARED_FILES[file_id]
                if username in file_info.get("allowed_users", []):
                    client_socket.send(json.dumps({"status": "OK", "message": "Access granted"}).encode())
                    print(f"Registry: Access check passed for user '{username}' on file ID {file_id}.")
                else:
                    client_socket.send(json.dumps({"status": "ERROR", "message": "Access denied"}).encode())
                    print(f"Registry: Access check failed for user '{username}' on file ID {file_id}.")
            else:
                client_socket.send(json.dumps({"status": "ERROR", "message": "File not found"}).encode())
                print(f"Registry: Access check failed - File with ID {file_id} not found.")


        else:
             print(f"Registry: Received unknown or unhandled command: {command_str}")
             # Optionally send an error response for unknown commands
             client_socket.send(json.dumps({"status": "ERROR", "message": "Unknown command"}).encode())


    except json.JSONDecodeError:
         print("Registry Error: Invalid JSON received.")
         client_socket.send(json.dumps({"status": "ERROR", "message": "Invalid request format"}).encode())
    except KeyError as e:
        print(f"Registry Error: Missing key in request: {e}")
        client_socket.send(json.dumps({"status": "ERROR", "message": f"Missing parameter: {e}"}).encode())
    except Exception as e:
        print(f"Registry Error handling client: {e}")
        client_socket.send(json.dumps({"status": "ERROR", "message": f"Internal server error: {e}"}).encode())
    finally:
        client_socket.close()


def start_registry_server(address=REGISTRY_ADDRESS, port=REGISTRY_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((address, port))
        server_socket.listen(5)
        print(f"Registry server listening on {address}:{port}")

        while True:
            client_sock, addr = server_socket.accept()
            # print(f"Registry: Accepted connection from {addr}") # Keep logging minimal
            threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()
    except OSError as e:
         print(f"Registry Error starting server: {e}")
    except KeyboardInterrupt:
         print("\nRegistry: Shutting down...")
    finally:
         server_socket.close()
         print("Registry server shut down.")


if __name__ == "__main__":
    start_registry_server()

