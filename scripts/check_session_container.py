import sqlite3

conn = sqlite3.connect('data/db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT session_id, user_id, container_id, container_status, name FROM sessions WHERE session_id = ?', ('ef345497',))
session = cursor.fetchone()

if session:
    print(f'Session ID: {session[0]}')
    print(f'User ID: {session[1]}')
    if session[2]:
        print(f'Container ID: {session[2][:12]}...')
    else:
        print('Container ID: None')
    print(f'Container Status: {session[3]}')
    print(f'Name: {session[4]}')
else:
    print('Session not found')

conn.close()
