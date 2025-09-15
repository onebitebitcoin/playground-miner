from django.db import models
from .encryption import encrypt_mnemonic, decrypt_mnemonic, is_encrypted_mnemonic
import logging

logger = logging.getLogger(__name__)


class Block(models.Model):
    height = models.PositiveIntegerField(unique=True)
    nonce = models.PositiveIntegerField()
    miner = models.CharField(max_length=64)
    difficulty = models.PositiveIntegerField()
    reward = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-height']

    def as_dict(self):
        return {
            'height': self.height,
            'nonce': self.nonce,
            'miner': self.miner,
            'difficulty': self.difficulty,
            'reward': self.reward,
            'timestamp': self.timestamp.isoformat(),
        }


class Nickname(models.Model):
    name = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Mnemonic(models.Model):
    username = models.CharField(max_length=64)
    mnemonic = models.TextField()  # Stores encrypted mnemonic
    is_assigned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Override save to encrypt mnemonic before storing"""
        if self.mnemonic and not is_encrypted_mnemonic(self.mnemonic):
            try:
                self.mnemonic = encrypt_mnemonic(self.mnemonic)
                logger.info(f"Encrypted mnemonic for user: {self.username}")
            except Exception as e:
                logger.error(f"Failed to encrypt mnemonic for user {self.username}: {e}")
                raise ValueError("Failed to encrypt mnemonic")

        super().save(*args, **kwargs)

    def get_mnemonic(self):
        """Get the decrypted mnemonic"""
        try:
            if self.mnemonic and is_encrypted_mnemonic(self.mnemonic):
                return decrypt_mnemonic(self.mnemonic)
            return self.mnemonic  # Return as-is if not encrypted (for migration compatibility)
        except Exception as e:
            logger.error(f"Failed to decrypt mnemonic for user {self.username}: {e}")
            raise ValueError("Failed to decrypt mnemonic")

    def set_mnemonic(self, plaintext_mnemonic):
        """Set a new mnemonic (will be encrypted on save)"""
        self.mnemonic = plaintext_mnemonic

    def __str__(self):
        try:
            mnemonic_preview = self.get_mnemonic()[:20] + "..." if len(self.get_mnemonic()) > 20 else self.get_mnemonic()
            return f"{self.username} - {mnemonic_preview}"
        except:
            return f"{self.username} - [encrypted]"

    def as_dict(self):
        """Return dictionary representation with decrypted mnemonic"""
        try:
            decrypted_mnemonic = self.get_mnemonic()
        except Exception as e:
            logger.error(f"Failed to decrypt mnemonic in as_dict for user {self.username}: {e}")
            # For admin purposes, show that it's encrypted
            decrypted_mnemonic = "[ENCRYPTION_ERROR]"

        return {
            'id': self.id,
            'username': self.username,
            'mnemonic': decrypted_mnemonic,
            'is_assigned': self.is_assigned,
            'created_at': self.created_at.isoformat(),
        }
