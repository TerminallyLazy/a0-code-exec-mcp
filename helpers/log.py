"""
Minimal log.py placeholder for MCP compatibility.
Provides no-op implementations of Log and LogItem classes used by Agent Zero.
"""

class LogItem:
    """Minimal placeholder for LogItem."""

    def __init__(self, guid=None, type="", heading="", content="", kvps=None, temp=False):
        self.guid = guid
        self.type = type
        self.heading = heading
        self.content = content
        self.kvps = kvps or {}
        self.temp = temp

    def update(self, heading=None, content=None, kvps=None):
        """Update log item - no-op for MCP."""
        if heading is not None:
            self.heading = heading
        if content is not None:
            self.content = content
        if kvps is not None:
            self.kvps.update(kvps)
        return self

    def stream(self, text):
        """Stream text to log item - no-op for MCP."""
        self.content += text
        return self


class Log:
    """Minimal placeholder for Log."""

    def __init__(self):
        self.items = []

    def log(self, type="", heading="", content="", kvps=None, temp=False):
        """Create a log entry - returns placeholder LogItem."""
        item = LogItem(type=type, heading=heading, content=content, kvps=kvps, temp=temp)
        self.items.append(item)
        return item

    def output(self, from_item=None):
        """Output log items - returns empty list for MCP."""
        return []

    def reset(self):
        """Reset log - no-op for MCP."""
        self.items = []
