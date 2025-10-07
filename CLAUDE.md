# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A minimal Model Context Protocol (MCP) server providing terminal and Python code execution tools. This is a simplified extraction from the Agent Zero codebase with SSH and Node.js support removed. The server provides 4 MCP tools that execute commands/code in persistent sessions.

## Development Commands

### Installation
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
python verify_package.py
```

### Testing
```bash
# Run the server
python -m ao_code_exec_mcp.server

# Or using the installed command
ao-code-exec-mcp
```

### Code Quality
```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Architecture Overview

### Core Components

**server.py** - FastMCP server entry point
- Uses FastMCP framework for simpler, more maintainable code
- Implements MCP protocol with automatic stdio handling
- Parses environment variables for configuration
- Registers 4 tools using FastMCP decorators: `execute_terminal`, `execute_python`, `output`, `reset`
- Tools use Python type hints for automatic schema generation

**tools.py** - Tool implementations
- `CodeExecutionTools` class manages all tool logic
- `execute_terminal`: Runs shell commands in persistent TTY sessions
- `execute_python`: Executes Python via IPython in isolated sessions
- `output`: Retrieves execution history from sessions
- `reset`: Clears session state
- All tools are async and thread-safe

**shell_local.py** - Shell session manager
- `ShellSessionManager` manages multiple independent TTY sessions
- Handles session lifecycle (create, execute, reset, close)
- Maintains output buffers and session state
- Sessions persist until explicitly reset

**tty_session.py** - Low-level TTY management
- Uses `pexpect` for cross-platform TTY handling
- Supports Unix (`spawn`) and Windows (`PopenSpawn`)
- Manages custom prompt markers for command execution
- Handles timeouts and output capture

### Key Design Patterns

**Session Management**: Each session (terminal or Python) maintains independent state. Terminal sessions preserve working directory and environment variables. Python sessions maintain variables and imports via separate shell sessions that run IPython scripts.

**Python Execution**: Python code is executed by wrapping it in a temporary script that uses IPython's `InteractiveShell.run_cell()`. The script captures stdout/stderr and returns results through the shell session manager. This allows persistent state without keeping IPython processes running.

**Configuration**: All settings come from environment variables (`SHELL_EXECUTABLE`, `INIT_COMMANDS`, `TIMEOUT_DEFAULT`, `TIMEOUT_FIRST`, `MAX_OUTPUT_LINES`), not config files. This aligns with standard MCP client configuration patterns.

**Threading Model**: Uses `asyncio.to_thread()` to run synchronous shell operations in thread pool, keeping the async MCP server responsive.

## Important Implementation Notes

### Virtual Environment Activation

When the MCP server runs inside a virtual environment, spawned shell sessions won't automatically have that environment active. Use `INIT_COMMANDS` to activate it:

```json
{
  "env": {
    "INIT_COMMANDS": "source /path/to/venv/bin/activate"
  }
}
```

Multiple init commands can be separated by semicolons or newlines.

### Session Identifiers

- Terminal sessions use the session ID directly
- Python sessions create a parallel shell session with ID `python_{session}`
- Both can coexist with the same base session name

### Timeout Handling

- First command in a new session uses `TIMEOUT_FIRST` (default 60s) since shell initialization takes time
- Subsequent commands use `TIMEOUT_DEFAULT` (default 30s)
- Python execution timeouts apply to the entire IPython script execution

### Platform Support

- Unix/Linux/macOS: Fully supported with `/bin/bash` default
- Windows: Experimental (untested) with `cmd.exe` default
- Platform detection via `sys.platform.startswith("win")`

## Making Changes

When modifying this codebase:

- **Adding new tools**: Register in `server.py` `handle_list_tools()`, implement in `tools.py`, add result formatter to `server.py`
- **Changing session behavior**: Modify `shell_local.py` for shell sessions, `tools.py` for Python sessions
- **Adjusting TTY handling**: Edit `tty_session.py` (careful: pexpect is platform-specific)
- **Adding configuration**: Add environment variable parsing in `server.py._parse_config()`

## Testing Checklist

Before significant changes, verify:
- Basic terminal commands (ls, pwd, cd)
- Terminal state persistence across commands
- Python code execution with imports
- Python session state (variables persist)
- Timeout handling
- Multiple independent sessions
- Session reset functionality
- Output retrieval

## Dependencies

- `mcp>=1.0.0` - MCP Python SDK
- `ipython>=8.0.0` - Python code execution engine
- `pexpect>=4.9.0` - TTY session management
- `psutil>=5.9.0` - Process utilities

## Differences from Agent Zero

This codebase removes SSH execution, Node.js/Deno runtimes, and complex runtime switching from Agent Zero. It provides dedicated tools (no runtime parameter) for better MCP integration. All execution is local-only with no sandboxing.
