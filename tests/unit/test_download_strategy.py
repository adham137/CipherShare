import os
import tempfile
import socket
import json
import pytest

from src.peer.strategies.download_strategy import DownloadStrategy
from src.utils.config import Config
from src.utils.commands_enum import Commands

# ─── Helpers & Decorators ────────────────────────────────────────────
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RESET  = "\033[0m"

def print_header(name):
    print(f"\n{CYAN}{'─' * 60}{RESET}")
    print(f"{YELLOW}▶ Running {name}{RESET}")
    print(f"{CYAN}{'─' * 60}{RESET}")

def print_footer(name):
    print(f"{GREEN}✔ {name} passed{RESET}")

class DummySocket:
    def __init__(self):
        self.sent = b""
    def sendall(self, data):
        self.sent += data

# ─── Fixture: Setup a temp shared directory ────────────────────────────────
@pytest.fixture
def shared_dir(tmp_path, monkeypatch):
    path = tmp_path / "shared"
    path.mkdir()
    # create two files
    f1 = path / "a.txt"; f1.write_text("AAA")
    f2 = path / "b.txt"; f2.write_text("BBB")
    # Point Config at our temp directory
    Config.SHARED_FILES_DIR = str(path)
    yield str(path)

# ─── Tests ─────────────────────────────────────────────────────────────

def test_get_file_path_valid(shared_dir):
    name = "test_get_file_path_valid"
    print_header(name)

    ds = DownloadStrategy()
    p0 = ds.get_file_path("0", shared_dir)
    assert p0.endswith(os.path.join("shared", "a.txt"))
    p1 = ds.get_file_path("1", shared_dir)
    assert p1.endswith(os.path.join("shared", "b.txt"))

    print_footer(name)

def test_get_file_path_invalid_id(shared_dir):
    name = "test_get_file_path_invalid_id"
    print_header(name)

    ds = DownloadStrategy()
    p = ds.get_file_path("42", shared_dir)
    assert p is None

    print_footer(name)

def test_get_file_path_bad_format(shared_dir):
    name = "test_get_file_path_bad_format"
    print_header(name)

    ds = DownloadStrategy()
    p = ds.get_file_path("not_int", shared_dir)
    assert p is None

    print_footer(name)

def test_execute_sends_file_and_done(shared_dir):
    name = "test_execute_sends_file_and_done"
    print_header(name)

    ds = DownloadStrategy()
    sock = DummySocket()
    ds.execute(sock, file_id_str="0")

    # Verify data and DONE marker
    assert b"AAA" in sock.sent
    assert str(Commands.DONE).encode() in sock.sent

    print_footer(name)
