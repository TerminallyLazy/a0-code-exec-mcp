"""
MCP Tools Implementation
Provides 4 tools: execute_terminal, execute_python, output, reset
"""

import asyncio
import logging
import sys
import os
import tempfile
from typing import Any, Dict, Optional
from pathlib import Path

from .shell_local import ShellSessionManager

logger = logging.getLogger(__name__)


class CodeExecutionTools:
    """
    Code execution tools for MCP.
    Provides terminal and Python execution with session management.
    """

    def __init__(
        self,
        executable: str = "/bin/bash",
        init_commands: Optional[list[str]] = None,
        default_timeout: int = 30,
        first_output_timeout: int = 60,
    ):
        """
        Initialize code execution tools.

        Args:
            executable: Default shell executable
            init_commands: Commands to run on session initialization
            default_timeout: Default command timeout
            first_output_timeout: Timeout for first command in a session
        """
        self.executable = executable
        self.init_commands = init_commands or []
        self.default_timeout = default_timeout
        self.first_output_timeout = first_output_timeout

        # Shell session manager
        self.shell_manager = ShellSessionManager(
            default_executable=executable,
            default_init_commands=init_commands,
            default_timeout=default_timeout,
        )

        # Python session state tracking (for IPython sessions)
        self.python_sessions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"CodeExecutionTools initialized (executable: {executable}, "
            f"init_commands: {len(init_commands)})"
        )

    async def execute_terminal(
        self,
        command: str,
        session: str = "default",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a terminal command in a persistent shell session.

        Args:
            command: Shell command to execute
            session: Session identifier
            timeout: Execution timeout in seconds

        Returns:
            Dict with:
                - success: bool
                - output: str
                - exit_code: int
                - session: str
                - error: Optional[str]
        """
        logger.info(f"Executing terminal command in session '{session}': {command[:50]}...")

        try:
            # Use first_output_timeout for first command in session
            if session not in self.shell_manager.sessions:
                timeout = timeout or self.first_output_timeout
            else:
                timeout = timeout or self.default_timeout

            # Execute the command
            result = await asyncio.to_thread(
                self.shell_manager.execute_command,
                command=command,
                session_id=session,
                timeout=timeout,
            )

            success = result.get("exit_code", -1) == 0 and not result.get("timed_out", False)

            return {
                "success": success,
                "output": result.get("output", ""),
                "exit_code": result.get("exit_code", -1),
                "session": session,
                "timed_out": result.get("timed_out", False),
                "error": result.get("error") if not success else None,
            }

        except Exception as e:
            logger.error(f"Terminal execution error: {e}")
            return {
                "success": False,
                "output": "",
                "exit_code": -1,
                "session": session,
                "error": f"Execution error: {str(e)}",
            }

    async def execute_python(
        self,
        code: str,
        session: str = "default",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute Python code using IPython in a persistent session.

        Args:
            code: Python code to execute
            session: Session identifier
            timeout: Execution timeout in seconds

        Returns:
            Dict with:
                - success: bool
                - output: str
                - error: Optional[str]
                - session: str
        """
        logger.info(f"Executing Python code in session '{session}'")

        try:
            timeout = timeout or self.default_timeout

            # Initialize session if needed
            if session not in self.python_sessions:
                await self._initialize_python_session(session)

            # Execute via IPython
            result = await self._execute_ipython_code(code, session, timeout)

            return {
                "success": result["success"],
                "output": result["output"],
                "error": result.get("error"),
                "session": session,
            }

        except Exception as e:
            logger.error(f"Python execution error: {e}")
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "session": session,
            }

    async def _initialize_python_session(self, session: str) -> None:
        """Initialize a Python/IPython session."""
        logger.info(f"Initializing Python session '{session}'")

        # Create session state
        self.python_sessions[session] = {
            "initialized": True,
            "output_history": [],
        }

        # Start IPython by importing it (this validates it's installed)
        try:
            import IPython
            logger.debug(f"IPython version: {IPython.__version__}")
        except ImportError:
            logger.error("IPython not installed - Python execution will fail")
            raise RuntimeError(
                "IPython is required for Python code execution. "
                "Install with: pip install ipython"
            )

    async def _execute_ipython_code(
        self, code: str, session: str, timeout: int
    ) -> Dict[str, Any]:
        """Execute code using IPython."""
        # Create a temporary Python script that uses IPython
        script = f'''
import sys
import io
from IPython.core.interactiveshell import InteractiveShell

# Capture stdout/stderr
old_stdout = sys.stdout
old_stderr = sys.stderr
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

try:
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    # Create IPython shell
    ipython = InteractiveShell.instance()

    # Execute the code
    result = ipython.run_cell("""
{code}
""", store_history=True)

    # Restore stdout/stderr
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    # Get outputs
    stdout_text = stdout_capture.getvalue()
    stderr_text = stderr_capture.getvalue()

    # Check for errors
    if result.error_in_exec or result.error_before_exec:
        print("ERROR:", stderr_text, file=sys.stderr)
        sys.exit(1)
    else:
        # Print captured output
        if stdout_text:
            print(stdout_text, end="")
        if stderr_text:
            print(stderr_text, file=sys.stderr, end="")

        # Print result if there is one
        if result.result is not None:
            print(repr(result.result))

except Exception as e:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    import traceback
    print(f"EXCEPTION: {{str(e)}}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
'''

        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(script)
            temp_file = f.name

        try:
            # Execute using Python
            python_cmd = f'{sys.executable} "{temp_file}"'

            # Use shell manager to execute
            result = await asyncio.to_thread(
                self.shell_manager.execute_command,
                command=python_cmd,
                session_id=f"python_{session}",
                timeout=timeout,
            )

            # Clean up temp file
            try:
                os.unlink(temp_file)
            except Exception:
                pass

            # Parse result
            success = result.get("exit_code", -1) == 0
            output = result.get("output", "")
            error = None

            if not success or result.get("timed_out"):
                error = output if "ERROR:" in output or "EXCEPTION:" in output else "Execution failed"

            # Store in session history
            if session in self.python_sessions:
                self.python_sessions[session]["output_history"].append({
                    "code": code,
                    "output": output,
                    "error": error,
                })

            return {
                "success": success,
                "output": output,
                "error": error,
            }

        except Exception as e:
            # Clean up temp file on error
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
            raise

    async def get_output(
        self,
        session: str = "default",
        lines: int = 50,
    ) -> Dict[str, Any]:
        """
        Get recent output from a session.

        Args:
            session: Session identifier
            lines: Number of recent lines to retrieve

        Returns:
            Dict with:
                - success: bool
                - output: str
                - session: str
                - lines_returned: int
        """
        logger.info(f"Getting output for session '{session}' (last {lines} lines)")

        try:
            # Get shell session output
            output = await asyncio.to_thread(
                self.shell_manager.get_output,
                session_id=session,
                lines=lines,
            )

            # If this is a Python session, append Python history
            if session in self.python_sessions:
                python_history = self.python_sessions[session]["output_history"][-lines:]
                python_output = []

                for item in python_history:
                    python_output.append(f">>> {item['code']}")
                    if item['output']:
                        python_output.append(item['output'])
                    if item['error']:
                        python_output.append(f"ERROR: {item['error']}")

                if python_output:
                    output = output + "\n\n--- Python History ---\n" + "\n".join(python_output)

            output_lines = output.count('\n') + 1 if output else 0

            return {
                "success": True,
                "output": output,
                "session": session,
                "lines_returned": output_lines,
            }

        except Exception as e:
            logger.error(f"Error getting output for session '{session}': {e}")
            return {
                "success": False,
                "output": "",
                "session": session,
                "error": str(e),
                "lines_returned": 0,
            }

    async def reset(
        self,
        session: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reset a session or all sessions.

        Args:
            session: Session to reset (None = reset all)

        Returns:
            Dict with:
                - success: bool
                - message: str
                - sessions_reset: str or int
        """
        try:
            if session is None:
                # Reset all sessions
                logger.info("Resetting all sessions")

                shell_count = await asyncio.to_thread(
                    self.shell_manager.reset_all_sessions
                )
                python_count = len(self.python_sessions)
                self.python_sessions.clear()

                total = shell_count + python_count

                return {
                    "success": True,
                    "message": f"Reset {total} sessions ({shell_count} shell, {python_count} Python)",
                    "sessions_reset": total,
                }
            else:
                # Reset specific session
                logger.info(f"Resetting session '{session}'")

                success = await asyncio.to_thread(
                    self.shell_manager.reset_session,
                    session_id=session,
                )

                # Also reset Python session if it exists
                if session in self.python_sessions:
                    del self.python_sessions[session]

                if f"python_{session}" in self.shell_manager.sessions:
                    await asyncio.to_thread(
                        self.shell_manager.reset_session,
                        session_id=f"python_{session}",
                    )

                return {
                    "success": success,
                    "message": f"Session '{session}' reset successfully" if success else f"Failed to reset session '{session}'",
                    "sessions_reset": session if success else None,
                }

        except Exception as e:
            logger.error(f"Error resetting sessions: {e}")
            return {
                "success": False,
                "message": f"Reset error: {str(e)}",
                "sessions_reset": None,
            }

    def list_sessions(self) -> list[Dict[str, Any]]:
        """List all active sessions."""
        sessions = self.shell_manager.list_sessions()

        # Add Python session info
        for session_id in self.python_sessions.keys():
            sessions.append({
                "session_id": session_id,
                "type": "python",
                "is_alive": True,
                "history_size": len(self.python_sessions[session_id]["output_history"]),
            })

        return sessions
