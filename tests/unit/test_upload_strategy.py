import os
import pytest

from src.peer.strategies.upload_strategy import UploadStrategy
from src.utils.config import Config
from src.utils.commands_enum import Commands

# ─── Helpers & Decorators ────────────────────────────────────────────
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RESET  = "\033[0m"

def print_header(name):
    print(f"\n{CYAN}{'─'*60}{RESET}")
    print(f"{YELLOW}▶ Running {name}{RESET}")
    print(f"{CYAN}{'─'*60}{RESET}")

def print_footer(name):
    print(f"{GREEN}✔ {name} passed{RESET}")

class DummySocket:
    """Returns predefined chunks to simulate client uploads."""
    def __init__(self, chunks):
        self._chunks = chunks

    def recv(self, bufsize):
        return self._chunks.pop(0)

# ─── Fixture: Temporary shared directory ─────────────────────────────────────
@pytest.fixture(autouse=True)
def temp_shared(tmp_path):
    d = tmp_path / "shared"
    d.mkdir()
    Config.SHARED_FILES_DIR = str(d)
    yield str(d)

# ─── Tests ─────────────────────────────────────────────────────────────

def test_execute_writes_file_and_stops(temp_shared):
    name = "test_execute_writes_file_and_stops"
    print_header(name)

    # simulate two data chunks followed by DONE
    data = [b"hello", b"world", str(Commands.DONE).encode()]
    sock = DummySocket(data.copy())

    up = UploadStrategy()
    up.execute(sock, filename="file.txt")

    # Verify file contents
    path = os.path.join(temp_shared, "file.txt")
    assert os.path.isfile(path)
    assert open(path, "rb").read() == b"helloworld"

    print_footer(name)
