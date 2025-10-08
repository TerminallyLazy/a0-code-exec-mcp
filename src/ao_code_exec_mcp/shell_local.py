"""
Shell Session Manager - Ported from Agent Zero
Local interactive session management with control code cleanup
"""

import logging
import re
from typing import Optional, Tuple

from .tty_session import TTYSession

logger = logging.getLogger(__name__)


def clean_string(input_string: str) -> str:
    """
    Remove ANSI escape codes and control characters from terminal output.
    Ported from Agent Zero's shell_ssh.py clean_string function.
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    cleaned = ansi_escape.sub("", input_string)

    cleaned = cleaned.replace("\x00", "")

    cleaned = re.sub(r"^[ \r]*(?:\r*\n>[ \r]*)*", "", cleaned)
    cleaned = re.sub(r"^(>\s*)+", "", cleaned)

    cleaned = cleaned.replace("\r\n", "\n")

    cleaned = cleaned.lstrip("\r ")

    lines = cleaned.split("\n")

    for i in range(len(lines)):
        parts = [part for part in lines[i].split("\r") if part.strip()]
        if parts:
            lines[i] = parts[-1].rstrip()

    return "\n".join(lines)


class LocalInteractiveSession:
    """
    Local interactive shell session manager ported from Agent Zero.
    Provides async terminal execution with proper output capture and cleanup.
    """

    def __init__(self, executable: str = "/bin/bash", init_commands: list[str] = None):
        self.executable = executable
        self.init_commands = init_commands or []
        self.session: Optional[TTYSession] = None
        self.full_output = ""

    async def connect(self):
        """Initialize the TTY session and run init commands."""
        self.session = TTYSession(self.executable)
        await self.session.start()
        await self.session.read_full_until_idle(idle_timeout=1, total_timeout=1)

        for cmd in self.init_commands:
            await self.session.sendline(cmd)
            await self.session.read_full_until_idle(idle_timeout=0.5, total_timeout=2)

    async def close(self):
        """Close the TTY session."""
        if self.session:
            await self.session.close()

    async def send_command(self, command: str):
        """Send a command to the terminal."""
        if not self.session:
            raise Exception("Shell not connected")
        self.full_output = ""
        await self.session.sendline(command)

    async def read_output(
        self, timeout: float = 0, reset_full_output: bool = False
    ) -> Tuple[str, Optional[str]]:
        """
        Read output from terminal with control code cleanup.
        Returns tuple of (full_output, partial_output).
        """
        if not self.session:
            raise Exception("Shell not connected")

        if reset_full_output:
            self.full_output = ""

        partial_output = await self.session.read_full_until_idle(
            idle_timeout=0.01, total_timeout=timeout
        )
        self.full_output += partial_output

        partial_output = clean_string(partial_output)
        clean_full_output = clean_string(self.full_output)

        if not partial_output:
            return clean_full_output, None
        return clean_full_output, partial_output
