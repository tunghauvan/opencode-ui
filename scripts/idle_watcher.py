#!/usr/bin/env python3
"""Idle container watcher service"""
import argparse
import logging
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import requests

DB_PATH = os.getenv("DB_PATH", "data/db.sqlite3")
AGENT_CONTROLLER_URL = os.getenv("AGENT_CONTROLLER_URL", "http://agent-controller:8001")
SERVICE_SECRET = os.getenv("AGENT_SERVICE_SECRET", "default-secret-change-in-production")
IDLE_THRESHOLD_SECONDS = int(os.getenv("IDLE_THRESHOLD_SECONDS", "300"))
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
REQUEST_TIMEOUT = 15

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [idle-watcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class IdleSession:
    session_id: str
    container_id: str
    last_activity: Optional[datetime]


def parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    if not timestamp:
        return None

    try:
        parsed = datetime.fromisoformat(timestamp)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            parsed = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            logging.debug("Could not parse timestamp %s", timestamp)
            return None


def get_idle_sessions(threshold_seconds: int) -> List[IdleSession]:
    """Return sessions whose last activity is older than the threshold"""
    now = datetime.now(timezone.utc)
    idle_sessions: List[IdleSession] = []

    if not os.path.exists(DB_PATH):
        logging.warning("Database file %s does not exist", DB_PATH)
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id, container_id, last_activity
            FROM sessions
            WHERE container_status = 'running' AND container_id IS NOT NULL
            """
        )

        for row in cursor.fetchall():
            last_activity = parse_timestamp(row["last_activity"])
            if last_activity is None:
                idle_sessions.append(
                    IdleSession(session_id=row["session_id"], container_id=row["container_id"], last_activity=None)
                )
                continue

            if (now - last_activity).total_seconds() >= threshold_seconds:
                idle_sessions.append(
                    IdleSession(session_id=row["session_id"], container_id=row["container_id"], last_activity=last_activity)
                )

    except Exception as exc:  # pragma: no cover - logging only
        logging.error("Failed to read sessions: %s", exc)
    finally:
        conn.close()

    return idle_sessions


def mark_session_stopped(session_id: str) -> None:
    """Update the database to mark the session as stopped"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE sessions
            SET container_id = NULL,
                container_status = 'stopped',
                updated_at = datetime('now')
            WHERE session_id = ?
            """,
            (session_id,)
        )
        conn.commit()
    except Exception as exc:
        logging.error("Failed to update session %s: %s", session_id, exc)
    finally:
        conn.close()


def stop_session(session: IdleSession) -> bool:
    """Stop an idle session through the agent controller"""
    headers = {
        "X-Service-Secret": SERVICE_SECRET,
    }
    url = f"{AGENT_CONTROLLER_URL}/sessions/{session.session_id}/stop"

    try:
        response = requests.post(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        logging.warning("Network error stopping %s: %s", session.session_id, exc)
        return False

    if response.status_code != 200:
        logging.warning("Agent controller responded %s for %s", response.status_code, session.session_id)
        return False

    logging.info("Stopped idle session %s", session.session_id)
    mark_session_stopped(session.session_id)
    return True


def run_once(threshold_seconds: int, dry_run: bool) -> None:
    idle_sessions = get_idle_sessions(threshold_seconds)

    if not idle_sessions:
        logging.info("No idle sessions older than %s seconds", threshold_seconds)
        return

    logging.info("Found %d idle sessions", len(idle_sessions))

    for session in idle_sessions:
        last_activity = session.last_activity.isoformat() if session.last_activity else "<unknown>"
        logging.info(
            "Session %s last active at %s, container=%s",
            session.session_id,
            last_activity,
            session.container_id,
        )

        if dry_run:
            logging.info("Dry run: skipping stop for %s", session.session_id)
            continue

        stop_session(session)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stop idle OpenCode sessions")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single check and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not stop containers, only report idling ones",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=CHECK_INTERVAL_SECONDS,
        help="Polling interval between checks (seconds)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=IDLE_THRESHOLD_SECONDS,
        help="Idle duration threshold (seconds)",
    )

    args = parser.parse_args()

    logging.info("Starting idle watcher (threshold=%s sec, interval=%s sec)", args.threshold, args.interval)

    try:
        while True:
            run_once(args.threshold, args.dry_run)

            if args.once:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Idle watcher interrupted, exiting")
        sys.exit(0)


if __name__ == "__main__":
    main()
