"""The terminal socket through Kajenn's native WebSocket."""
from terminal_checks import TerminalChecks
from test_kajenn_page_store import _Site


class TestTerminal(TerminalChecks):
    create_application = staticmethod(_Site)
