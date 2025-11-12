import sys
sys.path.insert(0, '.')
from core.database import engine, init_db
from core.models import User
from sqlalchemy.orm import sessionmaker

# Initialize database
init_db()

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check existing users
    users = db.query(User).all()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  ID: {user.id}, Login: {user.github_login}, GitHub ID: {user.github_id}")

    # Check sessions for first user
    if users:
        from core.models import Session
        sessions = db.query(Session).filter(Session.user_id == users[0].id).all()
        print(f"User {users[0].id} has {len(sessions)} sessions")

finally:
    db.close()