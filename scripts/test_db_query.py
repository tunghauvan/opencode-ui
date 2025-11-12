import sys
sys.path.insert(0, '.')
from core.database import get_db
from core.models import Session as SessionModel

# Test database connection and query
db = next(get_db())
try:
    print("Testing database query...")
    sessions = db.query(SessionModel).filter(SessionModel.user_id == "188960770").all()
    print(f"Found {len(sessions)} sessions")
    for session in sessions:
        print(f"Session: {session.session_id}, name: {session.name}")
finally:
    db.close()