# Getting started

This repository is a pre-alpha scaffold for gramlot applications hosted by genro asgi.
It does not yet expose a server command or a runnable application.

From the repository root:

```sh
uv sync --extra dev --extra docs
uv run python scripts/check.py
uv run python -m build
```

The source namespace is `gramlot_genro_asgi`. The development environment uses the committed
`uv.lock`; runtime host dependencies will be introduced with the first profile.
