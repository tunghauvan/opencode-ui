import sqlite3
conn = sqlite3.connect('data/db.sqlite3')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(sessions)')
columns = cursor.fetchall()
print('Sessions table columns:')
for col in columns:
    print(f'  {col[1]}: {col[2]} (nullable: {col[3]})')
conn.close()