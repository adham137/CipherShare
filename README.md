# CipherShare - Secure P2P File Sharing

**Course**: CSE451 Computer and Network Security  
**Team**: Moamen, Laila, Adham   

---

## 📖 Overview
This project is for the course CSE451:Computer and Network Security. CipherShare is a secure peer-to-peer (P2P) file-sharing system designed to ensure confidentiality, integrity, and controlled access. It combines encryption, a central registry for access management, and a user-friendly CLI to enable secure file transfers between authenticated users. 

## 🔑 Key Features
- **Secure Authentication**:  
  - Password hashing with **Argon2** and **PBKDF2**.
  - Session-based access using unique session IDs.
- **Encrypted File Transfers**:  
  - Files encrypted with **AES-256-CBC** before upload.
  - Decryption keys managed by the central registry.
- **Access Control**:  
  - File owners can share/revoke access to other users.
  - Registry enforces permissions for downloads.
- **Peer-to-Peer Architecture**:  
  - Peers handle direct file transfers after registry authorization.
  - Supports simultaneous uploads/downloads via threading.

## ⚙️ Technical Components
1. **Central Registry**:  
   - Manages user credentials, active peers, and file metadata.
   - Persists data in `registry_data.json`.
2. **Client**:  
   - Handles user interactions (login, file sharing, access management).
   - Connects to the registry and other peers.
3. **Peer Node**:  
   - Listens for incoming file requests.
   - Implements strategies for upload/download operations.

## 🛠️ Installation
1. **Clone the repository**:
   ```bash
   git clone [REPO_URL]
   cd adham137-ciphershare
   ```
2. **Set up a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install colorama pytest rich pyfiglet pycryptodome
   ```

## 🚀 Usage
1. **Start the Central Registry**:
   ```bash
   python src/central_registry/registry.py
   ```
2. **Run a Client** (in a new terminal):
   ```bash
   python src/client/fileshare_client.py
   ```
   - Follow the CLI menu to register, log in, and share files.

### Example Workflow
1. **Register & Log In**:  
   Create an account and log in to start sharing files.
2. **Upload a File**:  
   Files are encrypted locally and registered with the registry.
3. **Share Files**:  
   Grant access to other users via their usernames.
4. **Download Files**:  
   Request access to files shared with you. Decryption keys are fetched automatically.

## 🔒 Security Mechanisms
- **Password Hashing**: Argon2 for storage-safe password hashing.
- **Session Management**: Time-bound sessions with unique IDs.
- **File Integrity**: SHA-256 hashes verify file authenticity.
- **Encryption**: AES-256-CBC for file encryption; keys derived via PBKDF2.

## 🧪 Testing
Run unit tests to validate components:
```bash
# Run all tests
pytest tests/unit/ -q -s

# Test specific modules (e.g., cryptography)
pytest tests/unit/test_crypto_utils.py -q -s
```

## 📂 Directory Structure
```
adham137-ciphershare/
├── src/                  # Core logic
│   ├── central_registry  # Registry server and data management
│   ├── client            # User interface and client logic
│   ├── peer              # P2P file transfer strategies
│   └── utils             # Security, config, and UI helpers
├── tests/                # Unit and integration tests
└── shared_files/         # Default directory for uploaded files
```
