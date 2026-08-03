import pytest
from steganography.crypto import encrypt, decrypt, DecryptionError

def test_encrypt_decrypt():
    passphrase = "super_secret_password!"
    plaintext = b"This is a very secret message that needs to be encrypted."
    
    ciphertext_blob = encrypt(plaintext, passphrase)
    
    # Check that it's encrypted and has the right minimum length (16+12+16)
    assert ciphertext_blob != plaintext
    assert len(ciphertext_blob) >= 44
    
    decrypted = decrypt(ciphertext_blob, passphrase)
    assert decrypted == plaintext

def test_decrypt_wrong_passphrase():
    passphrase = "super_secret"
    plaintext = b"hello world 123"
    
    ciphertext = encrypt(plaintext, passphrase)
    
    with pytest.raises(DecryptionError, match="Invalid passphrase or tampered ciphertext"):
        decrypt(ciphertext, "wrong_passphrase")

def test_decrypt_tampered_ciphertext():
    passphrase = "super_secret"
    plaintext = b"hello world 123"
    
    ciphertext = bytearray(encrypt(plaintext, passphrase))
    # Flip a bit in the authentication tag / ciphertext
    ciphertext[-1] ^= 1
    
    with pytest.raises(DecryptionError, match="Invalid passphrase or tampered ciphertext"):
        decrypt(bytes(ciphertext), passphrase)

def test_short_ciphertext():
    with pytest.raises(DecryptionError, match="too short"):
        decrypt(b"short", "passphrase")
