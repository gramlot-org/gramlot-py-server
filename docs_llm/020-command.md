# 020 · The gramlot command

Document ID: **GP-020**.

[Paired view](../docs/020-command.md).

The package installs the command `gramlot`. Its form is environment first, then
verb: `gramlot <environment> <verb>`. The environments are the five adapters:
`uvicorn`, `django`, `flask`, `fastapi` and `kajenn`. There is no default
environment.

```sh
gramlot --help
gramlot django --help
gramlot django new --help
```

The npm package `@gramlot/gramlot-js-server` installs a command with the same
name, `gramlot`, for JavaScript pages
([gramlot-js-server](https://github.com/gramlot-org/gramlot-js-server)). The
two do not clash: this `gramlot` runs from the Python virtual environment where
the package is installed, and the npm `gramlot` runs through `npx` or
`node_modules/.bin`.

<a id="gp-020-005"></a>

## 005 · new: a project from the quick start

Block ID: **GP-020-005**.

`gramlot <environment> new <folder>` writes the quick start project of the
README into `folder`. The folder must not exist or must be empty; otherwise the
command stops with `<folder> exists and is not an empty folder` and writes
nothing.

| Environment | Files of the framework | Start command | Page |
| --- | --- | --- | --- |
| `uvicorn` | `app.py` | `uvicorn app:application` | <http://127.0.0.1:8000/> |
| `django` | `settings.py`, `urls.py` | `django-admin runserver --settings=settings --pythonpath=.` | <http://127.0.0.1:8000/> |
| `flask` | `app.py` | `flask --app app run --port 8000` | <http://127.0.0.1:8000/> |
| `fastapi` | `app.py` | `uvicorn app:app` | <http://127.0.0.1:8000/> |
| `kajenn` | `config.py` | `kajenn serve config.py --port 8000` | <http://127.0.0.1:8000/pages/> |

Every project also has:

- `requirements.txt`: `gramlot-py-server[<environment>]>=0.2.3`, and
  `gramlot-py-server[fastapi,uvicorn]>=0.2.3` for FastAPI, which needs a server;
- `pages/index.py`: the page, whose formula names the method `greeting`;
- `pages/index.js`: the page module, which exports `class Logic` with
  `greeting`. It runs in the browser.

The page has no inline code, so every project sends the strict Content
Security Policy profile. The command prints the files, the commands to install
and start the project, and the URL of the page:

```text
$ gramlot uvicorn new hello
Created hello for uvicorn:
  app.py
  requirements.txt
  pages/index.js
  pages/index.py
Start it:
  cd hello
  python -m pip install -r requirements.txt
  uvicorn app:application
Then open http://127.0.0.1:8000/
```

Flask starts on port 8000 like the other environments: on macOS the default
port of `flask run`, 5000, is taken by AirPlay Receiver. An existing project,
such as a Django site, needs no `new`: the guide of its framework shows how to
add the pages to it.

<a id="gp-020-010"></a>

## 010 · gallery: the examples served by the environment

Block ID: **GP-020-010**.

`gramlot <environment> gallery` serves the example gallery of
`gramlot-examples` with the adapter of the environment. It needs the extra
`gallery`, and FastAPI also needs Uvicorn:

```sh
python -m pip install "gramlot-py-server[django,gallery]"
gramlot django gallery
```

| Option | Default | Effect |
| --- | --- | --- |
| `--host HOST` | `127.0.0.1` | the address the server listens on |
| `--port PORT` | `8080` | the port the server listens on |
| `--mount PATH` | none | the prefix of every URL, for example `/py` |
| `--catalog CATALOG PAGES` | none | adds the families of a `catalog.json` and its pages folder; repeatable |
| `--serverless-download URL` | none | the URL of an offline gallery ZIP that the deployment serves; the gallery shows a footer link to it (section 030) |

The gallery lists the families of the `catalog.json` of `gramlot-examples`, as
the installed examples package defines them. Setup quick starts remain in this
server documentation and in the projects created by `gramlot <environment> new`;
they are not gallery sections or routes. Explicit `--catalog` extensions remain
supported. Without `--mount` the gallery is the site root, `/`. With
`--mount /py` the command prints `http://127.0.0.1:8080/py/`, `/py` answers 301
to `/py/`, and `/` answers 404: there is no redirect to the prefix.

The command stages one page per route in a temporary folder and serves it with
the `assets` of `build_gallery`, as described in
[GE-010 section 025](https://github.com/gramlot-org/gramlot-examples/blob/main/docs/010-gallery.md#ge-010-025)
of `gramlot-examples`:

- `index.py`: the gallery page, with the catalogues and with `logoUrl` and
  `galleryScript` under the prefix;
- `<key>.py`: the example page, which appends `<prefix>/gallery/dist/frame.js`
  so the example follows the theme of the gallery;
- `<key>.css`: the stylesheet of the example, when it has one;
- `<key>_aux.js`: `export {Logic} from "<prefix>/pages/<family>/<file>.js";`,
  the logic module of the example. The adapter serves that file as
  JavaScript.

The gallery sends no Content Security Policy: the examples use inline code. The
temporary folder is removed when the server stops.

<a id="gp-020-015"></a>

## 015 · Errors

Block ID: **GP-020-015**.

| Message | Cause |
| --- | --- |
| `gramlot django: asgiref is not installed. Install the extra: python -m pip install "gramlot-py-server[django]"` | the framework of the environment is missing; the module named is the first import that fails |
| `The gallery needs gramlot-examples: python -m pip install "gramlot-py-server[gallery]"` | `gallery` without the extra `gallery` |
| `gramlot fastapi gallery: uvicorn is not installed: python -m pip install "gramlot-py-server[uvicorn]"` | a gallery served by Uvicorn without it |
| `gramlot uvicorn new: hello exists and is not an empty folder` | `new` on a folder in use, or on a file |
| `argument environment: invalid choice` | an environment that is not registered |

A port in use stops the server of the framework with its own message: choose
another one with `--port`.

<a id="gp-020-020"></a>

## 020 · Environments are entry points

Block ID: **GP-020-020**.

`gramlot` reads the entry points of the group `gramlot_py_server.commands`. The
name of an entry point is an environment; its value is a function
`commands(verbs)` that adds the verbs of that environment to an
`argparse` subparsers object. Only the chosen environment is imported, so
`gramlot --help` needs no framework. This package declares:

```toml
[project.entry-points."gramlot_py_server.commands"]
uvicorn = "gramlot_py_server.uvicorn:commands"
django = "gramlot_py_server.django:commands"
flask = "gramlot_py_server.flask:commands"
fastapi = "gramlot_py_server.fastapi:commands"
kajenn = "gramlot_py_server.kajenn:commands"
```

Each verb sets `run` on its parser; `run(options)` returns the exit status. A
package that adds an adapter registers its environment the same way, and an
adapter adds a verb of its own in its `commands` without changing the others.
`gramlot_py_server.scaffold.add_new` and `gramlot_py_server.gallery.add_gallery`
add the two verbs of this package; `add_gallery` takes the function `serve` of
the adapter, which runs the server of the framework.

<a id="gp-020-025"></a>

## 025 · Update a packaged Python gallery

Block ID: **GP-020-025**.

Stop the running gallery. Activate the **same virtual environment** that runs it.
For Uvicorn and the common gallery:

```sh
python -m pip install --upgrade "gramlot-py-server[uvicorn,gallery]" gramlot gramlot-examples
python -m pip check
python -m pip show gramlot gramlot-examples gramlot-py-server
python -c "import sys, gramlot, gramlot_examples, gramlot_py_server; print(sys.executable); print(gramlot.__file__); print(gramlot_examples.__file__); print(gramlot_py_server.__file__)"
python -m gramlot_py_server.cli uvicorn gallery --port 8080
```

Keep your previous port/mount/catalog options. For another adapter, replace
`uvicorn` and its extra with that adapter; FastAPI also needs the `uvicorn` extra.
The explicit `python -m` start uses the interpreter just updated. Compare versions
with the repositories' READMEs, rather than expecting equal version numbers.

Name all three packages in the upgrade command: pip's default dependency strategy
is `only-if-needed`, so upgrading just the adapter may keep an older core or
examples package that still satisfies its minimum requirement. See
[pip's upgrade options](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-U).

**Published wheels contain the JavaScript bundles. No npm command is needed for
this route.** If the printed module paths point into repository checkouts, or you
use `PYTHONPATH`/editable installs, follow the
[source-checkout procedure](https://github.com/gramlot-org/gramlot-examples/blob/main/docs/010-gallery.md#ge-010-050)
instead; upgrading a wheel does not rebuild those source directories.

Reload the browser after restarting. Verify Publish/Subscribe and the inspector's
Styles tab using the [update checklist](https://github.com/gramlot-org/gramlot/blob/main/docs/public/018-quickstart.md#gc-018-025).
If a newer menu opens a 404 page, check that the old process really stopped and
that the browser uses the new process's port and mount path.


<a id="gp-020-030"></a>
## 030 · Hosted gallery download

Block ID: **GP-020-030**.

Hosted Python and Node galleries can display a footer link to a serverless ZIP.
Pass `--serverless-download /downloads/gramlot-gallery-serverless.zip` to
`gramlot uvicorn gallery` or `gramlot node gallery`. The deployment serves that
static file; the gallery does not generate an archive per request. Omit the option
when no archive is available. Custom gallery subclasses use
`serverless_download_url` (Python) or `serverlessDownloadUrl` (JavaScript).

Build the archive with `gramlot-serverless gallery OUTPUT`, include the complete
output directory, and tell users to unzip it and open `index.html`. Both hosted
galleries may serve the same artifact: Python server execution is not embedded in
the download; the serverless gallery uses the JavaScript equivalents and browser
Workers. Its named endpoints execute locally, without a Python or Node server.
