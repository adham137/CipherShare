import os
import json
import pytest

from src.client.fileshare_client import FileShareClient
from src.utils.commands_enum import Commands

# ─── Helpers & Fakes ─────────────────────────────────────────────────────────────

class DummySocket:
    """A fake socket for testing sendall()/recv() behavior."""
    def __init__(self, recv_bytes=b""):
        self._recv_bytes = recv_bytes
        self.sent = b""
        self.closed = False

    def sendall(self, data):
        self.sent += data

    def recv(self, bufsize):
        return self._recv_bytes

    def close(self):
        self.closed = True

class DummyPeer:
    """Stub for FileSharePeer to avoid real networking."""
    def __init__(self, port):
        self.port = 12345

    def start_peer(self):
        return

# ─── Fixture ────────────────────────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    """Return a FileShareClient with its socket connector stubbed out."""
    c = FileShareClient()
    monkeypatch.setattr(c, "_connect_socket", lambda a, p: DummySocket())
    return c

# ─── Decorative Print Helpers ────────────────────────────────────────────────────

CYAN   = "\033[36m"
YELLOW = "\033[33m"
GREEN  = "\033[32m"
RESET  = "\033[0m"

def print_header(name):
    print(f"\n{CYAN}{'─' * 60}{RESET}")
    print(f"{YELLOW}▶ Running {name}{RESET}")
    print(f"{CYAN}{'─' * 60}{RESET}")

def print_footer(name):
    print(f"{GREEN}✔ {name} passed{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

# ─── Unit Tests ──────────────────────────────────────────────────────────────────
def test_register_user_success(monkeypatch, client, capsys):
    print_header("test_register_user_success")
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(b'{"status": "OK"}'))
    client.peer_address = ("127.0.0.1", 5000)
    assert client.register_user("u", "p") is True
    assert "Registration successful" in capsys.readouterr().out
    print_footer("test_register_user_success")

def test_register_user_failure(monkeypatch, client, capsys):
    print_header("test_register_user_failure")
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(b'{"status": "ERROR", "message": "duplicate"}'))
    client.peer_address = ("127.0.0.1", 5000)
    assert not client.register_user("u", "p")
    assert "Registration failed" in capsys.readouterr().out
    print_warning("Duplicate registration handled correctly")
    print_footer("test_register_user_failure")

def test_login_user_success(monkeypatch, client, capsys):
    print_header("test_login_user_success")
    mock_reply = {"status": "OK", "session_id": "abc", "key": "somekey"}
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(json.dumps(mock_reply).encode()))
    client.peer_address = ("127.0.0.1", 5000)
    assert client.login_user("u", "p") is True
    assert client.session_id == "abc" and client.key == "somekey"
    assert "Login successful" in capsys.readouterr().out
    print_footer("test_login_user_success")

def test_login_user_failure(monkeypatch, client, capsys):
    print_header("test_login_user_failure")
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(b'{"status": "ERROR", "message": "invalid"}'))
    client.peer_address = ("127.0.0.1", 5000)
    assert not client.login_user("u", "x")
    out = capsys.readouterr().out
    assert "Login failed" in out and "invalid" in out
    print_warning("Login failure correctly handled")
    print_footer("test_login_user_failure")

def test_get_peers(monkeypatch, client):
    print_header("test_get_peers")
    client.session_id = "abc"
    client.peer_address = ("2.2.2.2", 2000)
    peer_list = [["1.1.1.1", 1000], ["2.2.2.2", 2000]]
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(json.dumps(peer_list).encode()))
    assert client.get_peers() == [("1.1.1.1", 1000)]
    print_footer("test_get_peers")

def test_register_file_with_registry(monkeypatch, client):
    print_header("test_register_file_with_registry")
    client.session_id = "abc"
    client.username = "user"
    client.peer_address = ("1.2.3.4", 4321)
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(b'{"status": "OK", "file_id": 77}'))
    assert client.register_file_with_registry("test.txt", "hash123") == 77
    print_footer("test_register_file_with_registry")

def test_get_files_from_registry(monkeypatch, client):
    print_header("test_get_files_from_registry")
    client.session_id = "abc"
    mock_files = {"file_1": {"filename": "a.txt"}}
    monkeypatch.setattr(client, "_connect_socket", lambda a, p: DummySocket(json.dumps(mock_files).encode()))
    assert client.get_files_from_registry()["file_1"]["filename"] == "a.txt"
    print_footer("test_get_files_from_registry")

def test_upload_file_not_logged_in(client):
    print_header("test_upload_file_not_logged_in")
    client.session_id = None
    assert client.upload_file("/tmp/f.txt") is False
    print_warning("Upload blocked without login")
    print_footer("test_upload_file_not_logged_in")

def test_upload_file_missing_file(monkeypatch, client, capsys):
    print_header("test_upload_file_missing_file")
    client.session_id = "abc"
    client.key = "k"
    client.peer_address = ("1.1.1.1", 1234)
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    assert client.upload_file("notfound.txt") is False
    assert "File not found" in capsys.readouterr().out
    print_warning("Upload blocked for missing file")
    print_footer("test_upload_file_missing_file")

def test_download_file_not_logged_in(client):
    print_header("test_download_file_not_logged_in")
    assert client.download_file("id1", "/tmp", ("1.1.1.1", 9999), "a.txt", "expected_hash") is False
    print_warning("Download blocked without login")
    print_footer("test_download_file_not_logged_in")

def test_start_peer_thread(monkeypatch, client):
    print_header("test_start_peer_thread")
    monkeypatch.setattr("src.client.fileshare_client.FileSharePeer", DummyPeer)
    assert client.start_peer_thread() is True
    assert client.peer_address[1] == 12345
    print_footer("test_start_peer_thread")