# 025 · Bakery demonstration

Document ID: **GD-025**.

Bakery is the main integration showcase: an existing Wagtail site with its own
pages, navigation, media and CMS, extended with Gramlot SPA pages.
The original project is [wagtail/bakerydemo](https://github.com/wagtail/bakerydemo).
The adapted snapshot and upstream license are in `examples/bakerydemo`.

<a id="gd-025-005"></a>

## 005 · Install and run

Block ID: **GD-025-005**.

Bakery is separate from the lightweight installed Polls demo. In a dedicated
Python 3.12+ environment, install the compatible Gramlot and gramlot-django
packages (currently local candidates), then the local demo requirements:

```sh
python -m pip install -r examples/bakerydemo/requirements/local.txt
gramlot-django demo bakery --project-dir examples/bakerydemo --open
```

This starts at `http://127.0.0.1:8063/`. Select **Explore breads** in the site's
navigation to enter the public Gramlot SPA inside the Bakery template. Wagtail
pages remain available normally. Below the explorer, **Python source**
opens the actual `explore.py` source in a read-only Python CodeMirror editor.
The small magnifier beside it opens the native Gramlot inspector. Styling is a
Django static file loaded by the host template; Python methods describe the data
and interface. The SPA dashboard is at `/spa_admin/` and
requires the demo login; the supplied local demo credentials are `admin` /
`changeme`.

Use `--port 8065` if another demo occupies port 8063. Use `--data-dir PATH` to
choose persistent demo storage; the default is `~/.gramlot-django/bakery`.
The launcher restores the bundled SQL archive into a new database on first use,
runs migrations and starts the standard Django development server on loopback.
It never replaces an existing database. Images and static resources come from
the supplied project directory; it must remain available while the server runs.

When run from this repository's editable installation, `--project-dir` can be
omitted. An installed wheel requires the adapted project directory explicitly:
it does not include the large Bakery source/media snapshot or install Wagtail.
No repository downloads or cloud/production dependencies are added by the CLI.

Polls remains available with `gramlot-django demo polls` as a small install test.

<a id="gd-025-010"></a>

## 010 · Reactive product services

Block ID: **GD-025-010**.

Explore first declares its visual blocks, then fills each grid block with an
explicit `GridStruct` and a named `rpcStore`. Endpoints return rows through
`DjangoPage.selection_result`; the collection store builds the browser Bag.
The products store follows the selected category and selects its first result
with `_onResult`. A `dataRpc` loads the selected product's details, using `_delay`
to coalesce the selection reset and the new key. Detail fields bind to `detail`.
Every query remains scoped to the current Wagtail site's published breads.

With the seeded demo running, use the optional Playwright runner to check real
category/selection RPCs and the source viewer:

```sh
python scripts/verify_bakery.py --url http://127.0.0.1:8065
```
