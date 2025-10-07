# Tool Response Formats

This document describes the response formats for each tool.

## execute_terminal

Executes a shell command and returns the result.

### Success Response
```json
{
  "success": true,
  "output": "command output here\nmultiline supported",
  "exit_code": 0,
  "session": "default",
  "timed_out": false,
  "error": null
}
```

### Failure Response
```json
{
  "success": false,
  "output": "partial output if any",
  "exit_code": 1,
  "session": "default",
  "timed_out": false,
  "error": "error message describing what went wrong"
}
```

### Timeout Response
```json
{
  "success": false,
  "output": "output captured before timeout",
  "exit_code": -1,
  "session": "default",
  "timed_out": true,
  "error": "Command timed out after 30 seconds"
}
```

**Fields:**
- `success`: Boolean indicating if command executed successfully (exit code 0)
- `output`: Standard output from the command
- `exit_code`: Command exit code (0 = success, -1 = timeout/error)
- `session`: Session identifier where command was executed
- `timed_out`: Boolean indicating if command exceeded timeout
- `error`: Error message if command failed (null on success)

---

## execute_python

Executes Python code using IPython and returns the result.

### Success Response
```json
{
  "success": true,
  "output": "execution output\nprint statements\nresult values",
  "error": null,
  "session": "default"
}
```

### Failure Response
```json
{
  "success": false,
  "output": "",
  "error": "Traceback (most recent call last):\n  File \"<stdin>\", line 1\n    syntax error\nSyntaxError: invalid syntax",
  "session": "default"
}
```

**Fields:**
- `success`: Boolean indicating if code executed without errors
- `output`: Captured stdout, print statements, and expression results
- `error`: Error message and traceback if code failed (null on success)
- `session`: Session identifier where code was executed

**Notes:**
- Variables and imports persist in the session
- Last expression value is automatically included in output
- Both stdout and stderr are captured
- Exceptions include full traceback

---

## output

Retrieves recent output from a session's execution history.

### Success Response
```json
{
  "success": true,
  "output": "$ ls -la\ntotal 24\ndrwxr-xr-x  5 user  staff  160 Jan  1 12:00 .\ndrwxr-xr-x 10 user  staff  320 Jan  1 11:00 ..\n\n>>> import sys\n>>> print(sys.version)\n3.11.0\n",
  "session": "default",
  "lines_returned": 42
}
```

### Error Response
```json
{
  "success": false,
  "output": "",
  "session": "nonexistent",
  "error": "Session 'nonexistent' does not exist",
  "lines_returned": 0
}
```

**Fields:**
- `success`: Boolean indicating if output was retrieved successfully
- `output`: Recent execution history formatted with commands and output
- `session`: Session identifier
- `lines_returned`: Number of lines in the output
- `error`: Error message if retrieval failed (absent on success)

**Output Format:**
- Terminal commands prefixed with `$`
- Python code prefixed with `>>>`
- Output follows each command/code block
- Errors are prefixed with `ERROR:`

---

## reset

Resets one or all execution sessions.

### Success Response (specific session)
```json
{
  "success": true,
  "message": "Session 'default' reset successfully",
  "sessions_reset": "default"
}
```

### Success Response (all sessions)
```json
{
  "success": true,
  "message": "Reset 5 sessions (3 shell, 2 Python)",
  "sessions_reset": 5
}
```

### Failure Response
```json
{
  "success": false,
  "message": "Reset error: Session 'xyz' does not exist",
  "sessions_reset": null
}
```

**Fields:**
- `success`: Boolean indicating if reset was successful
- `message`: Human-readable description of what was reset
- `sessions_reset`: Session name (string) or count (number) of reset sessions, null on failure

**Notes:**
- Resetting clears all state: variables, environment, history
- If session parameter is omitted, all sessions are reset
- After reset, the session can be used again with fresh state
