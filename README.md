# A0 Code Execution MCP

A minimal Model Context Protocol (MCP) server providing terminal and Python code execution tools. Extracted from the Agent Zero codebase with SSH and Node.js support removed for simplicity.

## Features

- **🖥️ Terminal Execution**: Run shell commands in persistent TTY sessions
- **🐍 Python Execution**: Execute Python code using IPython with session state
- **📝 Output History**: Retrieve execution history from sessions
- **🔄 Session Management**: Reset and manage multiple independent sessions
- **🔌 MCP Protocol**: Standard MCP server with stdio communication
- **🎯 Minimal**: No SSH, no Node.js, just local execution

## Tools

### 1. `execute_terminal`
Execute shell commands in a persistent terminal session with state preservation.

**Parameters:**
- `command` (string, required): Shell command to execute
- `session` (string, optional): Session identifier (default: "default")
- `timeout` (number, optional): Timeout in seconds (default: 30)

**Example:**
```python
{
  "command": "ls -la && pwd",
  "session": "default",
  "timeout": 30
}
```

### 2. `execute_python`
Execute Python code using IPython with persistent session variables.

**Parameters:**
- `code` (string, required): Python code to execute
- `session` (string, optional): Session identifier (default: "default")
- `timeout` (number, optional): Timeout in seconds (default: 30)

**Example:**
```python
{
  "code": "import numpy as np\nresult = np.array([1,2,3]).mean()\nprint(result)",
  "session": "data-analysis",
  "timeout": 60
}
```

### 3. `output`
Retrieve recent output from a session's execution history.

**Parameters:**
- `session` (string, optional): Session identifier (default: "default")
- `lines` (number, optional): Number of recent lines (default: 50)

**Example:**
```python
{
  "session": "default",
  "lines": 100
}
```

### 4. `reset`
Reset/clear execution sessions.

**Parameters:**
- `session` (string, optional): Session to reset (omit to reset all)

**Example:**
```python
{
  "session": "default"
}
```

## Installation

### Using UV (Recommended)

The easiest way to use this MCP server is with [UV](https://docs.astral.sh/uv/):

```bash
# Install from source
git clone <repository-url>
cd ao-code-exec-mcp
uv sync
```

Then configure your MCP client to use:
```json
{
  "command": "uv",
  "args": ["--directory", "/path/to/ao-code-exec-mcp", "run", "ao-code-exec-mcp"]
}
```

### Using Pip

```bash
# Install in development mode
pip install -e .

# Or install from source
pip install .
```

Then use the installed command directly or via Python module.

### Dependencies

- Python 3.10+
- `mcp>=1.0.0` - MCP Python SDK
- `fastmcp>=2.0.0` - FastMCP framework
- `ipython>=8.0.0` - Python code execution
- `pexpect>=4.9.0` - TTY session management
- `psutil>=5.9.0` - Process utilities

## Configuration

### MCP Client Configuration

Add to your MCP client's configuration file (e.g., `claude_desktop_config.json`):

**Option 1: Using UV (Recommended)**
```json
{
  "mcpServers": {
    "ao-code-exec": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/ao-code-exec-mcp",
        "run",
        "ao-code-exec-mcp"
      ],
      "env": {
        "SHELL_EXECUTABLE": "/bin/bash",
        "INIT_COMMANDS": "",
        "TIMEOUT_DEFAULT": "30",
        "TIMEOUT_FIRST": "60"
      }
    }
  }
}
```

**Option 2: Using Python directly**
```json
{
  "mcpServers": {
    "ao-code-exec": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["-m", "ao_code_exec_mcp.server"],
      "env": {
        "SHELL_EXECUTABLE": "/bin/bash",
        "INIT_COMMANDS": "",
        "TIMEOUT_DEFAULT": "30",
        "TIMEOUT_FIRST": "60"
      }
    }
  }
}
```

Replace `/path/to/your/venv/bin/python` with the Python interpreter where you installed the package.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SHELL_EXECUTABLE` | Shell to use for terminal commands | `/bin/bash` (Unix) or `cmd.exe` (Windows) |
| `INIT_COMMANDS` | Semicolon-separated initialization commands | `""` |
| `TIMEOUT_DEFAULT` | Default command timeout in seconds | `30` |
| `TIMEOUT_FIRST` | Timeout for first command in session | `60` |
| `MAX_OUTPUT_LINES` | Maximum output buffer size | `1000` |

### Initialization Commands

Use `INIT_COMMANDS` to set up the environment for each session:

```json
{
  "env": {
    "INIT_COMMANDS": "source /path/to/venv/bin/activate; export PATH=$PATH:/custom/bin"
  }
}
```

Multiple commands can be separated by semicolons or newlines.

## Usage Examples

### Terminal Commands

```bash
# Execute a simple command
execute_terminal(command="echo 'Hello World'", session="default")

# Navigate and run commands (state persists)
execute_terminal(command="cd /tmp", session="test")
execute_terminal(command="pwd", session="test")  # Shows /tmp

# Install packages
execute_terminal(command="pip install requests", session="default", timeout=120)

# Run build commands
execute_terminal(command="npm install && npm run build", session="project", timeout=300)
```

### Python Code

```python
# Simple calculation
execute_python(code="2 + 2", session="calc")

# Import and use libraries
execute_python(code="""
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
print(df.describe())
""", session="data")

# Variables persist across calls
execute_python(code="x = 10", session="vars")
execute_python(code="y = 20", session="vars")
execute_python(code="print(x + y)", session="vars")  # Prints 30
```

### Session Management

```python
# Work in multiple independent sessions
execute_python(code="x = 1", session="session1")
execute_python(code="x = 2", session="session2")
execute_python(code="print(x)", session="session1")  # Prints 1

# Review session output
output(session="session1", lines=50)

# Reset a session when done
reset(session="session1")

# Reset all sessions
reset()
```

## Virtual Environment Support

If the MCP server is installed in a virtual environment, you may need to activate it for shell sessions:

```json
{
  "env": {
    "INIT_COMMANDS": "source /path/to/venv/bin/activate"
  }
}
```

This ensures that commands like `pip install` use the correct environment.

## Platform Support

### Unix/Linux/macOS
- ✅ Fully supported
- Default shell: `/bin/bash` (or `$SHELL` environment variable)
- Uses `pexpect.spawn` for TTY management

### Windows
- ⚠️ Experimental support (untested)
- Default shell: `cmd.exe` (or `%COMSPEC%`)
- Uses `pexpect.popen_spawn.PopenSpawn` for compatibility

## Architecture

```
ao-code-exec-mcp/
├── src/ao_code_exec_mcp/
│   ├── __init__.py          # Package exports
│   ├── server.py            # MCP server implementation
│   ├── tools.py             # Tool implementations
│   ├── tty_session.py       # TTY session manager
│   ├── shell_local.py       # Shell session manager
│   └── prompts/
│       ├── system.md        # System prompt documentation
│       └── tool_response.md # Response format documentation
├── scripts/
│   └── initialize_terminal.sh  # Terminal initialization
├── pyproject.toml           # Package configuration
└── README.md
```

### Components

- **server.py**: MCP protocol handler, tool registration, stdio communication
- **tools.py**: Tool implementations (execute_terminal, execute_python, output, reset)
- **tty_session.py**: Low-level TTY session management using pexpect
- **shell_local.py**: High-level shell session manager with multiple session support
- **prompts/**: Documentation for system behavior and response formats

## Security Considerations

⚠️ **Important**: This MCP server executes code directly on your system.

- Code runs with the same permissions as the MCP server process
- No sandboxing or isolation (local execution only)
- Be cautious with untrusted input
- Review commands before execution in production environments
- Consider running in a container or VM for additional security

## Troubleshooting

### IPython not found
```bash
pip install ipython>=8.0.0
```

### Virtual environment not active in sessions
Add to configuration:
```json
{
  "env": {
    "INIT_COMMANDS": "source /path/to/venv/bin/activate"
  }
}
```

### Commands timing out
Increase timeout:
```json
{
  "env": {
    "TIMEOUT_DEFAULT": "60",
    "TIMEOUT_FIRST": "120"
  }
}
```

### Windows compatibility issues
- Ensure `pexpect` is installed
- Try using PowerShell: `"SHELL_EXECUTABLE": "powershell.exe"`
- Check for firewall or antivirus interference

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest
```

### Code Formatting
```bash
black src/
ruff check src/
```

## Framework

This server uses [FastMCP](https://gofastmcp.com), a modern framework for building MCP servers. FastMCP provides:

- 🚀 Simpler, decorator-based tool registration
- 📝 Automatic schema generation from type hints
- 🔧 Built-in stdio transport handling
- 🎯 Cleaner, more maintainable code

## Differences from Agent Zero

This MCP server is a minimal extraction from Agent Zero with:

- ✅ **Removed**: SSH execution support
- ✅ **Removed**: Node.js/Deno runtime support
- ✅ **Removed**: Complex runtime switching
- ✅ **Kept**: Local TTY session management
- ✅ **Kept**: Python IPython execution
- ✅ **Kept**: Session state persistence
- ✅ **Simplified**: Configuration via environment variables
- ✅ **Improved**: Dedicated MCP tools (no runtime parameter)
- ✅ **Modernized**: FastMCP framework for better developer experience

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- Report issues on GitHub
- Check documentation in `prompts/` directory
- Review MCP protocol documentation at https://modelcontextprotocol.io
