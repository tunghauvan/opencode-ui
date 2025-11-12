import sys
sys.path.insert(0, '.')
from core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, github_login FROM users LIMIT 5'))
    users = [dict(row) for row in result]
    print('Users:', users)