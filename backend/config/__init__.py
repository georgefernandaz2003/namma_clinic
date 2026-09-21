# Config package
from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def configure_sqlite_connection(sender, connection, **kwargs):
    """
    Optimizes SQLite for high-performance concurrent healthcare operations:
    - WAL mode for concurrent reads while writes occur
    - NORMAL synchronous mode for faster disk I/O while preserving durability
    - 30-second busy timeout to eliminate 'database is locked' errors
    - 64MB cache memory for instant query responses
    - Memory temp store and foreign key validation
    """
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = ON;')
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA busy_timeout = 30000;')
            cursor.execute('PRAGMA cache_size = -64000;')
            cursor.execute('PRAGMA temp_store = MEMORY;')
