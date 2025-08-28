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
