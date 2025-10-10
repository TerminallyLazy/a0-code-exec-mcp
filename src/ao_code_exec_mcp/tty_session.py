"""
TTY Session Manager - Ported from Agent Zero
Async pseudo-terminal session management for shell command execution
"""

import asyncio
import os
import platform
import time

try:
    if platform.system() == "Windows":
        import winpty
except ImportError:
    winpty = None


class TTYSession:
    """
    Async TTY session management ported from Agent Zero.
    Handles terminal sessions with proper echo control and output capture.
    """

    def __init__(self, executable: str = "/bin/bash"):
        self.executable = executable
        self.process = None
        self.is_windows = platform.system() == "Windows"
        self.use_pty = True

    async def start(self):
        """Start the TTY session."""
        if self.is_windows:
            await self._start_windows()
        else:
            await self._start_posix()

    async def _start_windows(self):
        """Start Windows TTY session."""
        if winpty is None:
            raise RuntimeError(
                "pywinpty is required for Windows support. Install with: pip install pywinpty"
            )

        self.process = winpty.PtyProcess.spawn(self.executable)
        await asyncio.sleep(0.1)

    async def _start_posix(self):
        """Start POSIX TTY session with fallback to non-PTY subprocess."""
        import fcntl
        import logging

        logger = logging.getLogger(__name__)

        force_no_pty = os.environ.get("FORCE_NO_PTY", "").lower() in (
            "1",
            "true",
            "yes",
        )

        if not force_no_pty:
            try:
                import pty
                import struct
                import termios

                master_fd, slave_fd = pty.openpty()

                self.process = await asyncio.create_subprocess_exec(
                    self.executable,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    preexec_fn=os.setsid,
                )

                os.close(slave_fd)
                self.master_fd = master_fd

                fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)

                winsize = struct.pack("HHHH", 24, 80, 0, 0)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

                await asyncio.sleep(0.1)

                await self.sendline("stty -echo")
                await asyncio.sleep(0.1)
                await self.read_full_until_idle(idle_timeout=0.5, total_timeout=2)

                self.use_pty = True
                logger.info("TTY session started with PTY")
                return
            except (OSError, ImportError) as e:
                logger.info(f"PTY allocation failed ({e}), falling back to subprocess mode")

        self.use_pty = False
        self.process = await asyncio.create_subprocess_exec(
            self.executable,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        logger.info("TTY session started in non-PTY subprocess mode")
        await asyncio.sleep(0.1)

    async def sendline(self, command: str):
        """Send a command to the terminal."""
        if self.is_windows:
            self.process.write(command + "\r\n")
        elif self.use_pty:
            os.write(self.master_fd, (command + "\n").encode("utf-8", errors="replace"))
        else:
            self.process.stdin.write((command + "\n").encode("utf-8", errors="replace"))
            await self.process.stdin.drain()

    async def read_full_until_idle(
        self, idle_timeout: float = 0.5, total_timeout: float = 30
    ) -> str:
        """Read output until idle or timeout."""
        output = ""
        start_time = time.time()
        last_output_time = start_time

        while True:
            current_time = time.time()

            if current_time - start_time > total_timeout:
                break

            if current_time - last_output_time > idle_timeout:
                break

            try:
                if self.is_windows:
                    chunk = self.process.read(1024)
                elif self.use_pty:
                    chunk = os.read(self.master_fd, 4096).decode("utf-8", errors="replace")
                else:
                    chunk_bytes = await asyncio.wait_for(
                        self.process.stdout.read(4096), timeout=0.1
                    )
                    if chunk_bytes:
                        chunk = chunk_bytes.decode("utf-8", errors="replace")
                    else:
                        chunk = None

                if chunk:
                    output += chunk
                    last_output_time = current_time
                else:
                    await asyncio.sleep(0.01)
            except (OSError, BlockingIOError, asyncio.TimeoutError):
                await asyncio.sleep(0.01)
            except Exception:
                break

        return output

    async def close(self):
        """Close the TTY session."""
        if self.is_windows:
            if self.process:
                self.process.terminate()
        else:
            if self.process:
                if not self.use_pty and self.process.stdin:
                    self.process.stdin.close()

                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    self.process.kill()

            if self.use_pty and hasattr(self, "master_fd"):
                os.close(self.master_fd)
