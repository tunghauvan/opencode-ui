import sqlite3
conn = sqlite3.connect('data/db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'Tables: {[t[0] for t in tables]}')
cursor.execute("SELECT id, github_login FROM users WHERE id = '188960770'")
user = cursor.fetchone()
print(f'User found: {user}')
if user:
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE user_id = '188960770'")
    sessions_count = cursor.fetchone()[0]
    print(f'Sessions count: {sessions_count}')
conn.close()