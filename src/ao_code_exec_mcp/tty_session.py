"""
TTY Session Manager - Local-only version
Manages persistent pseudo-terminal sessions for shell command execution
Stripped from A0 codebase - SSH support removed
"""

import os
import sys
import time
import logging
from typing import Optional, Dict, Any
import pexpect
from pexpect.popen_spawn import PopenSpawn

logger = logging.getLogger(__name__)


class TTYSession:
    """
    Manages a persistent pseudo-terminal session for command execution.
    Uses pexpect for cross-platform TTY handling.
    """

    def __init__(
        self,
        session_id: str,
        executable: str = "/bin/bash",
        init_commands: Optional[list[str]] = None,
        timeout: int = 30,
        cwd: Optional[str] = None,
    ):
        """
        Initialize a TTY session.

        Args:
            session_id: Unique identifier for this session
            executable: Shell executable to use (e.g., /bin/bash, /bin/zsh, cmd.exe)
            init_commands: Commands to run on session initialization
            timeout: Default timeout for command execution
            cwd: Working directory for the session
        """
        self.session_id = session_id
        self.executable = executable
        self.init_commands = init_commands or []
        self.timeout = timeout
        self.cwd = cwd or os.getcwd()

        self.process: Optional[pexpect.spawn] = None
        self.output_buffer: list[str] = []
        self.is_windows = sys.platform.startswith("win")

        # Platform-specific settings
        if self.is_windows:
            # Use PopenSpawn for Windows compatibility
            self.spawn_class = PopenSpawn
            self.prompt_marker = "AO_PROMPT_READY>"
        else:
            # Use standard spawn for Unix-like systems
            self.spawn_class = pexpect.spawn
            self.prompt_marker = "AO_PROMPT_READY>"

        self._initialize_session()

    def _initialize_session(self) -> None:
        """Initialize the TTY session and run init commands."""
        try:
            # Spawn the shell process
            if self.is_windows:
                self.process = PopenSpawn(
                    self.executable,
                    timeout=self.timeout,
                    encoding="utf-8",
                    cwd=self.cwd,
                )
            else:
                # Unix-like systems
                env = os.environ.copy()
                env["PS1"] = ""  # Disable prompt to avoid confusion

                self.process = pexpect.spawn(
                    self.executable,
                    timeout=self.timeout,
                    encoding="utf-8",
                    cwd=self.cwd,
                    env=env,
                )
                # Set terminal size
                self.process.setwinsize(100, 200)

            logger.info(f"TTY session '{self.session_id}' initialized with {self.executable}")

            # Set up prompt marker for reliable command boundary detection
            self._setup_prompt_marker()

            # Run initialization commands
            for cmd in self.init_commands:
                logger.debug(f"Running init command: {cmd}")
                self.execute_command(cmd)

        except Exception as e:
            logger.error(f"Failed to initialize TTY session '{self.session_id}': {e}")
            raise

    def _setup_prompt_marker(self) -> None:
        """Set up a custom prompt marker for reliable output parsing."""
        try:
            if self.is_windows:
                # Windows command prompt
                marker_cmd = f'prompt {self.prompt_marker}'
            else:
                # Unix shells - set PS1
                marker_cmd = f'export PS1="{self.prompt_marker}"'

            self.process.sendline(marker_cmd)
            time.sleep(0.1)  # Give shell time to update prompt

            # Clear any initial output
            try:
                self.process.expect(self.prompt_marker, timeout=2)
            except pexpect.TIMEOUT:
                logger.warning("Prompt marker setup timeout - continuing anyway")

        except Exception as e:
            logger.warning(f"Failed to set prompt marker: {e}")

    def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a command in the TTY session.

        Args:
            command: Command to execute
            timeout: Timeout in seconds (uses default if not specified)
            capture_output: Whether to capture and return output

        Returns:
            Dict containing:
                - output: Command output
                - exit_code: Exit code (0 on success)
                - timed_out: Whether the command timed out
        """
        if not self.process or not self.process.isalive():
            raise RuntimeError(f"TTY session '{self.session_id}' is not active")

        timeout = timeout or self.timeout
        output_lines = []

        try:
            # Send the command
            self.process.sendline(command)

            # Capture output until we see the prompt marker again
            if capture_output:
                try:
                    # Wait for the prompt marker to appear again
                    self.process.expect(self.prompt_marker, timeout=timeout)

                    # Get everything before the prompt
                    output = self.process.before

                    if output:
                        # Clean up the output
                        lines = output.split('\n')
                        # Remove the command echo (first line) and empty lines
                        if lines and command in lines[0]:
                            lines = lines[1:]
                        output_lines = [line for line in lines if line.strip()]

                except pexpect.TIMEOUT:
                    # Command timed out
                    logger.warning(f"Command timed out: {command[:50]}...")
                    output = self.process.before if self.process.before else ""
                    output_lines = output.split('\n') if output else []

                    return {
                        "output": "\n".join(output_lines),
                        "exit_code": -1,
                        "timed_out": True,
                    }

            # Check exit code
            exit_code = self._get_last_exit_code()

            # Store in buffer
            if capture_output and output_lines:
                self.output_buffer.extend(output_lines)
                # Keep buffer manageable (last 1000 lines)
                if len(self.output_buffer) > 1000:
                    self.output_buffer = self.output_buffer[-1000:]

            result = {
                "output": "\n".join(output_lines),
                "exit_code": exit_code,
                "timed_out": False,
            }

            return result

        except Exception as e:
            logger.error(f"Error executing command '{command[:50]}...': {e}")
            raise

    def _get_last_exit_code(self) -> int:
        """Get the exit code of the last command."""
        try:
            if self.is_windows:
                # Windows: use %ERRORLEVEL%
                self.process.sendline("echo %ERRORLEVEL%")
            else:
                # Unix: use $?
                self.process.sendline("echo $?")

            self.process.expect(self.prompt_marker, timeout=2)
            output = self.process.before.strip()

            # Parse the exit code
            lines = output.split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line.isdigit():
                    return int(line)

            return 0  # Assume success if we can't determine

        except Exception as e:
            logger.warning(f"Could not get exit code: {e}")
            return 0

    def get_output_buffer(self, lines: int = 50) -> str:
        """
        Get recent output from the buffer.

        Args:
            lines: Number of recent lines to return

        Returns:
            Recent output as a string
        """
        recent = self.output_buffer[-lines:] if self.output_buffer else []
        return "\n".join(recent)

    def reset(self) -> None:
        """Reset the session by closing and reinitializing."""
        logger.info(f"Resetting TTY session '{self.session_id}'")
        self.close()
        self.output_buffer.clear()
        self._initialize_session()

    def close(self) -> None:
        """Close the TTY session."""
        if self.process and self.process.isalive():
            try:
                self.process.sendline("exit")
                self.process.expect(pexpect.EOF, timeout=2)
            except Exception:
                pass  # Process might already be dead
            finally:
                self.process.close()
                logger.info(f"TTY session '{self.session_id}' closed")

    def is_alive(self) -> bool:
        """Check if the session is still active."""
        return self.process is not None and self.process.isalive()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
