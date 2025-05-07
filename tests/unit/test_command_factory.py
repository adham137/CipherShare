import pytest

from src.utils.commands_enum import Commands
from src.peer.command_factory import CommandFactory
from src.peer.strategies.upload_strategy import UploadStrategy
from src.peer.strategies.download_strategy import DownloadStrategy

# ─── Decorative Print Helpers ────────────────────────────────
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RESET  = "\033[0m"

def print_header(name):
    print(f"\n{CYAN}{'─' * 60}{RESET}")
    print(f"{YELLOW}▶ Running {name}{RESET}")
    print(f"{CYAN}{'─' * 60}{RESET}")

def print_footer(name, passed=True):
    # Entire footer in green
    status = "passed" if passed else "failed"
    print(f"{GREEN}✔ {name} {status}{RESET}")


# ─── Tests ────────────────────────────────────────────────────

def test_get_command_handler_known():
    name = "test_get_command_handler_known"
    print_header(name)

    up = CommandFactory.get_command_handler(Commands.UPLOAD)
    dl = CommandFactory.get_command_handler(Commands.DOWNLOAD)

    assert isinstance(up, UploadStrategy)
    assert isinstance(dl, DownloadStrategy)

    print_footer(name)

def test_get_command_handler_unknown():
    name = "test_get_command_handler_unknown"
    print_header(name)

    handler = CommandFactory.get_command_handler(Commands.REGISTER_USER)
    assert handler is None

    print_footer(name)
