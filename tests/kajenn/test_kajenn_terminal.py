"""The terminal socket through Kajenn's native WebSocket."""
from terminal_checks import TerminalChecks
from test_kajenn_page_store import KajennChannelSites


class TestTerminal(KajennChannelSites, TerminalChecks):
    pass
