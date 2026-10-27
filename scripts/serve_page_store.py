"""Serve the isolated PageStore fixture with Uvicorn on localhost."""
from pathlib import Path
import sys
from gramlot_py_server.uvicorn import serve

if __name__ == "__main__":
    serve(Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "page_store",
          host="127.0.0.1", port=int(sys.argv[1]), websocket=True, mount_path="/py")

