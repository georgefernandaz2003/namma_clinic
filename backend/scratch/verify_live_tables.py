import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%' ORDER BY name")
tables = cursor.fetchall()

print(f"Total Active Application Tables in SQLite: {len(tables)}\n")
for t in tables:
    tbl_name = t[0]
    cursor.execute(f"SELECT count(*) FROM `{tbl_name}`")
    count = cursor.fetchone()[0]
    print(f"  [EXISTS] Table `{tbl_name}` -> {count} records")
