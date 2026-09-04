import sqlite3
import os

def dump_sqlite_to_sql(db_path, sql_path):
    os.makedirs(os.path.dirname(sql_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    with open(sql_path, 'w', encoding='utf-8') as f:
        for line in con.iterdump():
            f.write(f'{line}\n')
    con.close()
    print(f"Exported {db_path} to {sql_path}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(base_dir, 'backend', 'db.sqlite3')
    sql_file = os.path.join(base_dir, 'database', 'db.sql')
    dump_sqlite_to_sql(db_file, sql_file)
