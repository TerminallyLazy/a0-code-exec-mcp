#!/usr/bin/env python3
"""
A0 Code Execution MCP Server - FastMCP Version
Provides terminal and Python code execution tools via MCP protocol using FastMCP
"""

import asyncio
import logging
import os
import sys
from typing import Any, Optional

from fastmcp import FastMCP

from .tools import CodeExecutionTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("ao-code-exec-mcp")


def create_server() -> FastMCP:
    """Create and configure the FastMCP server."""

    # Parse configuration from environment variables
    if sys.platform.startswith("win"):
        default_executable = os.environ.get("COMSPEC", "cmd.exe")
    else:
        default_executable = os.environ.get("SHELL", "/bin/bash")

    config = {
        "executable": os.environ.get("SHELL_EXECUTABLE", default_executable),
        "init_commands": _parse_init_commands(os.environ.get("INIT_COMMANDS", "")),
        "default_timeout": int(os.environ.get("TIMEOUT_DEFAULT", "30")),
        "first_output_timeout": int(os.environ.get("TIMEOUT_FIRST", "60")),
    }

    logger.info(f"Configuration: {config}")

    # Initialize code execution tools
    tools = CodeExecutionTools(
        executable=config["executable"],
        init_commands=config["init_commands"],
        default_timeout=config["default_timeout"],
        first_output_timeout=config["first_output_timeout"],
    )

    # Create FastMCP server
    mcp = FastMCP("A0 Code Execution")

    # Register tools
    @mcp.tool()
    async def execute_terminal(
        command: str,
        session: str = "default",
        timeout: Optional[int] = None,
    ) -> str:
        """
        Execute shell commands in a persistent terminal session.

        Commands run in a stateful environment where environment variables,
        working directory, and shell state persist between executions.

        Args:
            command: Shell command to execute
            session: Session identifier for command execution (default: "default")
            timeout: Command timeout in seconds (optional)

        Returns:
            Formatted execution result with output and exit code
        """
        result = await tools.execute_terminal(command, session, timeout)
        return _format_terminal_result(result)

    @mcp.tool()
    async def execute_python(
        code: str,
        session: str = "default",
        timeout: Optional[int] = None,
    ) -> str:
        """
        Execute Python code using IPython in a persistent session.

        Code runs in a stateful environment where variables, imports,
        and definitions persist between executions.

        Args:
            code: Python code to execute
            session: Session identifier for code execution (default: "default")
            timeout: Execution timeout in seconds (optional)

        Returns:
            Formatted execution result with output or errors
        """
        result = await tools.execute_python(code, session, timeout)
        return _format_python_result(result)

    @mcp.tool()
    async def output(
        session: str = "default",
        lines: int = 50,
    ) -> str:
        """
        Retrieve recent output from terminal or Python execution sessions.

        Returns a buffer of recent command outputs and results.

        Args:
            session: Session identifier to retrieve output from (default: "default")
            lines: Number of recent output lines to retrieve (default: 50)

        Returns:
            Recent session output
        """
        result = await tools.get_output(session, lines)
        return _format_output_result(result)

    @mcp.tool()
    async def reset(session: Optional[str] = None) -> str:
        """
        Reset/clear execution sessions.

        Closes the session and clears all state (variables, environment, history).
        If no session is specified, resets all sessions.

        Args:
            session: Session identifier to reset (optional, omit to reset all)

        Returns:
            Success message
        """
        result = await tools.reset(session)
        return _format_reset_result(result)

    logger.info(
        f"A0 Code Execution MCP Server initialized (executable: {config['executable']})"
    )

    return mcp


def _parse_init_commands(init_commands_str: str) -> list[str]:
    """Parse init commands from environment variable."""
    if not init_commands_str:
        return []

    commands = []
    for cmd in init_commands_str.replace("\n", ";").split(";"):
        cmd = cmd.strip()
        if cmd:
            commands.append(cmd)

    return commands


def _format_terminal_result(result: dict[str, Any]) -> str:
    """Format terminal execution result for display."""
    output_parts = []

    if result["success"]:
        output_parts.append(f"✓ Command executed successfully (session: {result['session']})")
    else:
        output_parts.append(f"✗ Command failed (session: {result['session']})")

    if result.get("output"):
        output_parts.append("\nOutput:")
        output_parts.append(result["output"])

    if result.get("error"):
        output_parts.append("\nError:")
        output_parts.append(result["error"])

    if result.get("timed_out"):
        output_parts.append("\n⚠ Command timed out")

    output_parts.append(f"\nExit code: {result.get('exit_code', 'unknown')}")

    return "\n".join(output_parts)


def _format_python_result(result: dict[str, Any]) -> str:
    """Format Python execution result for display."""
    output_parts = []

    if result["success"]:
        output_parts.append(f"✓ Python code executed successfully (session: {result['session']})")
    else:
        output_parts.append(f"✗ Python execution failed (session: {result['session']})")

    if result.get("output"):
        output_parts.append("\nOutput:")
        output_parts.append(result["output"])

    if result.get("error"):
        output_parts.append("\nError:")
        output_parts.append(result["error"])

    return "\n".join(output_parts)


def _format_output_result(result: dict[str, Any]) -> str:
    """Format output retrieval result for display."""
    if result["success"]:
        output_parts = [
            f"Session '{result['session']}' output ({result['lines_returned']} lines):",
            "",
            result["output"] if result["output"] else "(no output)",
        ]
        return "\n".join(output_parts)
    else:
        return f"Error retrieving output: {result.get('error', 'unknown error')}"


def _format_reset_result(result: dict[str, Any]) -> str:
    """Format reset result for display."""
    if result["success"]:
        return f"✓ {result['message']}"
    else:
        return f"✗ {result['message']}"


# Create the server instance
mcp = create_server()


def main() -> None:
    """Main entry point."""
    try:
        logger.info("Starting A0 Code Execution MCP Server (FastMCP)...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
