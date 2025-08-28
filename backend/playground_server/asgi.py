import asyncio
import json
import threading
from pathlib import Path

from django.core.asgi import get_asgi_application
from django.db.models import Max

from blocks.models import Block
from blocks.broadcast import broadcaster


django_asgi_app = get_asgi_application()

_ws_guest_counter = 0
_ws_guest_lock = threading.Lock()


def current_status():
    height = Block.objects.aggregate(m=Max('height'))['m'] or 0
    # Keep logic in sync with views
    DIFFICULTY_BASE = 10000
    step = height // 10
    difficulty = max(1, DIFFICULTY_BASE // (2 ** step))
    # reward per views
    next_height = height + 1
    step_r = (next_height - 1) // 20
    reward = max(1, 100 // (2 ** step_r))
    return { 'height': height, 'difficulty': difficulty, 'reward': reward }


async def ws_stream_app(scope, receive, send):
    global _ws_guest_counter
    assert scope['type'] == 'websocket'
    path = scope.get('path', '')
    if not path.startswith('/ws/stream'):
        # Reject other paths
        await send({'type': 'websocket.close'})
        return

    # Accept connection
    await send({'type': 'websocket.accept', 'headers': [(b'cache-control', b'no-cache')]})

    with _ws_guest_lock:
        _ws_guest_counter += 1
        nickname = f"guest {_ws_guest_counter}"

    # Subscribe to broadcaster
    q = broadcaster.add_listener({ 'nickname': nickname })
    # Notify peers
    broadcaster.publish({ 'type': 'peers', 'peers': broadcaster.peers() })

    async def send_json(obj: dict):
        await send({'type': 'websocket.send', 'text': json.dumps(obj)})

    try:
        # Initial snapshot
        blocks_snapshot = list(Block.objects.order_by('-height').values('height','nonce','miner','difficulty','reward','timestamp')[:200])
        await send_json({
            'type': 'snapshot',
            'blocks': blocks_snapshot,
            'status': current_status(),
            'me': { 'nickname': nickname },
            'peers': broadcaster.peers(),
        })

        last_hb = asyncio.get_event_loop().time()
        while True:
            # Handle client messages (we don't expect any, just keep alive)
            try:
                msg = await asyncio.wait_for(receive(), timeout=0.1)
                if msg['type'] == 'websocket.disconnect':
                    break
            except asyncio.TimeoutError:
                pass

            # Relay broadcast messages
            try:
                data = q.get_nowait()
                await send({'type': 'websocket.send', 'text': data})
            except Exception:
                pass

            # Heartbeat every 10s
            now = asyncio.get_event_loop().time()
            if now - last_hb > 10:
                await send_json({ 'type': 'status', 'status': current_status() })
                last_hb = now
    finally:
        broadcaster.remove_listener(q)
        broadcaster.publish({ 'type': 'peers', 'peers': broadcaster.peers() })
        await send({'type': 'websocket.close'})


async def application(scope, receive, send):
    if scope['type'] == 'websocket':
        return await ws_stream_app(scope, receive, send)
    # Fallback to Django for HTTP
    return await django_asgi_app(scope, receive, send)

