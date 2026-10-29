import sqlite3
import os
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')


print("Checking databases and glossaries...")

# 1. Check backend/data/admin.db
db_path = 'backend/data/admin.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables in admin.db:")
    for t in tables:
        t_name = t[0]
        cur.execute(f"SELECT COUNT(*) FROM `{t_name}`;")
        cnt = cur.fetchone()[0]
        print(f"  - {t_name}: {cnt} rows")
        if any(k in t_name.lower() for k in ['dict', 'gloss', 'word', 'term', 'vocab', 'trans']):
            # Print sample
            cur.execute(f"SELECT * FROM `{t_name}` LIMIT 5;")
            samples = cur.fetchall()
            cur.execute(f"PRAGMA table_info(`{t_name}`);")
            cols = [c[1] for c in cur.fetchall()]
            print(f"    Columns: {cols}")
            print(f"    First {len(samples)} rows: {samples}")
    conn.close()
else:
    print("backend/data/admin.db does not exist!")

# Check backup db if exists
backup_db = 'backend/backups/pre_tm_database_20261009_003649/admin.db'
if os.path.exists(backup_db):
    print("\n--- Inspecting Backup DB: " + backup_db + " ---")
    b_conn = sqlite3.connect(backup_db)
    b_cur = b_conn.cursor()
    b_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for t in b_cur.fetchall():
        t_name = t[0]
        b_cur.execute(f"SELECT COUNT(*) FROM `{t_name}`;")
        cnt = b_cur.fetchone()[0]
        print(f"  Backup table {t_name}: {cnt} rows")
        if 'dict' in t_name.lower() or 'entry' in t_name.lower() or 'trans' in t_name.lower() or 'memory' in t_name.lower():
            b_cur.execute(f"SELECT * FROM `{t_name}` LIMIT 5;")
            print("    samples:", b_cur.fetchall())
    b_conn.close()

# Also check all rows in translation_memory_entries in current admin.db
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("\n--- All rows in current admin.db translation_memory_entries ---")
    cur.execute("SELECT * FROM translation_memory_entries;")
    rows = cur.fetchall()
    print(f"Total rows: {len(rows)}")
    for r in rows:
        print(" ", r)
    conn.close()

