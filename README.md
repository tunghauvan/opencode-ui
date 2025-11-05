# OpenCode CLI Tool

A command-line interface tool for interacting with the OpenCode API, providing session management and chat functionality.

## Features

- � **API Integration** - Direct integration with OpenCode API
- � **Session Management** - List, create, and manage OpenCode sessions
- 💬 **Chat Functionality** - Send prompts and receive responses
- 🧪 **Testing Tools** - Built-in test cases for chat functionality
- 🐍 **Python Native** - Pure Python implementation with type hints

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd opencode-cli
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using modern Python packaging:
```bash
pip install -e .
```

## Configuration

Set environment variables:

```bash
# OpenCode settings
export OPENCODE_BASE_URL=http://localhost:4096
export OPENCODE_API_KEY=your-api-key  # optional
```

## Usage

### CLI Tester

The main CLI tool for testing and interacting with OpenCode:

```bash
# Test connection
python cli_tester.py --test-connection

# List all sessions
python cli_tester.py --list-sessions

# List sessions with detailed information
python cli_tester.py --list-sessions --detailed

# Get details of a specific session
python cli_tester.py --session-details <session_id>

# Send a chat message
python cli_tester.py --chat <session_id> "Hello, how are you?"

# Get server information
python cli_tester.py --server-info
```

### Chat Test Case

Run comprehensive chat functionality tests:

```bash
python chat_test_case.py
```

## Project Structure

```
├── cli_tester.py          # Main CLI tool for OpenCode API testing
├── chat_test_case.py      # Comprehensive chat functionality test
├── app/
│   └── core/
│       ├── config.py      # Configuration settings
│       └── opencode_client.py # OpenCode API client wrapper
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

## Development

### Running Tests

```bash
python chat_test_case.py
```

## License

MIT License