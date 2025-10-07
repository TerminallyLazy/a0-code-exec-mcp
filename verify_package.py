#!/usr/bin/env python3
"""
Package verification script
Checks that all required files and components are present
"""

import os
import sys
from pathlib import Path


def check_file(path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(path).exists():
        print(f"✓ {description}: {path}")
        return True
    else:
        print(f"✗ {description}: {path} (MISSING)")
        return False


def check_python_syntax(path: str) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(path) as f:
            compile(f.read(), path, 'exec')
        print(f"  ✓ Valid Python syntax: {path}")
        return True
    except SyntaxError as e:
        print(f"  ✗ Syntax error in {path}: {e}")
        return False


def main():
    """Run verification checks."""
    print("A0 Code Execution MCP - Package Verification")
    print("=" * 60)
    print()

    all_ok = True

    # Core Python files
    print("Core Python Files:")
    python_files = [
        ("src/ao_code_exec_mcp/__init__.py", "Package init"),
        ("src/ao_code_exec_mcp/server.py", "MCP server"),
        ("src/ao_code_exec_mcp/tools.py", "Tool implementations"),
        ("src/ao_code_exec_mcp/tty_session.py", "TTY session manager"),
        ("src/ao_code_exec_mcp/shell_local.py", "Shell session manager"),
    ]

    for path, desc in python_files:
        if check_file(path, desc):
            all_ok &= check_python_syntax(path)
        else:
            all_ok = False

    print()

    # Documentation files
    print("Documentation Files:")
    doc_files = [
        ("README.md", "Main README"),
        ("IMPLEMENTATION_NOTES.md", "Implementation notes"),
        ("src/ao_code_exec_mcp/prompts/system.md", "System prompt"),
        ("src/ao_code_exec_mcp/prompts/tool_response.md", "Response formats"),
    ]

    for path, desc in doc_files:
        all_ok &= check_file(path, desc)

    print()

    # Configuration files
    print("Configuration Files:")
    config_files = [
        ("pyproject.toml", "Package configuration"),
        ("mcp-config-example.json", "MCP config example"),
        (".gitignore", "Git ignore"),
        ("LICENSE", "License file"),
    ]

    for path, desc in config_files:
        all_ok &= check_file(path, desc)

    print()

    # Scripts
    print("Scripts:")
    script_files = [
        ("scripts/initialize_terminal.sh", "Terminal init script"),
    ]

    for path, desc in script_files:
        if check_file(path, desc):
            # Check if executable
            if os.access(path, os.X_OK):
                print(f"  ✓ Executable: {path}")
            else:
                print(f"  ✗ Not executable: {path}")
                all_ok = False
        else:
            all_ok = False

    print()

    # Check dependencies
    print("Python Dependencies:")
    dependencies = [
        ("mcp", "MCP SDK"),
        ("IPython", "IPython"),
        ("pexpect", "Pexpect"),
        ("psutil", "Psutil"),
    ]

    for module, desc in dependencies:
        try:
            __import__(module)
            print(f"✓ {desc} ({module}) is installed")
        except ImportError:
            print(f"✗ {desc} ({module}) is NOT installed")
            all_ok = False

    print()
    print("=" * 60)

    if all_ok:
        print("✓ All checks passed! Package is ready.")
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
