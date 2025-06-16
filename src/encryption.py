from cryptography.fernet import Fernet

class EncryptionHandler:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypts the given data (expects bytes)."""
        return self.cipher.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypts the given token (returns bytes)."""
        return self.cipher.decrypt(token)

    def encrypt_str(self, text: str) -> bytes:
        """Encrypts a string and returns encrypted bytes."""
        return self.encrypt(text.encode('utf-8'))

    def decrypt_str(self, token: bytes) -> str:
        """Decrypts bytes and returns the original string."""
        return self.decrypt(token).decode('utf-8')

def generate_key() -> bytes:
    """Generates a new encryption key."""
    return Fernet.generate_key()