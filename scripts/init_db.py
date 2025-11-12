import sys
sys.path.append('.')
from app.core.database import init_db
print('Initializing database...')
init_db()
print('Database initialized successfully!')