#!/usr/bin/env python3
"""
Stop All Sessions Script
Stops all running OpenCode sessions and their containers
"""

import sqlite3
import requests
import subprocess
import sys
import time
from typing import List, Dict, Any
import argparse

# Configuration
DB_PATH = 'data/db.sqlite3'
BACKEND_URL = 'http://localhost:8000'
AGENT_CONTROLLER_URL = 'http://localhost:8001'

class SessionStopper:
    """Handles stopping all sessions and their containers"""

    def __init__(self, db_path: str = DB_PATH, use_api: bool = True):
        self.db_path = db_path
        self.use_api = use_api
        self.stopped_sessions = []
        self.errors = []

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, session_id, user_id, name, status, is_active,
                       container_id, container_status, created_at, updated_at
                FROM sessions
                ORDER BY created_at DESC
            """)

            columns = [desc[0] for desc in cursor.description]
            sessions = []

            for row in cursor.fetchall():
                session = dict(zip(columns, row))
                sessions.append(session)

            conn.close()
            return sessions

        except Exception as e:
            print(f"❌ Error reading database: {e}")
            return []

    def stop_container_via_docker(self, container_id: str, session_id: str) -> bool:
        """Stop container directly using Docker commands"""
        try:
            print(f"  🐳 Stopping container {container_id} for session {session_id}...")

            # First try graceful stop
            result = subprocess.run(
                ['docker', 'stop', container_id],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"  ✅ Container {container_id} stopped gracefully")
            else:
                print(f"  ⚠️  Graceful stop failed, trying force stop...")
                # Try force stop
                result = subprocess.run(
                    ['docker', 'kill', container_id],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    print(f"  ✅ Container {container_id} force stopped")
                else:
                    print(f"  ❌ Failed to stop container {container_id}: {result.stderr}")
                    return False

            # Remove the container
            result = subprocess.run(
                ['docker', 'rm', container_id],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"  ✅ Container {container_id} removed")
            else:
                print(f"  ⚠️  Failed to remove container {container_id}: {result.stderr}")

            return True

        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout stopping container {container_id}")
            return False
        except Exception as e:
            print(f"  ❌ Error stopping container {container_id}: {e}")
            return False

    def stop_session_via_api(self, session: Dict[str, Any]) -> bool:
        """Stop session via backend API"""
        session_id = session['session_id']
        user_id = session['user_id']

        try:
            print(f"  🌐 Stopping session {session_id} via API...")

            # Create a test cookie for authentication (this assumes the user exists)
            cookies = {'user_id': user_id}

            response = requests.post(
                f"{BACKEND_URL}/api/backend/sessions/{session_id}/container/stop",
                cookies=cookies,
                timeout=30
            )

            if response.status_code == 200:
                print(f"  ✅ Session {session_id} stopped via API")
                return True
            else:
                print(f"  ❌ API call failed for session {session_id}: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error stopping session {session_id}: {e}")
            return False

    def update_session_in_db(self, session_id: str) -> bool:
        """Update session status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE sessions
                SET container_id = NULL, container_status = 'stopped', updated_at = datetime('now')
                WHERE session_id = ?
            """, (session_id,))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"  ❌ Error updating database for session {session_id}: {e}")
            return False

    def stop_session(self, session: Dict[str, Any]) -> bool:
        """Stop a single session"""
        session_id = session['session_id']
        container_id = session.get('container_id')
        container_status = session.get('container_status')

        print(f"\n🛑 Stopping session: {session_id}")
        print(f"   Container: {container_id or 'None'}")
        print(f"   Status: {container_status or 'Unknown'}")

        success = False

        # Only stop if there's a container
        if container_id and container_status in ['running', 'created']:
            if self.use_api:
                # Try API first
                success = self.stop_session_via_api(session)
                if not success:
                    print(f"  🔄 API failed, trying direct Docker stop...")
                    success = self.stop_container_via_docker(container_id, session_id)
            else:
                # Direct Docker stop
                success = self.stop_container_via_docker(container_id, session_id)
        else:
            print(f"  ℹ️  No running container for session {session_id}")
            success = True  # Not an error if no container

        # Update database regardless
        if success:
            self.update_session_in_db(session_id)
            self.stopped_sessions.append(session_id)
            return True
        else:
            self.errors.append(f"Failed to stop session {session_id}")
            return False

    def stop_all_sessions(self) -> Dict[str, Any]:
        """Stop all sessions"""
        print("🔍 Finding all sessions...")

        sessions = self.get_all_sessions()

        if not sessions:
            print("ℹ️  No sessions found in database")
        else:
            print(f"📋 Found {len(sessions)} sessions")

            # Count sessions with containers
            sessions_with_containers = [s for s in sessions if s.get('container_id')]
            print(f"🐳 {len(sessions_with_containers)} sessions have containers")

        # Stop orphaned containers
        print("\n🔍 Finding orphaned containers...")
        stopped_orphaned = self.stop_orphaned_containers()
        
        stopped_count = 0

        # Stop tracked sessions
        for session in sessions:
            if self.stop_session(session):
                stopped_count += 1

        print(f"\n{'='*60}")
        print("📊 SUMMARY")
        print(f"{'='*60}")
        print(f"Database sessions: {len(sessions)}")
        print(f"Sessions with containers: {len([s for s in sessions if s.get('container_id')])}")
        print(f"Orphaned containers stopped: {len(stopped_orphaned)}")
        print(f"Successfully stopped: {len(self.stopped_sessions)}")
        print(f"Errors: {len(self.errors)}")

        if self.errors:
            print("\n❌ Errors encountered:")
            for error in self.errors:
                print(f"   - {error}")

        if self.stopped_sessions:
            print("\n✅ Successfully stopped sessions:")
            for session_id in self.stopped_sessions:
                print(f"   - {session_id}")
        
        if stopped_orphaned:
            print("\n🧹 Stopped orphaned containers:")
            for container in stopped_orphaned:
                print(f"   - {container}")

        return {
            'total_sessions': len(sessions),
            'sessions_with_containers': len([s for s in sessions if s.get('container_id')]),
            'stopped_sessions': self.stopped_sessions,
            'stopped_orphaned': stopped_orphaned,
            'errors': self.errors
        }

    def get_orphaned_containers(self) -> List[str]:
        """Get orphaned agent containers that aren't tracked in database"""
        try:
            # Get all containers with "agent_" prefix
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=agent_', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Error getting containers: {result.stderr}")
                return []
            
            all_agent_containers = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Get containers tracked in database
            tracked_containers = set()
            sessions = self.get_all_sessions()
            for session in sessions:
                if session.get('container_id'):
                    tracked_containers.add(session['container_id'])
            
            # Find orphaned containers (exist in Docker but not in database)
            orphaned = []
            for container_name in all_agent_containers:
                # Extract container ID from name like "agent_ses1234"
                if '_' in container_name:
                    session_id = container_name.split('_', 1)[1]
                    # Check if this session exists in database
                    session_exists = any(s['session_id'] == session_id for s in sessions)
                    if not session_exists:
                        orphaned.append(container_name)
            
            return orphaned
            
        except Exception as e:
            print(f"❌ Error finding orphaned containers: {e}")
            return []

    def stop_orphaned_containers(self) -> List[str]:
        """Stop orphaned containers and return list of stopped ones"""
        orphaned = self.get_orphaned_containers()
        
        if not orphaned:
            return []
        
        print(f"\n🧹 Found {len(orphaned)} orphaned containers:")
        for container in orphaned:
            print(f"   - {container}")
        
        stopped = []
        for container_name in orphaned:
            print(f"\n🛑 Stopping orphaned container: {container_name}")
            
            # Extract container ID
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.ID}}'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    container_id = result.stdout.strip()
                    
                    if self.stop_container_via_docker(container_id, container_name.split('_', 1)[1]):
                        stopped.append(container_name)
                else:
                    print(f"  ❌ Could not find container ID for {container_name}")
                    
            except Exception as e:
                print(f"  ❌ Error stopping orphaned container {container_name}: {e}")
        
        return stopped

def main():
    parser = argparse.ArgumentParser(description="Stop all OpenCode sessions")
    parser.add_argument(
        '--direct',
        action='store_true',
        help='Use direct Docker commands instead of API calls'
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f'Database path (default: {DB_PATH})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be stopped without actually stopping'
    )

    args = parser.parse_args()

    print("🛑 OpenCode Session Stopper")
    print("=" * 50)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No sessions will be stopped")
        print()

    stopper = SessionStopper(db_path=args.db_path, use_api=not args.direct)

    if args.dry_run:
        # Just show what would be stopped
        sessions = stopper.get_all_sessions()
        print(f"📋 Would process {len(sessions)} sessions:")

        for session in sessions:
            container_id = session.get('container_id')
            status = session.get('container_status', 'unknown')
            has_container = container_id and status in ['running', 'created']

            print(f"   - {session['session_id']}: {'🐳 has container' if has_container else 'ℹ️  no container'} ({status})")
        
        sessions_with_containers = [s for s in sessions if s.get('container_id') and s.get('container_status') in ['running', 'created']]
        
        # Also show orphaned containers
        orphaned = stopper.get_orphaned_containers()
        print(f"\n🧹 Would also stop {len(orphaned)} orphaned containers:")
        for container in orphaned:
            print(f"   - {container}")
        
        total_containers = len(sessions_with_containers) + len(orphaned)
        print(f"\n🐳 Total containers to stop: {total_containers}")
        return

    # Actually stop sessions
    result = stopper.stop_all_sessions()

    # Exit with error code if there were errors
    if result['errors']:
        sys.exit(1)

if __name__ == '__main__':
    main()