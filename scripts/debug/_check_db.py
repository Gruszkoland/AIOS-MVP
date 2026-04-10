from arbitrage.database import init_db, get_conn
init_db()
c = get_conn()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Tables: {len(tables)}")
for t in tables:
    cnt = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  {t}: {cnt} rows")
c.close()
