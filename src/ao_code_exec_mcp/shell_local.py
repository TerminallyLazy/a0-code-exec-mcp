"""
Shell Session Manager - Local execution only
Manages multiple TTY sessions with session tracking
"""

import logging
import sys
from typing import Dict, Optional, Any
from .tty_session import TTYSession

logger = logging.getLogger(__name__)


class ShellSessionManager:
    """
    Manages multiple local shell sessions.
    Each session is identified by a session_id and maintains its own state.
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

        self.sessions: Dict[str, TTYSession] = {}

        logger.info(
            f"ShellSessionManager initialized with executable: {default_executable}"
        )

    def get_or_create_session(
        self,
        session_id: str,
        executable: Optional[str] = None,
        init_commands: Optional[list[str]] = None,
        timeout: Optional[int] = None,
    ) -> TTYSession:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Unique session identifier
            executable: Shell executable (uses default if not specified)
            init_commands: Initialization commands (uses default if not specified)
            timeout: Command timeout (uses default if not specified)

        Returns:
            TTYSession instance
        """
        # If session exists and is alive, return it
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.is_alive():
                return session
            else:
                # Session died, remove it
                logger.warning(f"Session '{session_id}' was dead, recreating")
                del self.sessions[session_id]

        # Create new session
        executable = executable or self.default_executable
        init_commands = init_commands or self.default_init_commands
        timeout = timeout or self.default_timeout

        session = TTYSession(
            session_id=session_id,
            executable=executable,
            init_commands=init_commands,
            timeout=timeout,
        )

        self.sessions[session_id] = session
        logger.info(f"Created new session '{session_id}'")

        return session

    def execute_command(
        self,
        command: str,
        session_id: str = "default",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a command in the specified session.

        Args:
            command: Command to execute
            session_id: Session to execute in
            timeout: Command timeout

        Returns:
            Dict with output, exit_code, and timed_out flag
        """
        session = self.get_or_create_session(session_id)

        try:
            result = session.execute_command(command, timeout=timeout)
            return result
        except Exception as e:
            logger.error(f"Error executing command in session '{session_id}': {e}")
            return {
                "output": "",
                "exit_code": -1,
                "timed_out": False,
                "error": str(e),
            }

    def get_output(self, session_id: str = "default", lines: int = 50) -> str:
        """
        Get recent output from a session.

        Args:
            session_id: Session to get output from
            lines: Number of recent lines to retrieve

        Returns:
            Recent output as string
        """
        if session_id not in self.sessions:
            return f"Session '{session_id}' does not exist"

        session = self.sessions[session_id]
        return session.get_output_buffer(lines)

    def reset_session(self, session_id: str = "default") -> bool:
        """
        Reset a specific session.

        Args:
            session_id: Session to reset

        Returns:
            True if reset successful
        """
        if session_id not in self.sessions:
            logger.warning(f"Cannot reset non-existent session '{session_id}'")
            return False

        try:
            session = self.sessions[session_id]
            session.reset()
            logger.info(f"Session '{session_id}' reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting session '{session_id}': {e}")
            # Remove the broken session
            del self.sessions[session_id]
            return False

    def reset_all_sessions(self) -> int:
        """
        Reset all sessions.

        Returns:
            Number of sessions reset
        """
        count = 0
        session_ids = list(self.sessions.keys())

        for session_id in session_ids:
            if self.reset_session(session_id):
                count += 1

        logger.info(f"Reset {count} sessions")
        return count

    def close_session(self, session_id: str) -> bool:
        """
        Close and remove a session.

        Args:
            session_id: Session to close

        Returns:
            True if closed successfully
        """
        if session_id not in self.sessions:
            return False

        try:
            session = self.sessions[session_id]
            session.close()
            del self.sessions[session_id]
            logger.info(f"Session '{session_id}' closed")
            return True
        except Exception as e:
            logger.error(f"Error closing session '{session_id}': {e}")
            return False

    def close_all_sessions(self) -> int:
        """
        Close all sessions.

        Returns:
            Number of sessions closed
        """
        count = 0
        session_ids = list(self.sessions.keys())

        for session_id in session_ids:
            if self.close_session(session_id):
                count += 1

        logger.info(f"Closed {count} sessions")
        return count

    def list_sessions(self) -> list[Dict[str, Any]]:
        """
        List all active sessions.

        Returns:
            List of session info dicts
        """
        sessions_info = []

        for session_id, session in self.sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "executable": session.executable,
                "is_alive": session.is_alive(),
                "output_buffer_size": len(session.output_buffer),
            })

        return sessions_info

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific session.

        Args:
            session_id: Session to get info for

        Returns:
            Session info dict or None if not found
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "executable": session.executable,
            "is_alive": session.is_alive(),
            "output_buffer_size": len(session.output_buffer),
            "cwd": session.cwd,
            "timeout": session.timeout,
        }

    def __del__(self):
        """Cleanup all sessions on deletion."""
        self.close_all_sessions()
