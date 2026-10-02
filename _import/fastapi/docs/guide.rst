FastAPI integration
===================

Historical PoC guide. ``GramlotApplication`` and ``mount_gramlot`` below
require modules absent from clean Gramlot 0.1.0. The current native path uses
``NativeHtmlApplication`` or ``mount_native_html``; see :doc:`getting-started`
and :doc:`050-native-html`.

Choose the amount of server code you need
-----------------------------------------

In this historical profile, ``gramlot-fastapi serve [directory]`` starts the host.
The adapter creates FastAPI and starts Uvicorn. You only author pages.

For a customized FastAPI application, create ``main.py`` at the application root:

.. code-block:: python

   from gramlot_fastapi import GramlotApplication

   app = GramlotApplication()

   @app.get('/health')
   def health():
       return {'status': 'ok'}

Run it from that root with ``uvicorn main:app``. ``GramlotApplication`` is a
FastAPI subclass; normal endpoint decorators, middleware registration and
FastAPI options remain available. The directory default is the working
directory, not the directory containing the calling Python file.

The discovery CLI does not load your custom ``main.py``. Use Uvicorn explicitly
when you want to execute that application module.

Integrate with an existing application
--------------------------------------

.. code-block:: python

   from fastapi import FastAPI
   from gramlot_fastapi import mount_gramlot

   app = FastAPI()
   mount_gramlot(app, directory='/srv/catalogue', prefix='/catalogue')
   mount_gramlot(app, directory='/srv/help', prefix='/help')

Each application root contains its own ``pages/`` directory. Each registration
has a separate page collection. Choose distinct prefixes and avoid collisions
with your existing routes. This registration is not the same operation as
mounting the whole Gramlot application below another ASGI URL prefix.

What happens after a request
----------------------------

1. At startup, the adapter discovers Page classes and registers routes and
   packaged static assets. It has not run the page's ``main`` yet.
2. ``GET /page/hello/`` checks the registry and returns an HTML shell containing
   a root element, an import map, startup data and the shared JavaScript entry.
3. The browser loads runtime modules and fetches ``/page/hello/recipe``.
4. The adapter creates a new Page and builder, calls ``main(root)``, then
   returns the Source tree as ``application/vnd.tytx+json``.
5. The browser decodes TYTX, loads the Source into the JavaScript builder and
   mounts it using the runtime Application. That creates the visible DOM.

The index follows the same shell/recipe flow. Its recipe builds the navigation
from the discovered files. Links navigate to full documents; this adapter does
not add a client-side router. This is not server-side HTML rendering of page
content, so do not assume content is in the initial HTML for crawlers.

Where the shared code lives
---------------------------

.. list-table:: Read the implementation in this order
   :header-rows: 1
   :widths: 45 55

   * - File
     - Responsibility
   * - ``src/gramlot_fastapi/__main__.py``
     - Command parsing and optional Uvicorn startup
   * - ``gramlot_fastapi/application.py``
     - FastAPI subclass, page collection, discovery and request methods
   * - ``gramlot_fastapi/runtime.py``
     - Wheel asset locations, URL mapping and import map constants
   * - ``gramlot.contrib._shared`` in Gramlot
     - Host-independent page registry, document rendering and runtime discovery

Constants describe conventions shared by applications. Instance properties
hold application configuration and discovered classes. Page and builder local
variables belong to a single request. ``PageCollection`` is separate from
FastAPI so its method names do not override FastAPI methods.

Supported scope
---------------

The current adapter supports pages, packaged resources, startup recipes and
role-checked Data and Source RPC. It does not retain sessions or configure
authentication. Custom FastAPI applications remain free to provide their own
endpoints and middleware.

Browser deployment under a reverse-proxy subpath or a parent ASGI mount
(``root_path``) is not supported yet; generated URLs assume registration at
the server root with the configured page prefix. The default local command is
a development entry point, not a production deployment recipe.

See :doc:`reference` for constructor options and routes.
