# src/peer/command_factory.py
from src.utils.commands_enum import Commands
from .strategies.command_strategy import CommandStrategy
from .strategies.upload_strategy import UploadStrategy
from .strategies.download_strategy import DownloadStrategy
from.strategies.get_peer_files_strategy import GetPeerFilesStrategy

class CommandFactory:
    """Factory class to create command strategy instances."""

    _strategies = {
        Commands.UPLOAD: UploadStrategy(),
        Commands.DOWNLOAD: DownloadStrategy(),
        Commands.GET_PEER_FILES: GetPeerFilesStrategy()
       
    }

    @staticmethod
    def get_command_handler(command: Commands) -> CommandStrategy | None:
        """
        Gets the strategy handler for a given command.

        Args:
            command: The command enum member.

        Returns:
            An instance of the corresponding CommandStrategy, or None if not found.
        """
        return CommandFactory._strategies.get(command)