"""
Log - Simplified version ported from Agent Zero
Logging utilities for code execution tracking
"""

import logging

logger = logging.getLogger(__name__)


class LogItem:
    """
    Simplified log item for code execution tracking.
    Ported from Agent Zero's log.py - removed agent dependencies.
    """

    def __init__(self, log_type: str, heading: str = "", content: str = ""):
        self.type = log_type
        self.heading = heading
        self.content = content

    def update(self, type: str = None, heading: str = None, content: str = None, **kwargs):
        """Update log item."""
        if type:
            self.type = type
        if heading:
            self.heading = heading
        if content is not None:
            self.content = content


class Log:
    """
    Simplified logging for code execution.
    Ported from Agent Zero's log.py - removed agent context.
    """

    def __init__(self):
        self.items = []

    def log(self, type: str, heading: str = "", content: str = "", **kwargs) -> LogItem:
        """Create and return a new log item."""
        item = LogItem(type, heading, content)
        self.items.append(item)
        logger.debug(f"[{type}] {heading}: {content[:100] if content else ''}")
        return item
