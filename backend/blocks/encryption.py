"""
Encryption utilities for sensitive data like mnemonics
"""
import base64
import os
from cryptography.fernet import Fernet
from decouple import config
import logging

logger = logging.getLogger(__name__)

class MnemonicEncryption:
    """
    Handles encryption and decryption of mnemonic phrases
    """

    def __init__(self):
        self._fernet = None
        self._initialize_cipher()

    def _initialize_cipher(self):
        """Initialize the Fernet cipher with the encryption key"""
        try:
            # Get encryption key from environment
            encryption_key = config('MNEMONIC_ENCRYPTION_KEY', default=None)

            if not encryption_key:
                # Generate a new key if none exists (for development only)
                logger.warning("No MNEMONIC_ENCRYPTION_KEY found in environment. Generating temporary key.")
                encryption_key = Fernet.generate_key().decode()
                logger.warning(f"Generated temporary key: {encryption_key}")
                logger.warning("Please add this key to your .env file as MNEMONIC_ENCRYPTION_KEY")

            # Convert string key to bytes if necessary
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()

            self._fernet = Fernet(encryption_key)

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Failed to initialize mnemonic encryption. Please check your MNEMONIC_ENCRYPTION_KEY.")

    def encrypt(self, mnemonic: str) -> str:
        """
        Encrypt a mnemonic phrase

        Args:
            mnemonic: The plaintext mnemonic phrase

        Returns:
            Base64 encoded encrypted mnemonic
        """
        try:
            if not mnemonic:
                raise ValueError("Mnemonic cannot be empty")

            # Encrypt the mnemonic
            encrypted_bytes = self._fernet.encrypt(mnemonic.encode())

            # Return base64 encoded string for database storage
            return base64.b64encode(encrypted_bytes).decode()

        except Exception as e:
            logger.error(f"Failed to encrypt mnemonic: {e}")
            raise ValueError("Failed to encrypt mnemonic")

    def decrypt(self, encrypted_mnemonic: str) -> str:
        """
        Decrypt an encrypted mnemonic phrase

        Args:
            encrypted_mnemonic: Base64 encoded encrypted mnemonic

        Returns:
            The plaintext mnemonic phrase
        """
        try:
            if not encrypted_mnemonic:
                raise ValueError("Encrypted mnemonic cannot be empty")

            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_mnemonic.encode())

            # Decrypt the mnemonic
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)

            return decrypted_bytes.decode()

        except Exception as e:
            logger.error(f"Failed to decrypt mnemonic: {e}")
            raise ValueError("Failed to decrypt mnemonic")

    def is_encrypted(self, text: str) -> bool:
        """
        Check if a text appears to be encrypted by trying to decrypt it

        Args:
            text: The text to check

        Returns:
            True if text appears to be encrypted
        """
        try:
            if not text:
                return False

            # Check if it's a valid base64 string first
            if len(text) < 10:
                return False

            # Try to decode as base64
            base64.b64decode(text.encode())

            # If it contains spaces or only lowercase letters, it's likely plaintext
            if ' ' in text and text.replace(' ', '').isalpha():
                return False

            # Check if it looks like a long base64 string (encrypted data is usually long)
            if len(text) > 100 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in text):
                return True

            return False

        except Exception:
            return False

# Global instance
mnemonic_encryptor = MnemonicEncryption()

def encrypt_mnemonic(mnemonic: str) -> str:
    """Convenience function to encrypt a mnemonic"""
    return mnemonic_encryptor.encrypt(mnemonic)

def decrypt_mnemonic(encrypted_mnemonic: str) -> str:
    """Convenience function to decrypt a mnemonic"""
    return mnemonic_encryptor.decrypt(encrypted_mnemonic)

def is_encrypted_mnemonic(text: str) -> bool:
    """Convenience function to check if text is encrypted"""
    return mnemonic_encryptor.is_encrypted(text)