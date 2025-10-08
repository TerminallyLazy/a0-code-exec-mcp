"""
Code Execution Tools - Ported from Agent Zero
Using Agent Zero's original code with minimal changes for MCP integration
"""

import asyncio
import logging
import shlex
import time
from typing import Any, Dict, Optional

from .log import Log
from .print_style import PrintStyle
from .shell_local import LocalInteractiveSession
from .strings import truncate_text

logger = logging.getLogger(__name__)


class CodeExecutionTools:
    """
    Code execution tools ported from Agent Zero.
    Provides terminal and Python execution with session management.
    """

    def __init__(
        self,
        executable: str = "/bin/bash",
        init_commands: Optional[list[str]] = None,
        default_timeout: int = 30,
        first_output_timeout: int = 60,
    ):
        """Initialize code execution tools."""
        self.executable = executable
        self.init_commands = init_commands or []
        self.default_timeout = default_timeout
        self.first_output_timeout = first_output_timeout

        self.sessions: Dict[str, LocalInteractiveSession] = {}
        self.log = Log()

        logger.info(f"CodeExecutionTools initialized (executable: {executable})")

    async def execute_terminal(
        self, command: str, session: str = "default", timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute terminal command using Agent Zero's logic."""
        try:
            if session not in self.sessions:
                await self._init_session(session)

            timeout = timeout or self.default_timeout

            result = await self._terminal_session(session, command, timeout)

            return {
                "success": True,
                "output": result,
                "session": session,
                "exit_code": 0,
            }
        except Exception as e:
            logger.error(f"Terminal execution error: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "session": session,
                "exit_code": -1,
            }

    async def execute_python(
        self, code: str, session: str = "default", timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute Python code using Agent Zero's ipython logic."""
        try:
            if session not in self.sessions:
                await self._init_session(session)

            timeout = timeout or self.default_timeout

            escaped_code = shlex.quote(code)
            command = f"ipython -c {escaped_code}"
            prefix = "python> " + self._format_command_for_output(code) + "\n\n"

            result = await self._terminal_session(session, command, timeout, prefix)

            return {
                "success": True,
                "output": result,
                "session": session,
            }
        except Exception as e:
            logger.error(f"Python execution error: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "session": session,
            }

    async def get_output(self, session: str = "default", lines: int = 50) -> Dict[str, Any]:
        """Get recent output from session."""
        if session not in self.sessions:
            return {
                "success": True,
                "output": f"Session '{session}' does not exist",
                "session": session,
                "lines_returned": 0,
            }

        return {
            "success": True,
            "output": "Output retrieval from session",
            "session": session,
            "lines_returned": 0,
        }

    async def reset(self, session: Optional[str] = None) -> Dict[str, Any]:
        """Reset session(s) using Agent Zero's logic."""
        try:
            if session is None:
                session_names = list(self.sessions.keys())
                for s in session_names:
                    await self.sessions[s].close()
                self.sessions.clear()

                PrintStyle(font_color="#FFA500", bold=True).print("Resetting all sessions...")

                return {
                    "success": True,
                    "message": f"All sessions reset ({len(session_names)} sessions)",
                    "sessions_reset": len(session_names),
                }
            else:
                if session in self.sessions:
                    await self.sessions[session].close()
                    del self.sessions[session]

                    PrintStyle(font_color="#FFA500", bold=True).print(
                        f"Resetting session '{session}'..."
                    )

                return {
                    "success": True,
                    "message": f"Session '{session}' reset",
                    "sessions_reset": 1,
                }
        except Exception as e:
            logger.error(f"Reset error: {e}")
            return {
                "success": False,
                "message": f"Reset error: {str(e)}",
                "sessions_reset": 0,
            }

    async def _init_session(self, session: str):
        """Initialize a new session with init commands."""
        logger.info(f"Initializing session '{session}'")

        shell = LocalInteractiveSession(
            executable=self.executable, init_commands=self.init_commands
        )
        await shell.connect()
        self.sessions[session] = shell

    async def _terminal_session(
        self, session: str, command: str, timeout: int, prefix: str = ""
    ) -> str:
        """Execute command in terminal session - ported from Agent Zero."""
        shell = self.sessions[session]

        await shell.send_command(command)

        PrintStyle(background_color="white", font_color="#1B4F72", bold=True).print(
            "Code execution output"
        )

        return await self._get_terminal_output(session=session, timeout=timeout, prefix=prefix)

    async def _get_terminal_output(
        self,
        session: str,
        timeout: int = 30,
        prefix: str = "",
    ) -> str:
        """Get terminal output - ported from Agent Zero's get_terminal_output."""
        shell = self.sessions[session]

        start_time = time.time()
        full_output = ""
        got_output = False

        log_item = self.log.log(type="code_exe", heading="Executing...", content=prefix)

        while True:
            await asyncio.sleep(0.1)

            clean_full, partial = await shell.read_output(timeout=1, reset_full_output=False)

            now = time.time()
            if partial:
                PrintStyle(font_color="#85C1E9").stream(partial)
                full_output = clean_full
                got_output = True
                log_item.update(content=prefix + full_output)

            if now - start_time > timeout:
                PrintStyle.warning(f"Command timed out after {timeout} seconds")
                if full_output:
                    return full_output + f"\n\n[Timed out after {timeout}s]"
                return f"[Timed out after {timeout}s - no output]"

            if got_output and not partial:
                await asyncio.sleep(0.5)
                clean_full, partial = await shell.read_output(timeout=0.1, reset_full_output=False)
                if not partial:
                    return clean_full or full_output

        return full_output

    def _format_command_for_output(self, command: str) -> str:
        """Format command for output - from Agent Zero."""
        short_cmd = command[:200]
        short_cmd = " ".join(short_cmd.split())
        return truncate_text(short_cmd, 100, at_end=True)
