#!/usr/bin/env python3
"""
OpenCode CLI - A command-line interface for interacting with OpenCode sessions
"""
import argparse
import datetime
import sys
from typing import Optional

from app.core.opencode_client import OpenCodeService


class OpenCodeCLI:
    """Command-line interface for OpenCode"""

    def __init__(self, base_url: str = "http://localhost:4096"):
        self.service = OpenCodeService()
        self.base_url = base_url

    def list_sessions(self, detailed: bool = False):
        """List all sessions"""
        try:
            sessions = self.service.list_sessions()
            if not sessions:
                print("No sessions found.")
                return

            print(f"\nFound {len(sessions)} sessions:\n")

            for i, session in enumerate(sessions, 1):
                print(f"{i}. {session.id}")
                if detailed:
                    if hasattr(session, 'time') and session.time:
                        if hasattr(session.time, 'created') and session.time.created:
                            dt = datetime.datetime.fromtimestamp(session.time.created / 1000)
                            print(f"   Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    if hasattr(session, 'title') and session.title:
                        print(f"   Title: {session.title}")
                    if hasattr(session, 'version'):
                        print(f"   Version: {session.version}")
                print()

        except Exception as e:
            print(f"Error listing sessions: {e}")

    def show_session_history(self, session_id: str, limit: Optional[int] = None):
        """Show chat history for a session"""
        try:
            print(f"\nChat History for Session {session_id}\n")
            print("=" * 60)

            # Get messages for the session
            messages = self.service.client.session.messages(session_id)
            if not messages:
                print("No messages found in this session.")
                return

            # Apply limit if specified
            if limit:
                messages = messages[-limit:]

            for msg in messages:
                info = msg.info

                # Display in chat format
                if info.role == "user":
                    # Get the main text content for user messages
                    content_parts = []
                    for part in msg.parts:
                        if hasattr(part, 'text') and part.text and part.text.strip():
                            content_parts.append(part.text.strip())
                    content = " ".join(content_parts)
                    print(f"You: {content}")
                    
                elif info.role == "assistant":
                    print("Assistant:")
                    
                    # Show all parts with their types
                    for part in msg.parts:
                        if hasattr(part, 'type'):
                            part_type = part.type
                            if part_type == 'text' and hasattr(part, 'text') and part.text:
                                # Regular text content
                                print(f"  {part.text}")
                            elif part_type in ['step-start', 'step-finish']:
                                # Tool usage steps
                                print(f"  [{part_type}]")
                                if hasattr(part, 'snapshot') and part.snapshot:
                                    print(f"    Snapshot: {part.snapshot}")
                            elif part_type == 'patch':
                                # Code patches/changes
                                print(f"  [{part_type}]")
                            elif part_type == 'tool':
                                # Tool usage - show tool name if available
                                tool_name = "tool"
                                if hasattr(part, 'name') and part.name:
                                    tool_name = part.name
                                elif hasattr(part, 'tool') and part.tool:
                                    tool_name = part.tool
                                elif hasattr(part, 'function') and part.function:
                                    tool_name = part.function
                                print(f"  [{tool_name}]")
                            else:
                                # Other part types
                                print(f"  [{part_type}]")
                                if hasattr(part, 'text') and part.text:
                                    print(f"    {part.text}")

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
            print(f"Error retrieving session history: {e}")

    def chat(self, session_id: str, message: str):
        """Send a chat message to a session"""
        try:
            print(f"You: {message}\n")

            # Send the message
            result = self.service.send_prompt(session_id, message)

            print("Assistant:", end=" ")
            # Handle the response object
            if hasattr(result, 'to_dict'):
                response_data = result.to_dict()
            elif hasattr(result, '__dict__'):
                response_data = result.__dict__
            else:
                response_data = result

            # Extract and display text parts
            if isinstance(response_data, dict) and 'parts' in response_data:
                for part in response_data['parts']:
                    if part.get('type') == 'text':
                        print(part.get('text', ''))

            # Display metadata
            if isinstance(response_data, dict) and 'info' in response_data:
                info = response_data['info']
                metadata = []
                if 'tokens' in info:
                    tokens = info['tokens']
                    metadata.append(f"{tokens.get('input', 0)}->{tokens.get('output', 0)} tokens")
                if metadata:
                    print(f"\n   ({' | '.join(metadata)})")
            else:
                print(f"\nResponse: {result}")

        except Exception as e:
            print(f"Error sending message: {e}")

    def test_connection(self):
        """Test connection to the server"""
        try:
            # Try to list sessions as a connection test
            sessions = self.service.list_sessions()
            print(f"✓ Connected successfully! Found {len(sessions)} sessions.")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="OpenCode CLI - Interact with OpenCode sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py sessions                    # List all sessions
  python cli.py sessions --detailed         # List sessions with details
  python cli.py history <session_id>        # Show full chat history
  python cli.py history <session_id> --limit 10  # Show last 10 messages
  python cli.py chat <session_id> "Hello!"  # Send a message
  python cli.py test                        # Test connection
        """
    )

    parser.add_argument(
        "command",
        choices=["sessions", "history", "chat", "test"],
        help="Command to execute"
    )

    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for the command"
    )

    parser.add_argument(
        "--url",
        default="http://localhost:4096",
        help="OpenCode server URL (default: http://localhost:4096)"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of messages to show"
    )

    args = parser.parse_args()

    # Create CLI instance
    cli = OpenCodeCLI(args.url)

    # Execute commands
    if args.command == "test":
        success = cli.test_connection()
        if not success:
            sys.exit(1)

    elif args.command == "sessions":
        cli.list_sessions(args.detailed)

    elif args.command == "history":
        if not args.args:
            print("Error: Session ID required for history command")
            sys.exit(1)
        session_id = args.args[0]
        cli.show_session_history(session_id, args.limit)

    elif args.command == "chat":
        if len(args.args) < 2:
            print("Error: Session ID and message required for chat command")
            sys.exit(1)
        session_id, message = args.args[0], " ".join(args.args[1:])
        cli.chat(session_id, message)


if __name__ == "__main__":
    main()