# CipherShare - Phase 1 Architecture

The architecture for Phase 1 is a simple client-server model over TCP/IP sockets, representing the most basic P2P interaction:

1.  **Peer Node (`fileshare_peer_phase1.py`)**:
    * Opens a TCP socket and listens on a specific port (e.g., 65432).
    * Accepts incoming connections from clients.
    * Handles basic commands (`LIST_FILES`, `DOWNLOAD_FILE`) in separate threads.
    * Sends back hardcoded responses (file lists or dummy data).

2.  **Client Node (`fileshare_client_phase1.py`)**:
    * Opens a TCP socket.
    * Connects to the Peer Node's IP address and port.
    * Sends commands (`LIST_FILES`, `DOWNLOAD_FILE`) to the peer.
    * Receives and prints the peer's responses.

