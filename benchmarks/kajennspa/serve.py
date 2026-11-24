import logging
import os
import socket
from pathlib import Path

import uvicorn
from kajenn import AsgiServer

if __name__ == "__main__":
    logging.getLogger("kajenn.auth_app.auth_app").setLevel(logging.ERROR)
    home = Path(os.environ["BENCH_HOME"])
    app = AsgiServer(config=str(Path(__file__).with_name("site_config.py")))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(256)
        (home / "port").write_text(str(sock.getsockname()[1]))
        uvicorn.Server(
            uvicorn.Config(
                app,
                ws="websockets-sansio",
                log_level="warning",
                access_log=False,
                timeout_graceful_shutdown=5,
            )
        ).run(sockets=[sock])
