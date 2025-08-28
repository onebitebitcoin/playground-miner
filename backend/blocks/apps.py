from django.apps import AppConfig
from django.db import connection


def _setup_sqlite_pragmas():
    try:
        if connection.vendor == 'sqlite':
            with connection.cursor() as c:
                c.execute('PRAGMA journal_mode=WAL;')
                c.execute('PRAGMA synchronous=NORMAL;')
                c.execute('PRAGMA temp_store=MEMORY;')
    except Exception:
        # Best-effort; ignore if not available
        pass


class BlocksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blocks'
    
    def ready(self):
        _setup_sqlite_pragmas()
