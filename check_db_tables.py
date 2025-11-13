import sqlite3

conn = sqlite3.connect('data/db.sqlite3')
c = conn.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print(f"Tables in database: {tables}")

# Get schema for each table
for table in tables:
    table_name = table[0]
    c.execute(f"PRAGMA table_info({table_name})")
    cols = c.fetchall()
    print(f"\n{table_name} columns: {cols}")

c.close()
