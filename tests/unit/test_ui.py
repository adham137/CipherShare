# # tests/unit/test_ui.py

# import builtins
# import sys
# import pytest

# from src.client.fileshare_client import FileShareClient
# from src.utils.ui_utils import client_ui

# # ─── Color Print Helpers ────────────────────────────────────────────────
# CYAN   = "\033[36m"
# YELLOW = "\033[33m"
# GREEN  = "\033[32m"
# RESET  = "\033[0m"

# def print_header(name):
#     sys.stderr.write(
#         f"\n{CYAN}{'─'*60}{RESET}\n"
#         f"{YELLOW}▶ Running {name}{RESET}\n"
#         f"{CYAN}{'─'*60}{RESET}\n"
#     )

# def print_footer(name):
#     sys.stderr.write(f"{GREEN}✔ {name} passed{RESET}\n")

# # ─── Stubbed Client Fixture ─────────────────────────────────────────────
# @pytest.fixture(autouse=True)
# def stub_client(monkeypatch):
#     c = FileShareClient()
#     c.username = None
#     c.session_id = None
#     c.peer_address = ("127.0.0.1", 5000)

#     monkeypatch.setattr(c, "register_user", lambda u, p: True)
#     monkeypatch.setattr(c, "login_user", lambda u, p: True)
#     monkeypatch.setattr(c, "get_peers", lambda: ["Alice", "Bob"])
#     monkeypatch.setattr(c, "upload_file", lambda f: True)
#     monkeypatch.setattr(c, "download_file", lambda *args, **kwargs: True)
#     monkeypatch.setattr(c, "get_files_from_registry", lambda: {})
#     monkeypatch.setattr(c, "share_file", lambda *args: True)
#     monkeypatch.setattr(c, "revoke_access", lambda *args: True)
#     return c

# # ─── Input Feeder ───────────────────────────────────────────────────────
# def feed_inputs(monkeypatch, inputs):
#     it = iter(inputs)
#     monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))

# # ─── Test: Register then Exit ───────────────────────────────────────────
# def test_register_then_exit(stub_client, capsys, monkeypatch):
#     name = "test_register_then_exit"
#     print_header(name)

#     # Flow: not logged in → Register → Exit
#     feed_inputs(monkeypatch, ["1", "moamen", "password123", "3"])
#     client_ui(stub_client)

#     out = capsys.readouterr().out
#     assert "Register – Create a new account" in out
#     assert "Login – Access your account" in out
#     assert "Exit – Quit the client" in out

#     print_footer(name)

# # ─── Test: List Peers → Logout → Exit ───────────────────────────────────
# def test_list_peers_logout_exit(stub_client, capsys, monkeypatch):
#     name = "test_list_peers_logout_exit"
#     print_header(name)

#     # Pretend already logged in
#     stub_client.username = "moamen"
#     stub_client.session_id = "session123"

#     # Flow: List Peers → [Enter] → Logout → Exit
#     feed_inputs(monkeypatch, ["4", "", "10", "3"])
#     client_ui(stub_client)

#     out = capsys.readouterr().out
#     assert "Available Peers" in out
#     assert "Logged out successfully" in out

#     print_footer(name)
