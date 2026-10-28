"""Serve the isolated PageStore fixture with the selected adapter."""
from pathlib import Path
import sys
from importlib import import_module

if __name__ == "__main__":
    serve = import_module(f"gramlot_py_server.{sys.argv[1]}").serve
    serve(Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "page_store",
          host="127.0.0.1", port=int(sys.argv[2]), websocket=True, mount_path="/py")

