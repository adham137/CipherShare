from enum import Enum, auto

class Commands(Enum):
    """Enum defining the commands used in the CipherShare protocol."""
    # Registry Commands
    REGISTER_PEER = auto()
    GET_PEERS = auto()
    REGISTER_FILE = auto()
    GET_FILES = auto()

    # Client-to-Peer Commands
    UPLOAD = auto()
    DOWNLOAD = auto()

    # Control Signals
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