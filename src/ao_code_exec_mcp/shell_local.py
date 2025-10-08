import re
from typing import Optional, Tuple
from . import tty_session


def clean_string(input_string):
    """Clean ANSI escape codes and control characters from terminal output."""
    # Remove ANSI escape codes
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    cleaned = ansi_escape.sub("", input_string)

    # remove null bytes
    cleaned = cleaned.replace("\x00", "")

    # remove ipython \r\r\n> sequences from the start
    cleaned = re.sub(r'^[ \r]*(?:\r*\n>[ \r]*)*', '', cleaned)
    # also remove any amount of '> ' sequences from the start
    cleaned = re.sub(r'^(>\s*)+', '', cleaned)

    # Replace '\r\n' with '\n'
    cleaned = cleaned.replace("\r\n", "\n")

    # remove leading \r and spaces
    cleaned = cleaned.lstrip("\r ")

    # Split the string by newline characters to process each segment separately
    lines = cleaned.split("\n")

    for i in range(len(lines)):
        # Handle carriage returns '\r' by splitting and taking the last part
        parts = [part for part in lines[i].split("\r") if part.strip()]
        if parts:
            lines[i] = parts[
                -1
            ].rstrip()  # Overwrite with the last part after the last '\r'

    return "\n".join(lines)

class LocalInteractiveSession:
    def __init__(self):
        self.session: tty_session.TTYSession|None = None
        self.full_output = ''

    async def connect(self):
        self.session = tty_session.TTYSession("/bin/bash")
        await self.session.start()
        await self.session.read_full_until_idle(idle_timeout=1, total_timeout=1)

    async def close(self):
        if self.session:
            self.session.kill()
            # self.session.wait()

    async def send_command(self, command: str):
        if not self.session:
            raise Exception("Shell not connected")
        self.full_output = ""
        await self.session.sendline(command)
 
    async def read_output(self, timeout: float = 0, reset_full_output: bool = False) -> Tuple[str, Optional[str]]:
        if not self.session:
            raise Exception("Shell not connected")

        if reset_full_output:
            self.full_output = ""

        # get output from terminal
        partial_output = await self.session.read_full_until_idle(idle_timeout=0.01, total_timeout=timeout)
        self.full_output += partial_output

        # clean output
        partial_output = clean_string(partial_output)
        clean_full_output = clean_string(self.full_output)

        if not partial_output:
            return clean_full_output, None
        return clean_full_output, partial_output