import os
import socket
from colorama import Fore, Style
# from src.client.fileshare_client import FileShareClient # Avoid circular import

# Assuming client object is passed to client_ui function

def client_ui(client):
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- CipherShare Client ---" + Style.RESET_ALL)
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
            print(Fore.YELLOW + "6. List Available Files")
            print(Fore.YELLOW + "7. Download File")
            print(Fore.YELLOW + "8. Share File") # New Option
            print(Fore.YELLOW + "9. Revoke Access") # New Option
            print(Fore.YELLOW + "10. Logout")
            print(Fore.YELLOW + "11. Exit" + Style.RESET_ALL)

            choice = input(Fore.GREEN + "Enter choice: " + Style.RESET_ALL)

            if choice == '4':
                peers = client.get_peers()
                if peers:
                    print(Fore.BLUE + "Available Peers (excluding self):" + Style.RESET_ALL)
                    for peer in peers:
                        print(Fore.BLUE + str(peer) + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + "No other peers found." + Style.RESET_ALL)

            elif choice == '5':
                filepath = input(Fore.GREEN + "Enter full file path to upload: " + Style.RESET_ALL)
                if not os.path.isfile(filepath):
                     print(Fore.RED + f"Error: File not found at '{filepath}'" + Style.RESET_ALL)
                     continue
                client.upload_file(filepath) # Upload to own peer

            elif choice == '6':
                files = client.get_files_from_registry()
                if files:
                    print(Fore.BLUE + "Available Files on the Network:" + Style.RESET_ALL)
                    # Sort by file_id for consistent display
                    sorted_file_ids = sorted(files.keys(), key=int)
                    for file_id in sorted_file_ids:
                        file_info = files[file_id]
                        # Display owner and allowed users
                        allowed_users = file_info.get('allowed_users', [])
                        print(Fore.BLUE + f"ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']} | Shared With: {', '.join(allowed_users)}" + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + "No files found in the registry." + Style.RESET_ALL)

            elif choice == '7':
                files = client.get_files_from_registry()
                if not files:
                    print(Fore.YELLOW + "No files available to download. Try listing files first (option 6)." + Style.RESET_ALL)
                    continue

                # Display files again for convenience
                print(Fore.BLUE + "Available Files on the Network:" + Style.RESET_ALL)
                sorted_file_ids = sorted(files.keys(), key=int)
                for file_id in sorted_file_ids:
                    file_info = files[file_id]
                    allowed_users = file_info.get('allowed_users', [])
                    print(Fore.BLUE + f"ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']} | Shared With: {', '.join(allowed_users)}" + Style.RESET_ALL)

                file_id_str = input(Fore.GREEN + "Enter file ID to download: " + Style.RESET_ALL)

                # Validate file_id and check if file exists in the list from registry
                if file_id_str not in files:
                    print(Fore.RED + f"Error: Invalid file ID '{file_id_str}'. File not found in the list." + Style.RESET_ALL)
                    continue

                file_info_to_download = files[file_id_str]
                owner_addr = file_info_to_download.get("owner_address")
                filename = file_info_to_download.get("filename")
                expected_hash = file_info_to_download.get("file_hash")

                if not owner_addr or not filename or not expected_hash:
                     print(Fore.RED + f"Error: Missing file information for ID {file_id_str} from registry." + Style.RESET_ALL)
                     continue

                destination_path = input(Fore.GREEN + "Enter destination directory path (e.g., ./downloads): " + Style.RESET_ALL)
                if not os.path.isdir(destination_path):
                     create_dest = input(Fore.YELLOW + f"Directory '{destination_path}' does not exist. Create it? (y/n): " + Style.RESET_ALL)
                     if create_dest.lower() == 'y':
                         try:
                             os.makedirs(destination_path)
                             print(Fore.GREEN + f"Created directory: {destination_path}" + Style.RESET_ALL)
                         except OSError as e:
                             print(Fore.RED + f"Error creating directory: {e}" + Style.RESET_ALL)
                             continue
                     else:
                         print(Fore.YELLOW + "Download cancelled." + Style.RESET_ALL)
                         continue

                # Call download_file which now handles access check and key retrieval internally
                client.download_file(file_id_str, destination_path, owner_addr, filename, expected_hash)


            elif choice == '8': # Share File
                files = client.get_files_from_registry()
                if not files:
                    print(Fore.YELLOW + "No files found in the registry to share." + Style.RESET_ALL)
                    continue

                print(Fore.BLUE + "Your Files (as owner):" + Style.RESET_ALL)
                owned_files = {fid: info for fid, info in files.items() if info.get("owner") == client.username}
                if not owned_files:
                    print(Fore.YELLOW + "You do not own any files to share." + Style.RESET_ALL)
                    continue

                sorted_owned_file_ids = sorted(owned_files.keys(), key=int)
                for file_id in sorted_owned_file_ids:
                    file_info = owned_files[file_id]
                    allowed_users = file_info.get('allowed_users', [])
                    print(Fore.BLUE + f"ID: {file_id} | Filename: {file_info['filename']} | Shared With: {', '.join(allowed_users)}" + Style.RESET_ALL)

                file_id_to_share = input(Fore.GREEN + "Enter the ID of the file you want to share: " + Style.RESET_ALL)

                if file_id_to_share not in owned_files:
                    print(Fore.RED + f"Error: Invalid file ID '{file_id_to_share}' or you do not own this file." + Style.RESET_ALL)
                    continue

                target_username = input(Fore.GREEN + "Enter the username to share with: " + Style.RESET_ALL)

                if target_username == client.username:
                    print(Fore.YELLOW + "Cannot share a file with yourself." + Style.RESET_ALL)
                    continue

                client.share_file(file_id_to_share, target_username)

            elif choice == '9': # Revoke Access
                files = client.get_files_from_registry()
                if not files:
                    print(Fore.YELLOW + "No files found in the registry." + Style.RESET_ALL)
                    continue

                print(Fore.BLUE + "Your Files (as owner) for Revoking Access:" + Style.RESET_ALL)
                owned_files = {fid: info for fid, info in files.items() if info.get("owner") == client.username}
                if not owned_files:
                    print(Fore.YELLOW + "You do not own any files to revoke access from." + Style.RESET_ALL)
                    continue

                sorted_owned_file_ids = sorted(owned_files.keys(), key=int)
                for file_id in sorted_owned_file_ids:
                    file_info = owned_files[file_id]
                    allowed_users = file_info.get('allowed_users', [])
                    print(Fore.BLUE + f"ID: {file_id} | Filename: {file_info['filename']} | Shared With: {', '.join(allowed_users)}" + Style.RESET_ALL)

                file_id_to_revoke = input(Fore.GREEN + "Enter the ID of the file to revoke access from: " + Style.RESET_ALL)

                if file_id_to_revoke not in owned_files:
                    print(Fore.RED + f"Error: Invalid file ID '{file_id_to_revoke}' or you do not own this file." + Style.RESET_ALL)
                    continue

                file_info_to_revoke = owned_files[file_id_to_revoke]
                allowed_users = file_info_to_revoke.get('allowed_users', [])

                if len(allowed_users) <= 1: # Only owner has access
                     print(Fore.YELLOW + "No other users have access to this file to revoke." + Style.RESET_ALL)
                     continue

                print(Fore.BLUE + "Users with Access (excluding owner):" + Style.RESET_ALL)
                users_to_revoke = [u for u in allowed_users if u != client.username]
                if not users_to_revoke:
                     print(Fore.YELLOW + "No other users have access to this file to revoke." + Style.RESET_ALL)
                     continue

                for i, user in enumerate(users_to_revoke):
                    print(Fore.BLUE + f"{i}: {user}" + Style.RESET_ALL)

                user_index_str = input(Fore.GREEN + f"Enter the index of the user to revoke access for (0 to {len(users_to_revoke)-1}): " + Style.RESET_ALL)
                try:
                    user_index = int(user_index_str)
                    if 0 <= user_index < len(users_to_revoke):
                        target_username_revoke = users_to_revoke[user_index]
                        client.revoke_access(file_id_to_revoke, target_username_revoke)
                    else:
                        print(Fore.RED + "Invalid user index." + Style.RESET_ALL)
                except ValueError:
                    print(Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL)


            elif choice == '10': # Logout
                client.username = None
                client.session_id = None
                client.key = None # Clear the user's key on logout
                print(Fore.GREEN + "Client: Logged out." + Style.RESET_ALL)
            elif choice == '11': # Exit
                print(Fore.YELLOW + "Exiting CipherShare Client." + Style.RESET_ALL)
                break
            else:
                print(Fore.RED + "Invalid choice." + Style.RESET_ALL)

