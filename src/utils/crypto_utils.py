# from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
# from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.backends import default_backend
# import secrets


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
