# Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install dependencies manually
pip install mcp>=1.0.0 ipython>=8.0.0 pexpect>=4.9.0 psutil>=5.9.0
```

### 2. Verify Installation

```bash
python verify_package.py
```

All checks should pass (green checkmarks).

### 3. Test the Server

```bash
# Start the server (it will wait for MCP protocol input on stdin)
python -m ao_code_exec_mcp.server
```

Press Ctrl+C to stop.

## Configuration

### Basic Configuration

Create or edit your MCP client configuration (e.g., Claude Desktop):

**Location (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Location (Linux):** `~/.config/Claude/claude_desktop_config.json`

**Location (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`

**Content:**
```json
{
  "mcpServers": {
    "ao-code-exec": {
      "command": "python",
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

### With Virtual Environment

```json
{
  "mcpServers": {
    "ao-code-exec": {
      "command": "python",
      "args": ["-m", "ao_code_exec_mcp.server"],
      "env": {
        "SHELL_EXECUTABLE": "/bin/bash",
        "INIT_COMMANDS": "source /path/to/venv/bin/activate",
        "TIMEOUT_DEFAULT": "30",
        "TIMEOUT_FIRST": "60"
      }
    }
  }
}
```

## Testing

### Test Terminal Execution

Once configured in your MCP client, try:

```
Can you run 'ls -la' for me?
```

The agent should use the `execute_terminal` tool.

### Test Python Execution

```
Can you calculate the sum of numbers 1 to 100 using Python?
```

The agent should use the `execute_python` tool with code like:
```python
sum(range(1, 101))
```

### Test Session Persistence

```
1. Create a variable x = 10 in Python
2. In the same session, print x + 5
```

The variable should persist between executions.

### Test Multiple Sessions

```
1. In session "session1", set x = 1
2. In session "session2", set x = 2
3. Print x in session "session1"
```

Each session should maintain independent state.

## Common Issues

### Issue: "mcp module not found"

**Solution:**
```bash
pip install mcp
```

### Issue: "IPython not found"

**Solution:**
```bash
pip install ipython
```

### Issue: Virtual environment not active in terminal

**Solution:** Add to configuration:
```json
{
  "env": {
    "INIT_COMMANDS": "source /path/to/your/venv/bin/activate"
  }
}
```

### Issue: Commands timing out

**Solution:** Increase timeout:
```json
{
  "env": {
    "TIMEOUT_DEFAULT": "60",
    "TIMEOUT_FIRST": "120"
  }
}
```

### Issue: Server not responding

**Check:**
1. Python path is correct
2. Package is installed (`pip show ao-code-exec-mcp`)
3. Check MCP client logs for errors
4. Try running server manually to see errors

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for architecture details
3. Review example configurations in [mcp-config-example.json](mcp-config-example.json)
4. Explore tool descriptions in [prompts/system.md](src/ao_code_exec_mcp/prompts/system.md)

## Support

- Check logs in your MCP client
- Run `python -m ao_code_exec_mcp.server` directly to see errors
- Review [README.md](README.md) troubleshooting section
- Check that all dependencies are installed: `python verify_package.py`
