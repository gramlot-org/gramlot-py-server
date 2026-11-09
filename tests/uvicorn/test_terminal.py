from gramlot_py_server.uvicorn import create_application
from terminal_checks import TerminalChecks


class TestTerminal(TerminalChecks):
    create_application = staticmethod(create_application)
