Gramlot FastAPI
===============

Python-first native HTML Gramlot Pages hosted by FastAPI.
The 0.1.0 entry points are ``NativeHtmlApplication`` and
``mount_native_html``. Core and adapter artifacts are local release candidates.
Older PoC examples and database guides remain historical material.

Start with :doc:`getting-started` for the native launch path and
:doc:`050-native-html` for its contract. :doc:`first-page` describes the
historical PoC CLI, outside native 0.1.0.

For historical database experiments, see :doc:`035-sqlalchemy`. Native 0.1.0
does not include a database integration.

`Browse the source code <https://github.com/gramlot-org/gramlot-fastapi/tree/main/src/gramlot_fastapi>`_
· `Concise documentation for LLMs <https://github.com/gramlot-org/gramlot-fastapi/tree/main/docs_llm>`_

.. toctree::
   :maxdepth: 1
   :caption: Start here

   005-overview
   getting-started
   first-page

.. toctree::
   :maxdepth: 1
   :caption: Integration

   guide
   025-inspector
   045-showcase
   035-sqlalchemy
   reference
   010-architecture
   040-server-and-database-integration
   050-native-html

.. toctree::
   :maxdepth: 1
   :caption: Contributing and POC records

   015-documentation
   030-readthedocs
   020-release
