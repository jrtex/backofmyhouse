import base64
import hashlib
from cryptography.fernet import Fernet

from app.config import get_settings


def get_encryption_key() -> bytes:
    """Derive a Fernet-compatible key from JWT_SECRET.

    Uses SHA-256 to hash the JWT secret, producing a 32-byte key,
    then base64 encodes it to create a valid Fernet key.
    """
    settings = get_settings()
    key_bytes = hashlib.sha256(settings.jwt_secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    fernet = Fernet(get_encryption_key())
    encrypted = fernet.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt an encrypted string value."""
    fernet = Fernet(get_encryption_key())
    decrypted = fernet.decrypt(ciphertext.encode())
    return decrypted.decode()
