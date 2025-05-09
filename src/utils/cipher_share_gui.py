import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Ensure project modules are in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.client.fileshare_client import FileShareClient

class ClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CipherShare - Secure File Sharing")
        self.geometry("720x480")
        self.configure(bg="#f0f2f5")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f0f2f5")
        self.style.configure("TButton", font=("Segoe UI", 10), padding=6)
        self.style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))

        self.client = FileShareClient()
        ok = self.client.start_peer_thread()
        if not ok:
            messagebox.showerror("Error", "Could not start peer listener. Exiting.")
            self.destroy()
            return

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (StartPage, LoginPage, RegisterPage, MainMenu):
            frame = F(parent=self.container, controller=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[F] = frame

        self.show_frame(StartPage)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()

class StartPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Welcome to CipherShare", style="Header.TLabel").pack(pady=30)

        ttk.Button(self, text="Login", width=30, command=lambda: controller.show_frame(LoginPage)).pack(pady=10)
        ttk.Button(self, text="Register", width=30, command=lambda: controller.show_frame(RegisterPage)).pack(pady=10)
        ttk.Button(self, text="Exit", width=30, command=controller.destroy).pack(pady=10)

class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Login to CipherShare", style="Header.TLabel").pack(pady=20)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", pady=5)
        ttk.Entry(form, textvariable=self.user_var, width=30).grid(row=0, column=1, pady=5)
        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", pady=5)
        ttk.Entry(form, textvariable=self.pass_var, show="*", width=30).grid(row=1, column=1, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Back", command=lambda: controller.show_frame(StartPage)).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Login", command=self.login).grid(row=0, column=1, padx=10)

    def login(self):
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Username and password cannot be empty.")
            return
        success = self.controller.client.login_user(username, password)
        if success:
            messagebox.showinfo("Success", "Logged in successfully.")
            self.controller.show_frame(MainMenu)
        else:
            messagebox.showerror("Error", "Login failed. Check credentials.")

class RegisterPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Register New Account", style="Header.TLabel").pack(pady=20)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", pady=5)
        ttk.Entry(form, textvariable=self.user_var, width=30).grid(row=0, column=1, pady=5)
        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", pady=5)
        ttk.Entry(form, textvariable=self.pass_var, show="*", width=30).grid(row=1, column=1, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Back", command=lambda: controller.show_frame(StartPage)).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Register", command=self.register).grid(row=0, column=1, padx=10)

    def register(self):
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Username and password cannot be empty.")
            return
        success = self.controller.client.register_user(username, password)
        if success:
            messagebox.showinfo("Success", "Registration successful. You can now login.")
            self.controller.show_frame(LoginPage)
        else:
            messagebox.showerror("Error", "Registration failed. Username might be taken.")

class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Main Menu", style="Header.TLabel").pack(pady=20)

        actions = [
            ("List Peers", self.list_peers),
            ("Upload File", self.upload_file),
            ("List Available Files", self.list_files),
            ("Download File", self.download_file),
            ("Share File", self.share_file),
            ("Revoke Access", self.revoke_access),
            ("Logout", self.logout),
            ("Exit", controller.destroy)
        ]

        for text, cmd in actions:
            ttk.Button(self, text=text, width=30, command=cmd).pack(pady=5)

    def list_peers(self):
        peers = self.controller.client.get_peers()
        msg = '\n'.join(peers) if peers else "No other peers found."
        messagebox.showinfo("Peers", msg)

    def upload_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            if self.controller.client.upload_file(filepath):
                messagebox.showinfo("Upload", "File uploaded successfully.")
            else:
                messagebox.showerror("Upload", "Upload failed.")

    def list_files(self):
        files = self.controller.client.get_files_from_registry()
        if files:
            content = '\n'.join(f"ID: {fid}, Name: {info['filename']}, Owner: {info['owner']}" for fid, info in files.items())
            messagebox.showinfo("Files", content)
        else:
            messagebox.showinfo("Files", "No files found.")

    def download_file(self):
        files = self.controller.client.get_files_from_registry()
        if not files:
            messagebox.showinfo("Download", "No files to download.")
            return
        fid = simple_input("Enter File ID to download:")
        if fid not in files:
            messagebox.showerror("Error", "Invalid File ID.")
            return
        dest = filedialog.askdirectory()
        info = files[fid]
        if dest and self.controller.client.download_file(fid, dest, info['owner_address'], info['filename'], info['file_hash']):
            messagebox.showinfo("Download", "Download successful.")
        else:
            messagebox.showerror("Download", "Download failed.")

    def share_file(self):
        fid = simple_input("Enter File ID to share:")
        user = simple_input("Enter username to share with:")
        if self.controller.client.share_file(fid, user):
            messagebox.showinfo("Share", f"File {fid} shared with {user}.")
        else:
            messagebox.showerror("Share", "Failed to share file.")

    def revoke_access(self):
        fid = simple_input("Enter File ID to revoke:")
        user = simple_input("Enter username to revoke access:")
        if self.controller.client.revoke_access(fid, user):
            messagebox.showinfo("Revoke", f"Access revoked for {user}.")
        else:
            messagebox.showerror("Revoke", "Failed to revoke access.")

    def logout(self):
        self.controller.client.username = None
        self.controller.client.session_id = None
        self.controller.client.key = None
        messagebox.showinfo("Logout", "Logged out successfully.")
        self.controller.show_frame(StartPage)

def simple_input(prompt):
    dialog = tk.Toplevel()
    dialog.title("Input")
    dialog.geometry("300x120")
    dialog.configure(bg="#f0f2f5")
    ttk.Label(dialog, text=prompt).pack(pady=10)
    entry = ttk.Entry(dialog)
    entry.pack(pady=5)
    result = {'value': None}
    def confirm():
        result['value'] = entry.get().strip()
        dialog.destroy()
    ttk.Button(dialog, text="OK", command=confirm).pack(pady=10)
    dialog.grab_set()
    dialog.wait_window()
    return result['value']

if __name__ == "__main__":
    app = ClientGUI()
    app.mainloop()
