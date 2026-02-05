import pytest

from app.utils.encryption import encrypt_value, decrypt_value, get_encryption_key


class TestEncryptionKey:
    def test_get_encryption_key_returns_bytes(self):
        """Encryption key should be bytes."""
        key = get_encryption_key()
        assert isinstance(key, bytes)

    def test_get_encryption_key_is_consistent(self):
        """Same JWT secret should produce same key."""
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        assert key1 == key2

    def test_get_encryption_key_valid_length(self):
        """Key should be 44 bytes (base64 encoded 32 bytes)."""
        key = get_encryption_key()
        assert len(key) == 44  # Fernet key is 32 bytes base64 encoded


class TestEncryptDecrypt:
    def test_encrypt_returns_different_value(self):
        """Encrypted value should be different from plaintext."""
        plaintext = "my-secret-api-key"
        encrypted = encrypt_value(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0

    def test_decrypt_returns_original_value(self):
        """Decrypted value should match original plaintext."""
        plaintext = "my-secret-api-key"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip(self):
        """Encryption and decryption should be reversible."""
        test_values = [
            "sk-abc123xyz",
            "very-long-api-key-with-special-chars-!@#$%^&*()",
            "",  # empty string
            "a",  # single character
        ]
        for plaintext in test_values:
            encrypted = encrypt_value(plaintext)
            decrypted = decrypt_value(encrypted)
            assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext_each_time(self):
        """Same plaintext should produce different ciphertext (due to IV)."""
        plaintext = "my-api-key"
        encrypted1 = encrypt_value(plaintext)
        encrypted2 = encrypt_value(plaintext)
        # Fernet uses random IV, so ciphertext should differ
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_ciphertext_raises(self):
        """Invalid ciphertext should raise an exception."""
        with pytest.raises(Exception):
            decrypt_value("not-a-valid-encrypted-value")

    def test_decrypt_tampered_ciphertext_raises(self):
        """Tampered ciphertext should raise an exception."""
        plaintext = "my-api-key"
        encrypted = encrypt_value(plaintext)
        tampered = encrypted[:-5] + "xxxxx"
        with pytest.raises(Exception):
            decrypt_value(tampered)
