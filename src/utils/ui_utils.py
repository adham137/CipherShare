import os
import socket
from colorama import Fore, Style
# from src.client.fileshare_client import FileShareClient

# def start_up():
#     username = password = choice = ""
#     while True:
#         print("n--- Please choose an option ---")
#         print("1. Login")
#         print("2. Register")
#         choice = input("Enter choice (0 to exit): ")
    
#         if choice == '0':
#             break
#         elif choice == '1' or choice == '2':
#             username = input("Username: ")
#             password = input("Password: ")
#             break
#         else:
#             print("Invalid choice. Please try again.")

#         return username, password, int(choice)

# --- Basic UI ---
# def client_ui(client: FileShareClient):
    # while True:
    #     print("\n--- CipherShare Client ---")
    #     print("1. List Peers")
    #     print("2. Upload File")
    #     print("3. List Available Files (from Registry)")
    #     print("4. Download File")
    #     # print("5. List My Shared Files") # Future
    #     print("6. Exit")
    #     print("------------------------")

    #     choice = input("Enter choice: ")

    #     if choice == '1':
    #         peers = client.get_peers()
    #         if peers:
    #             print("Available Peers (excluding self):")
    #             for i, peer in enumerate(peers):
    #                 print(f"{i}: {peer}")
    #         else:
    #             print("No other peers found.")
    #     elif choice == '2':
    #         filepath = input("Enter full file path to upload: ")
    #         if not os.path.isfile(filepath):
    #              print(f"Error: File not found at '{filepath}'")
    #              continue

    #         # peers = client.get_peers()
    #         # if not peers:
    #         #     print("No other peers available to upload to.")
    #         #     continue

    #         # print("Choose a peer to upload to:")
    #         # for i, peer in enumerate(peers):
    #         #     print(f"{i}: {peer}")
    #         # try:
    #         #      peer_index_str = input(f"Enter peer index (0 to {len(peers)-1}): ")
    #         #      peer_index = int(peer_index_str)
    #         #      if 0 <= peer_index < len(peers):
    #         #          selected_peer_address = peers[peer_index]
    #         #          client.upload_file(filepath, selected_peer_address)
    #         #      else:
    #         #          print("Invalid peer index.")
    #         # except ValueError:
    #         #      print("Invalid input. Please enter a number.")

    #         # Upload the file to your own peer instead
    #         client.upload_file(filepath, client.peer_address)

    #     elif choice == '3':
    #         files = client.get_files_from_registry()
    #         if files:
    #             print("Available Files on the Network:")
    #             # Sort by file_id for consistent display
    #             sorted_file_ids = sorted(files.keys(), key=int)
    #             for file_id in sorted_file_ids:
    #                 file_info = files[file_id]
    #                 print(f"ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']}")
    #         else:
    #             print("No files found in the registry.")

    #     elif choice == '4':
    #         files = client.get_files_from_registry()
    #         if not files:
    #             print("No files available to download. Try listing files first (option 3).")
    #             continue
            
    #         # Display files again for convenience
    #         print("Available Files on the Network:")
    #         sorted_file_ids = sorted(files.keys(), key=int)
    #         for file_id in sorted_file_ids:
    #             file_info = files[file_id]
    #             print(f"ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']}")
            
    #         file_id_str = input("Enter file ID to download: ")
            
    #         # Validate file_id
    #         if file_id_str not in files:
    #             print(f"Error: Invalid file ID '{file_id_str}'.")
    #             continue

    #         destination_path = input("Enter destination directory path (e.g., ./downloads): ")
    #         if not os.path.isdir(destination_path):
    #              create_dest = input(f"Directory '{destination_path}' does not exist. Create it? (y/n): ")
    #              if create_dest.lower() == 'y':
    #                  try:
    #                      os.makedirs(destination_path)
    #                      print(f"Created directory: {destination_path}")
    #                  except OSError as e:
    #                      print(f"Error creating directory: {e}")
    #                      continue
    #              else:
    #                  print("Download cancelled.")
    #                  continue



    #         # Add self address if known
    #         if client.peer_address:
    #              try:
    #                  owner_addr = files[file_id_str]["owner_address"]
    #                  client.download_file(file_id_str, destination_path, owner_addr, files[file_id_str]["filename"])

    #              except e:
    #                   print(e)

    #         else:
    #             print("Could not determine own peer address. Cannot proceed.")


    #     # elif choice == '5':
    #     #     shared_files = client.list_shared_files()
    #     #     print("Locally Tracked Shared Files:", shared_files)
    #     elif choice == '6':
    #         print("Exiting CipherShare Client.")
    #         break
    #     else:
    #         print("Invalid choice. Please try again.")

def client_ui(client):
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\nCipherShare Client" + Style.RESET_ALL)
        if not client.username:
            print(Fore.YELLOW + "1. Register")
            print(Fore.YELLOW + "2. Login")
            print(Fore.YELLOW + "3. Exit" + Style.RESET_ALL)
            choice = input(Fore.GREEN + "Enter choice: " + Style.RESET_ALL)

            if choice == '1':
                username = input(Fore.GREEN + "Enter username: " + Style.RESET_ALL)
                password = input(Fore.GREEN + "Enter password: " + Style.RESET_ALL)
                client.register_user(username, password)
            elif choice == '2':
                username = input(Fore.GREEN + "Enter username: " + Style.RESET_ALL)
                password = input(Fore.GREEN + "Enter password: " + Style.RESET_ALL)
                client.login_user(username, password)
            elif choice == '3':
                break
            else:
                print(Fore.RED + "Invalid choice." + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "4. List Peers")
            print(Fore.YELLOW + "5. Upload File")
            print(Fore.YELLOW + "6. Download File")
            print(Fore.YELLOW + "7. List Shared Files")
            print(Fore.YELLOW + "8. Logout")
            print(Fore.YELLOW + "9. Exit" + Style.RESET_ALL)

            choice = input(Fore.GREEN + "Enter choice: " + Style.RESET_ALL)

            if choice == '4':
                peers = client.get_peers()
                print(Fore.BLUE + "Available Peers:")
                for peer in peers:
                    print(Fore.BLUE + str(peer))
            elif choice == '5':
                filepath = input(Fore.GREEN + "Enter file path to upload: " + Style.RESET_ALL)
                # peers = client.get_peers()
                # if peers:
                # print(Fore.BLUE + "Choose a peer to upload to (index):")
                # for i, peer in enumerate(peers):
                #     print(Fore.BLUE + f"{i}: {peer}")
                # peer_index = int(input(Fore.GREEN + "Enter peer index: " + Style.RESET_ALL))
                client.upload_file(filepath, client.peer_address)
                filename = os.path.basename(filepath)
                client.register_file_with_registry(filename)
                # else:
                #     print(Fore.RED + "No peers available to upload.")
            elif choice == '6':
                files = client.get_files_from_registry()
                if files:
                    print(Fore.BLUE + "Available Files:")
                    for file_id, file_info in files.items():
                        print(Fore.BLUE + f"{file_id}: {file_info['filename']} (Owner: {file_info['owner']})")
                    file_id = input(Fore.GREEN + "Enter file ID to download: " + Style.RESET_ALL)
                    destination_path = input(Fore.GREEN + "Enter destination path: " + Style.RESET_ALL)
                    peers = client.get_peers()
                    if client.peer_address:
                         try:
                             owner_addr = files[file_id]["owner_address"]
                             client.download_file(file_id, destination_path, owner_addr, files[file_id]["filename"])

                         except e:
                              print(Fore.RED + e)

                    else:
                        print(Fore.RED + "Could not determine own peer address. Cannot proceed.")
                else:
                    print(Fore.RED + "No files available to download.")

            elif choice == '7':
                shared_files = client.list_shared_files()
                print(Fore.BLUE + "Shared Files:", shared_files)
            elif choice == '8':
                client.username = None
                client.session_id = None
                # client.client_socket.close()
                # client.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # client.connect_to_registry(REGISTRY_ADDRESS, REGISTRY_PORT)
                print(Fore.GREEN + "Client: Logged out." + Style.RESET_ALL)
            elif choice == '9':
                break
            else:
                print(Fore.RED + "Invalid choice.")