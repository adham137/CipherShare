import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText # Added for potentially large text output


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Try importing the client; catch ImportError if paths are wrong
try:
    from src.client.fileshare_client import FileShareClient
    # Also need access to Commands enum for download interaction
    from src.utils.commands_enum import Commands
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Please ensure gui_utils.py is placed correctly within the project structure.")
    sys.exit(1)


# --- Helper for running client operations in a separate thread ---
# Prevents freezing the GUI while network operations are in progress
def run_in_thread(func, callback=None, *args, **kwargs):
    def run():
        try:
            result = func(*args, **kwargs)
            if callback:
                # Call callback in the main GUI thread
                app.after(0, callback, result)
        except Exception as e:
            # Handle exceptions in the thread and report to GUI
            error_msg = f"An error occurred: {e}"
            if callback:
                 # Report error to GUI thread
                 app.after(0, lambda: messagebox.showerror("Operation Error", error_msg))
            else:
                 # If no specific callback, just show a general error
                 app.after(0, lambda: messagebox.showerror("Operation Error", error_msg))


    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# --- Custom Dialog for Simple Input ---
class SimpleInputDialog(tk.Toplevel):
    def __init__(self, parent, prompt):
        super().__init__(parent)
        self.transient(parent) # Set to be on top of the parent window
        self.title("Input Required")
        self.geometry("350x150")
        self.configure(bg="#e9ebee") # Light grey background
        self.result = None

        # Center the dialog over the parent
        parent_pos_x = parent.winfo_x()
        parent_pos_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        dialog_width = 350
        dialog_height = 150

        center_x = parent_pos_x + parent_width // 2 - dialog_width // 2
        center_y = parent_pos_y + parent_height // 2 - dialog_height // 2

        self.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")

        self.label = ttk.Label(self, text=prompt, wraplength=300, font=("Segoe UI", 10))
        self.label.pack(pady=10)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.entry_var, width=40, font=("Segoe UI", 10))
        self.entry.pack(pady=5)
        self.entry.focus_set() # Set focus to the entry widget

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        # Bind <Return> key to confirm
        self.bind('<Return>', lambda e=None: self.on_confirm())


        ttk.Button(button_frame, text="Cancel", command=self.on_cancel, width=10).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="OK", command=self.on_confirm, width=10).grid(row=0, column=1, padx=5)


        self.protocol("WM_DELETE_WINDOW", self.on_cancel) # Handle window closing
        self.grab_set() # Modal dialog: disables interaction with other windows
        self.wait_window() # Wait until the dialog is destroyed

    def on_confirm(self):
        self.result = self.entry_var.get().strip()
        self.destroy()

    def on_cancel(self):
        self.result = None # Indicate cancellation
        self.destroy()


# --- Main Application Class ---
class ClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CipherShare - Secure File Sharing")
        self.geometry("800x600") # Increased default window size
        self.configure(bg="#f0f2f5") # Light grey background

        # --- Styling ---
        self.style = ttk.Style()
        self.style.theme_use("clam") # 'clam' theme is usually more modern looking

        # Configure general frame and label styles
        self.style.configure("TFrame", background="#f0f2f5")
        self.style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#333") # Darker header text
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat", background="#007bff", foreground="white") # Blue flat button
        self.style.map("TButton", background=[('active', '#0056b3')]) # Darker blue on hover

        self.style.configure("TEntry", font=("Segoe UI", 10), padding=5)

        # Configure themed buttons for specific actions (optional, but good UX)
        self.style.configure("Accent.TButton", background="#28a745", foreground="white") # Green for primary actions
        self.style.map("Accent.TButton", background=[('active', '#218838')])
        self.style.configure("Warn.TButton", background="#ffc107", foreground="#212529") # Yellow for warnings/secondary actions
        self.style.map("Warn.TButton", background=[('active', '#e0a800')])
        self.style.configure("Danger.TButton", background="#dc3545", foreground="white") # Red for dangerous actions
        self.style.map("Danger.TButton", background=[('active', '#c82333')])


        self.client = FileShareClient()

        # --- Start Peer Thread ---
        # Run peer startup in a separate thread so GUI doesn't freeze during socket binding etc.
        run_in_thread(self.client.start_peer_thread, self.on_peer_startup_complete)

        # Placeholder until peer starts
        self.loading_label = ttk.Label(self, text="Starting peer listener...", style="Header.TLabel")
        self.loading_label.pack(pady=50)


    def on_peer_startup_complete(self, success):
        """Callback after peer thread attempts to start."""
        self.loading_label.pack_forget() # Hide loading message

        if success:
            print("Peer listener started successfully.") # Keep console print for debugging
            self.setup_frames() # Proceed to set up main GUI frames
        else:
            # start_peer_thread already shows an error box on failure
            self.destroy() # Close the GUI if peer failed to start


    def setup_frames(self):
        """Sets up the main frame container and different pages."""
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=10) # Added padding

        # Configure grid for switching frames
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Use a dictionary comprehension for cleaner frame creation
        for F in (StartPage, LoginPage, RegisterPage, MainMenu):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5) # Added padding to frames


        self.show_frame(StartPage)

    def show_frame(self, page):
        frame = self.frames[page]
        # Clear any previous state in the frame if necessary before showing
        if hasattr(frame, 'on_show_frame'):
             frame.on_show_frame()
        frame.tkraise()

    def get_client(self):
        """Helper to get the FileShareClient instance."""
        return self.client

# --- Base Page Frame (for common styling/behavior) ---
class BasePage(ttk.Frame):
    def __init__(self, parent, controller, title):
        super().__init__(parent)
        self.controller = controller

        # Use a header frame to keep title centered easily
        header_frame = ttk.Frame(self)
        header_frame.pack(pady=20, fill="x") # Fill horizontally to center content

        header_label = ttk.Label(header_frame, text=title, style="Header.TLabel")
        header_label.pack(expand=True) # Expand to center the label

        # Optional: Add a separator below the header
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=5)


    def on_show_frame(self):
        """Method called when this frame is brought to the front."""
        pass # Default implementation does nothing

# --- Start Page ---
class StartPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Welcome to CipherShare")

        # Use a frame to center the buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=30, expand=True) # Expand to push buttons down

        ttk.Button(button_frame, text="Login", width=30, command=lambda: controller.show_frame(LoginPage)).pack(pady=10)
        ttk.Button(button_frame, text="Register", width=30, command=lambda: controller.show_frame(RegisterPage)).pack(pady=10)
        ttk.Button(button_frame, text="Exit", width=30, command=controller.destroy, style="Danger.TButton").pack(pady=10)


# --- Login Page ---
class LoginPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Login to CipherShare")

        # Use a frame for the form to control layout
        form = ttk.Frame(self)
        form.pack(pady=20)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        # Use grid for form layout
        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="w", pady=5, padx=5) # Align left, add padding
        entry_user = ttk.Entry(form, textvariable=self.user_var, width=40)
        entry_user.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        entry_pass = ttk.Entry(form, textvariable=self.pass_var, show="*", width=40)
        entry_pass.grid(row=1, column=1, pady=5, padx=5)

        # Bind <Return> key in entry fields to trigger login
        entry_user.bind('<Return>', lambda e=None: self.login())
        entry_pass.bind('<Return>', lambda e=None: self.login())


        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Back", command=lambda: controller.show_frame(StartPage), style="Warn.TButton").grid(row=0, column=0, padx=10) # Use Warn style for Back
        ttk.Button(btn_frame, text="Login", command=self.login, style="Accent.TButton").grid(row=0, column=1, padx=10) # Use Accent style for Login


    def login(self):
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Username and password cannot be empty.")
            return

        # Run login in a separate thread
        run_in_thread(self.controller.get_client().login_user, self.on_login_complete, username, password)

    def on_login_complete(self, success):
        """Callback after login attempt."""
        if success:
            messagebox.showinfo("Success", "Logged in successfully.")
            # Clear password field after successful login for security
            self.pass_var.set("")
            self.controller.show_frame(MainMenu)
        else:
            # Error is shown by the client method itself, or handled by the thread error callback
            pass
            # messagebox.showerror("Error", "Login failed. Check credentials.") # Avoid double error messages if client shows one


# --- Register Page ---
class RegisterPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Register New Account")

        form = ttk.Frame(self)
        form.pack(pady=20)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        entry_user = ttk.Entry(form, textvariable=self.user_var, width=40)
        entry_user.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        entry_pass = ttk.Entry(form, textvariable=self.pass_var, show="*", width=40)
        entry_pass.grid(row=1, column=1, pady=5, padx=5)

        # Bind <Return> key
        entry_user.bind('<Return>', lambda e=None: self.register())
        entry_pass.bind('<Return>', lambda e=None: self.register())


        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Back", command=lambda: controller.show_frame(StartPage), style="Warn.TButton").grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Register", command=self.register, style="Accent.TButton").grid(row=0, column=1, padx=10)


    def register(self):
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Username and password cannot be empty.")
            return

        # Run registration in a separate thread
        run_in_thread(self.controller.get_client().register_user, self.on_register_complete, username, password)


    def on_register_complete(self, success):
        """Callback after registration attempt."""
        if success:
            messagebox.showinfo("Success", "Registration successful. You can now login.")
            # Clear fields after successful registration
            self.user_var.set("")
            self.pass_var.set("")
            self.controller.show_frame(LoginPage)
        else:
             # Error is shown by the client method itself, or handled by the thread error callback
             pass
             # messagebox.showerror("Error", "Registration failed. Username might be taken.") # Avoid double error messages


# --- Main Menu Page ---
class MainMenu(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "CipherShare Main Menu")

        # Frame to hold menu buttons
        menu_frame = ttk.Frame(self)
        menu_frame.pack(pady=20, expand=True) # Expand to center buttons

        actions = [
            ("List Active Peers", self.list_peers), # Clarified what this lists
            ("Upload File", self.upload_file),
            ("Discover Files on Peers", self.discover_files), # Use the new discovery method
            ("View Accessible Files (from Registry)", self.view_accessible_files_registry), # View files you can download
            ("Download File", self.download_file),
            ("Share File (via Registry)", self.share_file),
            ("Revoke Access (via Registry)", self.revoke_access),
            ("Logout", self.logout),
            ("Exit", controller.destroy)
        ]

        for text, cmd in actions:
            # Use different styles for buttons if appropriate
            button_style = "TButton"
            if text in ["Upload File", "Download File"]:
                button_style = "Accent.TButton"
            elif text in ["Share File", "Revoke Access"]:
                 button_style = "TButton" # Default style for less critical actions
            elif text == "Exit":
                 button_style = "Danger.TButton"
            elif text == "Logout":
                 button_style = "Warn.TButton" # Logout is like a soft exit

            ttk.Button(menu_frame, text=text, width=40, command=cmd, style=button_style).pack(pady=5) # Increased button width


    def list_peers(self):
        """Lists active peers using the registry."""
        # Run in thread as it involves network communication
        run_in_thread(self.controller.get_client().get_peers, self.show_peers_list)

    def show_peers_list(self, peers):
        """Callback to display the list of peers."""
        if peers:
            msg = "Active Peers:\n\n" + '\n'.join([f"{p[0]}:{p[1]}" for p in peers])
            messagebox.showinfo("Active Peers", msg)
        else:
            messagebox.showinfo("Active Peers", "No other active peers found.")

    def upload_file(self):
        """Opens a file dialog to select a file for upload."""
        filepath = filedialog.askopenfilename(
            title="Select file to upload",
            # Example file types (adjust as needed)
            filetypes=(("All files", "*.*"), ("Text files", "*.txt"), ("Document files", "*.docx *.pdf"))
        )
        if filepath:
            # Run upload in a separate thread
            run_in_thread(self.controller.get_client().upload_file, self.on_upload_complete, filepath)

    def on_upload_complete(self, success):
        """Callback after upload attempt."""
        if success:
            messagebox.showinfo("Upload Complete", "File uploaded and registered successfully.")
        else:
            # Error message is shown by the client method or thread error callback
            pass
            # messagebox.showerror("Upload Failed", "File upload failed.") # Avoid double error messages

    def discover_files(self):
        """Discovers files available on active peers."""
        # Run discovery in a separate thread
        run_in_thread(self.controller.get_client().get_files_from_peers, self.show_discovered_files)

    def show_discovered_files(self, all_peer_files):
        """Callback to display files discovered on peers."""
        # Use a new window or a dedicated frame for better presentation than messagebox
        discovery_window = tk.Toplevel(self.controller)
        discovery_window.title("Files Discovered on Peers")
        discovery_window.geometry("600x400")
        discovery_window.configure(bg="#e9ebee")

        ttk.Label(discovery_window, text="Files Available on Peers:", style="Header.TLabel").pack(pady=10)
        ttk.Separator(discovery_window, orient="horizontal").pack(fill="x", padx=10, pady=5)


        if not all_peer_files:
            ttk.Label(discovery_window, text="No files found on any active peers.", font=("Segoe UI", 11)).pack(pady=20)
            return

        # Use a Treeview to display files in a structured way
        tree_frame = ttk.Frame(discovery_window)
        tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Create a Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

        file_tree = ttk.Treeview(tree_frame,
                                 yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set,
                                 columns=("size"), # Define columns after the main identifier column
                                 show="tree headings") # 'tree headings' shows the first column and defined columns

        tree_scroll_y.config(command=file_tree.yview)
        tree_scroll_x.config(command=file_tree.xview)

        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        file_tree.pack(side="left", fill="both", expand=True)


        # Define Treeview columns and headings
        file_tree.heading("#0", text="Peer Address / Filename", anchor="w") # #0 is the default tree column
        file_tree.heading("size", text="Size", anchor="w")

        file_tree.column("#0", stretch=tk.YES, minwidth=200)
        file_tree.column("size", stretch=tk.NO, width=100)


        # Populate the Treeview
        for peer_addr, files_list in all_peer_files.items():
            # Insert the peer address as a top-level item
            peer_item_id = file_tree.insert("", tk.END, text=f"Peer: {peer_addr[0]}:{peer_addr[1]}", open=True, tags=('peer',)) # 'open=True' expands it by default
            # Add files under the peer address
            if files_list:
                for file_info in files_list:
                    filename = file_info.get("filename", "N/A")
                    filesize = file_info.get("size", "N/A")
                    file_tree.insert(peer_item_id, tk.END, text=filename, values=(filesize,), tags=('file',))
            else:
                 file_tree.insert(peer_item_id, tk.END, text="[No files shared]", tags=('no_files',))

        # Configure tags for basic styling (optional)
        file_tree.tag_configure('peer', font=("Segoe UI", 10, 'bold'), foreground='blue')
        file_tree.tag_configure('file', font=("Segoe UI", 10))
        file_tree.tag_configure('no_files', font=("Segoe UI", 10, 'italic'), foreground='gray')


    def view_accessible_files_registry(self):
        """Views files accessible to the user as listed by the registry."""
        # Run in thread
        run_in_thread(self.controller.get_client().get_files_from_registry, self.show_accessible_files_registry)

    def show_accessible_files_registry(self, files):
        """Callback to display files accessible from the registry in a structured way."""
        accessible_window = tk.Toplevel(self.controller)
        accessible_window.title("Your Accessible Files (from Registry)")
        accessible_window.geometry("700x400")
        accessible_window.configure(bg="#e9ebee")

        ttk.Label(accessible_window, text="Files You Can Download (from Registry):", style="Header.TLabel").pack(pady=10)
        ttk.Separator(accessible_window, orient="horizontal").pack(fill="x", padx=10, pady=5)


        if not files:
            ttk.Label(accessible_window, text="No files registered in the registry that you can access.", font=("Segoe UI", 11)).pack(pady=20)
            return

        # Use a Treeview for better presentation
        tree_frame = ttk.Frame(accessible_window)
        tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")


        registry_file_tree = ttk.Treeview(tree_frame,
                                          yscrollcommand=tree_scroll_y.set,
                                          xscrollcommand=tree_scroll_x.set,
                                          columns=("filename", "owner", "shared_with"),
                                          show="tree headings")

        tree_scroll_y.config(command=registry_file_tree.yview)
        tree_scroll_x.config(command=registry_file_tree.xview)

        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        registry_file_tree.pack(side="left", fill="both", expand=True)


        # Define columns and headings
        registry_file_tree.heading("#0", text="File ID", anchor="w") # Use File ID as the main tree column
        registry_file_tree.heading("filename", text="Filename", anchor="w")
        registry_file_tree.heading("owner", text="Owner", anchor="w")
        registry_file_tree.heading("shared_with", text="Shared With", anchor="w")

        # Configure column widths
        registry_file_tree.column("#0", stretch=tk.NO, minwidth=50, width=80)
        registry_file_tree.column("filename", stretch=tk.YES, minwidth=150)
        registry_file_tree.column("owner", stretch=tk.NO, minwidth=80, width=100)
        registry_file_tree.column("shared_with", stretch=tk.YES, minwidth=100)


        # Populate the Treeview
        # Sort by file ID for consistency
        for file_id in sorted(files.keys(), key=int):
            file_info = files[file_id]
            filename = file_info.get("filename", "N/A")
            owner = file_info.get("owner", "N/A")
            allowed_users = file_info.get("allowed_users", [])
            shared_with = ", ".join(allowed_users)

            registry_file_tree.insert("", tk.END, iid=file_id, # Use file_id as the internal item identifier
                                      text=str(file_id), # Display file_id in the first column
                                      values=(filename, owner, shared_with))

        # Add a note about how to download
        ttk.Label(accessible_window, text="Note: Use 'Download File' option and enter the File ID to download.", font=("Segoe UI", 9, 'italic'), foreground="gray").pack(pady=5)


    def download_file(self):
        """Initiates the download process."""
        # First, fetch the list of accessible files from the registry
        # This is done in a thread, and then the dialog is shown in the callback
        run_in_thread(self.controller.get_client().get_files_from_registry, self.prompt_for_download)


    def prompt_for_download(self, files):
        """Callback after getting accessible files, prompts user for file ID and destination."""
        if not files:
            messagebox.showinfo("Download", "No files available in the registry for you to download.")
            return

        # Create a Toplevel window to show the list and get input
        download_prompt_window = tk.Toplevel(self.controller)
        download_prompt_window.title("Download File")
        download_prompt_window.geometry("600x450")
        download_prompt_window.configure(bg="#e9ebee")

        ttk.Label(download_prompt_window, text="Select File to Download (from Registry):", style="Header.TLabel").pack(pady=10)
        ttk.Separator(download_prompt_window, orient="horizontal").pack(fill="x", padx=10, pady=5)


        # Display accessible files using a Treeview in this prompt window
        tree_frame = ttk.Frame(download_prompt_window)
        tree_frame.pack(pady=5, padx=10, fill="both", expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

        prompt_file_tree = ttk.Treeview(tree_frame,
                                          yscrollcommand=tree_scroll_y.set,
                                          xscrollcommand=tree_scroll_x.set,
                                          columns=("filename", "owner", "shared_with"),
                                          show="tree headings")

        tree_scroll_y.config(command=prompt_file_tree.yview)
        tree_scroll_x.config(command=prompt_file_tree.xview)

        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        prompt_file_tree.pack(side="left", fill="both", expand=True)

        prompt_file_tree.heading("#0", text="File ID", anchor="w")
        prompt_file_tree.heading("filename", text="Filename", anchor="w")
        prompt_file_tree.heading("owner", text="Owner", anchor="w")
        prompt_file_tree.heading("shared_with", text="Shared With", anchor="w")

        prompt_file_tree.column("#0", stretch=tk.NO, minwidth=50, width=80)
        prompt_file_tree.column("filename", stretch=tk.YES, minwidth=150)
        prompt_file_tree.column("owner", stretch=tk.NO, minwidth=80, width=100)
        prompt_file_tree.column("shared_with", stretch=tk.YES, minwidth=100)


        for file_id in sorted(files.keys(), key=int):
            file_info = files[file_id]
            filename = file_info.get("filename", "N/A")
            owner = file_info.get("owner", "N/A")
            allowed_users = file_info.get("allowed_users", [])
            shared_with = ", ".join(allowed_users)
            prompt_file_tree.insert("", tk.END, iid=file_id, text=str(file_id), values=(filename, owner, shared_with))

        # --- Input for File ID and Destination ---
        input_frame = ttk.Frame(download_prompt_window)
        input_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(input_frame, text="Enter File ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        file_id_var = tk.StringVar()
        file_id_entry = ttk.Entry(input_frame, textvariable=file_id_var, width=15)
        file_id_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(input_frame, text="Destination Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        dest_path_var = tk.StringVar()
        dest_path_entry = ttk.Entry(input_frame, textvariable=dest_path_var, width=40)
        dest_path_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(input_frame, text="Browse", command=lambda: self.select_download_folder(dest_path_var), width=10).grid(row=1, column=2, padx=5)


        # --- Action Buttons ---
        action_button_frame = ttk.Frame(download_prompt_window)
        action_button_frame.pack(pady=10)

        def start_download_action():
            fid = file_id_var.get().strip()
            dest = dest_path_var.get().strip()

            if not fid:
                messagebox.showwarning("Input Required", "Please enter a File ID.")
                return
            if not dest:
                 messagebox.showwarning("Input Required", "Please select a destination folder.")
                 return

            # Validate File ID
            if fid not in files:
                messagebox.showerror("Error", "Invalid File ID.")
                return

            info = files[fid]
            owner_addr = info.get("owner_address")
            filename = info.get("filename")
            file_hash = info.get("file_hash")

            if not all([owner_addr, filename, file_hash]):
                messagebox.showerror("Error", "Incomplete file information from registry.")
                return

            # Convert owner_addr list to tuple if necessary
            if isinstance(owner_addr, list):
                owner_addr = tuple(owner_addr)

            # Check if destination directory exists, prompt to create if not
            if not os.path.isdir(dest):
                if messagebox.askyesno("Create Directory", f"Directory '{dest}' does not exist. Create it?"):
                    try:
                        os.makedirs(dest)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to create directory: {e}")
                        return
                else:
                    return # User chose not to create directory

            download_prompt_window.destroy() # Close the prompt window

            # Run the download in a separate thread
            run_in_thread(self.controller.get_client().download_file, self.on_download_complete,
                          fid, dest, owner_addr, filename, file_hash)


        ttk.Button(action_button_frame, text="Download", command=start_download_action, style="Accent.TButton", width=15).grid(row=0, column=0, padx=10)
        ttk.Button(action_button_frame, text="Cancel", command=download_prompt_window.destroy, style="Warn.TButton", width=15).grid(row=0, column=1, padx=10)

        download_prompt_window.grab_set() # Make this window modal
        download_prompt_window.wait_window() # Wait until this window is closed


    def select_download_folder(self, dest_path_var):
        """Helper function to open a directory chooser dialog."""
        folder_selected = filedialog.askdirectory(title="Select Destination Folder")
        if folder_selected:
            dest_path_var.set(folder_selected)


    def on_download_complete(self, success):
        """Callback after download attempt."""
        if success:
            messagebox.showinfo("Download Complete", "File downloaded successfully.")
        else:
            # Error message is shown by the client method or thread error callback
             pass
            # messagebox.showerror("Download Failed", "File download failed.") # Avoid double error messages


    def share_file(self):
        """Prompts user for file ID and target username to share."""
        # Get accessible files from registry first to help user pick ID
        run_in_thread(self.controller.get_client().get_files_from_registry, self.prompt_for_share)

    def prompt_for_share(self, files):
        """Callback after getting accessible files, prompts for share details."""
        owned_files = {fid: info for fid, info in files.items() if info.get("owner") == self.controller.get_client().username}

        if not owned_files:
            messagebox.showinfo("Share File", "You don't own any files registered in the registry to share.")
            return

        # Create a Toplevel window for sharing
        share_window = tk.Toplevel(self.controller)
        share_window.title("Share File")
        share_window.geometry("500x350")
        share_window.configure(bg="#e9ebee")

        ttk.Label(share_window, text="Share Your Owned Files:", style="Header.TLabel").pack(pady=10)
        ttk.Separator(share_window, orient="horizontal").pack(fill="x", padx=10, pady=5)


        # Display owned files in a Treeview
        tree_frame = ttk.Frame(share_window)
        tree_frame.pack(pady=5, padx=10, fill="both", expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        share_file_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set,
                                      columns=("filename", "shared_with"),
                                      show="tree headings")
        tree_scroll_y.config(command=share_file_tree.yview)
        tree_scroll_y.pack(side="right", fill="y")
        share_file_tree.pack(side="left", fill="both", expand=True)

        share_file_tree.heading("#0", text="File ID", anchor="w")
        share_file_tree.heading("filename", text="Filename", anchor="w")
        share_file_tree.heading("shared_with", text="Shared With", anchor="w")

        share_file_tree.column("#0", stretch=tk.NO, minwidth=50, width=80)
        share_file_tree.column("filename", stretch=tk.YES, minwidth=150)
        share_file_tree.column("shared_with", stretch=tk.YES, minwidth=100)


        for file_id in sorted(owned_files.keys(), key=int):
            file_info = owned_files[file_id]
            filename = file_info.get("filename", "N/A")
            allowed_users = file_info.get("allowed_users", [])
            shared_with = ", ".join(allowed_users)
            share_file_tree.insert("", tk.END, iid=file_id, text=str(file_id), values=(filename, shared_with))

        # --- Input for File ID and Target User ---
        input_frame = ttk.Frame(share_window)
        input_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(input_frame, text="Enter File ID to Share:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        share_file_id_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=share_file_id_var, width=15).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(input_frame, text="Enter Username to Share With:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        share_target_user_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=share_target_user_var, width=30).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # --- Action Buttons ---
        action_button_frame = ttk.Frame(share_window)
        action_button_frame.pack(pady=10)

        def start_share_action():
            fid = share_file_id_var.get().strip()
            user = share_target_user_var.get().strip()

            if not fid or not user:
                messagebox.showwarning("Input Required", "Please enter both File ID and target username.")
                return

            # Validate File ID against owned files
            if fid not in owned_files:
                messagebox.showerror("Error", "Invalid File ID or you do not own this file.")
                return

            if user == self.controller.get_client().username:
                messagebox.showwarning("Cannot Share", "You cannot share a file with yourself.")
                return

            share_window.destroy() # Close the prompt window

            # Run share in a separate thread
            run_in_thread(self.controller.get_client().share_file, self.on_share_complete, fid, user)

        ttk.Button(action_button_frame, text="Share", command=start_share_action, style="Accent.TButton", width=15).grid(row=0, column=0, padx=10)
        ttk.Button(action_button_frame, text="Cancel", command=share_window.destroy, style="Warn.TButton", width=15).grid(row=0, column=1, padx=10)

        share_window.grab_set() # Make modal
        share_window.wait_window() # Wait


    def on_share_complete(self, success):
        """Callback after share attempt."""
        if success:
            messagebox.showinfo("Share Complete", "File shared successfully.")
        else:
            # Error message shown by client or thread callback
            pass
            # messagebox.showerror("Share Failed", "Failed to share file.") # Avoid double error messages


    def revoke_access(self):
        """Prompts user for file ID and target username to revoke access."""
        # Get accessible files (to identify owned files) from registry first
        run_in_thread(self.controller.get_client().get_files_from_registry, self.prompt_for_revoke)

    def prompt_for_revoke(self, files):
        """Callback after getting accessible files, prompts for revoke details."""
        owned_files = {fid: info for fid, info in files.items() if info.get("owner") == self.controller.get_client().username}

        if not owned_files:
            messagebox.showinfo("Revoke Access", "You don't own any files registered in the registry to revoke access from.")
            return

        # Create a Toplevel window for revoking
        revoke_window = tk.Toplevel(self.controller)
        revoke_window.title("Revoke File Access")
        revoke_window.geometry("600x400")
        revoke_window.configure(bg="#e9ebee")

        ttk.Label(revoke_window, text="Revoke Access to Your Owned Files:", style="Header.TLabel").pack(pady=10)
        ttk.Separator(revoke_window, orient="horizontal").pack(fill="x", padx=10, pady=5)


        # Display owned files and users with access
        tree_frame = ttk.Frame(revoke_window)
        tree_frame.pack(pady=5, padx=10, fill="both", expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        revoke_file_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set,
                                        columns=("filename", "shared_with"),
                                        show="tree headings")
        tree_scroll_y.config(command=revoke_file_tree.yview)
        tree_scroll_y.pack(side="right", fill="y")
        revoke_file_tree.pack(side="left", fill="both", expand=True)

        revoke_file_tree.heading("#0", text="File ID", anchor="w")
        revoke_file_tree.heading("filename", text="Filename", anchor="w")
        revoke_file_tree.heading("shared_with", text="Shared With (excluding owner)", anchor="w") # Clarified column header

        revoke_file_tree.column("#0", stretch=tk.NO, minwidth=50, width=80)
        revoke_file_tree.column("filename", stretch=tk.YES, minwidth=150)
        revoke_file_tree.column("shared_with", stretch=tk.YES, minwidth=100)


        for file_id in sorted(owned_files.keys(), key=int):
            file_info = owned_files[file_id]
            filename = file_info.get("filename", "N/A")
            allowed_users = file_info.get("allowed_users", [])
            # List users who have access, excluding the owner, as owner access cannot be revoked here
            users_to_revoke_from = [u for u in allowed_users if u != self.controller.get_client().username]
            shared_with_display = ", ".join(users_to_revoke_from)

            revoke_file_tree.insert("", tk.END, iid=file_id, text=str(file_id), values=(filename, shared_with_display))

        # --- Input for File ID and Target User ---
        input_frame = ttk.Frame(revoke_window)
        input_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(input_frame, text="Enter File ID to Revoke Access:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        revoke_file_id_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=revoke_file_id_var, width=15).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(input_frame, text="Enter Username to Revoke Access:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        revoke_target_user_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=revoke_target_user_var, width=30).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # --- Action Buttons ---
        action_button_frame = ttk.Frame(revoke_window)
        action_button_frame.pack(pady=10)

        def start_revoke_action():
            fid = revoke_file_id_var.get().strip()
            user = revoke_target_user_var.get().strip()

            if not fid or not user:
                messagebox.showwarning("Input Required", "Please enter both File ID and target username.")
                return

             # Validate File ID against owned files
            if fid not in owned_files:
                messagebox.showerror("Error", "Invalid File ID or you do not own this file.")
                return

            # Check if the target user actually has access (excluding the owner)
            file_info = owned_files[fid]
            allowed_users = file_info.get("allowed_users", [])
            users_who_can_be_revoked = [u for u in allowed_users if u != self.controller.get_client().username]

            if user not in users_who_can_be_revoked:
                 messagebox.showwarning("Cannot Revoke", f"User '{user}' does not have share access to this file.")
                 return

            revoke_window.destroy() # Close the prompt window

            # Run revoke in a separate thread
            run_in_thread(self.controller.get_client().revoke_access, self.on_revoke_complete, fid, user)

        ttk.Button(action_button_frame, text="Revoke", command=start_revoke_action, style="Danger.TButton", width=15).grid(row=0, column=0, padx=10) # Danger style for revoke
        ttk.Button(action_button_frame, text="Cancel", command=revoke_window.destroy, style="Warn.TButton", width=15).grid(row=0, column=1, padx=10)

        revoke_window.grab_set() # Make modal
        revoke_window.wait_window() # Wait


    def on_revoke_complete(self, success):
        """Callback after revoke attempt."""
        if success:
            messagebox.showinfo("Revoke Complete", "Access revoked successfully.")
        else:
            # Error message shown by client or thread callback
             pass
            # messagebox.showerror("Revoke Failed", "Failed to revoke access.") # Avoid double error messages


    def logout(self):
        """Logs out the user and returns to the start page."""
        self.controller.get_client().username = None
        self.controller.get_client().session_id = None
        self.controller.get_client().key = None
        messagebox.showinfo("Logout", "Logged out successfully.")
        self.controller.show_frame(StartPage)




# --- Main execution block ---
if __name__ == "__main__":
    # Ensure shared files directory exists if the GUI is run directly
    # This is also done in fileshare_client's __main__, but good to be robust
    try:
        # Assuming Config is available via the import path
        from src.utils.config import Config
        os.makedirs(Config.SHARED_FILES_DIR, exist_ok=True)
    except ImportError:
        print("Warning: Could not import Config. Ensure project structure is correct.")
        # Fallback if Config is not available
        if not os.path.exists("shared_files"):
             os.makedirs("shared_files", exist_ok=True)
             print("Created default 'shared_files' directory.")
    except Exception as e:
         print(f"Error ensuring shared_files directory exists: {e}")


    app = ClientGUI()
    app.mainloop()