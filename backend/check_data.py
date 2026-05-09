"""Quick data integrity check script."""
import sqlite3
import os

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sqlite")

for db in ["production", "equipment", "energy", "sessions"]:
    path = os.path.join(data_dir, f"{db}.db")
    if not os.path.exists(path):
        print(f"{db}.db: NOT FOUND at {path}")
        continue
    conn = sqlite3.connect(path)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"\n{db}.db tables:")
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {count} rows")
    conn.close()
