"""
MCP Tools Implementation - Agent Zero Style
Based on Agent Zero's code_execution_tool.py
"""

import asyncio
import logging
import re
import shlex
import time
from typing import Any, Dict, Optional

from .shell_manager import ShellSessionManager

logger = logging.getLogger(__name__)


class CodeExecutionTools:
    """
    Code execution tools for MCP using Agent Zero's implementation.
    """

    def __init__(
        self,
        executable: str = "/bin/bash",
        init_commands: Optional[list[str]] = None,
        default_timeout: int = 30,
        first_output_timeout: int = 60,
    ):
        self.shell_manager = ShellSessionManager(
            default_executable=executable,
            default_init_commands=init_commands or [],
            default_timeout=default_timeout,
        )
        self.default_timeout = default_timeout
        self.first_output_timeout = first_output_timeout

        logger.info(
            f"CodeExecutionTools initialized (executable: {executable}, "
            f"init_commands: {len(init_commands or [])})"
        )

    async def execute_terminal(
        self,
        command: str,
        session: str = "default",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute terminal command using Agent Zero pattern."""
        logger.info(f"Executing terminal command in session '{session}': {command[:50]}...")

        # Use first_output_timeout for first command in session
        if session not in self.shell_manager.sessions:
            timeout = timeout or self.first_output_timeout
        else:
            timeout = timeout or self.default_timeout

        prefix = "bash> " + self._format_command_for_output(command) + "\n\n"

        return await self._terminal_session(
            session=session,
            command=command,
            timeout=timeout,
            prefix=prefix
        )

    async def execute_python(
        self,
        code: str,
        session: str = "default",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute Python code using Agent Zero's ipython -c approach."""
        logger.info(f"Executing Python code in session '{session}'")
        timeout = timeout or self.default_timeout

        # Agent Zero's approach: ipython -c {escaped_code}
        escaped_code = shlex.quote(code)
        command = f"ipython -c {escaped_code}"
        prefix = "python> " + self._format_command_for_output(code) + "\n\n"

        return await self._terminal_session(
            session=session,
            command=command,
            timeout=timeout,
            prefix=prefix
        )

    async def _terminal_session(
        self,
        session: str,
        command: str,
        timeout: int,
        prefix: str = ""
    ) -> Dict[str, Any]:
        """
        Execute command in terminal session (Agent Zero pattern).
        Includes retry logic on connection loss.
        """
        # Try twice in case of connection loss
        for attempt in range(2):
            try:
                shell_session = await self.shell_manager.get_or_create_session(session)
                await shell_session.send_command(command)

                return await self._get_terminal_output(
                    session=session,
                    timeout=timeout,
                    prefix=prefix
                )
            except Exception as e:
                if attempt == 0:
                    # Retry once on connection loss
                    logger.warning(f"Connection error, retrying: {e}")
                    await self.shell_manager.reset_session(session)
                    continue
                else:
                    logger.error(f"Terminal session error: {e}")
                    return {
                        "success": False,
                        "output": "",
                        "session": session,
                        "error": f"Execution error: {str(e)}",
                    }

    async def _get_terminal_output(
        self,
        session: str,
        timeout: int,
        prefix: str = "",
        first_output_timeout: Optional[int] = None,
        between_output_timeout: int = 15,
        dialog_timeout: int = 5,
        max_exec_timeout: int = 180,
        sleep_time: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Get terminal output with Agent Zero's sophisticated detection logic.
        Includes prompt detection, dialog detection, and multiple timeout modes.
        """
        first_output_timeout = first_output_timeout or timeout

        # Shell prompt patterns (Agent Zero)
        prompt_patterns = [
            re.compile(r"\(venv\).+[$#] ?$"),  # (venv) ...$ or (venv) ...#
            re.compile(r"root@[^:]+:[^#]+# ?$"),  # root@container:~#
            re.compile(r"[a-zA-Z0-9_.-]+@[^:]+:[^$#]+[$#] ?$"),  # user@host:~$
            re.compile(r"bash-\d+\.\d+\$ ?$"),  # bash-3.2$
        ]

        # Dialog detection patterns (Agent Zero)
        dialog_patterns = [
            re.compile(r"Y/N", re.IGNORECASE),  # Y/N anywhere
            re.compile(r"yes/no", re.IGNORECASE),  # yes/no anywhere
            re.compile(r":\s*$"),  # line ending with colon
            re.compile(r"\?\s*$"),  # line ending with question mark
        ]

        start_time = time.time()
        last_output_time = start_time
        full_output = ""
        got_output = False

        shell_session = self.shell_manager.sessions.get(session)
        if not shell_session:
            return {
                "success": False,
                "output": "",
                "session": session,
                "error": "Session not found",
            }

        while True:
            await asyncio.sleep(sleep_time)

            # Read output
            try:
                full_output_new, partial_output = await shell_session.read_output(timeout=1)
                if full_output_new:
                    full_output = full_output_new
            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break

            now = time.time()

            if partial_output:
                last_output_time = now
                got_output = True

                # Check for shell prompt (command complete)
                last_lines = full_output.splitlines()[-3:] if full_output else []
                last_lines.reverse()

                for idx, line in enumerate(last_lines):
                    for pat in prompt_patterns:
                        if pat.search(line.strip()):
                            logger.debug("Detected shell prompt, command complete")
                            return {
                                "success": True,
                                "output": prefix + self._fix_output(full_output),
                                "session": session,
                                "exit_code": 0,
                            }

            # Max execution timeout
            if now - start_time > max_exec_timeout:
                logger.warning(f"Max execution timeout ({max_exec_timeout}s)")
                return {
                    "success": False,
                    "output": prefix + self._fix_output(full_output),
                    "session": session,
                    "error": f"Maximum execution time exceeded ({max_exec_timeout}s)",
                    "timed_out": True,
                }

            # Waiting for first output
            if not got_output:
                if now - start_time > first_output_timeout:
                    logger.warning(f"No output after {first_output_timeout}s")
                    return {
                        "success": False,
                        "output": prefix,
                        "session": session,
                        "error": f"No output received within {first_output_timeout}s",
                        "timed_out": True,
                    }
            else:
                # Waiting for more output
                if now - last_output_time > between_output_timeout:
                    logger.debug(f"No output for {between_output_timeout}s, returning")
                    return {
                        "success": True,
                        "output": prefix + self._fix_output(full_output),
                        "session": session,
                        "exit_code": 0,
                    }

                # Dialog detection
                if now - last_output_time > dialog_timeout:
                    last_lines = full_output.splitlines()[-2:] if full_output else []
                    for line in last_lines:
                        for pat in dialog_patterns:
                            if pat.search(line.strip()):
                                logger.debug("Detected dialog prompt")
                                return {
                                    "success": True,
                                    "output": prefix + self._fix_output(full_output),
                                    "session": session,
                                    "exit_code": 0,
                                    "dialog_detected": True,
                                }

    def _format_command_for_output(self, command: str) -> str:
        """Format command for output display (Agent Zero)."""
        # Truncate long commands
        short_cmd = command[:200]
        # Normalize whitespace
        short_cmd = " ".join(short_cmd.split())
        # Final truncation
        if len(short_cmd) > 100:
            short_cmd = short_cmd[:97] + "..."
        return short_cmd

    def _fix_output(self, output: str) -> str:
        """Clean and fix output (Agent Zero pattern)."""
        if not output:
            return ""

        # Remove single byte \xXX escapes
        output = re.sub(r"(?<!\\)\\x[0-9A-Fa-f]{2}", "", output)

        # Strip lines
        output = "\n".join(line.strip() for line in output.splitlines())

        # Truncate if too large (1MB limit)
        max_size = 1000000
        if len(output) > max_size:
            output = output[:max_size] + f"\n\n... (output truncated at {max_size} bytes)"

        return output

    async def get_output(
        self,
        session: str = "default",
        lines: int = 50,
    ) -> Dict[str, Any]:
        """Get recent output from a session."""
        logger.info(f"Getting output for session '{session}' (last {lines} lines)")

        try:
            output = await self.shell_manager.get_output(
                session_id=session,
                lines=lines,
            )

            return {
                "success": True,
                "output": output,
                "session": session,
                "lines_returned": len(output.splitlines()) if output else 0,
            }

        except Exception as e:
            logger.error(f"Error getting output: {e}")
            return {
                "success": False,
                "output": "",
                "session": session,
                "error": f"Error retrieving output: {str(e)}",
            }

    async def reset(
        self,
        session: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reset sessions."""
        try:
            if session is None:
                # Reset all sessions
                logger.info("Resetting all sessions")
                count = await self.shell_manager.reset_all_sessions()

                return {
                    "success": True,
                    "message": f"Reset {count} session(s)",
                    "sessions_reset": count,
                }
            else:
                # Reset specific session
                logger.info(f"Resetting session '{session}'")
                success = await self.shell_manager.reset_session(session_id=session)

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
            }
