# 050 · Getting started

Document ID: **GD-050**.

This repository provides `gramlot_django`, the Django-specific integration.
Keep the current Gramlot 0.1.5 checkout at `../gramlot-poc`, then run:

```sh
uv sync --extra dev --extra docs
uv run python scripts/check.py
```

The committed `uv.lock` and `tool.uv.sources` select the local core explicitly.
The published Gramlot 0.1.0a1 lacks the required current interfaces; a normal
index-only installation is not supported yet. To use pip, install the prepared
local core first, then this repository:

```sh
python -m pip install -e ../gramlot-poc
python -m pip install -e '.[dev,docs]'
```

Core source installation requires its prepared browser assets as documented in
Gramlot. This package consumes those assets and does not build a second runtime.

Run the customer demonstration from `examples/` using the environment above;
see [example setup](https://github.com/gramlot-org/gramlot-django/blob/develop/examples/README.md). Bakery has additional Wagtail
requirements and its own [setup instructions](https://github.com/gramlot-org/gramlot-django/blob/develop/examples/bakerydemo/GRAMLOT.md).
See [the integration guide](035-django.md) to add pages to an existing project.
