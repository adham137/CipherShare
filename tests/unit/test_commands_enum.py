# tests/unit/test_commands_enum.py

import pytest
from src.utils.commands_enum import Commands

# ─── Decorative Print Helpers ────────────────────────────────
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

# ─── Tests ────────────────────────────────────────────────────

def test_from_string_valid_cases():
    name = "test_from_string_valid_cases"
    print_header(name)

    # case-insensitive matching
    assert Commands.from_string("register_user") is Commands.REGISTER_USER
    assert Commands.from_string("Login_User")  is Commands.LOGIN_USER
    assert Commands.from_string("VERIFY_SESSION") is Commands.VERIFY_SESSION
    assert Commands.from_string("upload")      is Commands.UPLOAD
    assert Commands.from_string("Download")    is Commands.DOWNLOAD

    print_footer(name)

def test_from_string_invalid_returns_none():
    name = "test_from_string_invalid_returns_none"
    print_header(name)

    assert Commands.from_string("not_a_command") is None
    assert Commands.from_string("") is None
    assert Commands.from_string("123") is None

    print_footer(name)

def test_str_outputs_name():
    name = "test_str_outputs_name"
    print_header(name)

    for cmd in Commands:
        # str(cmd) should equal the enum member’s name
        assert str(cmd) == cmd.name

    print_footer(name)
