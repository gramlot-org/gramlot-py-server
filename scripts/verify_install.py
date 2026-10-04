"""Check one environment from a clean install: gramlot new, the project, the gallery.

Usage: python scripts/verify_install.py ENVIRONMENT WHEEL PLAYWRIGHT_ENTRY [--port PORT] [ENGINE ...]

In a temporary virtual environment the script installs WHEEL with the extra of
ENVIRONMENT and the extra gallery (the core and gramlot-examples come from PyPI),
then:

1. ``gramlot ENVIRONMENT new project``;
2. ``pip install -r requirements.txt`` in the project, with the folder of WHEEL as
   ``--find-links``, so the requirement resolves to WHEEL;
3. the start command that ``new`` printed, then the page it printed in a real
   browser: it shows "Hello, Ada";
4. ``gramlot ENVIRONMENT gallery --mount /py``, then ``/py/e01`` and
   ``/py/ENVIRONMENT-01`` in a real browser.

``--port`` serves the project on PORT instead of the port of the printed command,
for a machine where that port is in use; without it the command runs as printed. Node.js runs scripts/verify_url_browser.mjs with PLAYWRIGHT_ENTRY.
"""

import argparse
import os
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER_CHECK = ROOT / "scripts" / "verify_url_browser.mjs"
EXTRAS = {"fastapi": "fastapi,uvicorn"}


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def with_port(environment, command, url, port):
    """The start command and the URL with ``port`` in place of the default port."""
    if re.search(r"--port \d+", command):
        command = re.sub(r"--port \d+", f"--port {port}", command)
    elif environment == "django":
        command = f"{command} {port}"
    else:
        command = f"{command} --port {port}"
    return command, re.sub(r":\d+/", f":{port}/", url, count=1)


def wait_for(url, process, log):
    for _ in range(200):
        if process.poll() is not None:
            raise SystemExit(f"The server exited with {process.returncode}:\n{log.read_text()}")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.1)
    raise SystemExit(f"{url} did not answer:\n{log.read_text()}")


def browse(playwright, engines, url, text):
    for engine in engines:
        subprocess.run(["node", str(BROWSER_CHECK), playwright, engine, url, text], check=True)


def serve(command, cwd, env, log, url, check):
    """Run ``command`` until ``check`` returns, then stop it."""
    with log.open("w") as output:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
    try:
        wait_for(url, process, log)
        check()
    finally:
        process.terminate()
        process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("environment")
    parser.add_argument("wheel", type=Path)
    parser.add_argument("playwright")
    parser.add_argument("engines", nargs="*", default=["chromium"])
    parser.add_argument("--port", type=int)
    options = parser.parse_args()
    environment, wheel = options.environment, options.wheel.resolve()
    with tempfile.TemporaryDirectory(prefix=f"gramlot-install-{environment}-") as temporary:
        folder = Path(temporary)
        venv = folder / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        bin_dir = venv / ("Scripts" if os.name == "nt" else "bin")
        env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "VIRTUAL_ENV": str(venv)}
        env.pop("PYTHONPATH", None)
        pip = [str(bin_dir / "python"), "-m", "pip", "install", "-q"]
        extras = EXTRAS.get(environment, environment)
        subprocess.run([*pip, f"{wheel}[{extras},gallery]"], check=True, env=env)
        created = subprocess.run(["gramlot", environment, "new", "project"], cwd=folder, env=env,
                                 check=True, capture_output=True, text=True).stdout
        lines = created.splitlines()
        command = lines[lines.index("  python -m pip install -r requirements.txt") + 1].strip()
        url = re.search(r"Then open (\S+)", created).group(1)
        project = folder / "project"
        subprocess.run([*pip, "-r", "requirements.txt", "--find-links", str(wheel.parent)],
                       cwd=project, check=True, env=env)
        if options.port:
            command, url = with_port(environment, command, url, options.port)
        print(f"{environment}: {command} -> {url}", flush=True)
        serve(shlex.split(command), project, env, folder / "project.log", url,
              lambda: browse(options.playwright, options.engines, url, "Hello, Ada"))
        port = free_port()
        gallery = f"http://127.0.0.1:{port}/py/"
        print(f"{environment}: gramlot {environment} gallery --mount /py --port {port}", flush=True)

        def check_gallery():
            browse(options.playwright, options.engines, gallery + "e01", "Hello, Gramlot!")
            browse(options.playwright, options.engines, f"{gallery}{environment}-01", "Hello, Ada")

        serve(["gramlot", environment, "gallery", "--mount", "/py", "--port", str(port)], folder, env,
              folder / "gallery.log", gallery, check_gallery)
    print(f"PASS {environment}: new, project and gallery from a clean install", flush=True)


if __name__ == "__main__":
    main()
