
class Config:
    """Static configuration settings for CipherShare."""
    REGISTRY_IP = "127.0.0.1"           # Use 127.0.0.1 for localhost testing
    REGISTRY_PORT = 5000
    PEER_HOST = '127.0.0.1'             # Peer listens on localhost by default
    CHUNK_SIZE = 102400                 # 100KB chunk size for file transfers
    SHARED_FILES_DIR = "shared_files"   # Directory for peer to store received files