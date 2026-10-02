# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Run required lint, Django behavior tests and documentation checks."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "pytest", "tests"], cwd=ROOT, check=True)
    subprocess.run(
        [sys.executable, "-m", "sphinx", "-W", "--keep-going", "-b", "html",
         "docs", "docs/_build/html"], cwd=ROOT, check=True,
    )


if __name__ == "__main__":
    main()
