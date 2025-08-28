import json
import threading
import queue


class SSEBroadcaster:
    def __init__(self):
        self._lock = threading.Lock()
        # List of tuples: (queue, meta)
        # meta is a dict, e.g., {"nickname": "guest 1"}
        self._listeners = []

    def add_listener(self, meta=None):
        q = queue.Queue(maxsize=100)
        with self._lock:
            self._listeners.append((q, meta or {}))
        return q

    def remove_listener(self, q):
        with self._lock:
            for i, (qq, _m) in enumerate(list(self._listeners)):
                if qq is q:
                    self._listeners.pop(i)
                    break

    def publish(self, payload: dict):
        data = json.dumps(payload)
        with self._lock:
            for (q, _m) in list(self._listeners):
                try:
                    q.put_nowait(data)
                except queue.Full:
                    # drop slow listener
                    try:
                        self._listeners.remove((q, _m))
                    except ValueError:
                        pass

    def peers(self):
        with self._lock:
            return [ (m or {}).get('nickname') for (_q, m) in self._listeners if (m or {}).get('nickname') ]


broadcaster = SSEBroadcaster()
