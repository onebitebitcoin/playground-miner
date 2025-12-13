import json
import queue
import threading
import time


class FinanceStreamManager:
    """
    Thread-safe pub/sub manager for per-request finance analysis channels.
    Each channel is identified by a caller-provided string (e.g. UUID) so
    that concurrent browser sessions do not interfere with one another.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # channel_id -> {'queue': queue.Queue, 'listeners': int, 'created_at': float}
        self._channels = {}

    def prepare_channel(self, channel_id: str):
        """Ensure a channel exists even if a listener hasn't subscribed yet."""
        if not channel_id:
            return
        with self._lock:
            if channel_id not in self._channels:
                self._channels[channel_id] = {
                    'queue': queue.Queue(maxsize=500),
                    'listeners': 0,
                    'created_at': time.time()
                }

    def subscribe(self, channel_id: str):
        if not channel_id:
            raise ValueError("channel_id is required")
        with self._lock:
            channel = self._channels.get(channel_id)
            if not channel:
                channel = {
                    'queue': queue.Queue(maxsize=500),
                    'listeners': 0,
                    'created_at': time.time()
                }
                self._channels[channel_id] = channel
            channel['listeners'] += 1
            return channel['queue']

    def unsubscribe(self, channel_id: str):
        if not channel_id:
            return
        with self._lock:
            channel = self._channels.get(channel_id)
            if not channel:
                return
            channel['listeners'] -= 1
            if channel['listeners'] <= 0:
                self._channels.pop(channel_id, None)

    def publish(self, channel_id: str, payload: dict):
        if not channel_id or payload is None:
            return False
        with self._lock:
            channel = self._channels.get(channel_id)
            if not channel:
                return False
            q = channel['queue']
        data = json.dumps(payload, ensure_ascii=False)
        try:
            q.put_nowait(data)
            return True
        except queue.Full:
            # Drop the channel if the listener is too slow to prevent blocking producers
            with self._lock:
                if self._channels.get(channel_id) is channel:
                    self._channels.pop(channel_id, None)
            return False


finance_stream_manager = FinanceStreamManager()
