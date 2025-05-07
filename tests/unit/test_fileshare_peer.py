# tests/unit/test_fileshare_peer.py
import socket
import pytest

import src.peer.fileshare_peer as peer_module
from src.utils.commands_enum import Commands
from src.peer.command_factory import CommandFactory

# ─── Decorative Print Helpers ────────────────────────────────
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

# ─── Fakes ────────────────────────────────────────────────────

class DummySocket:
    """Simulates the server socket for both __init__ and accept()."""
    def __init__(self):
        self._client = None
        self._bound_addr = None

    def setsockopt(self, level, optname, value):
        # no-op
        pass

    def bind(self, addr):
        # record what gets bound
        self._bound_addr = addr

    def listen(self, backlog):
        pass

    def accept(self):
        # Return the queued client socket & a fake address
        return self._client, ('127.0.0.1', 9999)

    def set_client(self, client):
        self._client = client

    def getsockname(self):
        host, port = self._bound_addr
        # for ephemeral port tests, pretend OS assigned port 12345
        return (host, 12345)

    def close(self):
        pass

class DummyClientConn:
    """Simulates a client connection for handle_client_connection()."""
    def __init__(self, chunks):
        # chunks is a list of byte-strings to return on successive recv()
        self._chunks = chunks[:]
        self.sent = b""
        self.closed = False

    def recv(self, bufsize):
        # Return next chunk (or empty to indicate close)
        return self._chunks.pop(0) if self._chunks else b""

    def sendall(self, data):
        self.sent += data

    def close(self):
        self.closed = True

# ─── Tests ────────────────────────────────────────────────────

def test_init_picks_ephemeral_port(monkeypatch):
    name = "test_init_picks_ephemeral_port"
    print_header(name)

    # Monkey-patch socket.socket() to return our DummySocket
    dummy = DummySocket()
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: dummy)

    peer = peer_module.FileSharePeer(requested_port=0)
    # After __init__, peer.port should reflect our fake getsockname()
    assert peer.port == 12345

    print_footer(name)

def test_handle_unknown_command(capsys):
    name = "test_handle_unknown_command"
    print_header(name)

    # Bypass __init__
    peer = peer_module.FileSharePeer.__new__(peer_module.FileSharePeer)

    conn = DummyClientConn([b"FOO\n"])
    peer.handle_client_connection(conn, ('1.2.3.4', 1111))

    out = capsys.readouterr().out
    assert "unknown command" in out.lower() or "no handler" in out.lower()
    assert conn.closed

    print_footer(name)

def test_handle_upload_invokes_strategy():
    name = "test_handle_upload_invokes_strategy"
    print_header(name)

    # Stub out factory to return our fake upload handler
    called = {}
    class FakeUpload:
        def execute(self, client_socket, **kwargs):
            called['socket'] = client_socket
            called['filename'] = kwargs.get('filename')

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(CommandFactory, "get_command_handler",
                       lambda cmd: FakeUpload() if cmd == Commands.UPLOAD else None)

    peer = peer_module.FileSharePeer.__new__(peer_module.FileSharePeer)
    conn = DummyClientConn([b"UPLOAD\n", b"myfile.txt\n"])
    peer.handle_client_connection(conn, ('1.2.3.4', 2222))

    assert called['socket'] is conn
    assert called['filename'] == "myfile.txt"
    monkeypatch.undo()

    print_footer(name)

def test_handle_download_invokes_strategy():
    name = "test_handle_download_invokes_strategy"
    print_header(name)

    # Stub out factory to return our fake download handler
    called = {}
    class FakeDownload:
        def execute(self, client_socket, **kwargs):
            called['socket'] = client_socket
            called['file_id_str'] = kwargs.get('file_id_str')

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(CommandFactory, "get_command_handler",
                       lambda cmd: FakeDownload() if cmd == Commands.DOWNLOAD else None)

    peer = peer_module.FileSharePeer.__new__(peer_module.FileSharePeer)
    conn = DummyClientConn([b"DOWNLOAD\n", b"42\n"])
    peer.handle_client_connection(conn, ('5.6.7.8', 3333))

    assert called['socket'] is conn
    assert called['file_id_str'] == "42"
    monkeypatch.undo()

    print_footer(name)
