import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

class DecryptionError(Exception):
    """Custom exception for decryption failures to avoid leaking crypto internals."""
    pass

def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte key using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(passphrase.encode('utf-8'))

def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    """
    Encrypt plaintext using AES-256-GCM.
    Returns: salt (16 bytes) + nonce (12 bytes) + ciphertext_with_tag
    """
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext_with_tag

def decrypt(blob: bytes, passphrase: str) -> bytes:
    """
    Decrypt a blob (salt + nonce + ciphertext_with_tag) using AES-256-GCM.
    Raises DecryptionError on failure.
    """
    # Minimum length: 16 (salt) + 12 (nonce) + 16 (tag) = 44 bytes
    if len(blob) < 44:
        raise DecryptionError("Data blob is too short to be valid ciphertext.")
    
    salt = blob[:16]
    nonce = blob[16:28]
    ciphertext_with_tag = blob[28:]
    
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    
    try:
        return aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    except InvalidTag:
        raise DecryptionError("Invalid passphrase or tampered ciphertext")
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {str(e)}")
