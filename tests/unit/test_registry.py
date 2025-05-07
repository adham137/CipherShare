import json
import pytest

from src.utils.commands_enum import Commands
from src.utils.crypto_utils import generate_session_id
import src.central_registry.registry as registry_module

# ─── FakeSocket ──────────────────────────────────────────────────────────────────
class FakeSocket:
    def __init__(self, recv_data):
        self._recv_data = recv_data
        self.sent_data = b""
        self.closed = False

    def recv(self, bufsize):
        return self._recv_data

    def send(self, data):
        self.sent_data += data
        return len(data)

    def close(self):
        self.closed = True

# ─── Fixture: Clear Global State ─────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def clear_registry_state():
    registry_module.REGISTERED_PEERS.clear()
    registry_module.USER_CREDENTIALS.clear()
    registry_module.USER_SESSIONS.clear()
    registry_module.SHARED_FILES.clear()
    registry_module.FILE_ID_COUNTER = 0
    yield

# ─── Helper Function ──────────────────────────────────────────────────────────────
def send_request_and_get_response(request_dict):
    data_bytes = json.dumps(request_dict).encode()
    sock = FakeSocket(data_bytes)
    registry_module.handle_client(sock)
    return sock.sent_data

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
def register_and_login():
    send_request_and_get_response({
        "command": Commands.REGISTER_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    })
    login_resp = json.loads(send_request_and_get_response({
        "command": Commands.LOGIN_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    }).decode())
    return login_resp["session_id"]

def test_register_user_success():
    print_header("test_register_user_success")
    req = {
        "command": Commands.REGISTER_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    }
    resp = json.loads(send_request_and_get_response(req).decode())
    assert resp["status"] == "OK"
    print_footer("test_register_user_success")

def test_register_user_duplicate():
    print_header("test_register_user_duplicate")
    req = {
        "command": Commands.REGISTER_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    }
    send_request_and_get_response(req)
    resp_dup = json.loads(send_request_and_get_response(req).decode())
    assert resp_dup["status"] == "ERROR"
    print_footer("test_register_user_duplicate")

def test_login_user_success():
    print_header("test_login_user_success")
    send_request_and_get_response({
        "command": Commands.REGISTER_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    })
    resp = json.loads(send_request_and_get_response({
        "command": Commands.LOGIN_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    }).decode())
    assert resp["status"] == "OK"
    assert "session_id" in resp
    print_footer("test_login_user_success")

def test_login_user_invalid_password():
    print_header("test_login_user_invalid_password")
    send_request_and_get_response({
        "command": Commands.REGISTER_USER.name,
        "username": "moamen",
        "password": "password123",
        "peer_address": ("127.0.0.1", 5000)
    })
    resp = json.loads(send_request_and_get_response({
        "command": Commands.LOGIN_USER.name,
        "username": "moamen",
        "password": "wrongpass",
        "peer_address": ("127.0.0.1", 5000)
    }).decode())
    assert resp["status"] == "ERROR"
    print_footer("test_login_user_invalid_password")

def test_get_peers():
    print_header("test_get_peers")
    session_id = register_and_login()
    resp = json.loads(send_request_and_get_response({
        "command": Commands.GET_PEERS.name,
        "session_id": session_id
    }).decode())
    assert ["127.0.0.1", 5000] in resp
    print_footer("test_get_peers")

def test_register_file_and_get_files():
    print_header("test_register_file_and_get_files")
    session_id = register_and_login()
    resp = json.loads(send_request_and_get_response({
        "command": Commands.REGISTER_FILE.name,
        "session_id": session_id,
        "filename": "test.txt",
        "owner_address": ["127.0.0.1", 5000],
        "file_hash": "abc123"
    }).decode())
    assert resp["status"] == "OK"
    file_id = resp["file_id"]
    files = json.loads(send_request_and_get_response({
        "command": Commands.GET_FILES.name,
        "session_id": session_id
    }).decode())
    assert str(file_id) in files
    print_footer("test_register_file_and_get_files")