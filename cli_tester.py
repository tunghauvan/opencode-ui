#!/usr/bin/env python3
"""
OpenCode CLI Tester - Test OpenCode API endpoints
"""
import argparse
import datetime
import json
import sys
from typing import Optional

import opencode_ai


class OpenCodeTester:
    """CLI tool to test OpenCode API"""

    def __init__(self, base_url: str = "http://localhost:4096"):
        self.client = opencode_ai.Opencode(base_url=base_url)

    def test_connection(self) -> bool:
        """Test basic connection to OpenCode server"""
        try:
            # Try to list sessions as a basic connectivity test
            sessions = self.client.session.list()
            print(f"✅ Connected to OpenCode server at {self.client.base_url}")
            print(f"📊 Found {len(sessions)} sessions")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def list_sessions(self, detailed: bool = False):
        """List all sessions"""
        try:
            sessions = self.client.session.list()
            print(f"\n📋 Sessions ({len(sessions)} total):\n")

            for i, session in enumerate(sessions, 1):
                print(f"{i}. {session.title}")
                print(f"   ID: {session.id}")
                print(f"   Created: {session.time.created}")
                print(f"   Updated: {session.time.updated}")
                if detailed:
                    print(f"   Version: {session.version}")
                    print(f"   Project: {session.projectID}")
                    print(f"   Directory: {session.directory}")
                    if hasattr(session, 'summary') and session.summary:
                        print(f"   Summary: {session.summary}")
                print()

        except Exception as e:
            print(f"❌ Failed to list sessions: {e}")

    def get_session_details(self, session_id: str):
        """Get detailed information about a specific session"""
        try:
            # Note: OpenCode might not have a direct get/retrieve method
            # Let's try to find it in the list
            sessions = self.client.session.list()
            session = next((s for s in sessions if s.id == session_id), None)

            if session:
                print(f"\n📄 Session Details:\n")
                print(f"ID: {session.id}")
                print(f"Title: {session.title}")
                print(f"Created: {session.time.created}")
                print(f"Updated: {session.time.updated}")
                print(f"Version: {session.version}")
                print(f"Project ID: {session.projectID}")
                print(f"Directory: {session.directory}")
                if hasattr(session, 'summary') and session.summary:
                    print(f"Summary: {json.dumps(session.summary, indent=2)}")
            else:
                print(f"❌ Session {session_id} not found")
        except Exception as e:
            print(f"❌ Failed to get session details: {e}")

    def get_session_history(self, session_id: str):
        """Get the full chat history for a specific session"""
        try:
            print(f"\nChat History for Session {session_id}\n")
            print("=" * 60)

            # Try to get messages for the session
            messages = self.client.session.messages(session_id)
            if not messages:
                print("No messages found in this session.")
                return

            for msg in messages:
                info = msg.info

                # Format timestamp
                timestamp = ""
                if hasattr(info, 'time') and info.time and hasattr(info.time, 'created'):
                    dt = datetime.datetime.fromtimestamp(info.time.created / 1000)
                    timestamp = f"[{dt.strftime('%H:%M:%S')}] "

                # Get the main text content
                content_parts = []
                for part in msg.parts:
                    if hasattr(part, 'text') and part.text and part.text.strip():
                        content_parts.append(part.text.strip())

                content = " ".join(content_parts)

                if info.role == "user":
                    print(f"You: {content}")
                elif info.role == "assistant":
                    print(f"Assistant: {content}")

                    # Add metadata for assistant messages (compact)
                    metadata = []
                    if hasattr(info, 'cost') and info.cost is not None and info.cost > 0:
                        metadata.append(f"${info.cost}")
                    if hasattr(info, 'tokens') and info.tokens:
                        metadata.append(f"{int(info.tokens.input)}->{int(info.tokens.output)} tokens")
                    if metadata:
                        print(f"   ({' | '.join(metadata)})")

                print()  # Empty line between messages

        except Exception as e:
            print(f"Failed to get session history: {e}")
            print("Note: The API might not support fetching message history, or the session may not exist")

    def test_chat(self, session_id: str, message: str):
        """Test sending a chat message (if supported)"""
        try:
            print(f"\nTesting chat with session {session_id}:")
            print(f"You: {message}\n")

            # Try different formats for the parts
            result = self.client.session.chat(
                session_id,
                model_id="default",
                parts=[{"type": "text", "text": message}],  # Try 'text' instead of 'content'
                provider_id="default"
            )

            print("Chat response:")
            # Handle the response object
            if hasattr(result, 'to_dict'):
                response_data = result.to_dict()
            elif hasattr(result, '__dict__'):
                response_data = result.__dict__
            else:
                response_data = result

            # Extract and display text parts in chat format
            if isinstance(response_data, dict) and 'parts' in response_data:
                for part in response_data['parts']:
                    if part.get('type') == 'text':
                        print(f"Assistant: {part.get('text', '')}")
            
            # Display key metadata in compact format
            if isinstance(response_data, dict) and 'info' in response_data:
                info = response_data['info']
                metadata = []
                if 'tokens' in info:
                    tokens = info['tokens']
                    metadata.append(f"{tokens.get('input', 0)}->{tokens.get('output', 0)} tokens")
                if metadata:
                    print(f"   ({' | '.join(metadata)})")
            else:
                print(f"Response type: {type(result)}")
                print(f"Response: {result}")

        except Exception as e:
            print(f"Failed to send chat message: {e}")
            print("Note: Chat API might require specific model/provider configuration")

    def get_server_info(self):
        """Get server information if available"""
        try:
            # Try to get some basic server info
            print("\n🔍 Server Information:")
            print(f"Base URL: {self.client.base_url}")

            # Test different endpoints
            endpoints_to_test = [
                ("Sessions", lambda: len(self.client.session.list())),
            ]

            for name, test_func in endpoints_to_test:
                try:
                    result = test_func()
                    print(f"✅ {name}: {result}")
                except Exception as e:
                    print(f"❌ {name}: Failed ({e})")

        except Exception as e:
            print(f"❌ Failed to get server info: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="OpenCode API Tester CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_tester.py --test-connection
  python cli_tester.py --list-sessions
  python cli_tester.py --list-sessions --detailed
  python cli_tester.py --session-details ses_123
  python cli_tester.py --session-history ses_123
  python cli_tester.py --chat ses_123 "Hello world"
  python cli_tester.py --server-info
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:4096",
        help="OpenCode server URL (default: http://localhost:4096)"
    )

    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test basic connection to OpenCode server"
    )

    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all sessions"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed session information"
    )

    parser.add_argument(
        "--session-details",
        metavar="SESSION_ID",
        help="Get detailed information about a specific session"
    )

    parser.add_argument(
        "--session-history",
        metavar="SESSION_ID",
        help="Get the full chat history for a specific session"
    )

    parser.add_argument(
        "--chat",
        nargs=2,
        metavar=("SESSION_ID", "MESSAGE"),
        help="Send a chat message to a session"
    )

    parser.add_argument(
        "--server-info",
        action="store_true",
        help="Get server information"
    )

    args = parser.parse_args()

    # Create tester instance
    tester = OpenCodeTester(args.url)

    # Execute commands
    if args.test_connection:
        success = tester.test_connection()
        if not success:
            sys.exit(1)

    if args.list_sessions:
        tester.list_sessions(args.detailed)

    if args.session_details:
        tester.get_session_details(args.session_details)

    if args.session_history:
        tester.get_session_history(args.session_history)

    if args.chat:
        session_id, message = args.chat
        tester.test_chat(session_id, message)

    if args.server_info:
        tester.get_server_info()

    # If no arguments provided, show help
    if not any([
        args.test_connection,
        args.list_sessions,
        args.session_details,
        args.session_history,
        args.chat,
        args.server_info
    ]):
        parser.print_help()


if __name__ == "__main__":
    main()