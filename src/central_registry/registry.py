import socket
import threading
import json
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.utils.config import Config 
from src.utils.commands_enum import Commands 

REGISTRY_ADDRESS = Config.REGISTRY_IP 
REGISTRY_PORT = Config.REGISTRY_PORT  

REGISTERED_PEERS = {}  # {username: (host, port)}
SHARED_FILES = {}  # {file_id: {filename: , owner: }}
FILE_ID_COUNTER = 0


def handle_client(client_socket):
    global FILE_ID_COUNTER
    # print("Registry: A client has connected")
    try:
        data = client_socket.recv(1024).decode()
        request = json.loads(data)
        command_str = request.get("command")
        command = Commands.from_string(command_str) 

        if command == Commands.REGISTER_PEER: 
            username = request["username"]
            peer_address = tuple(request["peer_address"])
            REGISTERED_PEERS[username] = peer_address
            client_socket.send(b"OK") 
            print(f"Registry: Peer '{username}' registered: {peer_address}")

        elif command == Commands.GET_PEERS: 
            peer_list = list(REGISTERED_PEERS.values())
            client_socket.send(json.dumps(peer_list).encode())
            print(f"Registry: Sent peer list: {peer_list}")

        elif command == Commands.REGISTER_FILE: 
            filename = request["filename"]
            owner = request["owner"]
            file_id = FILE_ID_COUNTER
            SHARED_FILES[file_id] = {"filename": filename, "owner": owner}
            FILE_ID_COUNTER += 1
            client_socket.send(json.dumps({"file_id": file_id}).encode())
            print(f"Registry: File '{filename}' (Owner: {owner}) registered with ID: {file_id}")

        elif command == Commands.GET_FILES: 
            client_socket.send(json.dumps(SHARED_FILES).encode())
            print(f"Registry: Sent file list: {SHARED_FILES}")
        
        else:
             print(f"Registry: Received unknown command: {command_str}")
             # Optionally send an error response

    except json.JSONDecodeError:
         print("Registry Error: Invalid JSON received.")
    except KeyError as e:
        print(f"Registry Error: Missing key in request: {e}")
    except Exception as e:
        print(f"Registry Error handling client: {e}")
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
            print(f"Registry: Accepted connection from {addr}")
            threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()
    except OSError as e:
         print(f"Registry Error starting server: {e}")
    finally:
         server_socket.close()
         print("Registry server shut down.")


if __name__ == "__main__":
    start_registry_server()