from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

DEFAULT_KEY = hashlib.sha256(b'CipherShareSymmetricKey').digest()

def hash_password_SHA256(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16).encode('utf-8')  # Generate a random salt
    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    return hashed_password, salt.decode('utf-8')

def verify_password_256(password, hashed_password, salt):
    return hashlib.sha256(salt.encode('utf-8') + password.encode('utf-8')).hexdigest() == hashed_password

def generate_session_id():
    return secrets.token_hex(32)

def hash_password_argon2(password, salt=None):
    
    if salt is None:
        salt = secrets.token_hex(16).encode('utf-8')
    # print(f"Function (hash_password_argon2):\nis (salt) bytes ({isinstance(salt, (bytes, bytearray))})\nis (passwords) bytes ({isinstance(password, (bytes, bytearray))})\n")
    argon2 = Argon2id(
        salt=salt,
        length=32,
        iterations=16,
        memory_cost=65536,
        lanes=2,          
    )

    key = argon2.derive(password.encode('utf-8')).hex()
    # # print(f"Function (hash_password_argon2):\nis (key) bytes ({isinstance(key, (bytes, bytearray))})\n")
    return key, salt.decode('utf-8')

def verify_password_argon2(password, hashed_password_hex, salt):
    # print(f"Function (verify_password_argon2):\nis (salt) bytes ({isinstance(salt, (bytes, bytearray))})\nis (password) bytes ({isinstance(password, (bytes, bytearray))})\nis (hashed_password_hex) bytes ({isinstance(hashed_password_hex, (bytes, bytearray))})\n")
    argon2 = Argon2id(
        salt=salt.encode('utf-8'),
        length=32,
        iterations=16,
        memory_cost=65536,
        lanes=2,          
    )
    try:
        hashed_password_bytes = bytes.fromhex(hashed_password_hex)
        argon2.verify(password.encode("utf-8"), hashed_password_bytes) #argon2.verify_hash(hashed_password, password.encode('utf-8'))
        return True
    except Exception as e:
        # print(f"Verification Exception: {e}")
        return False

def derive_key_from_password(password, salt):
    # print(f"Function (derive_key_from_password):\nis (salt) bytes ({isinstance(salt, (bytes, bytearray))})\nis (password) bytes ({isinstance(password, (bytes, bytearray))})\n")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode('utf-8'),
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8')).hex()
    # print(f"Function (derive_key_from_password):\nis (key) bytes ({isinstance(key, (bytes, bytearray))})\n")
    return key

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
    print("File decrypted successfully")
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
