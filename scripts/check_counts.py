import sys, os, django
sys.path.insert(0, 'backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DATABASE_ENGINE'] = 'postgresql'
django.setup()

from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cursor.fetchall()]

table_counts = []
for t in tables:
    try:
        cursor.execute(f'SELECT count(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        table_counts.append((count, t))
    except Exception as e:
        pass

for c, t in sorted(table_counts, reverse=True):
    print(f"{c:6d} : {t}")
