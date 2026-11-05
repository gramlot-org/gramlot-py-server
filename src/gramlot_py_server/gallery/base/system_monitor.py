"""Local system demo: python -m gramlot_py_server.gallery.base.system_monitor."""

import argparse
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from gramlot_py_server.uvicorn import serve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8904)
    parser.add_argument(
        "--gallery",
        action="store_true",
        help="Open the lesson with explanation and Python source",
    )
    args = parser.parse_args()
    page = files("gramlot_examples").joinpath(
        "base/pages/86-system-analysis/system_analysis.py"
    )
    with TemporaryDirectory(prefix="gramlot-system-") as folder:
        if args.gallery:
            from gramlot_py_server.gallery import stage

            examples = Path(str(files("gramlot_examples")))
            catalogs = [
                (examples / "base/system-monitor-catalog.json", examples / "base/pages")
            ]
            assets = stage(Path(folder), catalogs, "")
            serve(
                folder, host="127.0.0.1", port=args.port, assets=assets, websocket=True
            )
            return

        (Path(folder) / "index.py").write_text(page.read_text())
        (Path(folder) / "audio.py").write_text(
            page.parent.joinpath("audio_spectrum.py").read_text()
        )
        serve(folder, host="127.0.0.1", port=args.port, websocket=True)


if __name__ == "__main__":
    main()
