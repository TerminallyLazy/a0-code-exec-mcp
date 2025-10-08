"""
PrintStyle - Simplified version ported from Agent Zero
Provides colored terminal output with styling
"""

import logging

import webcolors

logger = logging.getLogger(__name__)


class PrintStyle:
    """
    Styled text output for terminal.
    Simplified from Agent Zero's print_style.py - removed HTML logging and files.py dependency.
    """

    last_endline = True

    def __init__(
        self,
        bold=False,
        italic=False,
        underline=False,
        font_color="default",
        background_color="default",
        padding=False,
        log_only=False,
    ):
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.font_color = font_color
        self.background_color = background_color
        self.padding = padding
        self.padding_added = False
        self.log_only = log_only

    def _get_rgb_color_code(self, color, is_background=False):
        """Convert color name or hex to ANSI RGB code."""
        try:
            if color == "default":
                return ""

            if color.startswith("#") and len(color) == 7:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
            else:
                rgb_color = webcolors.name_to_rgb(color)
                r, g, b = rgb_color.red, rgb_color.green, rgb_color.blue

            if is_background:
                return f"\033[48;2;{r};{g};{b}m"
            else:
                return f"\033[38;2;{r};{g};{b}m"
        except (ValueError, AttributeError):
            return ""

    def _get_styled_text(self, text):
        """Apply ANSI styling to text."""
        start = ""
        end = "\033[0m"

        if self.bold:
            start += "\033[1m"
        if self.italic:
            start += "\033[3m"
        if self.underline:
            start += "\033[4m"

        start += self._get_rgb_color_code(self.font_color)
        start += self._get_rgb_color_code(self.background_color, True)

        return start + text + end

    def print(self, *args, sep=" ", **kwargs):
        """Print styled text with newline."""
        if self.padding and not self.padding_added:
            print()
            self.padding_added = True

        text = sep.join(map(str, args))
        styled = self._get_styled_text(text)

        if not self.log_only:
            print(styled, flush=True, **kwargs)

        PrintStyle.last_endline = True

    def stream(self, *args, sep=" ", **kwargs):
        """Stream styled text without newline."""
        text = sep.join(map(str, args))
        styled = self._get_styled_text(text)

        if not self.log_only:
            print(styled, end="", flush=True, **kwargs)

        PrintStyle.last_endline = False

    @staticmethod
    def standard(text: str):
        """Print standard text."""
        PrintStyle().print(text)

    @staticmethod
    def info(text: str):
        """Print info message."""
        PrintStyle(font_color="#0000FF", padding=True).print("Info: " + text)

    @staticmethod
    def success(text: str):
        """Print success message."""
        PrintStyle(font_color="#008000", padding=True).print("Success: " + text)

    @staticmethod
    def warning(text: str):
        """Print warning message."""
        PrintStyle(font_color="#FFA500", padding=True).print("Warning: " + text)

    @staticmethod
    def error(text: str):
        """Print error message."""
        PrintStyle(font_color="red", padding=True).print("Error: " + text)
