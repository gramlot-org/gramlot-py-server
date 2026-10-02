gramlot-py-server
=================

.. image:: _static/gramlot-logo.png
   :width: 160
   :alt: Gramlot

Python server adapters for Gramlot pages: Uvicorn, Django, Flask, FastAPI and
Kajenn. Gramlot describes web interfaces in Python or JavaScript and keeps them
bound to application state in the browser; see `The Gramlot family
<https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html>`_ for
the core and the other repositories. This package serves a folder of Python
``Page`` modules from the web framework of your choice, with one adapter module
and one extra per framework.

.. toctree::
   :maxdepth: 2
   :caption: Common

   005-introduction
   010-writing-pages
   015-troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Uvicorn

   105-tutorial
   110-configuration
   115-deployment
   120-reference

.. toctree::
   :maxdepth: 2
   :caption: Django

   205-django

.. toctree::
   :maxdepth: 2
   :caption: Flask

   305-flask

.. toctree::
   :maxdepth: 2
   :caption: FastAPI

   405-fastapi

.. toctree::
   :maxdepth: 2
   :caption: Kajenn

   505-kajenn

The concise view lives in the repository's docs_llm directory. The internal
notes (GP-905, GP-910) live in docs/internal and are not part of this manual.
