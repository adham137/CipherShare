# from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
# from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.backends import default_backend
import secrets
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


DEFAULT_KEY = hashlib.sha256(b'CipherShareSymmetricKey').digest()

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16).encode('utf-8')  # Generate a random salt
    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    return hashed_password, salt.decode('utf-8')

def verify_password(password, hashed_password, salt):
    return hashlib.sha256(salt.encode('utf-8') + password.encode('utf-8')).hexdigest() == hashed_password

def generate_session_id():
    return secrets.token_hex(32)

# def hash_password(password, salt=None):
#     if salt is None:
#         salt = secrets.token_bytes(16)
#     argon2 = Argon2id(
#         salt=salt,
#         time_cost=16,
#         memory_cost=65536,
#         parallelism=2,
#         hash_len=32,
#         backend=default_backend()
#     )
#     hashed_password = argon2.hash(password.encode('utf-8'))
#     return hashed_password, salt

# def verify_password(password, hashed_password, salt):
#     argon2 = Argon2id(
#         salt=salt,
#         time_cost=16,
#         memory_cost=65536,
#         parallelism=2,
#         hash_len=32,
#         backend=default_backend()
#     )
#     try:
#         argon2.verify_hash(hashed_password, password.encode('utf-8'))
#         return True
#     except:
#         return False

# def derive_key_from_password(password, salt):
#     kdf = PBKDF2HMAC(
#         algorithm=hashes.SHA256(),
#         length=32,
#         salt=salt,
#         iterations=100000,
#         backend=default_backend()
#     )
#     key = kdf.derive(password.encode('utf-8'))
#     return key

def encrypt_data(data: bytes, key: bytes = DEFAULT_KEY) -> bytes:
    """
    AES-CBC encrypt `data`, return IV||ciphertext.
    """
    iv = secrets.token_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(data, AES.block_size))
    return iv + ct

def decrypt_data(iv_and_ct: bytes, key: bytes = DEFAULT_KEY) -> bytes:
    """
    Split out IV, AES-CBC decrypt ciphertext, remove PKCS7 padding.
    """
    iv = iv_and_ct[:AES.block_size]
    ct = iv_and_ct[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt

def compute_hash(data: bytes) -> str:
    """
    SHA-256 over in-memory bytes.
    """
    return hashlib.sha256(data).hexdigest()

def compute_file_hash(filepath: str) -> str:
    """
    SHA-256 over a file on disk (streaming).
    """
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
