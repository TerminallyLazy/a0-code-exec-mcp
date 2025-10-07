#!/usr/bin/env python3
"""
A0 Code Execution MCP Server
Provides terminal and Python code execution tools via MCP protocol
"""

import asyncio
import logging
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .tools import CodeExecutionTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("ao-code-exec-mcp")


class A0CodeExecMCPServer:
    """MCP Server for A0 Code Execution Tools."""

    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("ao-code-exec-mcp")

        # Parse configuration from environment variables
        self.config = self._parse_config()

        # Initialize code execution tools
        self.tools = CodeExecutionTools(
            executable=self.config["executable"],
            init_commands=self.config["init_commands"],
            default_timeout=self.config["default_timeout"],
            first_output_timeout=self.config["first_output_timeout"],
        )

        # Setup MCP handlers
        self._setup_handlers()

        logger.info(
            f"A0 Code Execution MCP Server initialized "
            f"(executable: {self.config['executable']})"
        )

    def _parse_config(self) -> dict[str, Any]:
        """Parse configuration from environment variables."""
        # Detect platform defaults
        if sys.platform.startswith("win"):
            default_executable = os.environ.get("COMSPEC", "cmd.exe")
        else:
            default_executable = os.environ.get("SHELL", "/bin/bash")

        config = {
            "executable": os.environ.get("SHELL_EXECUTABLE", default_executable),
            "init_commands": self._parse_init_commands(
                os.environ.get("INIT_COMMANDS", "")
            ),
            "default_timeout": int(os.environ.get("TIMEOUT_DEFAULT", "30")),
            "first_output_timeout": int(os.environ.get("TIMEOUT_FIRST", "60")),
            "max_output_lines": int(os.environ.get("MAX_OUTPUT_LINES", "1000")),
        }

        logger.info(f"Configuration: {config}")
        return config

    def _parse_init_commands(self, init_commands_str: str) -> list[str]:
        """Parse init commands from environment variable."""
        if not init_commands_str:
            return []

        # Support both semicolon and newline-separated commands
        commands = []
        for cmd in init_commands_str.replace("\n", ";").split(";"):
            cmd = cmd.strip()
            if cmd:
                commands.append(cmd)

        return commands

    def _setup_handlers(self) -> None:
        """Setup MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="execute_terminal",
                    description=(
                        "Execute shell commands in a persistent terminal session. "
                        "Commands run in a stateful environment where environment variables, "
                        "working directory, and shell state persist between executions. "
                        "Use this for running bash/shell commands, system operations, "
                        "and command-line tools."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            },
                            "session": {
                                "type": "string",
                                "description": (
                                    "Session identifier for command execution. "
                                    "Commands in the same session share state."
                                ),
                                "default": "default",
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Command timeout in seconds",
                                "default": self.config["default_timeout"],
                            },
                        },
                        "required": ["command"],
                    },
                ),
                types.Tool(
                    name="execute_python",
                    description=(
                        "Execute Python code using IPython in a persistent session. "
                        "Code runs in a stateful environment where variables, imports, "
                        "and definitions persist between executions. "
                        "Use this for Python scripting, data analysis, calculations, "
                        "and algorithmic tasks. Supports all Python libraries and IPython features."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute",
                            },
                            "session": {
                                "type": "string",
                                "description": (
                                    "Session identifier for code execution. "
                                    "Code in the same session shares variables and state."
                                ),
                                "default": "default",
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Execution timeout in seconds",
                                "default": self.config["default_timeout"],
                            },
                        },
                        "required": ["code"],
                    },
                ),
                types.Tool(
                    name="output",
                    description=(
                        "Retrieve recent output from terminal or Python execution sessions. "
                        "Returns a buffer of recent command outputs and results. "
                        "Use this to review execution history or debug issues."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session": {
                                "type": "string",
                                "description": "Session identifier to retrieve output from",
                                "default": "default",
                            },
                            "lines": {
                                "type": "number",
                                "description": "Number of recent output lines to retrieve",
                                "default": 50,
                            },
                        },
                    },
                ),
                types.Tool(
                    name="reset",
                    description=(
                        "Reset/clear execution sessions. Closes the session and clears "
                        "all state (variables, environment, history). "
                        "If no session is specified, resets all sessions. "
                        "Use this to start fresh or recover from errors."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session": {
                                "type": "string",
                                "description": (
                                    "Session identifier to reset. "
                                    "If not specified, resets all sessions."
                                ),
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution requests."""
            arguments = arguments or {}

            try:
                if name == "execute_terminal":
                    result = await self.tools.execute_terminal(
                        command=arguments["command"],
                        session=arguments.get("session", "default"),
                        timeout=arguments.get("timeout"),
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=self._format_terminal_result(result),
                        )
                    ]

                elif name == "execute_python":
                    result = await self.tools.execute_python(
                        code=arguments["code"],
                        session=arguments.get("session", "default"),
                        timeout=arguments.get("timeout"),
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=self._format_python_result(result),
                        )
                    ]

                elif name == "output":
                    result = await self.tools.get_output(
                        session=arguments.get("session", "default"),
                        lines=arguments.get("lines", 50),
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=self._format_output_result(result),
                        )
                    ]

                elif name == "reset":
                    result = await self.tools.reset(
                        session=arguments.get("session"),
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=self._format_reset_result(result),
                        )
                    ]

                else:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Error: Unknown tool '{name}'",
                        )
                    ]

            except Exception as e:
                logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error executing {name}: {str(e)}",
                    )
                ]

    def _format_terminal_result(self, result: dict[str, Any]) -> str:
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

    def _format_python_result(self, result: dict[str, Any]) -> str:
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

    def _format_output_result(self, result: dict[str, Any]) -> str:
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

    def _format_reset_result(self, result: dict[str, Any]) -> str:
        """Format reset result for display."""
        if result["success"]:
            return f"✓ {result['message']}"
        else:
            return f"✗ {result['message']}"

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting A0 Code Execution MCP Server...")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ao-code-exec-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={},
                    ),
                ),
            )


def main() -> None:
    """Main entry point."""
    try:
        server = A0CodeExecMCPServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
