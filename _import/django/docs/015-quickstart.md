# 015 · First Django page

Document ID: **GD-015**.

**Release status:** use the [GitHub preview installation](010-github-preview.md).
The adapter and compatible core candidate are not published on PyPI.

<a id="gd-015-005"></a>

## 005 · Install

Block ID: **GD-015-005**.

In your project's Python virtual environment, install the current experimental preview:

```sh
python -m pip install 'git+https://github.com/gramlot-org/gramlot-django.git@main'
```

The dependency installs include Django and Gramlot's Python APIs and complete
compiled JavaScript runtime. Node, npm, a CDN, and a separate JS download are
not part of the application setup. Normal Django configuration still belongs
to your project. Wagtail and the Bakery demonstration are not base dependencies.

<a id="gd-015-010"></a>

## 010 · Try the included demo

Block ID: **GD-015-010**.

Run `gramlot-django demo --open` to start Polls without creating a project.
See [Polls demo](020-polls-demo.md) for its data directory and port options.

<a id="gd-015-015"></a>

## 015 · Create a page

Block ID: **GD-015-015**.

In an existing Django project, make `pages/hello.py` beside `manage.py`:

```python
from gramlot.page import endpoint
from gramlot_django import DjangoPage


class Page(DjangoPage):
    def main(self, root):
        root.h1('Hello Gramlot')
        root.dataRpc('greeting', self.greet, _on_start=True)
        root.p('^greeting')

    @endpoint
    def greet(self):
        return 'This message came from Python.'
```

Add the collection to your normal root URLconf, before any catch-all routes:

```python
from django.conf import settings
from django.urls import include, path
from gramlot_django import DjangoPageCollection

pages = DjangoPageCollection(settings.BASE_DIR, prefix='/ui')
urlpatterns = [path('ui/', include(pages.urls))]
```

Keep `django.middleware.csrf.CsrfViewMiddleware` in your middleware. Retain
Django's session/authentication middleware when using request users and page
permissions. Existing project URL patterns belong alongside the new include.
No `gramlot_django` entry in `INSTALLED_APPS` is needed for this integration.

Start the normal Django server and open `/ui/hello/`:

```sh
python manage.py runserver
```

<a id="gd-015-020"></a>

## 020 · Complete minimal project

Block ID: **GD-015-020**.

The repository's `examples/quickstart/` contains `manage.py`, settings, URLconf
and a page demonstrating binding, Data RPC, remote Source and the code editor.
Copy it into your own directory, activate the environment containing the
installed packages, and run:

```sh
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/tools/ui/hello/`. This example uses `DEBUG=False` and
a nested prefix. Its local demonstration key and allowed hosts must be replaced
for a real deployment. No database migration is needed by this particular page;
your own Django models still use Django's normal migration process.

<a id="gd-015-025"></a>

## 025 · Asset delivery and production

Block ID: **GD-015-025**.

The included runtime URLs serve the installed, versioned assets even with
`DEBUG=False`; `collectstatic` and an external CDN are not required for this path.
Your deployment can offload static delivery separately. Preserve matching
manifest URLs, MIME types and immutable cache behavior if you do so. Never mix
files from different browser builds.

The Python package and standalone GitHub ZIP carry the same browser payload.
Django uses the installed Python package by default. Existing-project templates,
authentication, ORM helpers and limits are documented in [the adapter guide](035-django.md).
