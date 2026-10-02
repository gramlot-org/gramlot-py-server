# 020 · Run the Polls demo

Document ID: **GD-020**.

The package includes a Django Polls site with ordinary server-rendered pages and a
Python-authored Gramlot SPA embedded in its shared site template. After installing the package, run:

```sh
gramlot-django demo
```

`gramlot-django demo polls` is equivalent. Open
`http://127.0.0.1:8064/polls/`, open a question, select an answer and submit the Django form to see results.
Use **Interactive workspace** in the site navigation to enter the Gramlot SPA.
The site header remains present and both routes use the same questions and votes.
Votes are stored in SQLite and survive restarts. This local demonstration allows
repeat votes; it is not an authenticated election application.

The launcher runs Django migrations, adds the initial question and choices if
missing, and starts Django's development server on the loopback interface.
Restarting does not reset votes or duplicate the initial records. Stop it with
Ctrl-C. The demo is included in the wheel: no checkout, Node, Wagtail or separate
JavaScript download is required.

<a id="gd-020-005"></a>

## 005 · Site structure

Block ID: **GD-020-005**.

- `/polls/`: Django question list.
- `/polls/<id>/`: Django voting form with CSRF protection.
- `/polls/<id>/results/`: Django results page after a normal POST/redirect.
- `/polls/spa/polls/`: Gramlot SPA within the Polls base template and navigation.

The host site uses ordinary Django views and templates following the Polls
application structure. It is a local implementation, not a verbatim copy of the
Django tutorial repository. Additional SPA pages belong in the collection's
`pages/` directory; the rest of the host site's routes continue to work normally.

<a id="gd-020-010"></a>

## 010 · Options

Block ID: **GD-020-010**.

```sh
gramlot-django demo polls --port 8070 --open
gramlot-django demo --data-dir /path/to/my-polls-data
```

- `--port`: local port, default `8064`.
- `--open`: also open the page in your default browser.
- `--data-dir`: persistent database directory, default `~/.gramlot-django/polls`.
  The launcher prints its location. Use a new directory for an independent demo.

The launcher works from any directory and writes no database into site-packages.
Its settings and example secret are for local demonstration. Existing Django
applications continue to use their own `manage.py` and settings.

Bakery still uses its separate [setup instructions](https://github.com/gramlot-org/gramlot-django/blob/develop/examples/bakerydemo/GRAMLOT.md).
Use `gramlot-django demo bakery --project-dir PATH` after installing its separate
dependencies; see [Bakery demo](025-bakery-demo.md).

<a id="gd-020-015"></a>

## 015 · Development and verification

Block ID: **GD-020-015**.

From an environment containing the development checkout, the same CLI is also
available as `python -m gramlot_django.cli demo`. After adding/updating console
entry points, reinstall the editable package to refresh the command executable.

The installed-package CI starts the actual console command outside the checkout.
Its browser test blocks off-site requests, casts a vote through the Django form, opens the embedded SPA, casts another
vote and verifies both counts through the ordinary Django results page. Behavior tests check seeding,
migrations, CSRF and rejection of votes for unpublished questions.
