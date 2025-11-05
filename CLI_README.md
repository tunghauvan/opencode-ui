# OpenCode CLI

A simple command-line interface for interacting with OpenCode sessions.

## Installation

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Usage

### Test Connection
```bash
python cli.py test
```

### List Sessions
```bash
# Basic list
python cli.py sessions

# Detailed list with creation time and titles
python cli.py sessions --detailed
```

### View Chat History
```bash
# Full history
python cli.py history <session_id>

# Last N messages only
python cli.py history <session_id> --limit 10
```

### Send Messages
```bash
python cli.py chat <session_id> "Your message here"
```

## Examples

```bash
# Test connection
python cli.py test

# List all sessions
python cli.py sessions

# View recent chat history (last 5 messages)
python cli.py history ses_5abcef5cbffeYMgknBF8CDVTjY --limit 5

# Send a message
python cli.py chat ses_5abcef5cbffeYMgknBF8CDVTjY "Explain Python decorators"
```

## Features

- **Chat Box Layout**: Messages displayed in a clean conversational format
- **Tool Usage Display**: Shows when AI uses tools like file operations, code execution, etc. with actual tool names
- **Session Management**: List and view details of all sessions
- **Message History**: View complete chat history with token usage
- **Interactive Chat**: Send messages and get responses
- **Pagination**: Limit message history display for better readability

## Example Output

When viewing chat history, tool usage is clearly indicated with tool names:

```
[2024-01-15 14:30:22] You: Create a Python function to calculate factorial

[2024-01-15 14:30:25] Assistant: I'll create a factorial function for you.

[step-start] Starting to create the factorial function
[bash] Running command to create file
[patch] Added recursive factorial implementation
[step-finish] Function created successfully

Here's the factorial function:

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

[2024-01-15 14:32:10] You: Explain streaming in web development

[2024-01-15 14:32:12] Assistant: Let me explain streaming...

[step-start] Analyzing the question
[reasoning] Breaking down the concept of streaming
[step-finish] Explanation ready
```