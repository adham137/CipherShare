import socket
from abc import ABC, abstractmethod

class CommandStrategy(ABC):
    """Abstract base class for command handling strategies."""

    @abstractmethod
    def execute(self, client_socket: socket.socket, **kwargs):
        """
        Executes the specific command logic.

        Args:
            client_socket: The socket connected to the client requesting the command.
            **kwargs: Additional arguments specific to the command (e.g., filename, file_id).
        """
        pass