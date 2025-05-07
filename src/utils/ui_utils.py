import os
import shutil
from pyfiglet import Figlet
from rich.console import Console
from rich.rule import Rule
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich import box
from rich.table import Table

console = Console()
figlet = Figlet(font='slant')


def print_centered_banner(text, subtitle=None, style="bold cyan", subtitle_style="bold magenta"):
    term_width = shutil.get_terminal_size().columns
    ascii_banner = figlet.renderText(text)
    centered_banner = "\n".join(line.center(term_width) for line in ascii_banner.splitlines())
    console.print(centered_banner, style=style)
    if subtitle:
        console.print(subtitle.center(term_width), style=subtitle_style)


def client_ui(client, clear_screen=True):
    while True:
        if clear_screen:
            os.system("clear")

        if client.username:
            print_centered_banner("CipherShare", subtitle=f"Welcome, {client.username} 👋")
        else:
            print_centered_banner("CipherShare")

        if not client.username:
            menu_text = Text()
            menu_text.append(" Register – Create a new account\n")
            menu_text.append(" Login – Access your account\n")
            menu_text.append(" Exit – Quit the client")
            console.print(Panel(menu_text, title="Main Menu", border_style="magenta", box=box.ROUNDED))
            choice = Prompt.ask("[green]Select an option[/] [1/2/3]", choices=["1", "2", "3"], default="1")

            if choice == "1":
                username = Prompt.ask("[green]Enter username[/]")
                password = Prompt.ask("[green]Enter password[/]", password=True)
                client.register_user(username, password)

            elif choice == "2":
                username = Prompt.ask("[green]Enter username[/]")
                password = Prompt.ask("[green]Enter password[/]", password=True)
                if client.login_user(username, password):
                    if clear_screen:
                        os.system("clear")
                    print_centered_banner("CipherShare", subtitle=f"Welcome, {username} 👋")
                    console.print(Panel(Text("✔ Successfully logged in!", style="bold green"),
                                        title="Login Successful", border_style="green", box=box.HEAVY))
                    input("\nPress Enter to continue...")

            elif choice == "3":
                if clear_screen:
                    os.system("clear")
                print_centered_banner("Goodbye!", style="bold red")
                console.print(Rule(style="red"))
                console.print("[yellow]Thank you for using CipherShare. Stay safe and encrypted![/]")
                console.print(Rule(style="red"))
                break

        else:
            # 🔐 Advanced Styled User Menu
            menu_table = Table(
                title="[bold underline cyan]🔐 User Menu",
                title_justify="center",
                box=box.ROUNDED,
                border_style="bright_magenta",
                show_header=True,
                header_style="bold white on black",
            )

            menu_table.add_column("Option", justify="center", style="bold yellow", width=10)
            menu_table.add_column("Description", justify="left", style="bold green")

            menu_table.add_row("4️⃣", "List Peers")
            menu_table.add_row("5️⃣", "Upload File")
            menu_table.add_row("6️⃣", "List Available Files")
            menu_table.add_row("7️⃣", "Download File")
            menu_table.add_row("8️⃣", "Share File")
            menu_table.add_row("9️⃣", "Revoke Access")
            menu_table.add_row("🔟", "Logout")
            menu_table.add_row("1️⃣1️⃣", "Exit")

            console.print(menu_table)
            choice = Prompt.ask("[cyan bold]Enter your choice[/]", choices=[str(i) for i in range(4, 12)])

            if choice == '4':
                peers = client.get_peers()
                if peers:
                    console.print("\n[bold blue]Available Peers (excluding self):[/]")
                    for peer in peers:
                        console.print(f"[blue]{peer}[/]")
                else:
                    console.print("[yellow]No other peers found.[/]")
                input("\nPress Enter to continue...")

            elif choice == '5':
                filepath = Prompt.ask("[green]Enter full file path to upload[/]")
                if not os.path.isfile(filepath):
                    console.print(f"[red]Error: File not found at '{filepath}'[/]")
                    continue
                client.upload_file(filepath)

            elif choice == '6':
                files = client.get_files_from_registry()
                if files:
                    console.print("[bold blue]Available Files on the Network:[/]")
                    for file_id in sorted(files.keys(), key=int):
                        file_info = files[file_id]
                        allowed = ", ".join(file_info.get("allowed_users", []))
                        console.print(f"[blue]ID: {file_id} | Filename: {file_info['filename']} | Owner: {file_info['owner']} | Shared With: {allowed}[/]")
                else:
                    console.print("[yellow]No files found in the registry.[/]")
                input("\nPress Enter to continue...")

            elif choice == '7':
                files = client.get_files_from_registry()
                if not files:
                    console.print("[yellow]No files available to download. Try listing files first (option 6).[/]")
                    continue

                for file_id in sorted(files.keys(), key=int):
                    info = files[file_id]
                    allowed = ", ".join(info.get("allowed_users", []))
                    console.print(f"[blue]ID: {file_id} | Filename: {info['filename']} | Owner: {info['owner']} | Shared With: {allowed}[/]")

                file_id = Prompt.ask("[green]Enter file ID to download[/]")
                if file_id not in files:
                    console.print(f"[red]Error: File ID '{file_id}' not found.[/]")
                    continue

                info = files[file_id]
                owner_addr = info.get("owner_address")
                filename = info.get("filename")
                file_hash = info.get("file_hash")

                if not all([owner_addr, filename, file_hash]):
                    console.print(f"[red]Error: Incomplete file info for ID {file_id}[/]")
                    continue

                dest_path = Prompt.ask("[green]Enter destination folder (e.g. ./downloads)[/]")
                if not os.path.isdir(dest_path):
                    create = Prompt.ask(f"[yellow]Directory '{dest_path}' does not exist. Create it? (y/n)[/]", choices=["y", "n"])
                    if create == 'y':
                        try:
                            os.makedirs(dest_path)
                            console.print(f"[green]Directory created: {dest_path}[/]")
                        except Exception as e:
                            console.print(f"[red]Error: {e}[/]")
                            continue
                    else:
                        continue

                client.download_file(file_id, dest_path, owner_addr, filename, file_hash)

            elif choice == '8':
                files = client.get_files_from_registry()
                owned_files = {fid: info for fid, info in files.items() if info.get("owner") == client.username}

                if not owned_files:
                    console.print("[yellow]You don’t own any files to share.[/]")
                    continue

                for file_id in sorted(owned_files.keys(), key=int):
                    info = owned_files[file_id]
                    allowed = ", ".join(info.get("allowed_users", []))
                    console.print(f"[blue]ID: {file_id} | Filename: {info['filename']} | Shared With: {allowed}[/]")

                file_id = Prompt.ask("[green]Enter the ID of the file to share[/]")
                if file_id not in owned_files:
                    console.print("[red]Invalid ID or not your file.[/]")
                    continue

                target_user = Prompt.ask("[green]Enter username to share with[/]")
                if target_user == client.username:
                    console.print("[yellow]You can't share a file with yourself.[/]")
                    continue

                client.share_file(file_id, target_user)

            elif choice == '9':
                files = client.get_files_from_registry()
                owned_files = {fid: info for fid, info in files.items() if info.get("owner") == client.username}

                if not owned_files:
                    console.print("[yellow]No owned files to revoke access from.[/]")
                    continue

                for file_id in sorted(owned_files.keys(), key=int):
                    info = owned_files[file_id]
                    allowed = info.get("allowed_users", [])
                    console.print(f"[blue]ID: {file_id} | Filename: {info['filename']} | Shared With: {', '.join(allowed)}[/]")

                file_id = Prompt.ask("[green]Enter the ID of the file to revoke access[/]")
                if file_id not in owned_files:
                    console.print("[red]Invalid ID or not your file.[/]")
                    continue

                users = [u for u in owned_files[file_id]["allowed_users"] if u != client.username]
                if not users:
                    console.print("[yellow]No users to revoke access from.[/]")
                    continue

                table = Table(title="Users with Access", box=box.MINIMAL_DOUBLE_HEAD)
                table.add_column("Index", style="yellow")
                table.add_column("Username", style="cyan")
                for i, user in enumerate(users):
                    table.add_row(str(i), user)
                console.print(table)

                idx = Prompt.ask(f"[green]Enter user index to revoke (0–{len(users)-1})[/]")
                try:
                    idx = int(idx)
                    if 0 <= idx < len(users):
                        client.revoke_access(file_id, users[idx])
                    else:
                        console.print("[red]Invalid index.[/]")
                except:
                    console.print("[red]Please enter a number.[/]")

            elif choice == '10':
                client.username = None
                client.session_id = None
                client.key = None
                console.print("[green]Logged out successfully.[/]")
            elif choice == '11':
                os.system('clear')
                print_centered_banner("Goodbye!", style="bold red")
                console.print(Rule(style="red"))
                console.print("[yellow]Thank you for using CipherShare. Stay safe and encrypted![/]")
                console.print(Rule(style="red"))
                break
