from django.db import models


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
    mnemonic = models.TextField()
    is_assigned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.mnemonic[:20]}..."

    def as_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'mnemonic': self.mnemonic,
            'is_assigned': self.is_assigned,
            'created_at': self.created_at.isoformat(),
        }
