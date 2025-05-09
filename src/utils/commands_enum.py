from enum import Enum, auto

class Commands(Enum):
    """Enum defining the commands used in the CipherShare protocol."""
# Registry Commands
    REGISTER_USER = auto()
    LOGIN_USER = auto()
    VERIFY_SESSION = auto()
    REGISTER_PEER = auto() 
    GET_PEERS = auto()

    REGISTER_FILE = auto()
    GET_FILES = auto() # get files from Registry (accessible to user)
    REQUEST_KEY = auto()

    # commands for access control
    SHARE_FILE = auto()
    REVOKE_ACCESS = auto()
    CHECK_ACCESS = auto()

    # client-to-peer Commands
    UPLOAD = auto()
    DOWNLOAD = auto()
    GET_PEER_FILES = auto() # New command to ask a peer what files it has

    # control Signals
    DONE = auto()
    ERROR = auto()


    # string -> enum
    @classmethod
    def from_string(cls, command_str):
        try:
            return cls[command_str.upper()]
        except KeyError:
            return None

    def __str__(self):
        return self.name

