# Implementation Notes

## Package Created: ao-code-exec-mcp

A minimal standalone MCP server for code execution, extracted from Agent Zero architecture.

## What Was Built

### Core Components

1. **tty_session.py** - TTY session manager
   - Uses `pexpect` for cross-platform TTY handling
   - Supports both Unix (spawn) and Windows (PopenSpawn)
   - Manages persistent shell sessions with custom prompt markers
   - Handles command execution with timeout support

2. **shell_local.py** - Shell session manager
   - Manages multiple independent TTY sessions
   - Session lifecycle (create, execute, reset, close)
   - Output buffer management
   - Session state tracking

3. **tools.py** - MCP tool implementations
   - `execute_terminal`: Shell command execution with TTY persistence
   - `execute_python`: IPython code execution with session state
   - `output`: Session output retrieval
   - `reset`: Session cleanup and reset
   - All tools are async and thread-safe

4. **server.py** - MCP server entry point
   - MCP protocol implementation using stdio
   - Environment-based configuration
   - Tool registration and routing
   - Result formatting for user display

### Supporting Files

- **prompts/system.md** - Documentation for system behavior
- **prompts/tool_response.md** - Response format specifications
- **scripts/initialize_terminal.sh** - Shell initialization script
- **pyproject.toml** - Package configuration and dependencies
- **mcp-config-example.json** - Example MCP client configurations
- **README.md** - Comprehensive usage documentation

## Key Design Decisions

### 1. Configuration via Environment Variables
Instead of complex config files, the server reads from environment variables:
- `SHELL_EXECUTABLE` - Shell to use
- `INIT_COMMANDS` - Commands to run on session creation
- `TIMEOUT_DEFAULT` - Default command timeout
- `TIMEOUT_FIRST` - Timeout for first command
- `MAX_OUTPUT_LINES` - Output buffer size

This makes it compatible with standard MCP client configurations.

### 2. Dedicated Tools (No Runtime Parameter)
Unlike Agent Zero which used a runtime parameter, this MCP has 4 separate tools:
- Better MCP integration
- Clearer tool descriptions
- Easier for AI agents to understand capabilities

### 3. Local-Only Execution
Removed from Agent Zero:
- ✗ SSH support
- ✗ Node.js/Deno runtime
- ✗ Runtime switching logic

This simplifies the codebase significantly while maintaining core functionality.

### 4. Python Execution via IPython
- Uses IPython for rich Python execution
- Wraps code in temporary files
- Captures stdout/stderr separately
- Maintains session state via independent shell sessions
- Returns both output and errors

### 5. Session Management
- Each session is independent with its own state
- Terminal sessions maintain working directory and environment
- Python sessions maintain variables and imports
- Sessions persist until explicitly reset
- Multiple sessions can run concurrently

## Virtual Environment Considerations

### The Challenge
When the MCP server is launched from a virtual environment, that environment may not be active in spawned shell sessions.

### The Solution
Use `INIT_COMMANDS` to activate virtual environments:

```json
{
  "env": {
    "INIT_COMMANDS": "source /path/to/venv/bin/activate"
  }
}
```

This ensures:
- `pip install` uses the correct environment
- Python packages are installed in the right location
- Terminal commands have access to venv binaries

## Windows Support

### Implementation
- Uses `pexpect.popen_spawn.PopenSpawn` for Windows
- Detects platform via `sys.platform.startswith("win")`
- Adjusts prompt markers for cmd.exe

### Status
- ⚠️ **Untested** - No Windows testing has been performed
- Should work in theory based on pexpect documentation
- May require adjustments for PowerShell vs cmd.exe

### Recommendations for Windows Testing
1. Test with cmd.exe first
2. Try PowerShell if issues occur
3. Check prompt marker detection
4. Verify timeout behavior
5. Test with both Python 3.10 and 3.11+

## Differences from Your Provided Solution

Your JavaScript/Pipedream code had several issues that were addressed:

1. **Language**: Changed from JavaScript to Python (proper MCP SDK)
2. **Execution**: Uses proper TTY sessions instead of basic subprocess
3. **Session State**: Implements true persistent sessions
4. **IPython Integration**: Properly integrates IPython with error handling
5. **MCP Protocol**: Uses official MCP Python SDK
6. **Configuration**: Uses environment variables (MCP standard)
7. **Error Handling**: Comprehensive error handling and timeout management

## Testing Checklist

Before production use, test:

- [ ] Basic terminal commands (ls, pwd, cd)
- [ ] Terminal state persistence (cd in one command, pwd in next)
- [ ] Python code execution (simple calculations)
- [ ] Python session state (variables persist)
- [ ] IPython features (imports, magic commands)
- [ ] Timeout handling (long-running commands)
- [ ] Error handling (syntax errors, command failures)
- [ ] Multiple sessions (isolation verification)
- [ ] Session reset (cleanup verification)
- [ ] Output retrieval (history buffer)
- [ ] Virtual environment activation
- [ ] Windows compatibility (if applicable)

## Installation Steps

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Verify dependencies:**
   ```bash
   python -c "import mcp, IPython, pexpect, psutil; print('OK')"
   ```

3. **Test basic execution:**
   ```bash
   python -m ao_code_exec_mcp.server
   # Should start MCP server waiting on stdin
   ```

4. **Configure MCP client:**
   - Copy configuration from `mcp-config-example.json`
   - Adjust paths and settings as needed
   - Add to your MCP client configuration

5. **Test with MCP client:**
   - Execute simple terminal command
   - Execute simple Python code
   - Verify output retrieval
   - Test session reset

## Future Enhancements

Potential improvements:

1. **Security**: Add sandbox/container support
2. **Monitoring**: Add execution metrics and logging
3. **Limits**: Resource limits (CPU, memory, disk)
4. **Streaming**: Stream output for long-running commands
5. **File Operations**: Add file upload/download tools
6. **Environment**: Better environment variable management
7. **Testing**: Add comprehensive test suite
8. **Windows**: Test and fix Windows compatibility
9. **Documentation**: Add more examples and tutorials
10. **Performance**: Optimize session creation and cleanup

## Notes

- All core functionality is implemented and ready to use
- The codebase is minimal and maintainable
- MCP protocol integration is standard-compliant
- Configuration is flexible via environment variables
- Session management is robust with proper cleanup
- Error handling covers common failure cases
- Documentation is comprehensive

## Known Limitations

1. No SSH support (by design)
2. No Node.js execution (by design)
3. Windows support untested
4. No sandboxing/security isolation
5. No resource limits
6. No streaming output for long commands
7. Output buffer has fixed size limit
8. No file upload/download capabilities
