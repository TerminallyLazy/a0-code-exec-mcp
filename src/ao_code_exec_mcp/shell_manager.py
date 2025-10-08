"""
Shell Session Manager
Manages multiple shell sessions using Agent Zero's TTY implementation
"""

import asyncio
import logging
from typing import Dict, Optional
from .shell_local import LocalInteractiveSession

logger = logging.getLogger(__name__)


class ShellSessionManager:
    """
    Manages multiple local shell sessions using Agent Zero's implementation.
    """

    def __init__(
        self,
        default_executable: str = "/bin/bash",
        default_init_commands: Optional[list[str]] = None,
        default_timeout: int = 30,
    ):
        """
        Initialize the shell session manager.

        Args:
            default_executable: Default shell executable
            default_init_commands: Default commands to run on new sessions
            default_timeout: Default timeout for command execution
        """
        self.default_executable = default_executable
        self.default_init_commands = default_init_commands or []
        self.default_timeout = default_timeout

        self.sessions: Dict[str, LocalInteractiveSession] = {}

        logger.info(
            f"ShellSessionManager initialized with executable: {default_executable}"
        )

    async def get_or_create_session(self, session_id: str) -> LocalInteractiveSession:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Session identifier

        Returns:
            LocalInteractiveSession instance
        """
        if session_id not in self.sessions:
            logger.info(f"Creating new session: {session_id}")
            session = LocalInteractiveSession()
            await session.connect()

            # Run initialization commands
            for cmd in self.default_init_commands:
                await session.send_command(cmd)
                # Wait for command to complete
                await session.read_output(timeout=self.default_timeout)

            self.sessions[session_id] = session

        return self.sessions[session_id]

    async def execute_command(
        self,
        command: str,
        session_id: str = "default",
        timeout: Optional[int] = None,
    ) -> dict:
        """
        Execute a command in a session.

        Args:
            command: Command to execute
            session_id: Session identifier
            timeout: Command timeout in seconds

        Returns:
            Dict with execution results
        """
        timeout = timeout or self.default_timeout
        session = await self.get_or_create_session(session_id)

        try:
            await session.send_command(command)
            full_output, _ = await session.read_output(timeout=timeout)

            return {
                "output": full_output,
                "exit_code": 0,  # Simplified - Agent Zero tracks this better
                "timed_out": False,
            }
        except asyncio.TimeoutError:
            full_output, _ = await session.read_output(timeout=0)
            return {
                "output": full_output,
                "exit_code": -1,
                "timed_out": True,
                "error": "Command timed out",
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "output": "",
                "exit_code": -1,
                "timed_out": False,
                "error": str(e),
            }

    async def get_output(self, session_id: str = "default", lines: int = 50) -> str:
        """
        Get recent output from a session.

        Args:
            session_id: Session identifier
            lines: Number of recent lines (not used in Agent Zero version)

        Returns:
            Session output
        """
        if session_id not in self.sessions:
            return ""

        session = self.sessions[session_id]
        full_output, _ = await session.read_output(timeout=0)
        return full_output

    async def reset_session(self, session_id: str) -> bool:
        """
        Reset a specific session.

        Args:
            session_id: Session to reset

        Returns:
            True if successful
        """
        if session_id in self.sessions:
            try:
                await self.sessions[session_id].close()
                del self.sessions[session_id]
                logger.info(f"Reset session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Error resetting session {session_id}: {e}")
                return False
        return False

    async def reset_all_sessions(self) -> int:
        """
        Reset all sessions.

        Returns:
            Number of sessions reset
        """
        count = len(self.sessions)
        for session_id in list(self.sessions.keys()):
            await self.reset_session(session_id)
        return count

    def list_sessions(self) -> list[dict]:
        """List all active sessions."""
        return [
            {
                "session_id": sid,
                "type": "terminal",
                "is_alive": True,
            }
            for sid in self.sessions.keys()
        ]
