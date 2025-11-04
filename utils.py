# utils.py
import hashlib, os, binascii

def hash_password(password: str):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return binascii.hexlify(dk).decode(), binascii.hexlify(salt).decode()

def is_int(s):
    try:
        int(s)
        return True
    except:
        return False

def is_float(s):
    try:
        float(s)
        return True
    except:
        return False
