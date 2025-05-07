import re
import pytest

from src.utils import crypto_utils

# ─── Decorative Print Helpers ─────────────────────────────────────────────
CYAN   = "\033[36m"
YELLOW = "\033[33m"
GREEN  = "\033[32m"
RESET  = "\033[0m"

def print_header(name):
    print(f"\n{CYAN}{'─'*60}{RESET}")
    print(f"{YELLOW}▶ Running {name}{RESET}")
    print(f"{CYAN}{'─'*60}{RESET}")

def print_footer(name, passed=True):
    mark = f"{GREEN}✔{RESET}"
    print(f"{mark} {GREEN}{name} passed{RESET}" if passed else f"{mark} {name} failed")

# ─── Tests ────────────────────────────────────────────────
def test_hash_and_verify_password_success():
    print_header("test_hash_and_verify_password_success")
    pw = "SuperSecret123!"
    hashed, salt = crypto_utils.hash_password_SHA256(pw)
    assert crypto_utils.verify_password_256(pw, hashed, salt)
    print_footer("test_hash_and_verify_password_success")

def test_hash_password_different_salts():
    print_header("test_hash_password_different_salts")
    pw = "UniqueSalt"
    h1, salt1 = crypto_utils.hash_password_SHA256(pw)
    h2, salt2 = crypto_utils.hash_password_SHA256(pw)
    assert salt1 != salt2
    assert h1 != h2
    print_footer("test_hash_password_different_salts")

def test_verify_password_failure():
    print_header("test_verify_password_failure")
    hashed, salt = crypto_utils.hash_password_SHA256("RightOne")
    assert not crypto_utils.verify_password_256("WrongOne", hashed, salt)
    print_footer("test_verify_password_failure")

def test_argon2_password_hash_and_verify_success():
    print_header("test_argon2_password_hash_and_verify_success")
    pw = "ArgonTest123!"
    hashed, salt = crypto_utils.hash_password_argon2(pw)
    assert crypto_utils.verify_password_argon2(pw, hashed, salt)
    print_footer("test_argon2_password_hash_and_verify_success")

def test_argon2_password_verify_failure():
    print_header("test_argon2_password_verify_failure")
    hashed, salt = crypto_utils.hash_password_argon2("CorrectPassword")
    assert not crypto_utils.verify_password_argon2("WrongPassword", hashed, salt)
    print_footer("test_argon2_password_verify_failure")

def test_generate_session_id_format_and_uniqueness():
    print_header("test_generate_session_id_format_and_uniqueness")
    sid1 = crypto_utils.generate_session_id()
    sid2 = crypto_utils.generate_session_id()
    assert re.fullmatch(r"[0-9a-f]{64}", sid1)
    assert re.fullmatch(r"[0-9a-f]{64}", sid2)
    assert sid1 != sid2
    print_footer("test_generate_session_id_format_and_uniqueness")

def test_derive_key_from_password():
    print_header("test_derive_key_from_password")
    password = "DeriveThis!"
    salt = "saltvalue"
    key1 = crypto_utils.derive_key_from_password(password, salt)
    key2 = crypto_utils.derive_key_from_password(password, salt)
    assert key1 == key2
    print_footer("test_derive_key_from_password")

def test_encrypt_decrypt_data():
    print_header("test_encrypt_decrypt_data")
    data = b"Confidential data here."
    fake_hash = "randomkey123456789"
    encrypted = crypto_utils.encrypt_data(data, fake_hash)
    decrypted = crypto_utils.decrypt_data(encrypted, fake_hash)
    assert decrypted == data
    print_footer("test_encrypt_decrypt_data")

def test_compute_hash():
    print_header("test_compute_hash")
    data = b"TestDataToHash"
    h = crypto_utils.compute_hash(data)
    assert re.fullmatch(r"[0-9a-f]{64}", h)
    print_footer("test_compute_hash")
